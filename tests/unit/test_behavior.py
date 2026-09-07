"""`fdt.engine.behavior` 단위 테스트 (SPEC v0.3 §6, PLAN §5.1 test_behavior).

4 프로필은 `fdt.gen.generator.generate(months=6, seed=7)` 로 메모리에서만
생성한다(파일에 쓰지 않는다). 6개월이면 §6 의 기본 윈도우(90일)가 항상
찬다. 이 테스트 파일은 평가 코드이므로 생성기·`ground_truth` 를 참조해도
되지만(SPEC 11장), `fdt/engine/behavior.py` 자체는 생성기·정답을 전혀
읽지 않는다(아래 순환 금지 테스트로 이중 확인).
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from datetime import time as dtime
from pathlib import Path

import pytest

from fdt.engine.behavior import detect_income_schedule, estimate_behavior
from fdt.engine.ledger import LedgerTx, normalize
from fdt.engine.taxonomy import (
    ENVELOPE_IDS,
    ESSENTIAL_ENVELOPES,
    FLEXIBLE_ENVELOPES,
    ConfirmStatus,
    ExcludeTag,
    Flow,
)
from fdt.gen import generate

END = date(2026, 9, 7)
MONTHS = 6
SEED = 7

_ALL_ENVELOPE_IDS = tuple(sorted(ENVELOPE_IDS.values()))
_FLEXIBLE_IDS = {ENVELOPE_IDS[name] for name in FLEXIBLE_ENVELOPES}
_ESSENTIAL_IDS = {ENVELOPE_IDS[name] for name in ESSENTIAL_ENVELOPES}
_YOSIK_ID = ENVELOPE_IDS["외식"]


# ---------------------------------------------------------------------------
# 작은 원장 조립 도우미(수작업 경계값 테스트용, LedgerTx 를 직접 만든다)
# ---------------------------------------------------------------------------


def make_tx(
    id_: int,
    d: date,
    *,
    envelope_id: int | None = None,
    amount: int = 10_000,
    flow: Flow = Flow.SPEND,
    card_id: int | None = None,
    account_id: int | None = None,
    confidence: float = 1.0,
    exclude_tag: ExcludeTag = ExcludeTag.NONE,
) -> LedgerTx:
    signed = amount if flow in (Flow.INCOME, Flow.REFUND) else -amount
    return LedgerTx(
        id=id_,
        date=d,
        time=dtime(12, 0, 0),
        account_id=account_id,
        card_id=card_id,
        signed_amount=signed,
        flow=flow,
        envelope_id=envelope_id,
        subcategory_id=None,
        confidence=confidence,
        source="SEED",
        merchant_name_raw=None,
        exclude_tag=exclude_tag,
        confirm_status=ConfirmStatus.AUTO,
        origin_tx_id=id_,
        counterparty_account_id=None,
    )


def _flat_budgets(amount: int = 100_000) -> dict[int, int]:
    return {eid: amount for eid in _ALL_ENVELOPE_IDS}


# ---------------------------------------------------------------------------
# 프로필 fixture (모듈 스코프 - 생성 비용 절감)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", params=["A_steady", "B_card_crunch", "C_impulsive", "D_goal_saver"])
def profile(request):
    name = request.param
    twin, _dict, gt = generate(name, seed=SEED, months=MONTHS, end=END)
    led = normalize(twin)
    return name, twin, led, gt


def _budgets_for(twin) -> dict[int, int]:
    ym = twin.as_of.strftime("%Y%m")
    budgets = _flat_budgets(300_000)
    for b in twin.budgets:
        if b.budget_month != ym:
            continue
        for e in b.envelopes:
            amount = e.confirmed_amount if e.confirmed_amount is not None else e.proposed_amount
            if amount is not None:
                budgets[e.envelope_id] = amount
    return budgets


@pytest.fixture(scope="module")
def profile_behavior(profile):
    name, twin, led, gt = profile
    beh = estimate_behavior(led, twin.as_of, budgets=_budgets_for(twin))
    return name, twin, led, gt, beh


# ---------------------------------------------------------------------------
# 1. 요일 배수 평균 1.0 (4 프로필 x 7 봉투 전부)
# ---------------------------------------------------------------------------


def test_weekday_mult_mean_is_one_for_generated_profiles(profile_behavior):
    _name, _twin, _led, _gt, beh = profile_behavior
    for env in beh.envelopes:
        mean = sum(env.weekday_mult) / 7
        assert abs(mean - 1.0) < 1e-9, (env.envelope_id, env.weekday_mult, mean)


def test_weekday_mult_all_ones_when_sample_small():
    as_of = date(2026, 9, 7)
    records = tuple(
        make_tx(i, as_of - timedelta(days=i * 3), envelope_id=_YOSIK_ID) for i in range(5)
    )
    beh = estimate_behavior(records, as_of, budgets=_flat_budgets())
    env = next(e for e in beh.envelopes if e.envelope_id == _YOSIK_ID)
    assert env.n_obs == 5 < 10
    assert env.weekday_mult == [1.0] * 7


# ---------------------------------------------------------------------------
# 2. 금액 로그정규: sigma 클립, pooled 경로, 기본값 경로
# ---------------------------------------------------------------------------


def test_amount_sigma_clipped_to_upper_bound():
    as_of = date(2026, 9, 7)
    amounts = [100, 100_000_000, 100, 100_000_000, 100]
    records = tuple(
        make_tx(i, as_of - timedelta(days=i), envelope_id=_YOSIK_ID, amount=a)
        for i, a in enumerate(amounts)
    )
    beh = estimate_behavior(records, as_of, budgets=_flat_budgets())
    env = next(e for e in beh.envelopes if e.envelope_id == _YOSIK_ID)
    assert env.amount_sigma == pytest.approx(1.5)


def test_amount_sigma_clipped_to_lower_bound():
    as_of = date(2026, 9, 7)
    records = tuple(
        make_tx(i, as_of - timedelta(days=i), envelope_id=_YOSIK_ID, amount=10_000)
        for i in range(5)
    )
    beh = estimate_behavior(records, as_of, budgets=_flat_budgets())
    env = next(e for e in beh.envelopes if e.envelope_id == _YOSIK_ID)
    assert env.amount_sigma == pytest.approx(0.2)


def test_amount_params_use_pooled_when_envelope_sample_below_five():
    """봉투 하나가 n<5 면 다른 봉투와 합친 pooled 분포를 쓴다."""

    as_of = date(2026, 9, 7)
    transport_id = ENVELOPE_IDS["교통비"]
    records = []
    rid = 0
    for i in range(3):
        records.append(make_tx(rid, as_of - timedelta(days=i), envelope_id=_YOSIK_ID, amount=5_000))
        rid += 1
    for i in range(3):
        records.append(
            make_tx(rid, as_of - timedelta(days=i + 10), envelope_id=transport_id, amount=50_000)
        )
        rid += 1

    beh = estimate_behavior(tuple(records), as_of, budgets=_flat_budgets())
    yosik = next(e for e in beh.envelopes if e.envelope_id == _YOSIK_ID)
    transport = next(e for e in beh.envelopes if e.envelope_id == transport_id)

    pooled_amounts = [5_000] * 3 + [50_000] * 3
    logs = [math.log(a) for a in pooled_amounts]
    expected_mu = sum(logs) / len(logs)

    assert yosik.n_obs == 3 < 5
    assert transport.n_obs == 3 < 5
    assert yosik.amount_mu == pytest.approx(expected_mu)
    assert yosik.amount_mu == pytest.approx(transport.amount_mu)


def test_amount_params_default_when_pooled_also_below_five():
    as_of = date(2026, 9, 7)
    records = tuple(
        make_tx(i, as_of - timedelta(days=i), envelope_id=_YOSIK_ID, amount=5_000) for i in range(2)
    )
    beh = estimate_behavior(records, as_of, budgets=_flat_budgets())
    env = next(e for e in beh.envelopes if e.envelope_id == _YOSIK_ID)
    assert env.amount_mu == pytest.approx(math.log(10_000))
    assert env.amount_sigma == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# 3. card_share
# ---------------------------------------------------------------------------


def test_card_share_zero_sample_falls_back_to_overall_ratio():
    as_of = date(2026, 9, 7)
    transport_id = ENVELOPE_IDS["교통비"]
    records = tuple(
        make_tx(i, as_of - timedelta(days=i), envelope_id=_YOSIK_ID, amount=5_000, card_id=20)
        for i in range(6)
    )
    beh = estimate_behavior(records, as_of, budgets=_flat_budgets())
    transport = next(e for e in beh.envelopes if e.envelope_id == transport_id)
    assert transport.n_obs == 0
    assert transport.card_share == pytest.approx(1.0)  # 전체(외식) 가 전부 카드


def test_card_share_defaults_to_half_when_no_spend_at_all():
    as_of = date(2026, 9, 7)
    beh = estimate_behavior((), as_of, budgets=_flat_budgets())
    for env in beh.envelopes:
        assert env.n_obs == 0
        assert env.card_share == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# 4. 탄력도(elasticity)
# ---------------------------------------------------------------------------


def test_elasticity_default_when_low_remaining_days_below_five():
    as_of = date(2026, 9, 7)
    records = tuple(
        make_tx(i, as_of - timedelta(days=i * 7), envelope_id=_YOSIK_ID, amount=1_000)
        for i in range(5)
    )
    # 예산이 충분히 커서 잔여율이 절대 0.2 밑으로 안 내려감 -> 저잔여일 0일.
    beh = estimate_behavior(records, as_of, budgets=_flat_budgets(10_000_000))
    env = next(e for e in beh.envelopes if e.envelope_id == _YOSIK_ID)
    assert env.elasticity == pytest.approx(1.0)


def test_elasticity_reacts_when_budget_runs_low_within_month():
    as_of = date(2026, 9, 7)
    budget = 100_000
    records = []
    rid = 1
    for month_start in (date(2026, 7, 1), date(2026, 8, 1), date(2026, 9, 1)):
        for day_offset, amt in enumerate([40_000, 40_000, 20_000]):
            d = month_start + timedelta(days=day_offset)
            if d <= as_of:
                records.append(make_tx(rid, d, envelope_id=_YOSIK_ID, amount=amt))
                rid += 1
        for day_offset in range(3, 20):
            d = month_start + timedelta(days=day_offset)
            if d <= as_of:
                records.append(make_tx(rid, d, envelope_id=_YOSIK_ID, amount=3_000))
                rid += 1
    beh = estimate_behavior(tuple(records), as_of, budgets=_flat_budgets(budget), window_days=90)
    env = next(e for e in beh.envelopes if e.envelope_id == _YOSIK_ID)
    # 저잔여일 소비(3,000)가 정상일 소비(40,000/20,000)보다 훨씬 작으므로
    # 탄력도는 하한(0.5) 근처로 클립된다.
    assert env.elasticity == pytest.approx(0.5)


def test_essential_envelope_elasticity_clipped_within_narrow_bounds(profile_behavior):
    """N11/S41: 필수 봉투(교통비/의료·건강/편의점·마트·잡화)는 탄력도가
    [0.8, 1.2] 안에 있어야 한다(4 프로필 전부)."""

    _name, _twin, _led, _gt, beh = profile_behavior
    for env in beh.envelopes:
        if env.envelope_id in _ESSENTIAL_IDS:
            assert 0.8 <= env.elasticity <= 1.2, (env.envelope_id, env.elasticity)


# ---------------------------------------------------------------------------
# 4b. N14/S43: 봉투 금액 추정(amount_mu/sigma)과 daily_rate 는 돌발 제외
# ---------------------------------------------------------------------------


def test_envelope_amount_estimate_excludes_shock_classified_records():
    as_of = date(2026, 9, 7)
    records = []
    rid = 1
    for i in range(29):
        records.append(
            make_tx(rid, as_of - timedelta(days=i), envelope_id=_YOSIK_ID, amount=10_000)
        )
        rid += 1
    # 돌발 1건: 1차 예비 mu 로 정한 임계(약 61,525원)를 훌쩍 넘는 금액.
    records.append(
        make_tx(rid, as_of - timedelta(days=29), envelope_id=_YOSIK_ID, amount=5_000_000)
    )

    beh = estimate_behavior(tuple(records), as_of, budgets=_flat_budgets())
    env = next(e for e in beh.envelopes if e.envelope_id == _YOSIK_ID)

    # 돌발 1건이 봉투 표본(n_obs)과 daily_rate/amount_mu 추정에서 제외된다.
    assert env.n_obs == 29
    assert env.amount_mu == pytest.approx(math.log(10_000))
    assert env.amount_sigma == pytest.approx(0.2)
    assert env.daily_rate == pytest.approx(29 / 30)


# ---------------------------------------------------------------------------
# 4c. N21: 이력 < 28일이면 봉투 pooled 전환 기준을 5 -> 10 으로 올린다
# ---------------------------------------------------------------------------


def test_short_history_raises_pooled_threshold_to_ten():
    as_of = date(2026, 9, 7)
    transport_id = ENVELOPE_IDS["교통비"]
    records = []
    rid = 1
    # 이력 10일 (< 28일 -> short_history) 안에 봉투당 7건(>=5, <10) 씩.
    for i in range(7):
        records.append(
            make_tx(rid, as_of - timedelta(days=i), envelope_id=_YOSIK_ID, amount=5_000)
        )
        rid += 1
    for i in range(7):
        records.append(
            make_tx(rid, as_of - timedelta(days=i), envelope_id=transport_id, amount=50_000)
        )
        rid += 1

    beh = estimate_behavior(tuple(records), as_of, budgets=_flat_budgets())
    assert beh.window_days < 28
    yosik = next(e for e in beh.envelopes if e.envelope_id == _YOSIK_ID)
    transport = next(e for e in beh.envelopes if e.envelope_id == transport_id)

    assert yosik.n_obs == 7
    # short_history 라 n_e(7) < 10 -> pooled(전체 14건) 로 대체되어, 봉투
    # 단독(5,000원) mu 와 달라야 한다.
    assert yosik.amount_mu == pytest.approx(transport.amount_mu)
    assert yosik.amount_mu != pytest.approx(math.log(5_000))


# ---------------------------------------------------------------------------
# 5. payday_boost / pre_payday_damp
# ---------------------------------------------------------------------------


def test_payday_boost_default_when_no_income_events():
    as_of = date(2026, 9, 7)
    records = tuple(
        make_tx(i, as_of - timedelta(days=i * 5), envelope_id=_YOSIK_ID, amount=10_000)
        for i in range(8)
    )
    beh = estimate_behavior(records, as_of, budgets=_flat_budgets())
    assert beh.payday_boost == pytest.approx(1.0)
    assert beh.pre_payday_damp == pytest.approx(1.0)


def test_payday_boost_and_pre_payday_damp_clip_to_bounds():
    """수입 간격 31일(>=12, N12/S35 겹침 없음)이면 두 값 모두 추정한다."""

    as_of = date(2026, 9, 7)
    window_start = as_of - timedelta(days=89)
    income_days = []
    d = as_of
    while d >= window_start:
        income_days.append(d)
        d -= timedelta(days=31)

    records = []
    rid = 1
    for idx, iday in enumerate(income_days):
        records.append(
            make_tx(1000 + idx, iday, amount=1_000_000, flow=Flow.INCOME, account_id=10)
        )

    d = window_start
    while d <= as_of:
        is_before = any(1 <= (iday - d).days <= 5 for iday in income_days)
        amount = 50_000 if is_before else 1_000
        records.append(make_tx(rid, d, envelope_id=_YOSIK_ID, amount=amount))
        rid += 1
        d += timedelta(days=1)

    beh = estimate_behavior(tuple(records), as_of, budgets=_flat_budgets(1_000_000), window_days=90)
    assert beh.income.irregular is False
    assert beh.income.median_gap_days == 31
    # 급여일 당일 소비가 작아 boost 는 하한(0.7), 급여 전 5일 소비가 커서
    # damp 는 상한(1.3) 으로 각각 클립된다.
    assert beh.payday_boost == pytest.approx(0.7)
    assert beh.pre_payday_damp == pytest.approx(1.3)


def test_payday_windows_overlap_forces_damp_to_one():
    """N12/S35: 수입 간격이 12일 미만이면 pre_payday_damp 는 1.0 으로
    고정하고(추정하지 않음), payday_boost 는 겹치는 "급여 전" 날을 분모·
    분자에서 제외하고 추정한다."""

    as_of = date(2026, 9, 7)
    window_start = as_of - timedelta(days=89)
    income_days = []
    d = as_of
    while d >= window_start:
        income_days.append(d)
        d -= timedelta(days=10)

    records = []
    rid = 1
    for idx, iday in enumerate(income_days):
        records.append(
            make_tx(1000 + idx, iday, amount=1_000_000, flow=Flow.INCOME, account_id=10)
        )

    d = window_start
    while d <= as_of:
        is_before = any(1 <= (iday - d).days <= 5 for iday in income_days)
        amount = 50_000 if is_before else 1_000
        records.append(make_tx(rid, d, envelope_id=_YOSIK_ID, amount=amount))
        rid += 1
        d += timedelta(days=1)

    beh = estimate_behavior(tuple(records), as_of, budgets=_flat_budgets(1_000_000), window_days=90)
    assert beh.income.median_gap_days is not None
    assert beh.income.median_gap_days < 12
    assert beh.pre_payday_damp == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 6. detect_income_schedule: A/B/C/D + 1건 이하
# ---------------------------------------------------------------------------


def test_detect_income_schedule_regular_salary(profile):
    name, twin, led, _gt = profile
    sched = detect_income_schedule(led, twin.as_of)
    if name == "A_steady":
        assert sched.irregular is False
        assert sched.expected == 3_150_000
        assert sched.next_date == date(2026, 9, 25)
    elif name == "B_card_crunch":
        # 더치페이(REFUND, DUTCH) 가 섞여도 INCOME 흐름만 집계하므로 규칙적으로
        # 판정돼야 한다(B2 회귀).
        assert sched.irregular is False
        assert sched.expected == 2_870_000
        assert sched.next_date == date(2026, 9, 25)
    elif name == "C_impulsive":
        assert sched.irregular is True
    elif name == "D_goal_saver":
        assert sched.irregular is False
        assert sched.expected == 2_600_000
        assert sched.next_date == date(2026, 9, 10)


def test_detect_income_schedule_single_event_returns_none():
    sched = detect_income_schedule(
        (make_tx(1, date(2026, 8, 1), amount=1_000_000, flow=Flow.INCOME, account_id=10),),
        date(2026, 9, 7),
    )
    assert sched.next_date is None
    assert sched.expected == 0
    assert sched.irregular is True
    assert sched.median_gap_days is None


def test_detect_income_schedule_empty_ledger_returns_none():
    sched = detect_income_schedule((), date(2026, 9, 7))
    assert sched.next_date is None
    assert sched.expected == 0
    assert sched.irregular is True


def test_detect_income_schedule_low_confidence_ignored():
    """confidence < 0.5 인 INCOME 은 수입 판정에서 제외된다."""

    records = tuple(
        make_tx(
            i,
            date(2026, 6, 25) + timedelta(days=30 * i),
            amount=1_000_000,
            flow=Flow.INCOME,
            confidence=0.4,
        )
        for i in range(3)
    )
    sched = detect_income_schedule(records, date(2026, 9, 7))
    assert sched.next_date is None
    assert sched.expected == 0
    assert sched.irregular is True


# ---------------------------------------------------------------------------
# 7. 정답 대조(느슨) - 프로필 hidden 값과 추정 방향 확인
# ---------------------------------------------------------------------------


def test_direction_against_hidden_params(profile_behavior):
    name, _twin, _led, _gt, beh = profile_behavior
    yosik = next(e for e in beh.envelopes if e.envelope_id == _YOSIK_ID)

    if name == "C_impulsive":
        assert yosik.elasticity > 1.0
        # 주말(토=5, 일=6) 소비 배수가 평일보다 커야 한다.
        weekday_avg = sum(yosik.weekday_mult[0:5]) / 5
        weekend_avg = (yosik.weekday_mult[5] + yosik.weekday_mult[6]) / 2
        assert weekend_avg > weekday_avg
    elif name == "A_steady":
        assert yosik.elasticity < 1.0 or yosik.elasticity == pytest.approx(1.0)
        assert yosik.card_share <= 0.5
    elif name == "B_card_crunch":
        assert yosik.card_share >= 0.8


# ---------------------------------------------------------------------------
# 8. 순환 금지(모듈 단위) - 아키텍처 테스트와 중복이지만 이 파일에서도 확인
# ---------------------------------------------------------------------------


def test_behavior_module_has_no_forbidden_strings():
    src = Path("fdt/engine/behavior.py").read_text(encoding="utf-8").lower()
    for token in ("ground_truth", "hidden_params", "yaml"):
        assert token not in src, f"behavior.py 에 금지 문자열 '{token}' 발견"


def test_behavior_module_does_not_import_gen_or_random_or_time():
    src = Path("fdt/engine/behavior.py").read_text(encoding="utf-8")
    assert "import random" not in src
    assert "fdt.gen" not in src
    assert "from time import" not in src or "perf_counter" in src


# ---------------------------------------------------------------------------
# 9. 재현성
# ---------------------------------------------------------------------------


def test_reproducibility_same_input_same_output(profile):
    _name, twin, led, _gt = profile
    budgets = _budgets_for(twin)
    beh1 = estimate_behavior(led, twin.as_of, budgets=budgets)
    beh2 = estimate_behavior(led, twin.as_of, budgets=budgets)
    assert beh1.model_dump(mode="json") == beh2.model_dump(mode="json")
