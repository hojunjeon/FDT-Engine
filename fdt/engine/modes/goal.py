"""GOAL 모드 러너 (SPEC 8.4).

`simulate()` 를 기준 1회, 계획(weekly_caps) 검증용으로 1회, 총 두 번만
호출한다(`plan_achieve_prob` 이 "상한을 실제 주입해 재시뮬"해야 하므로 -
PLAN Phase 4 완료 조건). 두 호출 모두 같은 `SimContext`(같은 seed) 를 써서
CRN 을 지킨다.

계산 순서(SPEC 8.4):
1. `H = target_date - as_of` (1~365, ENVELOPE_ADHERE 는 이번 달 말일까지).
   범위를 벗어나면 이 러너가 직접 `FdtError(E-REQ-RANGE)` 를 던진다(작업
   지시 "러너에서 검사").
2. 기준 시뮬 `base = run_sim(make_context(engine, req, horizon_days=H))` ->
   `achieve_prob`(goal_type 별 지표, 아래 `_achieve_prob`/
   `_envelope_adhere_achieve_prob` 참조).
3. 확정 유입 `I`(수입 일정 재사용, 아래 `_confirmed_income` - `state.income`
   의 이미 추정된 일정만 읽고 Behavior 의 수입 추정 자체를 다시 하지
   않는다), 확정 유출 `F`(약정 큐 합(`CARD_BILL` 제외) + 카드 상태 기반
   합 - `_confirmed_outflow` + `_card_confirmed_outflow`, 리뷰 N9/S44).
4. `available`, `baseline_discretionary`(기준 시뮬의 봉투 지출 합 중앙값,
   월 경계 리셋을 되짚어 H 기간 전체 누적으로 복원 - `_cumulative_envelope_totals`),
   `reduction_ratio`(`[0,1]` 로 클립 - available<0 이면 1.0, available>=baseline
   이면 0.0), `required.total_discretionary_cap`(세 겹 클램프: `available`,
   `baseline_discretionary`, `Σ현재 확정 예산 x H/30` 중 최솟값 - 리뷰
   블로커 B5(i), SPEC 제안 S55. 예전에는 두 겹만 클램프해 `available >=
   baseline` 인 주에 상한이 확정 예산을 넘어서(D 프로필 실측 830,000원/월
   ->1,249,160원/월) `plan_achieve_prob` 이 역행했다).
5. 주차 분할과 봉투 배분(`_build_weekly_caps`) - 필수 봉투 하한을 항상
   보장하고(협상 불가 보호), 하한 합이 그 주의 재량 한도를 넘으면 필수만
   채우고 유연은 0 으로 낮춘다(그 주 실제 total_cap 이 하한 합으로
   올라간다 - "협상 불가" 보호가 상한 예산 자체보다 우선한다는 뜻이다).
6. 주차 상한을 봉투별 월 단위 **하드 캡**으로 환산(`cap 합 x 30 / H`, 아래
   `_weekly_caps_to_monthly_hard_caps` 참조)해 `Overrides.hard_caps`(J1,
   SPEC 제안 S55)로 실제 재시뮬 -> `plan_achieve_prob`. 예전에는 소프트
   `Overrides.budgets`(elasticity_gate 문턱만 바꾼다)를 썼는데, 그 문턱을
   올리면 소비가 오히려 늘어나 "절약 계획" 이 달성 확률을 역행시키는
   결함이 있었다(리뷰 블로커 B5) - `hard_caps` 는 진짜 상한이라 이 문제가
   구조적으로 재발하지 않는다.

ENVELOPE_ADHERE 의 `achieve_prob`/`plan_achieve_prob` 은 봉투별 잔여의
**합**이 아니라 **전 봉투 AND**(그 시점에 모든 봉투가 각자 예산 이내)로
잰다(`_envelope_adhere_achieve_prob`, `_common.envelope_adherence_mask` 공용
- `optimize.py` 의 `REACH_GOAL(ENVELOPE_ADHERE)` 분기와 같은 규칙이다,
리뷰 블로커 B5). 합으로 재면 한 봉투의 여유가 다른 봉투의 초과를 상쇄해
버려 SPEC 8.4 "이번 달 **전 봉투** 예산 내" 를 재는 지표가 될 수 없다.
`_goal_indicator` 가 반환하는 "봉투별 잔여 합" 배열은 `gap` 계산에만 계속
쓴다.

ENVELOPE_ADHERE 는 `target_amount`/`target_date` 가 없다(SPEC 8.4 표). 이
러너는 그 경우 `target_date = state.cycle.budget_cycle_end`, 내부 계산용
`target_amount = 0` 으로 취급한다(SPEC 이 이 두 필드를 명시하지 않으므로,
"이번 달 전 봉투 예산 내" 를 "봉투 잔여 합 지표의 목표치는 0(초과 없음)"
으로 읽은 해석이다 - 아래 "SPEC 과 다르게 한 점" 참고, 보고에도 남긴다).
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from fdt.engine._dateutil import add_months
from fdt.engine.errors import E_REQ_RANGE, FdtError
from fdt.engine.modes import register
from fdt.engine.modes._common import envelope_adherence_mask, make_context, run_sim, to_int
from fdt.engine.schemas.request import GoalParams, ModeRequest
from fdt.engine.schemas.result import EnvelopeCap, Gap, GoalResult, Required, WeeklyCap
from fdt.engine.schemas.state import CardState, Committed, IncomeSchedule, State
from fdt.engine.simulate import Overrides, SimulationResult
from fdt.engine.taxonomy import ENVELOPE_IDS, Mode

__all__ = ["run_goal"]

# SPEC 8.4 protect_essential 하한 대상(필수 봉투). risk.py 도 같은 이름
# 집합을 별도로 선언한다(모듈 간 private 심볼을 import 하지 않는다는 이
# 저장소의 관례 - risk.py:33 주석 참조) - SPEC 규칙 자체를 재선언한 것이지
# 우연히 같은 값이 아니다.
_ESSENTIAL_IDS: frozenset[int] = frozenset(
    ENVELOPE_IDS[name] for name in ("교통비", "의료·건강", "편의점·마트·잡화")
)

_IRREGULAR_INCOME_FACTOR = 0.8
_ESSENTIAL_FLOOR_RATIO = 0.8
_WEEK_DAYS = 7
_MONTH_DAYS = 30
_CAP_ROUND_UNIT = 100


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# 확정 유입/유출 (SPEC 8.4 계산 문단)
# ---------------------------------------------------------------------------


def _confirmed_income(income: IncomeSchedule, as_of: date, target_date: date) -> int:
    """확정 유입 `I` (SPEC 8.4: "규칙적이면 H 안 수입 횟수 x expected(as_of
    이후 next_date 부터 매월 같은 일자, 말일 보정), 불규칙 expected x
    (H/median_gap) x 0.8, next 없으면 0").

    `state.income`(Behavior 가 이미 추정한 일정)만 읽는다 - 수입 일정
    추정(§6.6) 자체를 다시 하지 않는다(작업 지시 금지 사항 "수입 일정·큐
    계산 중복 구현"). 월 진행은 공용 `fdt.engine._dateutil.add_months`
    (리뷰 N10: 이전에는 `simulate.py`/`state.py` 와 각각 사본을 들고
    있었다)로 계산한다 - `income.next_date` 를 고정 앵커로 `add_months`
    를 반복 호출하므로("매월 같은 일자, 말일 보정") 앵커 일자가 절대
    드리프트하지 않는다(`add_months` docstring 참조).
    """

    if income.next_date is None:
        return 0

    if income.irregular:
        if not income.median_gap_days:
            return 0
        horizon = (target_date - as_of).days
        occurrences = horizon / income.median_gap_days
        return round(income.expected * occurrences * _IRREGULAR_INCOME_FACTOR)

    count = 0
    k = 0
    d: date | None = income.next_date
    while d is not None and d <= target_date:
        count += 1
        k += 1
        d = add_months(income.next_date, k)
    return count * income.expected


def _card_confirmed_outflow(cards: list[CardState]) -> int:
    """카드대금(미청구 `unbilled` + 미결제 `issued_unpaid`) 총액 (리뷰 N9,
    SPEC 제안 S44).

    약정 큐의 `CARD_BILL` 항목은 `simulate()` 가 이중 반영을 피하려고
    무시하고 카드 상태에서 청구를 직접 재구성하는 것과 같은 정보다
    (`state.py` 의 `unbilled`/`issued_unpaid` 가 정본, S44). 이전에는
    `_confirmed_outflow` 가 큐의 `CARD_BILL` 을 필터 없이 그대로 더해
    `simulate` 와 다른 원천을 읽었다(같은 큐를 두 코드가 다르게 읽는 문제,
    `available` 과소 추정 -> `reduction_ratio` 과대). 이 함수가 카드 상태
    기반 값을 **한 번만** 계상하도록 대체한다.
    """

    total = 0
    for card in cards:
        total += card.unbilled
        total += sum(billing.amount for billing in card.issued_unpaid)
    return total


def _confirmed_outflow(committed: list[Committed], as_of: date, target_date: date) -> int:
    """확정 유출 `F` (SPEC 8.4: "큐 + 월 반복", 본문 "큐(H+7 재생성) amount
    합(SELF_TRANSFER 포함)"). `kind == "CARD_BILL"` 항목은 제외한다(리뷰
    N9/S44) - 그 금액은 `_card_confirmed_outflow` 가 카드 상태에서 직접
    계상하므로, 여기서 큐 항목까지 더하면 이중 계상이 아니라 **다른 값**을
    두 번 세는 것이다(큐는 as_of 스냅샷, 카드 상태는 `simulate` 가 실제로
    읽는 정본).
    """

    return sum(
        item.amount
        for item in committed
        if as_of < item.due <= target_date and item.kind != "CARD_BILL"
    )


# ---------------------------------------------------------------------------
# 기준선 재량 지출 (SPEC 8.4 baseline_discretionary)
# ---------------------------------------------------------------------------


def _cumulative_envelope_totals(sim: SimulationResult) -> dict[int, np.ndarray]:
    """`sim.envelope_spend` 는 달이 바뀌면 리셋된다(SPEC 7.2 5단계 "달이
    바뀌면 spent 리셋") - `baseline_discretionary` 는 H 기간 **전체** 누적
    지출이 필요하므로, 리셋 지점을 되짚어 매일 증분을 다시 더한다(리셋
    당일은 그 값 자체가 이미 그날 하루치다 - 리셋이 그날 소비 반영 전에
    일어난다, SPEC 7.2 5단계는 리셋 이후에 도는 하루 처리의 일부다).
    as_of 당일(k=0, 이미 확정된 이번 달 지출)은 제외한다 - 주차 상한은
    as_of+1 부터 적용되는 미래 재량 지출 몫이다(§8.4 "주차 분할(as_of+1
    부터)").
    """

    dates = sim.dates
    n_paths = sim.envelope_spend.shape[0]
    totals: dict[int, np.ndarray] = {}
    for i, eid in enumerate(sim.envelope_ids):
        total = np.zeros(n_paths, dtype=np.float64)
        prev = sim.envelope_spend[:, i, 0].astype(np.float64)
        for k in range(1, len(dates)):
            cur = sim.envelope_spend[:, i, k].astype(np.float64)
            daily = cur if dates[k].day == 1 else cur - prev
            total += daily
            prev = cur
        totals[eid] = total
    return totals


# ---------------------------------------------------------------------------
# achieve_prob / gap 지표 (SPEC 8.4 goal_type 표)
# ---------------------------------------------------------------------------


def _goal_indicator(
    goal_type: str, sim: SimulationResult, state: State
) -> np.ndarray:
    """goal_type 별 "경로 지표" 배열(path 축, 실수) - `gap` 이 이 배열에서
    나온다. `achieve_prob`/`plan_achieve_prob` 은 BALANCE/SAVE 만 이 배열을
    그대로 쓰고, ENVELOPE_ADHERE 는 `_envelope_adhere_achieve_prob`(AND
    마스크, 아래 참조)을 따로 쓴다 - 봉투별 잔여의 **합** 은 한 봉투의
    여유가 다른 봉투의 초과를 상쇄해 버려 "전 봉투 예산 내" 를 재는 지표가
    될 수 없기 때문이다(리뷰 블로커 B5). 이 배열은 ENVELOPE_ADHERE 의
    `gap`(연속값이 필요한 보조 지표) 용으로만 계속 쓴다.
    """

    if goal_type == "BALANCE":
        return sim.balances[:, -1].astype(np.float64)
    if goal_type == "SAVE":
        # M2 확정: PRIMARY 잔액 증가분이되, **경제 잔액**(청구서 미납·억제
        # 수요까지 반영) 기준으로 잰다(리뷰 N8) - `balances` 기준이면
        # 카드 미결제 청구서가 쌓인 경로에서 "저축했다" 로 과대 계상된다.
        return (sim.economic[:, -1] - sim.economic[:, 0]).astype(np.float64)

    # ENVELOPE_ADHERE: 봉투별 (budget - spent) 합 - `gap` 보조 지표용으로만
    # 남긴다(위 docstring 참조, H 가 이번 달 말일까지라 월 경계 리셋이 없어
    # `envelope_spend[:, :, -1]` 을 그대로 써도 된다).
    budget_by_id = {e.envelope_id: e.budget for e in state.envelopes}
    remaining = np.zeros(sim.envelope_spend.shape[0], dtype=np.float64)
    for i, eid in enumerate(sim.envelope_ids):
        remaining += budget_by_id.get(eid, 0) - sim.envelope_spend[:, i, -1].astype(np.float64)
    return remaining


def _achieve_prob(goal_type: str, indicator: np.ndarray, target_amount: int) -> float:
    if indicator.size == 0:
        return 0.0
    return float(np.mean(indicator >= target_amount))


def _envelope_adhere_achieve_prob(sim: SimulationResult, state: State, idx: int) -> float:
    """ENVELOPE_ADHERE 의 진짜 지표: 그 시점에 **전 봉투가 AND** 로 각자
    예산 이내인 경로 비율(리뷰 블로커 B5, `optimize.py` 의
    `REACH_GOAL(ENVELOPE_ADHERE)` 분기와 같은 규칙을 `_common.
    envelope_adherence_mask` 로 공용화한 것)."""

    budgets = {e.envelope_id: e.budget for e in state.envelopes}
    mask = envelope_adherence_mask(sim, budgets, idx)
    return float(mask.mean()) if mask.size else 0.0


def _gap(indicator: np.ndarray, target_amount: int) -> Gap:
    diff = indicator - target_amount
    median = to_int(float(np.median(diff))) if diff.size else 0
    p10 = to_int(float(np.percentile(diff, 10))) if diff.size else 0
    return Gap(median=median, p10=p10)


# ---------------------------------------------------------------------------
# 주차 분할 · 봉투 배분 (SPEC 8.4 "주차 상한", "봉투 배분")
# ---------------------------------------------------------------------------


def _week_day_counts(horizon_days: int) -> list[int]:
    """as_of+1 부터 7일 단위, 마지막 주는 잔여일(SPEC 8.4 "주차 분할")."""

    counts: list[int] = []
    remaining = horizon_days
    while remaining > 0:
        take = min(_WEEK_DAYS, remaining)
        counts.append(take)
        remaining -= take
    return counts


def _round_down_100(value: float) -> int:
    return int(value) // _CAP_ROUND_UNIT * _CAP_ROUND_UNIT


def _round_envelope_caps(
    raw_alloc: dict[int, float], essential_ids: frozenset[int]
) -> tuple[int, dict[int, int]]:
    """봉투별 100원 내림 + 잔여를 가장 큰 유연 봉투에 배분(SPEC 8.4 "caps
    100원 단위 내림, 잔여를 가장 큰 유연 봉투에 배분해 Σ == total_cap").
    반환하는 `total_cap` 은 `raw_alloc` 합의 반올림 값이다(이 주의 실제
    합의를 그대로 보고한다 - 필수 하한이 원래 목표보다 커진 주는 이
    `total_cap` 도 그만큼 커진다).
    """

    total_cap = to_int(sum(raw_alloc.values()))
    floored = {eid: _round_down_100(v) for eid, v in raw_alloc.items()}
    remainder = total_cap - sum(floored.values())

    if remainder != 0 and floored:
        # "가장 큰 유연 봉투" 가 우선이지만, 필수만 채우는 주(essential_only,
        # 유연이 전부 0)에는 유연 봉투에 잔여를 더하면 "유연 0" 이 깨진다
        # (§8.4 "필수만 채우고 유연 0"). 배분액이 0 보다 큰 봉투 중에서
        # 고른다 - 우선 유연, 없으면 필수, 그마저 없으면(전부 0) 첫 봉투.
        positive_flexible = [
            eid for eid in floored if eid not in essential_ids and raw_alloc[eid] > 0
        ]
        positive_any = [eid for eid in floored if raw_alloc[eid] > 0]
        pool = positive_flexible or positive_any or list(floored.keys())
        target_id = max(pool, key=lambda eid: raw_alloc[eid])
        floored[target_id] += remainder

    return total_cap, floored


def _allocate_week(
    target_w: float,
    baseline_e: dict[int, float],
    baseline_share: dict[int, float],
    essential_ids: frozenset[int],
    days_w: int,
    horizon_days: int,
    protect_essential: bool,
) -> tuple[dict[int, float], bool]:
    """이 주의 봉투별 원시(반올림 전) 배분과, 필수 하한 보호가 발동해
    유연 봉투를 0 으로 내렸는지(`essential_only`) 를 반환한다.

    필수 봉투 하한은 `0.8 x baseline_e x days_w/H` 로 고정이다(SPEC 8.4) -
    그 주의 실제 재량 한도(`target_w`, 이미 reduction_ratio 가 반영됨)와
    무관하게 계산한다. 하한 합이 `target_w` 를 넘으면(감액이 필수 봉투조차
    지킬 수 없을 만큼 심하면) 필수는 하한 그대로 보장하고 유연은 0 으로
    낮춘다 - 그 주의 실제 합계(`_round_envelope_caps` 가 반환하는
    `total_cap`)는 이때 `target_w` 대신 하한 합으로 올라간다("협상 불가"
    보호가 예산 자체보다 우선한다).
    """

    envelope_ids = list(baseline_e.keys())
    fraction = days_w / horizon_days if horizon_days else 0.0

    floor_e: dict[int, float] = {}
    if protect_essential:
        for eid in envelope_ids:
            if eid in essential_ids:
                floor_e[eid] = _ESSENTIAL_FLOOR_RATIO * baseline_e[eid] * fraction

    sum_floor = sum(floor_e.values())

    if protect_essential and sum_floor > target_w:
        alloc = {eid: floor_e.get(eid, 0.0) for eid in envelope_ids if eid in essential_ids}
        for eid in envelope_ids:
            if eid not in essential_ids:
                alloc[eid] = 0.0
        return alloc, True

    baseline_alloc = {eid: target_w * baseline_share.get(eid, 0.0) for eid in envelope_ids}
    alloc = dict(baseline_alloc)
    for eid, floor_amount in floor_e.items():
        alloc[eid] = max(alloc[eid], floor_amount)

    used_by_essential = sum(alloc[eid] for eid in floor_e)
    remaining = max(0.0, target_w - used_by_essential)
    flexible_ids = [eid for eid in envelope_ids if eid not in floor_e]
    flexible_baseline_sum = sum(baseline_alloc[eid] for eid in flexible_ids)
    if flexible_baseline_sum > 0:
        for eid in flexible_ids:
            alloc[eid] = remaining * (baseline_alloc[eid] / flexible_baseline_sum)
    elif flexible_ids:
        share = remaining / len(flexible_ids)
        for eid in flexible_ids:
            alloc[eid] = share

    return alloc, False


def _build_weekly_caps(
    horizon_days: int,
    as_of: date,
    total_discretionary_cap: int,
    baseline_e: dict[int, float],
    baseline_discretionary: float,
    essential_ids: frozenset[int],
    protect_essential: bool,
) -> tuple[list[WeeklyCap], bool]:
    envelope_ids = list(baseline_e.keys())
    baseline_share = (
        {eid: baseline_e[eid] / baseline_discretionary for eid in envelope_ids}
        if baseline_discretionary > 0
        else {eid: 1.0 / len(envelope_ids) for eid in envelope_ids}
        if envelope_ids
        else {}
    )

    weekly_caps: list[WeeklyCap] = []
    any_essential_only = False
    offset = 1
    for days_w in _week_day_counts(horizon_days):
        target_w = total_discretionary_cap * days_w / horizon_days
        raw_alloc, essential_only = _allocate_week(
            target_w,
            baseline_e,
            baseline_share,
            essential_ids,
            days_w,
            horizon_days,
            protect_essential,
        )
        any_essential_only = any_essential_only or essential_only

        total_cap, caps_by_env = _round_envelope_caps(raw_alloc, essential_ids)
        weekly_caps.append(
            WeeklyCap(
                week_start=as_of + timedelta(days=offset),
                days=days_w,
                total_cap=total_cap,
                by_envelope=[
                    EnvelopeCap(envelope_id=eid, cap=cap)
                    for eid, cap in sorted(caps_by_env.items())
                ],
            )
        )
        offset += days_w

    return weekly_caps, any_essential_only


def _weekly_caps_to_monthly_hard_caps(
    weekly_caps: list[WeeklyCap], horizon_days: int
) -> dict[int, int]:
    """주차 cap -> 월 단위 하드 캡 환산(`Overrides.hard_caps`, SPEC 8.4
    "상한을 실제 주입해 재시뮬", 리뷰 블로커 B5 + SPEC 제안 S55).

    이전에는 `Overrides.budgets`(소프트, elasticity_gate 문턱만 바꾼다)로
    재시뮬했다 - `available >= baseline_discretionary` 인 주(reduction_
    ratio=0)에서 이 환산값이 확정 예산보다 커지면 예산"인상"이 되어 gate
    문턱이 낮아지고(remaining_ratio 가 0.2 밑으로 안 내려가) 오히려 소비가
    **늘어**(`plan_achieve_prob` 역행 2/10 실측, W9/B5) 버렸다. `Overrides.
    hard_caps` 는 진짜 상한(그 달 누적 체결분이 캡에 닿으면 λ->0)이라 캡이
    확정 예산보다 크더라도 기준 행동 이상으로 소비를 늘리지 않는다 -
    구조적으로 이 회귀가 재발할 수 없다.

    환산 규칙은 그대로다: 봉투별 H 기간 총 cap x 30/H - `hard_caps` 도
    `budgets` 와 같은 "월 누적" 단위이므로(J1 `Overrides.hard_caps`
    docstring), H 일 동안 쓰라고 배분한 총액을 30일 기준으로 스케일한다.
    """

    totals: dict[int, int] = {}
    for wc in weekly_caps:
        for cap in wc.by_envelope:
            totals[cap.envelope_id] = totals.get(cap.envelope_id, 0) + cap.cap
    return {
        eid: to_int(total * _MONTH_DAYS / horizon_days) for eid, total in totals.items()
    }


# ---------------------------------------------------------------------------
# 러너
# ---------------------------------------------------------------------------


@register(Mode.GOAL)
def run_goal(engine, req: ModeRequest) -> GoalResult:
    params: GoalParams = req.params  # type: ignore[assignment]
    state = engine.state
    as_of = state.as_of

    if params.goal_type == "ENVELOPE_ADHERE":
        target_date = state.cycle.budget_cycle_end
        target_amount = 0
    else:
        assert params.target_date is not None and params.target_amount is not None
        target_date = params.target_date
        target_amount = params.target_amount

    horizon_days = (target_date - as_of).days
    if not (1 <= horizon_days <= 365):
        raise FdtError(
            code=E_REQ_RANGE,
            message=f"GOAL 의 target_date 는 as_of 기준 1~365일 이내여야 한다 (H={horizon_days})",
            details={"horizon_days": horizon_days},
        )

    ctx = make_context(engine, req, horizon_days=horizon_days)
    base_sim = run_sim(ctx)

    indicator = _goal_indicator(params.goal_type, base_sim, state)
    gap = _gap(indicator, target_amount)
    if params.goal_type == "ENVELOPE_ADHERE":
        # AND 마스크(리뷰 블로커 B5) - `indicator`(봉투별 잔여의 합)는
        # `gap` 보조 지표로만 쓴다.
        achieve_prob = _envelope_adhere_achieve_prob(base_sim, state, horizon_days)
    else:
        achieve_prob = _achieve_prob(params.goal_type, indicator, target_amount)

    notes: list[str] = []
    if state.income.irregular:
        notes.append("불규칙 수입은 기대치의 80%만 반영")

    confirmed_income = _confirmed_income(state.income, as_of, target_date)
    confirmed_outflow = _confirmed_outflow(ctx.committed, as_of, target_date) + (
        _card_confirmed_outflow(state.cards)
    )

    if params.goal_type == "SAVE":
        available = confirmed_income - confirmed_outflow - target_amount
    else:
        available = state.liquidity + confirmed_income - confirmed_outflow - target_amount

    baseline_totals = _cumulative_envelope_totals(base_sim)
    baseline_e = {eid: float(np.median(arr)) for eid, arr in baseline_totals.items()}
    baseline_discretionary = sum(baseline_e.values())

    feasible = available >= 0
    if not feasible:
        notes.append("가용액(확정 유입-확정 유출-목표액)이 음수라 현재 행동으로는 달성이 어렵다")

    if baseline_discretionary > 0:
        reduction_ratio = _clip(1.0 - available / baseline_discretionary, 0.0, 1.0)
    else:
        reduction_ratio = 0.0

    # 세 겹 클램프(리뷰 블로커 B5(i), SPEC 제안 S55): available/baseline 로
    # 유도한 상한이 "현재 확정 예산의 H 기간 총액"을 넘을 수 없다 - 예전에는
    # `available >= baseline_discretionary` 인 주에 이 상한이 확정 예산(D
    # 프로필 실측 830,000원/월)의 1.5배(1,249,160원/월)까지 치솟았다.
    current_budget_total_h = sum(e.budget for e in state.envelopes) * horizon_days / _MONTH_DAYS
    capped_by_available = baseline_discretionary * (1.0 - reduction_ratio)
    total_discretionary_cap = to_int(
        max(0.0, min(capped_by_available, current_budget_total_h))
    )

    weekly_caps, essential_only_hit = _build_weekly_caps(
        horizon_days,
        as_of,
        total_discretionary_cap,
        baseline_e,
        baseline_discretionary,
        _ESSENTIAL_IDS,
        params.protect_essential,
    )
    if essential_only_hit:
        notes.append("필수 봉투 하한 보장을 위해 일부 주차의 유연 봉투 지출 한도를 0으로 낮췄다")

    monthly_hard_caps = _weekly_caps_to_monthly_hard_caps(weekly_caps, horizon_days)
    plan_sim = run_sim(ctx, overrides=Overrides(hard_caps=monthly_hard_caps))
    if params.goal_type == "ENVELOPE_ADHERE":
        plan_achieve_prob = _envelope_adhere_achieve_prob(plan_sim, state, horizon_days)
    else:
        plan_indicator = _goal_indicator(params.goal_type, plan_sim, state)
        plan_achieve_prob = _achieve_prob(params.goal_type, plan_indicator, target_amount)

    return GoalResult(
        feasible=feasible,
        achieve_prob=achieve_prob,
        gap=gap,
        required=Required(
            total_discretionary_cap=total_discretionary_cap,
            reduction_ratio=reduction_ratio,
            baseline_discretionary=to_int(baseline_discretionary),
        ),
        weekly_caps=weekly_caps,
        plan_achieve_prob=plan_achieve_prob,
        notes=notes,
    )
