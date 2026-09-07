"""Behavior(행동 모델) 추정 (SPEC v0.3 §6).

원장(`LedgerTx`)만 읽는다. 생성기 프로필 설정이나 정답 파일은 절대 읽지
않는다(순환 검증 금지, SPEC §6 "Behavior 는 원장만 읽는다").

공개 함수 (다른 작업 ID 가 import 하는 계약):

- `estimate_behavior(ledger, as_of, *, budgets, window_days=None) -> Behavior`
- `detect_income_schedule(ledger, as_of) -> IncomeSchedule`

S49(오케스트레이터 결정, 리뷰 `docs/reviews/20260907_W6_W10.md` 항목 2-3
`R10`): 추정 창을 `[as_of-89, as_of]` 90일 고정에서 "가용 이력 전체(상한
180일), 하한 28일(부족하면 있는 만큼)" 로 완화했다. `window_days=None`
이면 `min(180, 실제 이력 일수)` 를 쓴다. 90일 창에서 봉투별 건수 추정이
시드에 따라 ±26% 흩어져 30일 누적 소비가 0.74~1.10배로 갈리던 것이
A·D 프로필 커버리지 이탈의 직접 원인이었다(표본 크기 ∝ 창 길이이므로
창을 넓히면 표준오차가 준다).
"""

from __future__ import annotations

import calendar
import math
from collections import Counter
from datetime import date, timedelta
from itertools import pairwise

import numpy as np

from fdt.engine.ledger import LedgerTx
from fdt.engine.schemas.behavior import Behavior, EnvelopeBehavior, ShockModel
from fdt.engine.schemas.state import IncomeSchedule
from fdt.engine.taxonomy import ENVELOPE_IDS, ESSENTIAL_ENVELOPES, ExcludeTag, Flow

__all__ = ["detect_income_schedule", "estimate_behavior"]

# ---------------------------------------------------------------------------
# 상수 (SPEC §6 표)
# ---------------------------------------------------------------------------

# S49: 창은 더 이상 90일 고정이 아니다. `window_days=None` 이면
# `min(_MAX_WINDOW_DAYS, 가용 이력 일수)` 를 쓴다(하한 28일은 `_resolve_window`
# 가 이미 이력 부족 시 실제 이력 일수로 자동 클립하므로 별도 강제가 필요
# 없다 - 요청값이 28 미만이어도 결과는 항상 "있는 만큼"이 된다).
_MAX_WINDOW_DAYS = 180
_WEEKDAY_ALPHA = 2.0

_DEFAULT_AMOUNT_MU = math.log(10_000)
_DEFAULT_AMOUNT_SIGMA = 0.6

_DEFAULT_SHOCK_PROB = 0.01
_DEFAULT_SHOCK_MU = math.log(100_000)
_DEFAULT_SHOCK_SIGMA = 0.6

# SPEC v0.3 §6 (S38): 돌발 임계(max(50_000, 5*exp(mu_e)))가 일상 소비의
# 오른쪽 꼬리를 잘라내 절단분포를 만들기 때문에, 하한 없이 원시 표준편차를
# 그대로 쓰면 sigma≈0(사실상 결정론적 돌발)이 되어 더 나쁘다. 하한 0.3 은 SPEC
# §6 표에 명문화된 안정화 상수다.
_SHOCK_SIGMA_FLOOR = 0.3

