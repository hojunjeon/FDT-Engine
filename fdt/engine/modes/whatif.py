"""WHATIF 모드 러너 (SPEC 8.3).

`simulate()` 를 같은 시드(CRN)로 두 번 호출한다: 주입 없는 `base`, 요청이
담은 `params.injections` 를 그대로 넘긴 `branch`(SPEC 8.3, 7.1). 전이 규칙
자체는 여기서 재구현하지 않는다 - `SimulationResult.stats()` 가 이미 계산한
값만 뺄셈·판정한다(작업 지시 금지 사항 "전이 규칙 재구현", "수치 재계산").

설계 메모(작업 지시 대비 실제 코드 확인 결과, 보고에도 적음): SPEC 8.3
표의 7종 주입(SPEND/INCOME/RECURRING_SPEND/FIXED_CHANGE/BUDGET_CHANGE/
EXTERNAL/EMERGENCY_DRAW) 은 `fdt.engine.simulate.simulate()` 가 `injections`
인자 하나로 전부 직접 처리한다(`simulate.py` 의 `for inj in injections:`
분기 참조) - `Overrides` 로 변환해야 하는 타입이 없다. 그래서 이 모듈은
`run_sim(ctx, injections=req.params.injections)` 하나만 부르고, 별도의
"injection -> Overrides 변환 헬퍼"를 두지 않는다.

기준 비교 기준(SPEC 7.4 요구 "stats(economic=True) 로 비교"): `base`/
`branch` 의 `trajectory`/`min_point`/`end_point`/`shortfall_prob`/
`card_shortfall_prob` 은 전부 **경제 잔액**(청구서·미납 의무·억제 수요까지
반영한 잠재 부족, SPEC 7.2 8단계 `economic`) 기준이다 - `BranchSummary`
docstring 에도 명시한다. 실제 잔액(`balances`) 기준 궤적이 필요하면
FORECAST 모드를 쓴다.
"""

from __future__ import annotations

from fdt.engine.modes import register
from fdt.engine.modes._common import (
    level_from_probs,
    make_context,
    point_stats,
    run_sim,
    to_int,
)
from fdt.engine.schemas.request import ModeRequest, WhatIfParams
from fdt.engine.schemas.result import (
    BranchSummary,
    EnvelopeDelta,
    FirstShortfallDate,
    TrajectorySummary,
    WhatIfDelta,
    WhatIfResult,
)
from fdt.engine.schemas.simulate import PathStats
from fdt.engine.simulate import SimulationResult
from fdt.engine.taxonomy import Mode

__all__ = ["classify_verdict", "run_whatif"]

# SPEC 8.3.1 판정 문턱 (리뷰 S52 재정의: `verdict` 는 "주입의 효과"(델타)만
# 본다 - 분기의 절대 위험은 `branch_level` 로 따로 낸다. 재정의 전 규칙(분기
# `card_shortfall_prob >= 0.5` 또는 분기 최저 < 0 -> DANGER)은 기준선이 이미
# 위험한 사용자(C 프로필)에게 0원 주입도 DANGER 를 답하게 만들어 WHATIF 를
# 무의미하게 했다 - 리뷰 20260907_W6_W10.md §4c 실측.
_CAUTION_DELTA_SHORTFALL_PROB = 0.15
_CAUTION_MIN_RATIO = 0.5
_DANGER_DELTA_CARD_SHORTFALL_PROB = 0.3


def classify_verdict(
    *,
    base_min_balance: int,
    branch_min_balance: int,
    delta_card_shortfall_prob: float,
    delta_shortfall_prob: float,
) -> str:
    """WHATIF `verdict` 판정 - **델타(주입의 효과) 기준만** 본다(S52).

    ```
    delta.card_shortfall_prob >= 0.3 또는
        (기준 최저 >= 0 이고 분기 최저 < 0, 즉 주입이 새로 마이너스를 만듦)
                                                                   -> DANGER
    delta.shortfall_prob >= 0.15 또는
        (기준 최저 > 0 이고 분기 최저 < 기준 최저 * 0.5)          -> CAUTION
    그 외                                                          -> OK
    ```

    분기 자체의 절대 위험(기준선이 이미 위험한지)은 이 함수가 answer 하지
    않는다 - `level_from_probs` 로 계산해 `WhatIfResult.branch_level` 에
    별도로 낸다.
    """

    danger_newly_negative = branch_min_balance < 0 and base_min_balance >= 0
    if delta_card_shortfall_prob >= _DANGER_DELTA_CARD_SHORTFALL_PROB or danger_newly_negative:
        return "DANGER"

    caution_by_ratio = (
        base_min_balance > 0 and branch_min_balance < base_min_balance * _CAUTION_MIN_RATIO
    )
    if delta_shortfall_prob >= _CAUTION_DELTA_SHORTFALL_PROB or caution_by_ratio:
        return "CAUTION"

    return "OK"


