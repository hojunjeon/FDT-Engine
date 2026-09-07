"""엔진 출력 스키마 `EngineResult` (SPEC 8, 9장).

모드별 result, facts(발화용 사실), viz(렌더러 독립 시각화 명세) 를 담는
공통 봉투. 차트 라이브러리 이름·색상 코드·픽셀 값은 출력에 나오면 안 된다
(SPEC 0장 핵심 원칙 4, 4.2-6). `Viz` 계열은 이를 `model_validator` 로
검사한다.

이 모듈의 공개 이름(`Fact`, `Viz` 각 8종, `Annotation`,
`ForecastResult`/`WhatIfResult`/`GoalResult`/`RiskResult`/`OptimizeResult`,
`EngineMeta`, `EngineError`, `EngineResult`)은 다른 구현자가 그대로
import 하는 계약이다.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from fdt.engine.errors import FdtError
from fdt.engine.schemas.request import Injection, ModeRequest
from fdt.engine.taxonomy import Mode

# ---------------------------------------------------------------------------
# 공용
# ---------------------------------------------------------------------------


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# 렌더러 종속 정보를 실어 나르는 것으로 알려진 "라이브러리명" 키만 금지한다.
# 값 자체(색상 코드·픽셀·라이브러리명 언급)는 아래 `_value_is_forbidden` 로 검사한다.
FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {"matplotlib", "plotly", "vega", "chart.js", "recharts", "d3"}
)

_HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}\b")
_RGB_RE = re.compile(r"rgb\(")
_PX_RE = re.compile(r"\d+px\b")
_LIB_NAME_RE = re.compile(r"matplotlib|plotly|vega|chart\.js|recharts|d3", re.IGNORECASE)


def _value_is_forbidden(value: str) -> bool:
    return bool(
        _HEX_COLOR_RE.search(value)
        or _RGB_RE.search(value)
        or _PX_RE.search(value)
        or _LIB_NAME_RE.search(value)
    )


def _walk_check_forbidden(obj: Any) -> None:
    """dict/list/str 를 재귀로 훑어 금지된 키·값이 없는지 검사한다."""

    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str) and key.strip().lower() in FORBIDDEN_KEYS:
                raise ValueError(
                    f"viz 명세에 렌더러 종속 키 '{key}' 는 쓸 수 없다 (SPEC 0, 4.2-6)"
                )
            _walk_check_forbidden(value)
    elif isinstance(obj, list):
        for item in obj:
            _walk_check_forbidden(item)
    elif isinstance(obj, str) and _value_is_forbidden(obj):
        raise ValueError(
            f"viz 명세에 렌더러 종속 값 '{obj}' 는 쓸 수 없다 (SPEC 0, 4.2-6)"
        )


# ---------------------------------------------------------------------------
# Fact (SPEC 9.2)
# ---------------------------------------------------------------------------

FactUnit = Literal["KRW", "%", "prob", "date", "점", "일", "ratio", "text"]


class Fact(_Base):
    key: str
    label: str
    value: bool | int | float | str
    unit: FactUnit
    precision: int
    allowed_renderings: list[str]
    importance: int = Field(ge=1, le=3)
    hint: str | None = None


# ---------------------------------------------------------------------------
# Annotation (SPEC 9.3)
# ---------------------------------------------------------------------------


class Annotation(_Base):
    type: Literal["point", "vline", "hline", "range"]
    x: date | None = None
    y: float | None = None
    x2: date | None = None
    y2: float | None = None
    label: str = ""


# ---------------------------------------------------------------------------
# Viz 8종 (SPEC 9.3)
# ---------------------------------------------------------------------------


class _VizBase(_Base):
    id: str
    title: str
    priority: int = Field(ge=1, le=3)
    caption: str = ""
    annotations: list[Annotation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _no_forbidden_keys(self) -> _VizBase:
        _walk_check_forbidden(self.model_dump(mode="json"))
        return self


class LineSeries(_Base):
    name: str
    y: list[float]


class LineBand(_Base):
    lower: list[float]
    upper: list[float]


class LineBandData(_Base):
    x: list[date]
    series: list[LineSeries]
    band: LineBand


class LineBandEncoding(_Base):
    x: Literal["date"] = "date"
    y: Literal["KRW"] = "KRW"


class LineBandViz(_VizBase):
    kind: Literal["line_band"] = "line_band"
    data: LineBandData
    encoding: LineBandEncoding = Field(default_factory=LineBandEncoding)


class EventPoint(_Base):
    date: date
    kind: str
    name: str
    amount: int
    fail_prob: float


class EventTimelineData(_Base):
    events: list[EventPoint]


class EventTimelineEncoding(_Base):
    x: Literal["date"] = "date"
    size: Literal["amount"] = "amount"
    color: Literal["fail_prob"] = "fail_prob"


class EventTimelineViz(_VizBase):
    kind: Literal["event_timeline"] = "event_timeline"
    data: EventTimelineData
    encoding: EventTimelineEncoding = Field(default_factory=EventTimelineEncoding)


class GaugeData(_Base):
    value: float
    min: float = 0
    max: float = 100
    thresholds: list[float] = Field(default_factory=list)
    level: str


class GaugeEncoding(_Base):
    unit: str


class GaugeViz(_VizBase):
    kind: Literal["gauge"] = "gauge"
    data: GaugeData
    encoding: GaugeEncoding


class ProgressItem(_Base):
    name: str
    value: float
    max: float
    projected: float | None = None


class ProgressBarsData(_Base):
    items: list[ProgressItem]


class ProgressBarsEncoding(_Base):
    unit: Literal["KRW"] = "KRW"


class ProgressBarsViz(_VizBase):
    kind: Literal["progress_bars"] = "progress_bars"
    data: ProgressBarsData
    encoding: ProgressBarsEncoding = Field(default_factory=ProgressBarsEncoding)


class DeltaItem(_Base):
    name: str
    base: float
    branch: float
    delta: float
    unit: str


class DeltaBarsData(_Base):
    items: list[DeltaItem]


class DeltaBarsViz(_VizBase):
    kind: Literal["delta_bars"] = "delta_bars"
    data: DeltaBarsData
    encoding: dict[str, str] = Field(default_factory=dict)


class Stack(_Base):
    name: str
    y: list[float]


class StepBarsData(_Base):
    x: list[date]
    stacks: list[Stack]
    total: list[float]


class StepBarsEncoding(_Base):
    x: Literal["date"] = "date"
    y: Literal["KRW"] = "KRW"


class StepBarsViz(_VizBase):
    kind: Literal["step_bars"] = "step_bars"
    data: StepBarsData
    encoding: StepBarsEncoding = Field(default_factory=StepBarsEncoding)


class RankedItem(_Base):
    rank: int
    label: str
    effect: float
    unit: str
    detail: str = ""


class RankedBarsData(_Base):
    items: list[RankedItem]


class RankedBarsViz(_VizBase):
    kind: Literal["ranked_bars"] = "ranked_bars"
    data: RankedBarsData
    encoding: dict[str, str] = Field(default_factory=dict)


class ColumnSpec(_Base):
    key: str
    label: str
    unit: str | None = None


class TableData(_Base):
    columns: list[ColumnSpec]
    rows: list[dict[str, Any]]


class TableViz(_VizBase):
    kind: Literal["table"] = "table"
    data: TableData
    encoding: dict[str, str] = Field(default_factory=dict)


Viz = Annotated[
    LineBandViz
    | EventTimelineViz
    | GaugeViz
    | ProgressBarsViz
    | DeltaBarsViz
    | StepBarsViz
    | RankedBarsViz
    | TableViz,
    Field(discriminator="kind"),
]


# ---------------------------------------------------------------------------
# FORECAST (SPEC 8.2)
# ---------------------------------------------------------------------------


class Trajectory(_Base):
    dates: list[date]
    median: list[float]
    p10: list[float]
    p90: list[float]
    mean: list[float]


class EconomicStats(_Base):
    median: list[float]
    p10: list[float]
    p90: list[float]


class PointStat(_Base):
    date: date
    median_balance: int
    p10_balance: int | None = None


class EnvelopeForecast(_Base):
    envelope_id: int
    name: str
    budget: int
    spent_now: int
    projected_month_end_median: float
    exhaust_date_median: date | None = None
    overrun_prob: float


class EventForecast(_Base):
    date: date
    kind: str
    name: str
    amount: int
    fail_prob: float


class ForecastResult(_Base):
    trajectory: Trajectory
    economic: EconomicStats
    min_point: PointStat
    end_point: PointStat
    envelopes: list[EnvelopeForecast] = Field(default_factory=list)
    events: list[EventForecast] = Field(default_factory=list)
    shortfall_prob: float
    card_shortfall_prob: float


# ---------------------------------------------------------------------------
# WHATIF (SPEC 8.3)
# ---------------------------------------------------------------------------


class TrajectorySummary(_Base):
    dates: list[date] | None = None
    median: list[float]
    p10: list[float]
    p90: list[float]


class BranchSummary(_Base):
    trajectory: TrajectorySummary
    min_point: PointStat
    end_point: PointStat
    shortfall_prob: float
    card_shortfall_prob: float


class FirstShortfallDate(_Base):
    base: date | None = None
    branch: date | None = None


class EnvelopeDelta(_Base):
    envelope_id: int
    remaining_change: int
    overrun_prob_change: float


class WhatIfDelta(_Base):
    min_balance: int
    end_balance: int
    shortfall_prob: float
    card_shortfall_prob: float
    first_shortfall_date: FirstShortfallDate
    envelopes: list[EnvelopeDelta] = Field(default_factory=list)


class WhatIfResult(_Base):
    base: BranchSummary
    branch: BranchSummary
    delta: WhatIfDelta
    verdict: Literal["OK", "CAUTION", "DANGER"]
    crn: bool = True


# ---------------------------------------------------------------------------
# GOAL (SPEC 8.4)
# ---------------------------------------------------------------------------


class Gap(_Base):
    median: int
    p10: int


class Required(_Base):
    total_discretionary_cap: int
    reduction_ratio: float
    baseline_discretionary: int


class EnvelopeCap(_Base):
    envelope_id: int
    cap: int


class WeeklyCap(_Base):
    week_start: date
    days: int
    total_cap: int
    by_envelope: list[EnvelopeCap] = Field(default_factory=list)


class GoalResult(_Base):
    feasible: bool
    achieve_prob: float
    gap: Gap
    required: Required
    weekly_caps: list[WeeklyCap] = Field(default_factory=list)
    plan_achieve_prob: float
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# RISK (SPEC 8.5)
# ---------------------------------------------------------------------------


class PaymentRisk(_Base):
    due: date
    kind: str
    name: str
    amount: int
    fail_prob: float
    median_balance_before: int


class AccelerationAlert(_Base):
    kind: Literal["ACCELERATION"] = "ACCELERATION"
    severity: Literal["WARNING", "DANGER"]
    ratio: float


class ConcerningTxAlert(_Base):
    kind: Literal["CONCERNING_TX"] = "CONCERNING_TX"
    severity: Literal["WARNING", "DANGER"]
    tx_id: int
    amount: int
    envelope_id: int
    remaining_before: int
    threshold: int


Alert = Annotated[
    AccelerationAlert | ConcerningTxAlert,
    Field(discriminator="kind"),
]


class Health(_Base):
    score: int
    level: Literal["SAFE", "WARNING", "DANGER"]
    coverage: float
    adherence: float
    risk: float


class RiskResult(_Base):
    risk_score: int = Field(ge=0, le=100)
    level: Literal["SAFE", "WARNING", "DANGER"]
    shortfall_prob: float
    card_shortfall_prob: float
    worst_day: date
    expected_shortfall: int
    payment_risks: list[PaymentRisk] = Field(default_factory=list)
    alerts: list[Alert] = Field(default_factory=list)
    safe_to_spend_today: int
    health: Health


# ---------------------------------------------------------------------------
# OPTIMIZE (SPEC 8.6)
# ---------------------------------------------------------------------------


class OptimizeBaseline(_Base):
    shortfall_prob: float
    card_shortfall_prob: float
    end_balance_median: float


class AppliedAction(_Base):
    """OPTIMIZE 후보 1건이 실제로 적용한 행동 (SPEC 8.6 `ranked[].actions[]`, S9).

    7종 `Injection` 유니온을 그대로 감싸고, 예산 삭감 비율 등 부가 정보만
    덧붙인다. `Injection` 서브타입은 `extra="forbid"` 라 `cut_ratio` 같은
    필드를 직접 담을 수 없어 별도 래퍼로 정의했다.
    """

    injection: Injection
    cut_ratio: float | None = None
    label: str | None = None


class RankedAction(_Base):
    rank: int
    actions: list[AppliedAction]
    effect: dict[str, float | int | str]
    feasibility_note: str | None = None


class Recommended(_Base):
    rank: int
    combined_effect: dict[str, Any] = Field(default_factory=dict)


class OptimizeResult(_Base):
    objective: Literal["MIN_SHORTFALL_PROB", "MAX_END_BALANCE", "REACH_GOAL"]
    baseline: OptimizeBaseline
    ranked: list[RankedAction] = Field(default_factory=list)
    recommended: Recommended | None = None
    evaluated: int
    sim_calls: int


# ---------------------------------------------------------------------------
# EngineResult 봉투 (SPEC 9.1)
# ---------------------------------------------------------------------------

ResultUnion = ForecastResult | WhatIfResult | GoalResult | RiskResult | OptimizeResult

_MODE_RESULT: dict[Mode, type[BaseModel]] = {
    Mode.FORECAST: ForecastResult,
    Mode.WHATIF: WhatIfResult,
    Mode.GOAL: GoalResult,
    Mode.RISK: RiskResult,
    Mode.OPTIMIZE: OptimizeResult,
}


class EngineMeta(_Base):
    engine_id: str
    as_of: date
    mode: Mode
    seed: int
    n_paths: int
    horizon_days: int
    elapsed_ms: int
    engine_version: str
    warnings: list[dict[str, Any]] = Field(default_factory=list)


class EngineError(_Base):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class EngineResult(_Base):
    schema_version: Literal["engine-result/1"] = "engine-result/1"
    meta: EngineMeta
    request: ModeRequest
    result: ResultUnion | None = None
    facts: list[Fact] = Field(default_factory=list)
    viz: list[Viz] = Field(default_factory=list)
    status: Literal["OK", "ERROR"]
    error: EngineError | None = None

    @model_validator(mode="after")
    def _check_status(self) -> EngineResult:
        if self.status == "OK":
            if self.result is None:
                raise ValueError("status=OK 면 result 가 필수다 (SPEC 9.1)")
            if self.error is not None:
                raise ValueError("status=OK 면 error 는 없어야 한다 (SPEC 9.1)")
            expected = _MODE_RESULT[self.meta.mode]
            if not isinstance(self.result, expected):
                raise ValueError(
                    f"meta.mode={self.meta.mode.value} 인데 result 타입이 "
                    f"{expected.__name__} 이 아니다 (받은 타입: {type(self.result).__name__})"
                )
        else:  # ERROR
            if self.error is None:
                raise ValueError("status=ERROR 면 error 가 필수다 (SPEC 9.1)")
            if self.result is not None:
                raise ValueError("status=ERROR 면 result 는 없어야 한다 (SPEC 9.1)")
        return self

    def fact_renderings(self) -> set[str]:
        """모든 facts 의 allowed_renderings 합집합."""

        renderings: set[str] = set()
        for fact in self.facts:
            renderings.update(fact.allowed_renderings)
        return renderings

    def strip_volatile(self) -> dict[str, Any]:
        """재현성 비교(골든 테스트)용 dump. elapsed_ms 를 제거한다."""

        dumped = self.model_dump(mode="json")
        meta = dumped.get("meta")
        if isinstance(meta, dict):
            meta.pop("elapsed_ms", None)
        return dumped


__all__ = [
    "FORBIDDEN_KEYS",
    "AccelerationAlert",
    "Alert",
    "Annotation",
    "AppliedAction",
    "BranchSummary",
    "ColumnSpec",
    "ConcerningTxAlert",
    "DeltaBarsData",
    "DeltaBarsViz",
    "DeltaItem",
    "EconomicStats",
    "EngineError",
    "EngineMeta",
    "EngineResult",
    "EnvelopeCap",
    "EnvelopeDelta",
    "EnvelopeForecast",
    "EventForecast",
    "EventPoint",
    "EventTimelineData",
    "EventTimelineEncoding",
    "EventTimelineViz",
    "Fact",
    "FactUnit",
    "FdtError",
    "FirstShortfallDate",
    "Gap",
    "GaugeData",
    "GaugeEncoding",
    "GaugeViz",
    "GoalResult",
    "Health",
    "LineBand",
    "LineBandData",
    "LineBandEncoding",
    "LineBandViz",
    "LineSeries",
    "OptimizeBaseline",
    "OptimizeResult",
    "PaymentRisk",
    "PointStat",
    "ProgressBarsData",
    "ProgressBarsEncoding",
    "ProgressBarsViz",
    "ProgressItem",
    "RankedAction",
    "RankedBarsData",
    "RankedBarsViz",
    "RankedItem",
    "Recommended",
    "Required",
    "ResultUnion",
    "RiskResult",
    "Stack",
    "StepBarsData",
    "StepBarsEncoding",
    "StepBarsViz",
    "TableData",
    "TableViz",
    "Trajectory",
    "TrajectorySummary",
    "Viz",
    "WeeklyCap",
    "WhatIfDelta",
    "WhatIfResult",
]
