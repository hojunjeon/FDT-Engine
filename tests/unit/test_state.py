"""State(t) 빌드 단위 테스트 (SPEC 5장, PLAN 5.1 test_state, W3 완료 조건).

4 프로필(생성기 산출물)을 실제 `fdt.engine.state`(과 `fdt.engine.ledger`)에
통과시켜 검증한다. 이 테스트 파일은 평가 코드이므로 `ground_truth` 를 읽어도
되지만(SPEC 11장), `fdt/engine/**` 자체는 여기서도 `ground_truth` 를
참조하지 않는다 - 이 파일이 참조할 뿐이다(`test_ledger_profiles.py` 와 같은
전제).

`months=3, seed=7, end=2026-09-07` 로 고정한다(`test_ledger_profiles.py` 와
동일한 조합. 이 조합에서의 구체적인 수치는 실제 생성 결과를 스크립트로 직접
확인해 하드코딩했다 - "수작업 계산"에 해당한다).
"""

from __future__ import annotations

import copy
from datetime import date, time, timedelta

import pytest

from fdt.engine import ledger as ledger_mod
from fdt.engine.ledger import LedgerTx
from fdt.engine.schemas.input import TwinInput
from fdt.engine.state import (
    build_committed_queue,
    build_state,
    build_state_with_warnings,
    propose_budgets,
)
from fdt.engine.taxonomy import ENVELOPE_IDS, ConfirmStatus, ExcludeTag, Flow
from fdt.gen import PROFILE_NAMES, generate

END = date(2026, 9, 7)
MONTHS = 3
SEED = 7


def _gen(name: str):
    return generate(name, seed=SEED, months=MONTHS, end=END)


# ---------------------------------------------------------------------------
# 1. liquidity/emergency_fund == ground_truth.daily_balance (4 프로필 x as_of 3개)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
@pytest.mark.parametrize("offset_days", [0, 30, 60])
def test_liquidity_and_emergency_match_ground_truth(name: str, offset_days: int) -> None:
    twin, _d, gt = _gen(name)
    led = ledger_mod.normalize(twin)
    as_of = twin.as_of - timedelta(days=offset_days)

    state = build_state(twin, led, as_of=as_of)

    day_snapshot = gt["daily_balance"][as_of.isoformat()]
    primary_ids = [a.id for a in state.accounts if a.role == "PRIMARY"]
    emergency_ids = [a.id for a in state.accounts if a.role == "EMERGENCY"]
    assert len(primary_ids) == 1, f"{name}: PRIMARY 계좌가 정확히 1개여야 함"

    expected_liquidity = day_snapshot[str(primary_ids[0])]
    expected_emergency = sum(day_snapshot[str(aid)] for aid in emergency_ids)

    assert state.liquidity == expected_liquidity, (
        f"{name} as_of={as_of}: liquidity {state.liquidity} != {expected_liquidity}"
    )
    assert state.emergency_fund == expected_emergency, (
        f"{name} as_of={as_of}: emergency_fund {state.emergency_fund} != {expected_emergency}"
    )


# ---------------------------------------------------------------------------
# 2. as_of 이후 거래 무영향: 같은 twin, 다른 컷오프의 원장이라도 State(as_of=D)
#    는 동일해야 한다(모든 계좌가 opening_balance 를 갖는 4 프로필 기본 생성이라
#    account_balance_at 도 date<=as_of 필터만으로 정확하다).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_future_tx_no_leakage(name: str) -> None:
    twin, _d, _gt = _gen(name)
    as_of = twin.as_of - timedelta(days=30)

    ledger_full = ledger_mod.normalize(twin)
    ledger_truncated = ledger_mod.normalize(twin, as_of=as_of)
    assert len(ledger_truncated) < len(ledger_full), f"{name}: 컷오프가 실제로 걸러내지 못함"

    state_full = build_state(twin, ledger_full, as_of=as_of)
    state_truncated = build_state(twin, ledger_truncated, as_of=as_of)

    assert state_full == state_truncated, (
        f"{name}: as_of({as_of}) 이후 거래가 State 에 영향을 줌"
    )