def _summary_from(stats: PathStats) -> tuple[BranchSummary, int, int]:
    """`PathStats`(economic=True) -> `BranchSummary` + (min_balance, end_balance) 원값.

    `min_balance`/`end_balance` 는 델타 계산에도 그대로 쓰이도록 정수로
    같이 반환한다(반올림은 `to_int`/`point_stats` 가 이미 했다 - 중복
    반올림하지 않는다).
    """

    trajectory = TrajectorySummary(
        dates=stats.dates,
        median=[float(v) for v in stats.median],
        p10=[float(v) for v in stats.p10],
        p90=[float(v) for v in stats.p90],
    )
    min_point, end_point = point_stats(stats)
    summary = BranchSummary(
        trajectory=trajectory,
        min_point=min_point,
        end_point=end_point,
        shortfall_prob=stats.shortfall_prob,
        card_shortfall_prob=stats.card_shortfall_prob,
    )
    return summary, min_point.median_balance, end_point.median_balance


def _envelope_ids_in_injections(injections) -> list[int]:
    """주입이 직접 건드린 봉투 id 목록(순서 보존, 중복 제거).

    `delta.envelopes[]` 를 시뮬레이션이 만들어낸 전 봉투가 아니라 주입이
    실제로 겨냥한 봉투로만 한정한다 - SPEC 8.3 예시도 주입이 건드린 봉투
    하나만 담는다.
    """

    seen: dict[int, None] = {}
    for inj in injections:
        eid = getattr(inj, "envelope_id", None)
        if eid is not None:
            seen.setdefault(eid, None)
    return list(seen)


def _envelope_deltas(
    envelope_ids: list[int],
    base_sim: SimulationResult,
    branch_sim: SimulationResult,
    base_stats: PathStats,
    branch_stats: PathStats,
) -> list[EnvelopeDelta]:
    out: list[EnvelopeDelta] = []
    for eid in envelope_ids:
        base_budget = base_sim.envelope_budgets.get(eid)
        branch_budget = branch_sim.envelope_budgets.get(eid)
        if base_budget is None or branch_budget is None:
            continue
        base_spend = base_stats.envelope_spend_median.get(eid, 0)
        branch_spend = branch_stats.envelope_spend_median.get(eid, 0)
        base_remaining = base_budget - base_spend
        branch_remaining = branch_budget - branch_spend
        base_overrun = base_stats.envelope_overrun_prob.get(eid, 0.0)
        branch_overrun = branch_stats.envelope_overrun_prob.get(eid, 0.0)
        out.append(
            EnvelopeDelta(
                envelope_id=eid,
                remaining_change=to_int(branch_remaining - base_remaining),
                overrun_prob_change=round(branch_overrun - base_overrun, 4),
            )
        )
    return out


@register(Mode.WHATIF)
def run_whatif(engine, req: ModeRequest) -> WhatIfResult:
    params = req.params  # WhatIfParams (ModeRequest 가 mode 로 미리 확정)
    assert isinstance(params, WhatIfParams)  # mypy 유니온 narrowing (S39 와 무관, 타입만)

    ctx = make_context(engine, req)
    base_sim = run_sim(ctx)
    branch_sim = run_sim(ctx, injections=params.injections)

    base_stats = base_sim.stats(economic=True)
    branch_stats = branch_sim.stats(economic=True)

    base_summary, base_min_balance, base_end_balance = _summary_from(base_stats)
    branch_summary, branch_min_balance, branch_end_balance = _summary_from(branch_stats)

    envelope_ids = _envelope_ids_in_injections(params.injections)
    envelope_deltas = _envelope_deltas(
        envelope_ids, base_sim, branch_sim, base_stats, branch_stats
    )

    delta_shortfall_prob = round(branch_stats.shortfall_prob - base_stats.shortfall_prob, 6)
    delta_card_shortfall_prob = round(
        branch_stats.card_shortfall_prob - base_stats.card_shortfall_prob, 6
    )

    delta = WhatIfDelta(
        min_balance=branch_min_balance - base_min_balance,
        end_balance=branch_end_balance - base_end_balance,
        shortfall_prob=delta_shortfall_prob,
        card_shortfall_prob=delta_card_shortfall_prob,
        first_shortfall_date=FirstShortfallDate(
            base=base_stats.first_shortfall_date_median,
            branch=branch_stats.first_shortfall_date_median,
        ),
        envelopes=envelope_deltas,
    )

    verdict = classify_verdict(
        base_min_balance=base_min_balance,
        branch_min_balance=branch_min_balance,
        delta_card_shortfall_prob=delta.card_shortfall_prob,
        delta_shortfall_prob=delta.shortfall_prob,
    )
    branch_level = level_from_probs(
        branch_stats.shortfall_prob, branch_stats.card_shortfall_prob
    )

    return WhatIfResult(
        base=base_summary,
        branch=branch_summary,
        delta=delta,
        verdict=verdict,  # type: ignore[arg-type]
        branch_level=branch_level,  # type: ignore[arg-type]
        crn=True,
    )
