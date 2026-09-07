"""엔진 객체 `Engine` 과 `build_engine` (SPEC 4장).

`fdt/engine/**` 는 파일·콘솔 I/O 를 하지 않는다(SPEC 4.2-7). `Engine.save`/
`Engine.load` 로 표기된 SPEC 4.1 의 기능은 이 모듈에 없다 - 대신
`Engine.to_dict()`/`Engine.from_dict()` 만 여기 두고, 실제 파일 읽기·쓰기는
`fdt/tools/engine_io.py` 의 `save_engine`/`load_engine` 이 담당한다.

공개 이름 (다른 작업 ID 가 import 하는 계약): `Engine`, `EngineBuildMeta`,
`build_engine`.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import date
from datetime import time as dt_time
from typing import Any

from pydantic import ValidationError

import fdt
from fdt.engine.behavior import detect_income_schedule, estimate_behavior
from fdt.engine.errors import (
    E_ENGINE_ID_MISMATCH,
    E_MODE_NOT_IMPLEMENTED,
    E_REQ_INVALID,
    E_REQ_RANGE,
    W_INPUT_FUTURE_TX,
    W_INPUT_SHORT_HISTORY,
    FdtError,
    FdtWarning,
)
from fdt.engine.ledger import LedgerTx, history_days, normalize, reconcile
from fdt.engine.modes import MODE_RUNNERS
from fdt.engine.schemas.behavior import Behavior
from fdt.engine.schemas.input import Externals, TwinInput
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.schemas.result import EngineError as ResultEngineError
from fdt.engine.schemas.result import EngineMeta as ResultEngineMeta
from fdt.engine.schemas.result import EngineResult
from fdt.engine.schemas.state import State
from fdt.engine.state import build_state_with_warnings
from fdt.engine.taxonomy import ConfirmStatus, ExcludeTag, Flow

__all__ = ["Engine", "EngineBuildMeta", "build_engine"]

# 두 파트를 이어붙일 때 값 안에 등장할 수 없는 구분자(유닛 구분 문자)를 써서
# "twin json" + "as_of" + "budgets_override json" 세 조각이 우연히 같은
# 바이트열로 겹치지 않게 한다.
_ID_SEP = "␟"


@dataclass(frozen=True, slots=True)
class EngineBuildMeta:
    """`Engine.meta` (SPEC 4.1). `built_at` 은 재현성을 위해 두지 않는다.

    `budgets_override` 는 SPEC 4.1 표에는 없지만, `Engine.from_dict` 가
    `engine_id` 를 재계산해 검증하려면 빌드 시점에 쓰인 예산 재정의 값이
    필요해서 여기 보관한다(엔진 필드 자체는 아니고 메타 정보로 취급).
    """

    engine_id: str
    as_of: date
    schema_version: str = "engine/1"
    engine_version: str = fdt.__version__
    warnings: list[FdtWarning] = field(default_factory=list)
    budgets_override: dict[int, int] | None = None


def _compute_engine_id(
    twin: TwinInput, as_of: date, budgets_override: dict[int, int] | None
) -> str:
    """`twin.model_dump_json() + as_of + budgets_override` 를 sha256 해 앞
    12자를 쓴다 (SPEC 4.1 "engine_id(입력 해시 12자)")."""

    parts = [
        twin.model_dump_json(),
        as_of.isoformat(),
        json.dumps(budgets_override or {}, sort_keys=True),
    ]
    blob = _ID_SEP.join(parts).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


def _ledger_tx_to_dict(tx: LedgerTx) -> dict[str, Any]:
    payload = asdict(tx)
    payload["date"] = tx.date.isoformat()
    payload["time"] = tx.time.isoformat()
    # Flow/ExcludeTag/ConfirmStatus 는 StrEnum(문자열 서브클래스)라 asdict 가
    # 이미 JSON 직렬화 가능한 값을 담고 있다. 명시적으로 str 로 고정해
    # 저장된 JSON 이 항상 순수 문자열이 되도록 한다.
    payload["flow"] = str(tx.flow.value)
    payload["exclude_tag"] = str(tx.exclude_tag.value)
    payload["confirm_status"] = str(tx.confirm_status.value)
    return payload


def _ledger_tx_from_dict(payload: dict[str, Any]) -> LedgerTx:
    return LedgerTx(
        id=payload["id"],
        date=date.fromisoformat(payload["date"]),
        time=dt_time.fromisoformat(payload["time"]),
        account_id=payload["account_id"],
        card_id=payload["card_id"],
        signed_amount=payload["signed_amount"],
        flow=Flow(payload["flow"]),
        envelope_id=payload["envelope_id"],
        subcategory_id=payload["subcategory_id"],
        confidence=payload["confidence"],
        source=payload["source"],
        merchant_name_raw=payload["merchant_name_raw"],
        exclude_tag=ExcludeTag(payload["exclude_tag"]),
        confirm_status=ConfirmStatus(payload["confirm_status"]),
        origin_tx_id=payload["origin_tx_id"],
        counterparty_account_id=payload["counterparty_account_id"],
    )


@dataclass
class Engine:
    """엔진 객체 (SPEC 4.1). `build_engine` 으로만 만든다.

    `ledger` 는 정규화된 불변 원장(SPEC 4.2-4), `state` 는 as_of 스냅샷,
    `behavior` 는 원장에서 추정한 행동 모델, `externals` 는 twin 이 담고
    있던 외부 변수의 사본이다. `twin` 은 원본을 그대로 들고 있고 이 클래스
    누구도 이를 수정하지 않는다(불변 취급).
    """

    meta: EngineBuildMeta
    twin: TwinInput
    ledger: tuple[LedgerTx, ...]
    state: State
    behavior: Behavior
    externals: Externals

    def fork(self) -> Engine:
        """What-if 용 얕은 복제 (SPEC 4.1). 원장은 공유(불변), state 만 깊은 복사."""

        return Engine(
            meta=self.meta,
            twin=self.twin,
            ledger=self.ledger,
            state=self.state.model_copy(deep=True),
            behavior=self.behavior,
            externals=self.externals,
        )

    def run(self, req: ModeRequest) -> EngineResult:
        """모드 디스패치 (SPEC 8~9장).

        이번 단계에는 `fdt.engine.modes.MODE_RUNNERS` 가 비어 있으므로 모든
        요청이 `E-MODE-NOT_IMPLEMENTED` 오류로 끝난다. 러너가 등록되면
        `runner(self, req)` 가 모드별 `ResultUnion` 하나를 만들어 낸다.
        측정에는 SPEC 4.2-2 가 허용하는 `time.perf_counter()` 만 쓴다.
        """

        start = time.perf_counter()
        result = None
        error: ResultEngineError | None = None
        status: str = "OK"
        try:
            runner = MODE_RUNNERS.get(req.mode)
            if runner is None:
                raise FdtError(
                    code=E_MODE_NOT_IMPLEMENTED,
                    details={"mode": req.mode.value},
                )
            result = runner(self, req)
        except FdtError as exc:
            status = "ERROR"
            error = ResultEngineError(code=exc.code, message=exc.message, details=exc.details)
        except ValidationError as exc:
            status = "ERROR"
            error = ResultEngineError(
                code=E_REQ_INVALID,
                message=str(exc),
                details={
                    "errors": [
                        {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
                        for e in exc.errors()
                    ]
                },
            )

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        result_meta = ResultEngineMeta(
            engine_id=self.meta.engine_id,
            as_of=self.meta.as_of,
            mode=req.mode,
            seed=req.seed,
            n_paths=req.n_paths,
            horizon_days=req.horizon_days,
            elapsed_ms=elapsed_ms,
            engine_version=self.meta.engine_version,
            warnings=[asdict(w) for w in self.meta.warnings],
        )
        return EngineResult(
            meta=result_meta,
            request=req,
            result=result,
            facts=[],
            viz=[],
            status=status,  # type: ignore[arg-type]
            error=error,
        )

    def to_dict(self) -> dict[str, Any]:
        """JSON 직렬화 가능한 dict (SPEC 4.1 "Engine.save" 가 쓰는 내용).

        파일에 쓰는 일은 이 메서드가 하지 않는다 - 반환값을 어디에 쓸지는
        `fdt/tools/engine_io.py` 몫이다.
        """

        return {
            "schema_version": self.meta.schema_version,
            "meta": {
                "engine_id": self.meta.engine_id,
                "as_of": self.meta.as_of.isoformat(),
                "schema_version": self.meta.schema_version,
                "engine_version": self.meta.engine_version,
                "warnings": [asdict(w) for w in self.meta.warnings],
                "budgets_override": self.meta.budgets_override,
            },
            "twin": json.loads(self.twin.model_dump_json()),
            "ledger": [_ledger_tx_to_dict(tx) for tx in self.ledger],
            "state": self.state.model_dump(mode="json"),
            "behavior": self.behavior.model_dump(mode="json"),
            "externals": self.externals.model_dump(mode="json"),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Engine:
        """`to_dict()` 의 역. 재계산 없이 그대로 복원한다.

        `twin` 을 다시 해시해 저장된 `engine_id` 와 다르면
        `FdtError(E-ENGINE-ID-MISMATCH)` 를 던진다(SPEC 4.1 "load 는 재계산
        없이 복원하며 engine_id 가 다르면 로드 거부").
        """

        meta_raw = data["meta"]
        twin = TwinInput.model_validate(data["twin"])
        as_of = date.fromisoformat(meta_raw["as_of"])
        budgets_override_raw = meta_raw.get("budgets_override")
        budgets_override = (
            {int(k): int(v) for k, v in budgets_override_raw.items()}
            if budgets_override_raw
            else None
        )

        recomputed_id = _compute_engine_id(twin, as_of, budgets_override)
        if recomputed_id != meta_raw["engine_id"]:
            raise FdtError(
                code=E_ENGINE_ID_MISMATCH,
                details={"stored": meta_raw["engine_id"], "recomputed": recomputed_id},
            )

        warnings = [
            FdtWarning(
                code=w["code"],
                message=w.get("message", ""),
                details=w.get("details", {}),
            )
            for w in meta_raw.get("warnings", [])
        ]
        meta = EngineBuildMeta(
            engine_id=meta_raw["engine_id"],
            as_of=as_of,
            schema_version=meta_raw.get("schema_version", "engine/1"),
            engine_version=meta_raw.get("engine_version", fdt.__version__),
            warnings=warnings,
            budgets_override=budgets_override,
        )

        ledger_tuple = tuple(_ledger_tx_from_dict(d) for d in data["ledger"])
        state = State.model_validate(data["state"])
        behavior = Behavior.model_validate(data["behavior"])
        externals = Externals.model_validate(data["externals"])

        return cls(
            meta=meta,
            twin=twin,
            ledger=ledger_tuple,
            state=state,
            behavior=behavior,
            externals=externals,
        )


def build_engine(
    twin: TwinInput,
    *,
    as_of: date | None = None,
    budgets_override: dict[int, int] | None = None,
    strict: bool = False,
) -> Engine:
    """`TwinInput` -> `Engine` (SPEC 4.1, 3.3 입력 검증).

    순서 (SPEC 3.3, 작업 지시 build_engine 순서 그대로):
    1. `as_of` 기본값은 `twin.as_of`. 그보다 뒤 날짜면 `E-REQ-RANGE`.
    2. `as_of` 이후 거래가 있으면 `W-INPUT-FUTURE_TX` 경고(무시하고 진행).
       `ledger.future_tx_count(twin)` 은 `twin.as_of` 고정 기준이라 `as_of`
       를 앞으로 당겨 만든 홀드아웃 스냅샷에서는 놓치므로, 여기서는
       `twin.transactions_until(as_of)` 와의 차이로 직접 센다.
    3. `ledger.normalize(twin, as_of)` 로 원장을 만든다.
    4. `ledger.reconcile(strict=strict)` 경고를 모은다(`strict=True` 면
       내부에서 바로 `FdtError(E-RECON)` 를 던진다).
    5. `history_days(ledger) < 28` 이면 `W-INPUT-SHORT_HISTORY`.
    6. `detect_income_schedule` 로 수입 일정을 추정한다.
    7. `build_state_with_warnings` 로 State 를 만들고, 그 봉투 예산을
       `estimate_behavior` 에 넘긴다(예산 소스 우선순위는 State 담당).
    8. `engine_id` 를 계산한다.
    9. `externals` 는 twin 것을 그대로 쓴다.
    """

    effective_as_of = as_of if as_of is not None else twin.as_of
    if effective_as_of > twin.as_of:
        raise FdtError(
            code=E_REQ_RANGE,
            message=(
                f"as_of({effective_as_of.isoformat()}) 는 twin.as_of"
                f"({twin.as_of.isoformat()}) 보다 뒤일 수 없다"
            ),
            details={"as_of": effective_as_of.isoformat(), "twin_as_of": twin.as_of.isoformat()},
        )

    warnings: list[FdtWarning] = []

    future_count = len(twin.transactions) - len(twin.transactions_until(effective_as_of))
    if future_count > 0:
        warnings.append(FdtWarning(code=W_INPUT_FUTURE_TX, details={"count": future_count}))

    ledger = normalize(twin, as_of=effective_as_of)
    warnings.extend(reconcile(twin, ledger, strict=strict))

    n_history_days = history_days(ledger)
    if n_history_days < 28:
        warnings.append(
            FdtWarning(code=W_INPUT_SHORT_HISTORY, details={"history_days": n_history_days})
        )

    income = detect_income_schedule(ledger, effective_as_of)

    state, queue_warnings = build_state_with_warnings(
        twin,
        ledger,
        as_of=effective_as_of,
        budgets_override=budgets_override,
        income=income,
    )
    warnings.extend(queue_warnings)

    budgets = {envelope.envelope_id: envelope.budget for envelope in state.envelopes}
    behavior = estimate_behavior(ledger, effective_as_of, budgets=budgets)

    engine_id = _compute_engine_id(twin, effective_as_of, budgets_override)

    meta = EngineBuildMeta(
        engine_id=engine_id,
        as_of=effective_as_of,
        warnings=warnings,
        budgets_override=budgets_override,
    )

    return Engine(
        meta=meta,
        twin=twin,
        ledger=ledger,
        state=state,
        behavior=behavior,
        externals=twin.externals,
    )