# ---------------------------------------------------------------------------
# 3. 예산 소스 우선순위: D(CONFIRMED), A(as_of 가 budgets_month 밖 -> ENGINE),
#    override(CONFIRMED)
# ---------------------------------------------------------------------------


def test_budget_source_confirmed_from_input_budgets() -> None:
    twin, _d, _gt = _gen("D_goal_saver")
    led = ledger_mod.normalize(twin)
    state = build_state(twin, led)  # as_of == twin.as_of, budgets_month 일치

    env = state.envelope_by_id(ENVELOPE_IDS["외식"])
    assert env is not None
    assert env.budget_source == "CONFIRMED"
    assert env.budget == 260_000


def test_budget_source_engine_when_no_matching_budget_month() -> None:
    twin, _d, _gt = _gen("A_steady")
    led = ledger_mod.normalize(twin)
    as_of = twin.as_of - timedelta(days=60)  # 입력 budgets 는 twin.as_of 월에만 있음

    state = build_state(twin, led, as_of=as_of)
    env = state.envelope_by_id(ENVELOPE_IDS["외식"])
    assert env is not None
    assert env.budget_source == "ENGINE"


def test_budget_source_override_wins() -> None:
    twin, _d, _gt = _gen("B_card_crunch")
    led = ledger_mod.normalize(twin)
    state = build_state(twin, led, budgets_override={ENVELOPE_IDS["외식"]: 123_450})

    env = state.envelope_by_id(ENVELOPE_IDS["외식"])
    assert env is not None
    assert env.budget_source == "CONFIRMED"
    assert env.budget == 123_450


# ---------------------------------------------------------------------------
# 4. propose_budgets: 완결 월 3/1~2/0 케이스 + 만원 올림 + 하한 10,000원
# ---------------------------------------------------------------------------


def _spend_tx(tx_id: int, tx_date: date, envelope_id: int, amount: int) -> LedgerTx:
    return LedgerTx(
        id=tx_id,
        date=tx_date,
        time=time(12, 0, 0),
        account_id=10,
        card_id=None,
        signed_amount=-amount,
        flow=Flow.SPEND,
        envelope_id=envelope_id,
        subcategory_id=None,
        confidence=1.0,
        source="SEED",
        merchant_name_raw=None,
        exclude_tag=ExcludeTag.NONE,
        confirm_status=ConfirmStatus.CONFIRMED,
        origin_tx_id=tx_id,
        counterparty_account_id=None,
    )


_EAT = ENVELOPE_IDS["외식"]
_OTHER_ENVELOPES = [eid for eid in ENVELOPE_IDS.values() if eid != _EAT]


def test_propose_budgets_three_completed_months_uses_median_and_floor() -> None:
    as_of = date(2026, 9, 7)
    led = (
        _spend_tx(1, date(2026, 6, 15), _EAT, 100_000),
        _spend_tx(2, date(2026, 7, 15), _EAT, 120_000),
        _spend_tx(3, date(2026, 8, 15), _EAT, 140_000),
    )

    proposals = propose_budgets(led, as_of)
    assert proposals[_EAT] == 120_000  # median(100k,120k,140k) 는 이미 만원 단위
    for eid in _OTHER_ENVELOPES:
        assert proposals[eid] == 10_000  # 하한


def test_propose_budgets_one_to_two_completed_months_uses_average() -> None:
    as_of = date(2026, 9, 7)
    led = (
        _spend_tx(1, date(2026, 7, 10), _EAT, 90_000),
        _spend_tx(2, date(2026, 8, 20), _EAT, 130_000),
    )

    proposals = propose_budgets(led, as_of)
    assert proposals[_EAT] == 110_000  # 평균(90k,130k) = 110k, 이미 만원 단위