_MIN_AMOUNT_SAMPLE = 5
# N21/SPEC §3.3 "이력 < 28일이면 Behavior 는 기본값 비중을 높인다": 이력이
# 짧을 때(윈도우 실제 일수 < 28)만 봉투별 pooled 전환 기준을 5 -> 10 으로
# 올려 소표본 잡음을 줄인다. 이력이 충분하면 기존 기준(5)을 그대로 쓴다.
_MIN_AMOUNT_SAMPLE_SHORT_HISTORY = 10
_SHORT_HISTORY_DAYS = 28
_MIN_WEEKDAY_SAMPLE = 10
_MIN_PAYDAY_BOOST_SAMPLE_DAYS = 14
_MIN_PRE_PAYDAY_SAMPLE_DAYS = 10
# N11/S41: 저잔여일 표본 가드를 5 -> 10 으로 올린다. 저잔여일이 5~10일
# 구간일 때 한두 건의 큰 결제가 비율을 지배해 필수 봉투 탄력도가 상·하한에
# 자주 튀는 문제(SPEC S24 의도 위반)를 완화한다.
_MIN_ELASTICITY_LOW_DAYS = 10
# N11/S41: 필수 봉투(교통비/의료·건강/편의점·마트·잡화)는 탄력도를 1.0
# 근처로 더 좁게 클립하고, 유연 봉투는 기존 범위를 유지한다.
_ESSENTIAL_ELASTICITY_BOUNDS = (0.8, 1.2)
_FLEXIBLE_ELASTICITY_BOUNDS = (0.5, 2.0)
# N12/S35: 급여 창 겹침(수입 간격 < 12일 또는 불규칙) 임계.
_PAYDAY_WINDOW_OVERLAP_GAP_DAYS = 12
# S49 항목 2: daily_rate 축소 추정(shrinkage, alpha=14, pooled_rate 로
# 당김)은 시도·측정했으나 채택하지 않는다 - D_goal_saver seed=1 커버리지가
# 오히려 악화됐다(0.233 -> 0.067). 근거는 docs/EVAL_REPORT.md 변경 이력.

_ENVELOPE_EXCLUDED_TAGS: frozenset[ExcludeTag] = frozenset(
    {ExcludeTag.EMERGENCY, ExcludeTag.CARRYOVER}
)

_ALL_ENVELOPE_IDS: tuple[int, ...] = tuple(sorted(ENVELOPE_IDS.values()))
_ESSENTIAL_ENVELOPE_IDS: frozenset[int] = frozenset(
    ENVELOPE_IDS[name] for name in ESSENTIAL_ENVELOPES
)


# ---------------------------------------------------------------------------
# 작은 통계 도우미 (numpy 만 사용, random/time 미사용)
# ---------------------------------------------------------------------------


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _lognormal_params(amounts: list[int]) -> tuple[float, float]:
    """로그정규 MLE. SPEC §6: n<5 면 호출자가 pooled/기본값으로 대체한다."""

    if len(amounts) < _MIN_AMOUNT_SAMPLE:
        return _DEFAULT_AMOUNT_MU, _DEFAULT_AMOUNT_SIGMA
    logs = [math.log(a) for a in amounts if a > 0]
    if len(logs) < _MIN_AMOUNT_SAMPLE:
        return _DEFAULT_AMOUNT_MU, _DEFAULT_AMOUNT_SIGMA
    arr = np.asarray(logs, dtype=float)
    mu = float(arr.mean())
    sigma = float(arr.std(ddof=0))
    return mu, min(1.5, max(0.2, sigma))


