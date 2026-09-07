"""시각화 명세(viz) 빌더 (SPEC 9.3, 9.4).

`build_viz(mode, result, facts, as_of=...)` 는 모드별 `ResultUnion` 과
`build_facts()` 가 만든 `facts` 목록을 받아 렌더러 독립 `Viz` 8종 명세
목록을 만든다. annotations 라벨과 caption 의 숫자는 반드시 `facts` 의
`allowed_renderings` 에서 그대로 가져온다(재계산·재포맷 금지, SPEC 9.3,
14 R7). 색상 코드·픽셀·차트 라이브러리명은 쓰지 않는다(`Viz` 모델 자체가
`model_validator` 로 이를 강제한다).

viz.py 는 엔진 코어(`fdt/engine/**`)이므로 파일·콘솔 I/O 를 하지 않는다.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from fdt.engine import taxonomy
from fdt.engine.schemas.result import (
    Annotation,
    ColumnSpec,
    DeltaBarsData,
    DeltaBarsViz,
    DeltaItem,
    EventPoint,
    EventTimelineData,
    EventTimelineViz,
    Fact,
    ForecastResult,
    GaugeData,
    GaugeEncoding,
    GaugeViz,
    GoalResult,
    LineBand,
    LineBandData,
    LineBandViz,
    LineSeries,
    OptimizeResult,
    ProgressBarsData,
    ProgressBarsViz,
    ProgressItem,
    RankedBarsData,
    RankedBarsViz,
    RankedItem,
    ResultUnion,
    RiskResult,
    Stack,
    StepBarsData,
    StepBarsViz,
    TableData,
    TableViz,
    Viz,
    WhatIfResult,
)
from fdt.engine.taxonomy import Mode

# ---------------------------------------------------------------------------
# 공용 헬퍼
# ---------------------------------------------------------------------------


def _facts_by_key(facts: list[Fact]) -> dict[str, Fact]:
    return {f.key: f for f in facts}


def _render(facts_by_key: dict[str, Fact], key: str, index: int = 0) -> str:
    """facts 의 `allowed_renderings` 중 하나를 그대로 가져온다.

    caption·annotation 라벨은 이 함수가 돌려주는 문자열만 조합해서 만든다 -
    새 숫자를 문자열 포매팅으로 만들어 넣지 않는다(SPEC 14 R7).
    """

    fact = facts_by_key.get(key)
    if fact is None or not fact.allowed_renderings:
        return ""
    idx = index if index < len(fact.allowed_renderings) else 0
    return fact.allowed_renderings[idx]


def _dates_or_fallback(dates: list[date] | None, as_of: date, length: int) -> list[date]:
    if dates:
        return dates
    return [as_of + timedelta(days=i) for i in range(length)]


def _envelope_name(envelope_id: int) -> str:
    if 1 <= envelope_id <= len(taxonomy.ENVELOPES):
        return taxonomy.ENVELOPES[envelope_id - 1]
    return f"봉투{envelope_id}"


def _joined_action_label(actions: list[Any], rank: int) -> str:
    """조합 후보 라벨을 이어붙인다 (B8, `facts.py` 의 같은 이름 함수와 규칙
    동일 - `ra.actions[0].label` 만 읽으면 2 행동 조합이 1위와 같은 라벨로
    보인다)."""

    labels = [a.label for a in actions if a.label]
    if labels:
        return "; ".join(labels)
    return f"행동 {rank}위"


# ---------------------------------------------------------------------------
# FORECAST
# ---------------------------------------------------------------------------


def _viz_forecast(
    result: ForecastResult,
    facts_by_key: dict[str, Fact],
    as_of: date,
    horizon_days: int | None = None,
) -> list[Viz]:
    min_label = f"최저점 {_render(facts_by_key, 'min_balance_median')}".strip()
    line_band = LineBandViz(
        id="balance_trajectory",
        title="잔액 예측",
        priority=1,
        data=LineBandData(
            x=result.trajectory.dates,
            series=[LineSeries(name="중앙값", y=result.trajectory.median)],
            band=LineBand(lower=result.trajectory.p10, upper=result.trajectory.p90),
        ),
        annotations=[
            Annotation(
                type="point",
                x=result.min_point.date,
                y=float(result.min_point.median_balance),
                label=min_label,
            )
        ],
        caption=(
            f"말일 예상 잔액은 {_render(facts_by_key, 'end_balance_median')}, "
            f"부족 확률은 {_render(facts_by_key, 'shortfall_prob')}다."
        ),
    )

    progress_bars = ProgressBarsViz(
        id="envelope_progress",
        title="봉투별 사용률",
        priority=1,
        data=ProgressBarsData(
            items=[
                ProgressItem(
                    name=env.name,
                    value=env.spent_now,
                    max=env.budget,
                    projected=env.projected_month_end_median,
                )
                for env in result.envelopes
            ]
        ),
        caption="봉투별 이번 달 사용액과 예산 대비 진행률.",
    )

    event_timeline = EventTimelineViz(
        id="events",
        title="예정 이벤트",
        priority=1,
        data=EventTimelineData(
            events=[
                EventPoint(
                    date=ev.date,
                    kind=ev.kind,
                    name=ev.name,
                    amount=ev.amount,
                    fail_prob=ev.fail_prob,
                )
                for ev in result.events
            ]
        ),
        caption="예정된 결제·수입 이벤트.",
    )

    return [line_band, progress_bars, event_timeline]


# ---------------------------------------------------------------------------
# WHATIF
# ---------------------------------------------------------------------------


def _viz_whatif(
    result: WhatIfResult,
    facts_by_key: dict[str, Fact],
    as_of: date,
    horizon_days: int | None = None,
) -> list[Viz]:
    length = len(result.base.trajectory.median)
    dates = _dates_or_fallback(
        result.branch.trajectory.dates or result.base.trajectory.dates, as_of, length
    )

    line_band = LineBandViz(
        id="base_vs_branch",
        title="기준 vs 분기 잔액",
        priority=1,
        data=LineBandData(
            x=dates,
            series=[
                LineSeries(name="기준", y=result.base.trajectory.median),
                LineSeries(name="분기", y=result.branch.trajectory.median),
            ],
            band=LineBand(lower=result.branch.trajectory.p10, upper=result.branch.trajectory.p90),
        ),
        annotations=[
            Annotation(
                type="point",
                x=result.branch.min_point.date,
                y=float(result.branch.min_point.median_balance),
                label=f"분기 최저점 {_render(facts_by_key, 'branch_min_balance')}",
            )
        ],
        caption=(
            f"판정은 {_render(facts_by_key, 'verdict')}, "
            f"최저 잔액 변화는 {_render(facts_by_key, 'delta_min_balance')}다."
        ),
    )

    delta_bars = DeltaBarsViz(
        id="whatif_delta",
        title="기준 대비 분기 변화",
        priority=1,
        data=DeltaBarsData(
            items=[
                DeltaItem(
                    name="최저 잔액",
                    base=float(result.base.min_point.median_balance),
                    branch=float(result.branch.min_point.median_balance),
                    delta=float(result.delta.min_balance),
                    unit="KRW",
                ),
                DeltaItem(
                    name="말일 잔액",
                    base=float(result.base.end_point.median_balance),
                    branch=float(result.branch.end_point.median_balance),
                    delta=float(result.delta.end_balance),
                    unit="KRW",
                ),
                DeltaItem(
                    name="부족 확률",
                    base=round(result.base.shortfall_prob * 100),
                    branch=round(result.branch.shortfall_prob * 100),
                    delta=round(result.delta.shortfall_prob * 100),
                    unit="%",
                ),
            ]
        ),
        caption=f"부족 확률 변화는 {_render(facts_by_key, 'delta_shortfall_prob')}다.",
    )

    return [line_band, delta_bars]


# ---------------------------------------------------------------------------
# GOAL
# ---------------------------------------------------------------------------


def _goal_level(achieve_prob: float) -> str:
    if achieve_prob >= 0.7:
        return "SAFE"
    if achieve_prob >= 0.4:
        return "WARNING"
    return "DANGER"


def _viz_goal(
    result: GoalResult,
    facts_by_key: dict[str, Fact],
    as_of: date,
    horizon_days: int | None = None,
) -> list[Viz]:
    gauge_value = result.achieve_prob * 100
    gauge = GaugeViz(
        id="achieve_prob",
        title="목표 달성 확률",
        priority=1,
        data=GaugeData(
            value=gauge_value,
            min=0,
            max=100,
            thresholds=[40, 70],
            level=_goal_level(result.achieve_prob),
        ),
        encoding=GaugeEncoding(unit="%"),
        caption=f"목표 달성 확률은 {_render(facts_by_key, 'achieve_prob')}다.",
    )

    week_dates = [wc.week_start for wc in result.weekly_caps]
    envelope_order: list[int] = []
    for wc in result.weekly_caps:
        for cap in wc.by_envelope:
            if cap.envelope_id not in envelope_order:
                envelope_order.append(cap.envelope_id)

    stacks = []
    for envelope_id in envelope_order:
        ys: list[float] = []
        for wc in result.weekly_caps:
            match = next((c.cap for c in wc.by_envelope if c.envelope_id == envelope_id), 0)
            ys.append(float(match))
        stacks.append(Stack(name=_envelope_name(envelope_id), y=ys))

    step_bars = StepBarsViz(
        id="weekly_caps",
        title="주차별 지출 상한",
        priority=1,
        data=StepBarsData(
            x=week_dates,
            stacks=stacks,
            total=[float(wc.total_cap) for wc in result.weekly_caps],
        ),
        caption=f"지출 축소 비율은 {_render(facts_by_key, 'reduction_ratio')}다.",
    )

    # GoalResult 에는 잔액 궤적이 없어(SPEC 8.4), line_band 는 주차 누적 상한을
    # 대체 시계열로 쓴다. p10/p90 밴드에 해당하는 값이 없어 중앙값과 동일하게
    # 채운 퇴화(degenerate) 밴드다 - SPEC 과 다르게 한 점(보고 참조, N16).
    # SPEC 9.4 는 GOAL line_band 에 "목표선 hline" 을 요구한다 - 퇴화 밴드는
    # 그대로 두고, `total_discretionary_cap`(총 재량 지출 한도) 를 그
    # 목표선으로 그린다.
    if week_dates:
        cumulative: list[float] = []
        running = 0.0
        for wc in result.weekly_caps:
            running += wc.total_cap
            cumulative.append(running)
        line_x = week_dates
        line_y = cumulative
    else:
        line_x = [as_of]
        line_y = [0.0]

    goal_line_annotations = []
    cap_fact = facts_by_key.get("total_discretionary_cap")
    if cap_fact is not None:
        goal_line_annotations.append(
            Annotation(
                type="hline",
                y=float(cap_fact.value),
                label=f"총 재량 지출 한도 {_render(facts_by_key, 'total_discretionary_cap')}",
            )
        )

    line_band = LineBandViz(
        id="goal_cap_trajectory",
        title="목표 누적 지출 상한",
        priority=1,
        data=LineBandData(
            x=line_x,
            series=[LineSeries(name="누적 상한", y=line_y)],
            band=LineBand(lower=line_y, upper=line_y),
        ),
        annotations=goal_line_annotations,
        caption=f"부족액(중앙값)은 {_render(facts_by_key, 'gap_median')}다.",
    )

    return [gauge, step_bars, line_band]


# ---------------------------------------------------------------------------
# RISK
# ---------------------------------------------------------------------------


def _viz_risk(
    result: RiskResult,
    facts_by_key: dict[str, Fact],
    as_of: date,
    horizon_days: int | None = None,
) -> list[Viz]:
    # S58: 제목의 "30일" 은 하드코딩이었다(`--horizon 60` 으로 실행해도
    # "30일" 이 나왔다, 항목 7-1). `horizon_days` 를 받아 실제 요청값을
    # 반영하고, 없으면(레거시 호출부) 숫자 없는 제목으로 낮춘다.
    title = f"{horizon_days}일 결제 부족 위험" if horizon_days is not None else "결제 부족 위험"
    gauge = GaugeViz(
        id="risk",
        title=title,
        priority=1,
        data=GaugeData(
            value=result.risk_score, min=0, max=100, thresholds=[20, 50], level=result.level
        ),
        encoding=GaugeEncoding(unit="점"),
        caption=(
            f"위험 점수 {_render(facts_by_key, 'risk_score', 1)}, "
            f"{_render(facts_by_key, 'level')} 단계."
        ),
    )

    rows = [
        {
            "due": pr.due.isoformat(),
            "name": pr.name,
            "amount": pr.amount,
            "fail_prob": round(pr.fail_prob * 100),
        }
        for pr in result.payment_risks
    ]
    worst = max(result.payment_risks, key=lambda p: p.fail_prob, default=None)
    annotations = []
    if worst is not None:
        annotations.append(
            Annotation(
                type="point",
                x=worst.due,
                label=f"가장 위험한 결제일 {_render(facts_by_key, 'payment_risk_due_1')}",
            )
        )
    table = TableViz(
        id="payments",
        title="결제일별 부족 확률",
        priority=1,
        data=TableData(
            columns=[
                ColumnSpec(key="due", label="결제일", unit="date"),
                ColumnSpec(key="name", label="항목"),
                ColumnSpec(key="amount", label="금액", unit="KRW"),
                ColumnSpec(key="fail_prob", label="부족 확률", unit="%"),
            ],
            rows=rows,
        ),
        annotations=annotations,
        caption=f"오늘 안심 소비 한도는 {_render(facts_by_key, 'safe_to_spend_today')}다.",
    )

    # RiskResult 에는 별도 events 목록이 없어(SPEC 8.5), payment_risks 를
    # event_timeline 의 원천으로 재사용한다 - SPEC 과 다르게 한 점(보고 참조).
    event_timeline = EventTimelineViz(
        id="risk_events",
        title="위험 결제 타임라인",
        priority=1,
        data=EventTimelineData(
            events=[
                EventPoint(
                    date=pr.due,
                    kind=pr.kind,
                    name=pr.name,
                    amount=pr.amount,
                    fail_prob=pr.fail_prob,
                )
                for pr in result.payment_risks
            ]
        ),
        caption=f"예상 부족액은 {_render(facts_by_key, 'expected_shortfall')}다.",
    )

    return [gauge, table, event_timeline]


# ---------------------------------------------------------------------------
# OPTIMIZE
# ---------------------------------------------------------------------------


def _optimize_unit(objective: str) -> str:
    if objective == "MAX_END_BALANCE":
        return "KRW"
    return "%"


def _optimize_effect_value(effect: dict[str, float | int | str], objective: str) -> float:
    delta = effect.get("delta")
    if isinstance(delta, (int, float)):
        return float(delta) * 100 if objective != "MAX_END_BALANCE" else float(delta)
    return 0.0


def _viz_optimize(
    result: OptimizeResult,
    facts_by_key: dict[str, Fact],
    as_of: date,
    horizon_days: int | None = None,
) -> list[Viz]:
    unit = _optimize_unit(result.objective)
    items = []
    for ra in result.ranked:
        label = _joined_action_label(ra.actions, ra.rank)
        items.append(
            RankedItem(
                rank=ra.rank,
                label=label,
                effect=_optimize_effect_value(ra.effect, result.objective),
                unit=unit,
                # B8/항목 7-1: `ra.feasibility_note` 는 `optimize.py` 가 만든
                # 자유 문장으로, "이번 달 이미 사용 X원, 남은 한도 Y원" 처럼
                # facts 에 등록되지 않은 금액을 그대로 담고 있다(§9.3 R7
                # 위반). facts 로 등록하지 않은 값이므로 렌더러에 넘기지
                # 않는다(리뷰 수정 지시의 두 옵션 중 "비운다" 쪽을 택함).
                detail="",
            )
        )

    ranked_bars = RankedBarsViz(
        id="ranked_actions",
        title="행동 후보 효과 순위",
        priority=1,
        data=RankedBarsData(items=items),
        caption=f"1위 행동은 {_render(facts_by_key, 'top_action_label')}다.",
    )

    baseline_pct = round(result.baseline.shortfall_prob * 100)
    delta_items = [
        DeltaItem(
            name="부족 확률",
            base=baseline_pct,
            branch=(
                baseline_pct + _optimize_effect_value(result.ranked[0].effect, "MIN_SHORTFALL_PROB")
            )
            if result.ranked
            else baseline_pct,
            delta=_optimize_effect_value(result.ranked[0].effect, "MIN_SHORTFALL_PROB")
            if result.ranked
            else 0.0,
            unit="%",
        )
    ]
    delta_bars = DeltaBarsViz(
        id="optimize_delta",
        title="권장 조합 효과",
        priority=1,
        data=DeltaBarsData(items=delta_items),
        caption=f"기준 부족 확률은 {_render(facts_by_key, 'baseline_shortfall_prob')}다.",
    )

    return [ranked_bars, delta_bars]


_MODE_BUILDERS: dict[Mode, Callable[[Any, dict[str, Fact], date, int | None], list[Viz]]] = {
    Mode.FORECAST: _viz_forecast,
    Mode.WHATIF: _viz_whatif,
    Mode.GOAL: _viz_goal,
    Mode.RISK: _viz_risk,
    Mode.OPTIMIZE: _viz_optimize,
}


def build_viz(
    mode: Mode,
    result: ResultUnion,
    facts: list[Fact],
    *,
    as_of: date,
    horizon_days: int | None = None,
) -> list[Viz]:
    """모드별 result + facts -> viz 명세 목록 (SPEC 9.3, 9.4).

    `horizon_days` 는 요청(`ModeRequest.horizon_days`) 값을 그대로 받는다
    (S58) - 지금은 RISK gauge 제목만 실제로 쓴다("30일" 하드코딩 결함,
    항목 7-1). 다른 모드는 이미 구체적인 날짜/기간을 결과에서 뽑아 쓰므로
    받기만 하고 쓰지 않는다(자리만 맞춘다).
    """

    builder = _MODE_BUILDERS.get(mode)
    if builder is None:
        raise ValueError(f"알 수 없는 모드: {mode!r}")
    facts_by_key = _facts_by_key(facts)
    return builder(result, facts_by_key, as_of, horizon_days)  # type: ignore[arg-type]


__all__ = ["build_viz"]