def test_propose_budgets_zero_completed_months_uses_last_28_days_scaled() -> None:
    as_of = date(2026, 9, 7)
    # 완결 월 없음(9월만 데이터가 있고, 9월은 as_of 시점에 완결되지 않음).
    led = (
        _spend_tx(1, date(2026, 9, 1), _EAT, 30_000),
        _spend_tx(2, date(2026, 9, 7), _EAT, 40_000),
    )

    proposals = propose_budgets(led, as_of)
    # 70,000 * 30/28 = 75,000 -> 올림 80,000
    assert proposals[_EAT] == 80_000


# ---------------------------------------------------------------------------
# 5. 약정 큐: B 프로필 화요일 as_of(2026-08-18) 미청구/미결제 - 실측값을
#    직접 스크립트로 확인해 하드코딩했다(카드20/카드21).
# ---------------------------------------------------------------------------


def _b_state_at(as_of: date):
    twin, d, gt = _gen("B_card_crunch")
    led = ledger_mod.normalize(twin)
    return build_state(twin, led, as_of=as_of), twin, d, gt


def test_committed_queue_b_card20_tuesday_as_of() -> None:
    as_of = date(2026, 8, 18)
    assert as_of.weekday() == 1  # 화요일
    state, _twin, _d, _gt = _b_state_at(as_of)

    card20 = next(c for c in state.cards if c.id == 20)
    assert card20.unbilled == 28_000
    assert [(b.billing_date, b.amount) for b in card20.issued_unpaid] == [
        (date(2026, 8, 17), 146_500)
    ]

    card_bill_20 = [c for c in state.committed if c.kind == "CARD_BILL" and c.card_id == 20]
    by_due = {(c.due, c.amount): c for c in card_bill_20}
    assert (date(2026, 8, 25), 28_000) in by_due  # 미청구(다음 월요일 발행 후 첫 화요일)
    assert by_due[(date(2026, 8, 25), 28_000)].certainty == pytest.approx(0.9)
    assert (date(2026, 8, 19), 146_500) in by_due  # 미결제(due=8/18 <= as_of -> as_of+1 보정)
    assert by_due[(date(2026, 8, 19), 146_500)].certainty == pytest.approx(1.0)


def test_committed_queue_b_card21_saturday_due() -> None:
    as_of = date(2026, 8, 18)
    state, _twin, _d, _gt = _b_state_at(as_of)

    card21 = next(c for c in state.cards if c.id == 21)
    assert card21.unbilled == 14_200
    assert {(b.billing_date, b.amount) for b in card21.issued_unpaid} == {
        (date(2026, 8, 3), 594_000),
        (date(2026, 8, 10), 197_000),
        (date(2026, 8, 17), 356_300),
    }

    card_bill_21 = [c for c in state.committed if c.kind == "CARD_BILL" and c.card_id == 21]
    unbilled_row = next(c for c in card_bill_21 if c.amount == 14_200)
    assert unbilled_row.due.weekday() == 5  # 토요일 (withdrawal_weekday=5)

    # 각 미결제 청구서(연체된 것들)의 금액이 전부 별개 항목으로 살아남아야
    # 한다(연체로 보정된 due 가 우연히 같아도 amount 로 구분돼야 함, N-바이-테스트
    # 회귀: 같은 due 로 뭉쳐 하나가 사라지는 버그가 있었다).
    unpaid_amounts = sorted(c.amount for c in card_bill_21 if c.amount != 14_200)
    assert unpaid_amounts == [197_000, 356_300, 594_000]


def test_committed_queue_monday_as_of_unbilled_boundary() -> None:
    as_of = date(2026, 8, 31)
    assert as_of.weekday() == 0  # 월요일: 이번 청구 주기는 당일부터
    state, _twin, _d, _gt = _b_state_at(as_of)

    card20 = next(c for c in state.cards if c.id == 20)
    card21 = next(c for c in state.cards if c.id == 21)
    assert card20.unbilled == 98_500
    assert card21.unbilled == 30_000


