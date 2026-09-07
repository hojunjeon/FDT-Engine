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
import inspect
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
    E_REQ_RANGE,
    W_INPUT_FUTURE_TX,
    W_INPUT_SHORT_HISTORY,
    FdtError,
    FdtWarning,
    extract_errors,
)
from fdt.engine.facts import build_facts
from fdt.engine.ledger import LedgerTx, account_balance_at, history_days, normalize, reconcile
from fdt.engine.modes import MODE_RUNNERS, load_all
from fdt.engine.schemas.behavior import Behavior
from fdt.engine.schemas.input import Externals, TwinInput
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.schemas.result import EngineError as ResultEngineError
from fdt.engine.schemas.result import EngineMeta as ResultEngineMeta
from fdt.engine.schemas.result import EngineResult, ResultWarning
from fdt.engine.schemas.state import State
from fdt.engine.state import build_state_with_warnings
from fdt.engine.taxonomy import ConfirmStatus, ExcludeTag, Flow
from fdt.engine.viz import build_viz

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
        """What-if 용 얕은 복제 (SPEC 4.1). 원장은 공유(불변), state 만 깊은 복사.

        N15: `meta` 도 얕은 공유가 아니라 새 `EngineBuildMeta` 로 복사한다.
        `warnings` 는 가변 리스트라 원본과 공유하면 분기 쪽에서 경고를
        추가할 때 원본(기준) 엔진이 오염된다(W6 메모 7). 다른 필드는 전부
        불변(str/date)이라 얕은 복사로 충분하다.
        """

        forked_meta = EngineBuildMeta(
            engine_id=self.meta.engine_id,
            as_of=self.meta.as_of,
            schema_version=self.meta.schema_version,
            engine_version=self.meta.engine_version,
            warnings=list(self.meta.warnings),
            budgets_override=self.meta.budgets_override,
        )
        return Engine(
            meta=forked_meta,
            twin=self.twin,
            ledger=self.ledger,
            state=self.state.model_copy(deep=True),
            behavior=self.behavior,
            externals=self.externals,
        )

    def run(self, req: ModeRequest) -> EngineResult:
        """모드 디스패치 (SPEC 8~9장).

        `load_all()` 로 `fdt.engine.modes.*` 를 (첫 호출에서만) 로드해
        레지스트리를 채운 뒤, `req.mode` 러너를 찾아 `runner(self, req)` 를
        호출한다 - 다섯 모드 전부 `simulate()` 하나만 부른다(SPEC 4.2-5).
        러너가 없는 모드(아직 구현되지 않은 모드)는 `E-MODE-NOT_IMPLEMENTED`
        오류로 끝난다. 성공하면 그 result 로 `build_facts`/`build_viz` 를
        만들어 §9.2/§9.3 계약대로 채운다(재계산 없이 result 값만 뽑는다 -
        모드 러너의 결정을 여기서 다시 계산하지 않는다). 측정에는 SPEC
        4.2-2 가 허용하는 `time.perf_counter()` 만 쓴다.
        """

        load_all()

        start = time.perf_counter()
        result = None
        facts: list[Any] = []
        viz: list[Any] = []
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
            facts = build_facts(
                req.mode, result, as_of=self.meta.as_of, horizon_days=req.horizon_days
            )
            viz = build_viz(
                req.mode, result, facts, as_of=self.meta.as_of, horizon_days=req.horizon_days
            )
        except FdtError as exc:
            status = "ERROR"
            error = ResultEngineError(code=exc.code, message=exc.message, details=exc.details)
        except ValidationError as exc:
            # N1·N22·S39: 메시지를 정규식으로 파싱하지 않는다.
            # `extract_errors` 가 각 오류 항목을 구조화된 `FdtError` 로
            # 복원한다(코드가 `E-REQ-MISSING`/`E-REQ-RANGE`/`E-REQ-INVALID`
            # 로 정확히 갈린다 - SPEC 8.1). 첫 오류를 대표 `error` 로 삼고,
            # 전체 목록은 `error.details["errors"]` 에 싣는다.
            status = "ERROR"
            fdt_errors = extract_errors(exc)
            first = fdt_errors[0]
            error = ResultEngineError(
                code=first.code,
                message=first.message,
                details={
                    **first.details,
                    "errors": [
                        {
                            "code": e.code,
                            "message": e.message,
                            "loc": e.details.get("loc"),
                        }
                        for e in fdt_errors
                    ],
                },
            )

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        # N14: OPTIMIZE 는 시뮬 예산 때문에 요청값(req.n_paths)보다 실제
        # n_paths 를 하향할 수 있다(`optimize.py` 의 자동 하향). 그 실제
        # 사용값이 `result.n_paths_used` 에 있으면 그 값을 싣고, 없으면
        # (다른 모드, 또는 아직 그 필드가 없는 구버전 result) 요청값을
        # 그대로 쓴다(getattr 방어).
        n_paths_used = getattr(result, "n_paths_used", None)
        n_paths_meta = n_paths_used if isinstance(n_paths_used, int) else req.n_paths
        result_meta = ResultEngineMeta(
            engine_id=self.meta.engine_id,
            as_of=self.meta.as_of,
            mode=req.mode,
            seed=req.seed,
            n_paths=n_paths_meta,
            horizon_days=req.horizon_days,
            elapsed_ms=elapsed_ms,
            engine_version=self.meta.engine_version,
            warnings=[
                ResultWarning(code=w.code, message=w.message, details=w.details)
                for w in self.meta.warnings
            ],
        )
        return EngineResult(
            meta=result_meta,
            request=req,
            result=result,
            facts=facts,
            viz=viz,
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
    3. `ledger.normalize(twin, as_of=twin.as_of)` 로 **전체 기간** 원장을
       만든다(B1·B2, 리뷰 20260907_W3_W4_W5.md). 이전에는 `as_of=effective_as_of`
       로 원장을 이 시점에 잘라, `account_balance_at`/`reconcile` 이 그
       잘린 원장을 "전체 기간" 인 것처럼 읽어 (a) `opening_balance` 가 없는
       계좌의 역산이 `as_of` 초과 구간을 못 찾아 항상 0을 빼는 미래 잔액
       누수, (b) 과거 `as_of` 홀드아웃 빌드가 늘 가짜 `W-RECON`/`E-RECON`
       을 내는 두 버그를 만들었다.
    4. `ledger.reconcile(strict=strict)` 을 **전체 기간 원장**·`twin.as_of`
       기준으로 수행해 경고를 모은다(`strict=True` 면 내부에서 바로
       `FdtError(E-RECON)` 를 던진다) - 대사는 그 정의상 항상 `twin.as_of`
       시점 진짜 잔액과 맞춰야 하므로 `effective_as_of` 와 무관하다.
    5. 저장·이후 계산에 쓸 원장은 전체 기간 원장을 `effective_as_of` 이하로
       절단한 튜플이다(`Engine.ledger` 계약 - 모드 러너는 이 절단 원장만
       본다, W6 메모 8). `history_days`/`detect_income_schedule`/
       `estimate_behavior` 는 전부 이 절단 원장만 봐서 미래 데이터가 새지
       않는다.
    6. `history_days(ledger) < 28` 이면 `W-INPUT-SHORT_HISTORY`.
    7. `detect_income_schedule` 로 수입 일정을 추정한다.
    8. `build_state_with_warnings` 로 State 를 만든다. **전체 기간 원장**을
       넘겨야 `account_balance_at` 의 역산(opening_balance 없는 계좌)이
       정확하다 - `state.py` 내부의 모든 다른 계산(큐·카드·봉투·지표)은
       `_ledger_until(ledger, as_of)` 로 스스로 `effective_as_of` 까지
       다시 걸러 쓰므로 전체 기간 원장을 받아도 미래가 새지 않는다. 그
       봉투 예산은 `estimate_behavior` 에 넘긴다(예산 소스 우선순위는
       State 담당).
    9. `engine_id` 를 계산한다.
    10. `externals` 는 twin 것을 그대로 쓴다.
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

    # B1·B2: 대사·잔액 역산은 항상 전체 기간 원장을 봐야 한다.
    full_ledger = normalize(twin, as_of=twin.as_of)
    warnings.extend(reconcile(twin, full_ledger, strict=strict))

    # `Engine.ledger` 계약: as_of 이하로 절단한 튜플만 저장·전파한다.
    ledger = tuple(record for record in full_ledger if record.date <= effective_as_of)

    n_history_days = history_days(ledger)
    if n_history_days < 28:
        warnings.append(
            FdtWarning(code=W_INPUT_SHORT_HISTORY, details={"history_days": n_history_days})
        )

    income = detect_income_schedule(ledger, effective_as_of)

    # `build_state_with_warnings` 가 잔액을 자체 계산(`account_balance_at`)
    # 하므로 전체 기간 원장을 넘겨야 opening_balance 없는 계좌의 역산이
    # 맞는다. H2 가 별도로 `account_balances` 인자를 추가하기로 했다면
    # 그쪽을 쓰고, 아직 없으면(2026-09-07 기준 없음) full_ledger 를 그대로
    # 넘기는 우회로 충분하다 - 나머지 state 계산은 내부에서 스스로
    # `effective_as_of` 로 다시 필터한다(B1 우회 방식, 보고 참조).
    state_params = inspect.signature(build_state_with_warnings).parameters
    if "account_balances" in state_params:
        account_balances = {
            account.id: account_balance_at(twin, full_ledger, account.id, effective_as_of)
            for account in twin.accounts
        }
        state, queue_warnings = build_state_with_warnings(
            twin,
            ledger,
            as_of=effective_as_of,
            budgets_override=budgets_override,
            income=income,
            account_balances=account_balances,
        )
    else:
        state, queue_warnings = build_state_with_warnings(
            twin,
            full_ledger,
            as_of=effective_as_of,
            budgets_override=budgets_override,
            income=income,
        )
    warnings.extend(queue_warnings)

    budgets = {envelope.envelope_id: envelope.budget for envelope in state.envelopes}
    # S49: 창 길이를 명시적으로 넘기지 않는다 - `estimate_behavior` 가
    # "가용 이력 전체, 상한 180일" 을 스스로 계산한다(리뷰
    # docs/reviews/20260907_W6_W10.md 항목 2-3, SPEC §14 R10).
    behavior = estimate_behavior(ledger, effective_as_of, budgets=budgets, window_days=None)

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
