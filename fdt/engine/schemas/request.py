"""모드 요청 스키마 `ModeRequest` (SPEC 8장).

엔진에 들어오는 실행 요청 전체. 모드 선택은 요청자가 명시하며 엔진은
추론하지 않는다(SPEC 8.1). 필수 파라미터 누락은 코드 `E-REQ-MISSING`,
범위 밖은 `E-REQ-RANGE` 를 담은 `FdtError`(pydantic 의 `ValidationError` 가
감싸는 `ValueError` 의 서브클래스)로 실패한다. 기본값으로 조용히 대체하지
않는다.

N1·N22·S39: 코드를 메시지 문자열에 태우던 옛 관례 대신 `FdtError(code=...,
details=...)` 를 던진다. `ValidationError.errors(include_context=True)` 의
`ctx["error"]` 로 원 예외를 그대로 꺼낼 수 있어(`fdt.engine.errors.
extract_errors()`), 호출자가 메시지를 정규식으로 파싱할 필요가 없다.

이 모듈의 공개 이름(`ModeRequest`, `ForecastParams`, `WhatIfParams`,
`GoalParams`, `RiskParams`, `OptimizeParams`, `Injection` 각 서브타입)은
다른 구현자가 그대로 import 하는 계약이다.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal, NoReturn

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from fdt.engine import taxonomy
from fdt.engine.errors import E_REQ_MISSING, E_REQ_RANGE, FdtError
from fdt.engine.taxonomy import Mode

AMOUNT_MIN = 0
AMOUNT_MAX = 1_000_000_000_000


class _Base(BaseModel):
    """공용 base: 미지정 필드 금지."""

    model_config = ConfigDict(extra="forbid")


def _fail(code: str, message: str, details: dict[str, Any] | None = None) -> NoReturn:
    raise FdtError(code=code, message=message, details=details)


def _require(cond: bool, code: str, message: str) -> None:
    if not cond:
        _fail(code, message)


def _check_amount(v: int) -> int:
    if not (AMOUNT_MIN <= v <= AMOUNT_MAX):
        _fail(E_REQ_RANGE, f"금액은 {AMOUNT_MIN}~{AMOUNT_MAX} 사이여야 한다 (받은 값: {v})")
    return v


Amount = Annotated[int, AfterValidator(_check_amount)]


def _check_horizon(v: int) -> int:
    if not (1 <= v <= 365):
        _fail(E_REQ_RANGE, f"horizon_days 는 1~365 사이여야 한다 (받은 값: {v})")
    return v


def _check_n_paths(v: int) -> int:
    if not (100 <= v <= 10000):
        _fail(E_REQ_RANGE, f"n_paths 는 100~10000 사이여야 한다 (받은 값: {v})")
    return v


def _check_envelope_id(v: int) -> int:
    n = len(taxonomy.ENVELOPES)
    if not (1 <= v <= n):
        _fail(E_REQ_RANGE, f"envelope_id 는 1~{n} 사이여야 한다 (받은 값: {v})")
    return v


HorizonDays = Annotated[int, AfterValidator(_check_horizon)]
NPaths = Annotated[int, AfterValidator(_check_n_paths)]
EnvelopeId = Annotated[int, AfterValidator(_check_envelope_id)]


# ---------------------------------------------------------------------------
# FORECAST
# ---------------------------------------------------------------------------


class ForecastParams(_Base):
    include_envelopes: bool = True
    include_events: bool = True


# ---------------------------------------------------------------------------
# WHATIF 주입 (SPEC 8.3 표)
# ---------------------------------------------------------------------------


class SpendInjection(_Base):
    type: Literal["SPEND"] = "SPEND"
    on: date | None = None
    days_from_now: int | None = None
    amount: Amount
    envelope_id: EnvelopeId
    method: Literal["CARD", "CASH"]

    @model_validator(mode="after")
    def _check_on(self) -> SpendInjection:
        _require(
            (self.on is None) != (self.days_from_now is None),
            E_REQ_MISSING,
            "SPEND 주입은 on 또는 days_from_now 중 정확히 하나가 필요하다",
        )
        return self


class IncomeInjection(_Base):
    type: Literal["INCOME"] = "INCOME"
    on: date | None = None
    days_from_now: int | None = None
    amount: Amount

    @model_validator(mode="after")
    def _check_on(self) -> IncomeInjection:
        _require(
            (self.on is None) != (self.days_from_now is None),
            E_REQ_MISSING,
            "INCOME 주입은 on 또는 days_from_now 중 정확히 하나가 필요하다",
        )
        return self


class RecurringSpendInjection(_Base):
    type: Literal["RECURRING_SPEND"] = "RECURRING_SPEND"
    start: date
    every_days: int | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    amount: Amount
    envelope_id: EnvelopeId
    method: Literal["CARD", "CASH"]
    until: date | None = None

    @model_validator(mode="after")
    def _check_recurrence(self) -> RecurringSpendInjection:
        _require(
            (self.every_days is None) != (self.day_of_month is None),
            E_REQ_MISSING,
            "RECURRING_SPEND 는 every_days 또는 day_of_month 중 정확히 하나가 필요하다",
        )
        return self


class FixedChangeInjection(_Base):
    type: Literal["FIXED_CHANGE"] = "FIXED_CHANGE"
    fixed_expense_id: int
    new_amount: Amount | None = None
    cancel: bool = False
    from_: date | None = Field(default=None, alias="from")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @model_validator(mode="after")
    def _check_change(self) -> FixedChangeInjection:
        _require(
            (self.new_amount is not None) != bool(self.cancel),
            E_REQ_MISSING,
            "FIXED_CHANGE 는 new_amount 또는 cancel 중 정확히 하나가 필요하다",
        )
        _require(
            self.from_ is not None,
            E_REQ_MISSING,
            "FIXED_CHANGE 는 from(적용 시작일) 이 필요하다",
        )
        return self


class BudgetChangeInjection(_Base):
    type: Literal["BUDGET_CHANGE"] = "BUDGET_CHANGE"
    envelope_id: EnvelopeId
    new_budget: Amount
    behavior_follows: bool = True


class ExternalInjection(_Base):
    type: Literal["EXTERNAL"] = "EXTERNAL"
    price_index_mult: float | None = None
    loan_rate_delta_bp: int | None = None
    income_growth_pct: float | None = None

    @model_validator(mode="after")
    def _check_any(self) -> ExternalInjection:
        _require(
            any(
                v is not None
                for v in (self.price_index_mult, self.loan_rate_delta_bp, self.income_growth_pct)
            ),
            E_REQ_MISSING,
            "EXTERNAL 주입은 최소 한 필드가 필요하다",
        )
        return self


class EmergencyDrawInjection(_Base):
    type: Literal["EMERGENCY_DRAW"] = "EMERGENCY_DRAW"
    on: date | None = None
    days_from_now: int | None = None
    amount: Amount

    @model_validator(mode="after")
    def _check_on(self) -> EmergencyDrawInjection:
        _require(
            (self.on is None) != (self.days_from_now is None),
            E_REQ_MISSING,
            "EMERGENCY_DRAW 주입은 on 또는 days_from_now 중 정확히 하나가 필요하다",
        )
        return self


Injection = Annotated[
    SpendInjection
    | IncomeInjection
    | RecurringSpendInjection
    | FixedChangeInjection
    | BudgetChangeInjection
    | ExternalInjection
    | EmergencyDrawInjection,
    Field(discriminator="type"),
]


class WhatIfParams(_Base):
    injections: list[Injection] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _check_injections_present(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("injections"):
            _fail(E_REQ_MISSING, "WHATIF 는 injections 가 최소 1개 필요하다")
        return data


# ---------------------------------------------------------------------------
# GOAL
# ---------------------------------------------------------------------------


class GoalParams(_Base):
    goal_type: Literal["BALANCE", "SAVE", "ENVELOPE_ADHERE"]
    target_amount: Amount | None = None
    target_date: date | None = None
    protect_essential: bool = True

    @model_validator(mode="after")
    def _check_targets(self) -> GoalParams:
        if self.goal_type in ("BALANCE", "SAVE"):
            _require(
                self.target_amount is not None and self.target_date is not None,
                E_REQ_MISSING,
                f"{self.goal_type} 는 target_amount, target_date 가 모두 필요하다",
            )
        else:  # ENVELOPE_ADHERE
            _require(
                self.target_amount is None and self.target_date is None,
                E_REQ_MISSING,
                "ENVELOPE_ADHERE 는 target_amount, target_date 를 생략해야 한다",
            )
        return self


# ---------------------------------------------------------------------------
# RISK
# ---------------------------------------------------------------------------


class RiskParams(_Base):
    recent_tx_ids: list[int] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# OPTIMIZE
# ---------------------------------------------------------------------------


class OptimizeConstraints(_Base):
    protect_essential: bool = True
    max_cut_ratio: float = Field(default=0.5, ge=0.0, le=1.0)
    allow_emergency_draw: bool = False


class OptimizeParams(_Base):
    objective: Literal["MIN_SHORTFALL_PROB", "MAX_END_BALANCE", "REACH_GOAL"]
    candidates: Literal["AUTO"] | list[Injection] = "AUTO"
    max_actions: int = Field(default=3, ge=1, le=3)
    constraints: OptimizeConstraints = Field(default_factory=OptimizeConstraints)
    goal: GoalParams | None = None

    @model_validator(mode="after")
    def _check_goal(self) -> OptimizeParams:
        if self.objective == "REACH_GOAL":
            _require(
                self.goal is not None,
                E_REQ_MISSING,
                "objective=REACH_GOAL 은 goal 파라미터가 필요하다",
            )
        return self


ParamsUnion = ForecastParams | WhatIfParams | GoalParams | RiskParams | OptimizeParams

_MODE_PARAMS: dict[Mode, type[_Base]] = {
    Mode.FORECAST: ForecastParams,
    Mode.WHATIF: WhatIfParams,
    Mode.GOAL: GoalParams,
    Mode.RISK: RiskParams,
    Mode.OPTIMIZE: OptimizeParams,
}


class ModeRequest(_Base):
    """공통 요청 (SPEC 8.1)."""

    schema_version: Literal["mode-request/1"] = "mode-request/1"
    mode: Mode
    horizon_days: HorizonDays = 30
    n_paths: NPaths = 1000
    seed: int = 42
    params: ParamsUnion

    @model_validator(mode="before")
    @classmethod
    def _parse_params_by_mode(cls, data: Any) -> Any:
        """`mode` 값 기준으로 `params` 를 명시적으로 파싱한다 (SPEC 8.1, B2).

        평범한 `Union`은 pydantic smart-union 이 왼쪽 타입부터 맞춰보므로,
        서로 다른 모드의 params 가 우연히도(전부 선택 필드라) 다른 모드의
        params 로 잘못 파싱될 수 있다(예: `{"mode":"RISK","params":{}}` 가
        `ForecastParams` 로 파싱됨). `mode` 로 params 클래스를 먼저 확정해
        그 클래스로만 파싱한다.
        """

        if not isinstance(data, dict):
            return data

        mode_raw = data.get("mode")
        if mode_raw is None:
            _fail(E_REQ_MISSING, "mode 가 필요하다")
        try:
            mode = Mode(mode_raw)
        except ValueError:
            _fail(
                E_REQ_RANGE,
                f"mode 는 {[m.value for m in Mode]} 중 하나여야 한다 (받은 값: {mode_raw!r})",
            )

        params_cls = _MODE_PARAMS[mode]
        raw_params = data.get("params")
        _require(
            raw_params is not None,
            E_REQ_MISSING,
            f"mode={mode.value} 에는 params 가 필요하다",
        )

        if not isinstance(raw_params, params_cls):
            data = dict(data)
            data["params"] = params_cls.model_validate(raw_params)
        return data

    @model_validator(mode="after")
    def _check_params_match_mode(self) -> ModeRequest:
        expected = _MODE_PARAMS[self.mode]
        if not isinstance(self.params, expected):
            _fail(
                E_REQ_MISSING,
                f"mode={self.mode.value} 에는 {expected.__name__} 이 필요하다 "
                f"(받은 타입: {type(self.params).__name__})",
            )
        return self