def test_card_bill_not_counted_in_envelope_spent() -> None:
    twin, _d, _gt = _gen("B_card_crunch")
    led = ledger_mod.normalize(twin)
    # 원장 규칙(NFR-BGT-01): CARD_BILL 은 봉투가 없다(ledger.py 가 이미
    # 보장하지만, State 가 이 위에서 spent 를 계산하므로 다시 확인한다).
    assert all(r.envelope_id is None for r in led if r.flow == Flow.CARD_BILL)
    card_bill_count = sum(1 for r in led if r.flow == Flow.CARD_BILL)
    assert card_bill_count > 0, "카드대금 레코드가 없으면 공허한 테스트"


# ---------------------------------------------------------------------------
# 6. LOAN 이자 10원 단위 + loan_rate_delta_bp 반영 (B 프로필)
# ---------------------------------------------------------------------------


def test_loan_interest_10won_rounding_and_delta_bp() -> None:
    twin, _d, _gt = _gen("B_card_crunch")
    led = ledger_mod.normalize(twin)

    state = build_state(twin, led)
    loans = [c for c in state.committed if c.kind == "LOAN"]
    assert loans
    # balance=12,000,000, rate=6.8% -> 12_000_000*6.8/100/12 = 68,000 (이미 10원 단위)
    assert all(c.amount == 68_000 for c in loans)

    twin.externals.loan_rate_delta_bp = 100  # +1.0%p
    state2 = build_state(twin, led)
    loans2 = [c for c in state2.committed if c.kind == "LOAN"]
    assert loans2
    assert all(c.amount == 78_000 for c in loans2)


# ---------------------------------------------------------------------------
# 7. 변동형 고정비: 원장에 매칭되는 거래가 없으면 0원 + 경고
# ---------------------------------------------------------------------------


def test_variable_fixed_expense_unknown_amount_emits_warning() -> None:
    _twin, d, _gt = _gen("A_steady")
    d2 = copy.deepcopy(d)
    d2["fixed_expenses"].append(
        {
            "id": 999,
            "name": "변동생활비",
            "expense_type": "UTILITY",
            "amount": 0,
            "is_variable": True,
            "payment_day": 12,
            "withdrawal_account_id": 10,
            "card_id": None,
            "active": True,
        }
    )
    twin2 = TwinInput.model_validate(d2)
    led2 = ledger_mod.normalize(twin2)

    state, warnings = build_state_with_warnings(twin2, led2)

    matching = [c for c in state.committed if c.name == "변동생활비"]
    assert matching
    assert all(c.amount == 0 for c in matching)
    assert all(c.certainty == pytest.approx(0.8) for c in matching)

    codes = [w.code for w in warnings]
    assert "W-FIXED-VARIABLE-UNKNOWN" in codes
    matching_warning = next(w for w in warnings if w.code == "W-FIXED-VARIABLE-UNKNOWN")
    assert matching_warning.details["fixed_expense_id"] == 999


# ---------------------------------------------------------------------------
# 8. 원장 탐지 반복 자기이체 (A 프로필, 매달 30만원 비상금 이체)
# ---------------------------------------------------------------------------


def test_self_transfer_detected_in_a_profile() -> None:
    twin, _d, _gt = _gen("A_steady")
    led = ledger_mod.normalize(twin)
    state = build_state(twin, led)

    self_transfers = [c for c in state.committed if c.kind == "SELF_TRANSFER"]
    assert self_transfers, "A 프로필의 매달 비상금 이체가 큐에 잡히지 않음"
    for item in self_transfers:
        assert item.amount == 300_000
        assert item.account_id == 10
        assert item.card_id is None
        assert twin.as_of < item.due <= twin.as_of + timedelta(days=90)


# ---------------------------------------------------------------------------
# 9. 중복 제거: 동일 (kind, name, due, amount) 는 큐에 하나만
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_committed_queue_has_no_duplicate_entries(name: str) -> None:
    twin, _d, _gt = _gen(name)
    led = ledger_mod.normalize(twin)
    state = build_state(twin, led)

    keys = [(c.kind, c.name, c.due, c.amount) for c in state.committed]
    assert len(keys) == len(set(keys)), f"{name}: 약정 큐에 중복 항목이 있음"