def _clamped_month_date(year: int, month: int, day: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def _next_day_of_month(as_of: date, day_of_month: int) -> date:
    """`as_of` 이후 첫 번째로 `day_of_month`(말일 보정)에 해당하는 날짜."""

    year, month = as_of.year, as_of.month
    for _ in range(24):
        candidate = _clamped_month_date(year, month, day_of_month)
        if candidate > as_of:
            return candidate
        month += 1
        if month == 13:
            month, year = 1, year + 1
    return as_of + timedelta(days=1)  # pragma: no cover - 실질적으로 도달 불가


# ---------------------------------------------------------------------------
# 원장 -> 윈도우 / 유효 소비 (SPEC §6 첫 문단)
# ---------------------------------------------------------------------------


def _default_window_request(ledger: tuple[LedgerTx, ...], as_of: date) -> int:
    """S49: `window_days=None` 일 때의 요청 창 길이.

    "가용 이력 전체, 상한 180일" - 가용 이력이 180일보다 길면 180일로
    자르고, 짧으면 있는 만큼만 요청한다(하한 28일 강제는 불필요: 이력이
    28일 미만이면 이 값도 28 미만이 되고, `_resolve_window` 가 어차피
    `min(available)` 로 시작점을 클립해 결과 `n_days` 는 항상 실제
    이력 일수와 같아진다).
    """

    available = [record.date for record in ledger if record.date <= as_of]
    if not available:
        return 1
    history_days = (as_of - min(available)).days + 1
    return min(_MAX_WINDOW_DAYS, history_days)


def _resolve_window(
    ledger: tuple[LedgerTx, ...], as_of: date, window_days: int
) -> tuple[date, int]:
    """윈도우 시작일과 실제 이력 일수. 이력이 짧으면 실제 이력 일수를 쓴다."""

    requested_start = as_of - timedelta(days=window_days - 1)
    available = [record.date for record in ledger if record.date <= as_of]
    if not available:
        return as_of, 1
    start = max(requested_start, min(available))
    return start, (as_of - start).days + 1


def _refund_key(record: LedgerTx) -> tuple[int | None, date, int]:
    return (record.card_id, record.date, abs(record.signed_amount))


def _effective_spends(
    ledger: tuple[LedgerTx, ...], start: date, end: date
) -> list[LedgerTx]:
    """SPEND 만, 같은 날·같은 카드·같은 금액의 승인+취소 쌍 제거 (SPEC §6)."""

    candidates = [
        record
        for record in ledger
        if record.flow == Flow.SPEND
        and record.envelope_id is not None
        and start <= record.date <= end
    ]
    refund_counts: Counter[tuple[int | None, date, int]] = Counter(
        _refund_key(record)
        for record in ledger
        if record.flow == Flow.REFUND
        and record.card_id is not None
        and start <= record.date <= end
    )

    effective: list[LedgerTx] = []
    for record in candidates:
        if record.card_id is not None:
            key = _refund_key(record)
            if refund_counts[key] > 0:
                refund_counts[key] -= 1
                continue
        effective.append(record)
    return effective


def _daily_totals(records: list[LedgerTx]) -> dict[date, int]:
    totals: dict[date, int] = {}
    for record in records:
        totals[record.date] = totals.get(record.date, 0) + abs(record.signed_amount)
    return totals


# ---------------------------------------------------------------------------
# 수입 일정 (SPEC §6.6)
# ---------------------------------------------------------------------------


def _income_event_days(
    ledger: tuple[LedgerTx, ...], as_of: date
) -> list[tuple[date, int]]:
    """INCOME 거래(confidence >= 0.5)를 일자별로 합산한 (날짜, 금액) 목록."""

    totals: dict[date, int] = {}
    for record in ledger:
        if record.flow != Flow.INCOME or record.confidence < 0.5 or record.date > as_of:
            continue
        totals[record.date] = totals.get(record.date, 0) + record.signed_amount
    return sorted(totals.items())


def detect_income_schedule(
    ledger: tuple[LedgerTx, ...], as_of: date
) -> IncomeSchedule:
    """SPEC §6.6 수입 일정 추정.

    간격 cv <= 0.25 이고 day-of-month 최빈 비율 >= 0.6 이면 규칙적: 다음
    예정일은 `as_of` 이후 첫 그 day-of-month(말일 보정), 금액은 중앙값. 그
    외에는 불규칙: 다음 예정일 = 마지막 수입일 + 중앙 간격(as_of 이하면
    as_of+1). 수입 1건 이하면 next_date=None, expected=0, irregular=True.
    """

    events = _income_event_days(ledger, as_of)
    dates = [d for d, _amount in events]
    amounts = [amount for _d, amount in events]

    if len(dates) <= 1:
        return IncomeSchedule(next_date=None, expected=0, irregular=True, median_gap_days=None)

    gaps = [(b - a).days for a, b in pairwise(dates)]
    mean_gap = sum(gaps) / len(gaps)
    if mean_gap > 0:
        variance = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
        cv = math.sqrt(variance) / mean_gap
    else:
        cv = 0.0

    dom_counts = Counter(d.day for d in dates)
    # 최다 빈도, 동률이면 작은 day-of-month 를 고른다(결정론적 tie-break).
    mode_dom, mode_count = min(dom_counts.items(), key=lambda item: (-item[1], item[0]))
    p_dom = mode_count / len(dates)
    expected = round(_median([float(a) for a in amounts]))
    median_gap = max(1, round(_median([float(g) for g in gaps])))

    if cv <= 0.25 and p_dom >= 0.6:
        next_date = _next_day_of_month(as_of, mode_dom)
        return IncomeSchedule(
            next_date=next_date, expected=expected, irregular=False, median_gap_days=median_gap
        )

    next_date = dates[-1] + timedelta(days=median_gap)
    if next_date <= as_of:
        next_date = as_of + timedelta(days=1)
    return IncomeSchedule(
        next_date=next_date, expected=expected, irregular=True, median_gap_days=median_gap
    )


# ---------------------------------------------------------------------------
# payday_boost / pre_payday_damp (SPEC §6 표, §7.2 5단계)
# ---------------------------------------------------------------------------


def _is_after_income(day: date, income_dates: list[date]) -> bool:
    # 수입 후 7일: 급여일 당일 포함 7일(거리 0..6).
    return any(0 <= (day - income_day).days <= 6 for income_day in income_dates)


def _is_before_income(day: date, income_dates: list[date]) -> bool:
    # 다음 수입 5일 전: 급여일 자체는 제외한 5일(거리 1..5).
    return any(1 <= (income_day - day).days <= 5 for income_day in income_dates)


def _payday_boost(
    daily_spend: dict[date, int],
    window_start: date,
    as_of: date,
    income_dates: list[date],
    *,
    exclude_before_window: bool,
) -> float:
    """SPEC §6/S35: 수입 간격이 12일 미만(또는 불규칙)이라 급여 후 창과
    다음 급여 전 창이 겹칠 때는, "다음 수입 5일 전" 창에 속한 날을 분모·
    분자(after_vals/other_vals) 양쪽 모두에서 제외하고 추정한다."""

    after_vals: list[int] = []
    other_vals: list[int] = []
    day = window_start
    while day <= as_of:
        val = daily_spend.get(day, 0)
        if _is_after_income(day, income_dates):
            after_vals.append(val)
        elif exclude_before_window and _is_before_income(day, income_dates):
            pass
        else:
            other_vals.append(val)
        day += timedelta(days=1)

    if len(after_vals) < _MIN_PAYDAY_BOOST_SAMPLE_DAYS or not other_vals:
        return 1.0
    baseline = sum(other_vals) / len(other_vals)
    if baseline <= 0:
        return 1.0
    ratio = (sum(after_vals) / len(after_vals)) / baseline
    return min(2.0, max(0.7, ratio))


def _pre_payday_damp(
    daily_spend: dict[date, int], window_start: date, as_of: date, income_dates: list[date]
) -> float:
    before_vals: list[int] = []
    other_vals: list[int] = []
    day = window_start
    while day <= as_of:
        val = daily_spend.get(day, 0)
        is_before = _is_before_income(day, income_dates)
        is_after = _is_after_income(day, income_dates)
        if is_before:
            before_vals.append(val)
        elif not is_after:
            # SPEC 요구사항: "그 외" 는 급여 후 7일과 급여 전 5일을 모두
            # 제외한 날.
            other_vals.append(val)
        day += timedelta(days=1)

    if len(before_vals) < _MIN_PRE_PAYDAY_SAMPLE_DAYS or not other_vals:
        return 1.0
    baseline = sum(other_vals) / len(other_vals)
    if baseline <= 0:
        return 1.0
    ratio = (sum(before_vals) / len(before_vals)) / baseline
    return min(1.3, max(0.5, ratio))


# ---------------------------------------------------------------------------
# 봉투별 요일 배수 (SPEC §6 표)
# ---------------------------------------------------------------------------


def _weekday_mult(
    env_records: list[LedgerTx], window_start: date, as_of: date, daily_rate: float
) -> list[float]:
    if len(env_records) < _MIN_WEEKDAY_SAMPLE:
        return [1.0] * 7

    days_per_weekday = [0] * 7
    day = window_start
    while day <= as_of:
        days_per_weekday[day.weekday()] += 1
        day += timedelta(days=1)

    counts = [0] * 7
    for record in env_records:
        counts[record.date.weekday()] += 1

    raw = [
        (counts[w] + _WEEKDAY_ALPHA) / (daily_rate * days_per_weekday[w] + _WEEKDAY_ALPHA)
        for w in range(7)
    ]
    raw_mean = sum(raw) / 7
    if raw_mean <= 0:
        return [1.0] * 7
    return [value / raw_mean for value in raw]


# ---------------------------------------------------------------------------
# 봉투별 탄력도 (SPEC §6 표)
# ---------------------------------------------------------------------------


def _envelope_daily_net_spend(
    ledger: tuple[LedgerTx, ...], envelope_id: int, as_of: date
) -> dict[date, int]:
    """봉투 e 의 일별 순지출(양수, EMERGENCY/CARRYOVER 제외). 전체 이력 사용
    (탄력도의 "해당 월 1일 ~ t-1" 누적은 윈도우 경계 밖도 필요할 수 있다)."""

    totals: dict[date, int] = {}
    for record in ledger:
        if record.envelope_id != envelope_id:
            continue
        if record.flow not in (Flow.SPEND, Flow.REFUND):
            continue
        if record.exclude_tag in _ENVELOPE_EXCLUDED_TAGS:
            continue
        if record.date > as_of:
            continue
        totals[record.date] = totals.get(record.date, 0) - record.signed_amount
    return totals


def _elasticity(
    ledger: tuple[LedgerTx, ...],
    envelope_id: int,
    window_start: date,
    as_of: date,
    budget: int,
    *,
    essential: bool,
) -> float:
    daily_net = _envelope_daily_net_spend(ledger, envelope_id, as_of)
    safe_budget = max(1, budget)

    low_values: list[int] = []
    normal_values: list[int] = []
    prior = 0
    current_month: tuple[int, int] | None = None
    day = window_start
    while day <= as_of:
        month = (day.year, day.month)
        if month != current_month:
            month_start = date(day.year, day.month, 1)
            prior = sum(
                amount for d, amount in daily_net.items() if month_start <= d < day
            )
            current_month = month
        amount = daily_net.get(day, 0)
        remaining_ratio = 1.0 - prior / safe_budget
        if remaining_ratio < 0.2:
            low_values.append(amount)
        else:
            normal_values.append(amount)
        prior += amount
        day += timedelta(days=1)

    if len(low_values) < _MIN_ELASTICITY_LOW_DAYS or not normal_values:
        return 1.0
    baseline = sum(normal_values) / len(normal_values)
    if baseline <= 0:
        return 1.0
    ratio = (sum(low_values) / len(low_values)) / baseline
    lo, hi = _ESSENTIAL_ELASTICITY_BOUNDS if essential else _FLEXIBLE_ELASTICITY_BOUNDS
    return min(hi, max(lo, ratio))


# ---------------------------------------------------------------------------
# 돌발 지출 (SPEC §6 표)
# ---------------------------------------------------------------------------


def _shock_threshold(env_mu: float) -> float:
    """돌발 판정 임계: max(50,000원, 5 * exp(mu_e)). N14/S43: 봉투 금액
    추정(amount_mu/sigma)과 daily_rate 는 이 임계 이상인 돌발 건을 제외하고
    2차 재추정한다(1차 mu 로 돌발 판정 -> 2차 재추정)."""

    return max(50_000.0, 5.0 * math.exp(env_mu))


def _shock_model(
    spends: list[LedgerTx], amount_mu_by_env: dict[int, float], n_days: int
) -> ShockModel:
    shocks: list[int] = []
    for record in spends:
        amount = abs(record.signed_amount)
        env_mu = amount_mu_by_env.get(record.envelope_id, _DEFAULT_AMOUNT_MU)  # type: ignore[arg-type]
        threshold = _shock_threshold(env_mu)
        if amount >= threshold:
            shocks.append(amount)

    if not shocks:
        return ShockModel(
            daily_prob=_DEFAULT_SHOCK_PROB, mu=_DEFAULT_SHOCK_MU, sigma=_DEFAULT_SHOCK_SIGMA
        )

    logs = [math.log(a) for a in shocks]
    arr = np.asarray(logs, dtype=float)
    mu = float(arr.mean())
    sigma = float(arr.std(ddof=0)) if len(logs) > 1 else 0.0
    daily_prob = len(shocks) / max(1, n_days)
    return ShockModel(daily_prob=daily_prob, mu=mu, sigma=max(_SHOCK_SIGMA_FLOOR, sigma))


# ---------------------------------------------------------------------------
# 공개 함수: estimate_behavior
# ---------------------------------------------------------------------------


def estimate_behavior(
    ledger: tuple[LedgerTx, ...],
    as_of: date,
    *,
    budgets: dict[int, int],
    window_days: int | None = None,
) -> Behavior:
    """SPEC §6 전체 표를 따라 Behavior 를 추정한다. 원장만 읽는다.

    S49: `window_days=None`(기본값)이면 "가용 이력 전체, 상한 180일" 을
    쓴다. 명시적으로 정수를 넘기면(예: 테스트에서 좁은 창을 재현할 때)
    그 값을 그대로 요청한다 - 이력이 짧으면 여전히 실제 이력 일수로
    클립된다.
    """

    requested_window = (
        _default_window_request(ledger, as_of) if window_days is None else window_days
    )
    window_start, n_days = _resolve_window(ledger, as_of, requested_window)
    spends = _effective_spends(ledger, window_start, as_of)
    daily_spend = _daily_totals(spends)

    income = detect_income_schedule(ledger, as_of)
    income_dates = [d for d, _amount in _income_event_days(ledger, as_of)]

    total_spends = len(spends)
    pooled_amounts = [abs(record.signed_amount) for record in spends]
    pooled_mu, pooled_sigma = _lognormal_params(pooled_amounts)
    overall_card_share = (
        sum(1 for record in spends if record.card_id is not None) / total_spends
        if total_spends
        else 0.5
    )

    by_env: dict[int, list[LedgerTx]] = {eid: [] for eid in _ALL_ENVELOPE_IDS}
    for record in spends:
        if record.envelope_id in by_env:
            by_env[record.envelope_id].append(record)

    # N21/S: 이력이 짧으면(윈도우 실제 일수 < 28) 봉투별 pooled 전환 기준을
    # 5 -> 10 으로 올린다. 이력이 충분하면 기존 기준(5)을 그대로 쓴다.
    short_history = n_days < _SHORT_HISTORY_DAYS
    envelope_min_amount_sample = (
        _MIN_AMOUNT_SAMPLE_SHORT_HISTORY if short_history else _MIN_AMOUNT_SAMPLE
    )

    # N12/S35: 수입 간격이 12일 미만이거나 불규칙이면 급여 후 창과 다음
    # 급여 전 창이 겹친다. 이 경우 pre_payday_damp 는 추정하지 않고 1.0 으로
    # 고정하며, payday_boost 는 겹치는 "급여 전" 날을 분모·분자에서 제외한다.
    payday_windows_overlap = (
        income.irregular
        or income.median_gap_days is None
        or income.median_gap_days < _PAYDAY_WINDOW_OVERLAP_GAP_DAYS
    )
    payday_boost = _payday_boost(
        daily_spend,
        window_start,
        as_of,
        income_dates,
        exclude_before_window=payday_windows_overlap,
    )
    pre_payday_damp = (
        1.0
        if payday_windows_overlap
        else _pre_payday_damp(daily_spend, window_start, as_of, income_dates)
    )

    # N14/S43: 봉투 금액 추정(amount_mu/sigma)과 daily_rate 는 돌발로 분류된
    # 건(금액 >= max(50_000, 5*exp(mu_e)))을 제외하고 2차로 재추정한다.
    # 1차: 전체 표본으로 예비 mu 를 구해 돌발 임계를 정한다.
    prelim_mu_by_env: dict[int, float] = {}
    for envelope_id in _ALL_ENVELOPE_IDS:
        prelim_amounts = [abs(record.signed_amount) for record in by_env[envelope_id]]
        if len(prelim_amounts) >= envelope_min_amount_sample:
            prelim_mu_by_env[envelope_id], _sigma = _lognormal_params(prelim_amounts)
        else:
            prelim_mu_by_env[envelope_id] = pooled_mu

    # S49 항목 2 비교 측정 결과(docs/EVAL_REPORT.md 변경 이력 참조): 창
    # 확대(180일)에 더해 daily_rate 축소 추정(alpha=14, pooled_rate 로
    # 당김)까지 켜서 측정했더니 D_goal_saver seed=1 커버리지가 오히려
    # 악화됐다(0.233 -> 0.067, B_card_crunch 도 커버리지 통과 시드 수가
    # 줄었다) - 실측 결과 **채택하지 않는다**. 이 문제의 원인은 표본
    # 부족(창을 넓히거나 pooled 로 당겨 고칠 수 있는 것)이 아니라 시드마다
    # 다른 실제 생성 과정의 분산이므로, daily_rate 를 pooled 평균으로
    # 당기면 표본이 두꺼운 프로필까지 편향만 더한다. 창 확대만 남긴다.
    envelope_behaviors: list[EnvelopeBehavior] = []
    amount_mu_by_env: dict[int, float] = {}
    for envelope_id in _ALL_ENVELOPE_IDS:
        env_records_all = by_env[envelope_id]
        n_env_all = len(env_records_all)
        daily_rate_all = n_env_all / n_days

        weekday_mult = _weekday_mult(env_records_all, window_start, as_of, daily_rate_all)

        card_share = (
            sum(1 for record in env_records_all if record.card_id is not None) / n_env_all
            if n_env_all
            else overall_card_share
        )

        # 2차: 1차 mu 로 정한 임계 이상인 돌발 건을 제외하고 재추정한다.
        threshold = _shock_threshold(prelim_mu_by_env[envelope_id])
        env_records = [
            record for record in env_records_all if abs(record.signed_amount) < threshold
        ]
        n_env = len(env_records)
        daily_rate = n_env / n_days

        amounts = [abs(record.signed_amount) for record in env_records]
        if len(amounts) >= envelope_min_amount_sample:
            amount_mu, amount_sigma = _lognormal_params(amounts)
        else:
            amount_mu, amount_sigma = pooled_mu, pooled_sigma
        amount_mu_by_env[envelope_id] = amount_mu

        elasticity = _elasticity(
            ledger,
            envelope_id,
            window_start,
            as_of,
            budgets.get(envelope_id, 10_000),
            essential=envelope_id in _ESSENTIAL_ENVELOPE_IDS,
        )

        envelope_behaviors.append(
            EnvelopeBehavior(
                envelope_id=envelope_id,
                daily_rate=daily_rate,
                weekday_mult=weekday_mult,
                amount_mu=amount_mu,
                amount_sigma=amount_sigma,
                card_share=card_share,
                elasticity=elasticity,
                n_obs=n_env,
            )
        )

    shock = _shock_model(spends, amount_mu_by_env, n_days)

    return Behavior(
        as_of=as_of,
        window_days=n_days,
        envelopes=envelope_behaviors,
        payday_boost=payday_boost,
        pre_payday_damp=pre_payday_damp,
        shock=shock,
        income=income,
    )