def test_build_committed_queue_matches_state_committed() -> None:
    """공개 시그니처 `build_committed_queue(twin, ledger, as_of, cards, horizon_cap)`
    가 `build_state` 내부와 같은 결과를 낸다(다른 작업이 독립적으로 호출할 수
    있어야 하므로)."""

    twin, _d, _gt = _gen("B_card_crunch")
    led = ledger_mod.normalize(twin)
    state = build_state(twin, led)

    queue = build_committed_queue(twin, led, twin.as_of, state.cards, horizon_cap=90)
    assert {(c.kind, c.name, c.due, c.amount) for c in queue} == {
        (c.kind, c.name, c.due, c.amount) for c in state.committed
    }


# ---------------------------------------------------------------------------
# 10. 지표: acceleration, unconfirmed_count(SPEND PENDING 만), progress
#     (C 프로필, 수작업 계산과 대조)
# ---------------------------------------------------------------------------


def test_indicators_acceleration_and_unconfirmed_count() -> None:
    twin, _d, _gt = _gen("C_impulsive")
    led = ledger_mod.normalize(twin)
    as_of = twin.as_of
    state = build_state(twin, led, as_of=as_of)

    led_upto = [r for r in led if r.date <= as_of]
    earliest = min(r.date for r in led_upto)
    history_days = (as_of - earliest).days + 1

    def _manual_window_avg(max_days: int) -> float:
        days = min(history_days, max_days)
        window_start = as_of - timedelta(days=days - 1)
        totals = ledger_mod.envelope_net_spend(tuple(led_upto), window_start, as_of)
        return sum(totals.values()) / days

    manual_7d = _manual_window_avg(7)
    manual_90d = _manual_window_avg(90)
    manual_accel = manual_7d / max(manual_90d, 1000.0)

    assert state.indicators.spend_7d_avg == pytest.approx(manual_7d)
    assert state.indicators.spend_90d_avg == pytest.approx(manual_90d)
    assert state.indicators.acceleration == pytest.approx(manual_accel)

    month_start = as_of.replace(day=1)
    manual_unconfirmed = sum(
        1
        for r in led_upto
        if r.flow == Flow.SPEND
        and r.confirm_status == ConfirmStatus.PENDING
        and month_start <= r.date <= as_of
    )
    assert manual_unconfirmed > 0, "PENDING SPEND 이 하나도 없으면 공허한 테스트"
    assert state.indicators.unconfirmed_count == manual_unconfirmed


def test_cycle_progress() -> None:
    twin, _d, _gt = _gen("C_impulsive")
    led = ledger_mod.normalize(twin)
    state = build_state(twin, led)

    assert state.cycle.budget_cycle_start == state.as_of.replace(day=1)
    assert state.cycle.progress == pytest.approx(state.as_of.day / state.cycle.budget_cycle_end.day)


# ---------------------------------------------------------------------------
# 11. 홀드아웃 issued_unpaid 재구성이 실제 청구서 상태와 일치 (B, as_of-30)
# ---------------------------------------------------------------------------


def test_holdout_issued_unpaid_reconstruction_matches_billing_status() -> None:
    twin, d, _gt = _gen("B_card_crunch")
    led = ledger_mod.normalize(twin)
    as_of = twin.as_of - timedelta(days=30)

    state = build_state(twin, led, as_of=as_of)

    for card_id in (20, 21):
        expected: list[tuple[date, int]] = []
        for billing in d["card_billings"]:
            if billing["card_id"] != card_id:
                continue
            billing_date = date.fromisoformat(billing["billing_date"])
            if billing_date > as_of:
                continue
            paid_at = date.fromisoformat(billing["paid_at"]) if billing["paid_at"] else None
            if paid_at is None or paid_at > as_of:
                expected.append((billing_date, billing["total_amount"]))
        expected.sort()

        card_state = next(c for c in state.cards if c.id == card_id)
        actual = sorted((b.billing_date, b.amount) for b in card_state.issued_unpaid)
        assert actual == expected, f"card {card_id} @ {as_of}: {actual} != {expected}"
