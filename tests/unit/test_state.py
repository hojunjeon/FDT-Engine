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
import itertools
from datetime import date, time, timedelta

import pytest

from fdt.engine import ledger as ledger_mod
from fdt.engine.ledger import LedgerTx
from fdt.engine.schemas.input import TwinInput
from fdt.engine.state import (
    _primary_account_id,  # N6: 2/3순위 분기는 전체 파이프라인으로 닿지 않아
    # (아래 테스트 docstring 참조) 이 내부 헬퍼를 직접 단위 테스트한다.
    build_committed_queue,
    build_state,
    build_state_with_warnings,
    propose_budgets,
)
from fdt.engine.taxonomy import ENVELOPE_IDS, SUBCATEGORIES, ConfirmStatus, ExcludeTag, Flow
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
    # N20: SPEC R6 facts `unknown_variable_fixed` 가 필요로 하는 이름·유형·계좌·
    # 카드까지 details 에 실려야 한다(fixed_expense_id 만으로는 부족).
    assert matching_warning.details["fixed_expense_id"] == 999
    assert matching_warning.details["name"] == "변동생활비"
    assert matching_warning.details["expense_type"] == "UTILITY"
    assert matching_warning.details["withdrawal_account_id"] == 10
    assert matching_warning.details["card_id"] is None


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


# ---------------------------------------------------------------------------
# 12. B3/S30/S31: 대출이자 이중 계상 회귀 - 원장 탐지가 loans[]/fixed_expenses
#     항목을 다시 잡지 않는다. 비활성 고정비 이름도 유령을 만들지 않는다.
# ---------------------------------------------------------------------------


def test_loan_interest_not_double_counted_by_ledger_detection() -> None:
    """B3 회귀: 큐에 "대출이자" 이름의 LOAN 항목만 있어야 하고(원장 탐지가 만드는
    DETECTED_FIXED "대출이자" 유령이 없어야 한다), due 당 정확히 1건이며, 90일
    큐의 대출이자 총 유출이 손계산(68,000원 x 발생 횟수)과 일치해야 한다."""

    twin, _d, _gt = _gen("B_card_crunch")
    led = ledger_mod.normalize(twin)
    state = build_state(twin, led)

    loan_named = [c for c in state.committed if c.name == "대출이자"]
    assert loan_named, "대출이자 항목이 없으면 공허한 테스트"
    assert all(c.kind == "LOAN" for c in loan_named), (
        f"대출이자 이름인데 kind 가 LOAN 이 아닌 유령 항목: "
        f"{[(c.kind, c.due, c.amount) for c in loan_named if c.kind != 'LOAN']}"
    )
    assert all(c.source_loan_id is not None for c in loan_named)

    due_counts: dict[date, int] = {}
    for item in loan_named:
        due_counts[item.due] = due_counts.get(item.due, 0) + 1
    assert all(count == 1 for count in due_counts.values()), (
        f"같은 due 에 대출이자가 2건 이상: {due_counts}"
    )

    # balance=12,000,000, rate=6.8% -> 68,000원/월(이미 10원 단위, 기존
    # test_loan_interest_10won_rounding_and_delta_bp 와 동일한 손계산 기준).
    expected_total = 68_000 * len(loan_named)
    assert sum(c.amount for c in loan_named) == expected_total


def test_inactive_fixed_expense_name_does_not_create_ghost_detected_item() -> None:
    """B3 회귀: 고정비를 비활성화(`active=False`)해도 과거 원장에는 활성 시절의
    `FIXED` 레코드가 그대로 남는다. 제외 목록이 `active` 인 것만 본다면 그
    이름으로 원장 탐지가 다시 유령 `DETECTED_FIXED` 항목을 만들 것이다."""

    _twin, d, _gt = _gen("A_steady")
    d2 = copy.deepcopy(d)
    target = d2["fixed_expenses"][0]
    target_name = target["name"]
    target["active"] = False
    twin2 = TwinInput.model_validate(d2)
    led2 = ledger_mod.normalize(twin2)
    state = build_state(twin2, led2)

    # 비활성화됐으니 fixed_expenses 경로의 정상 항목도 당연히 없어야 한다.
    assert not any(
        c.name == target_name and c.source_fixed_expense_id == target["id"]
        for c in state.committed
    )
    ghost = [c for c in state.committed if c.name == target_name and c.kind == "DETECTED_FIXED"]
    assert ghost == [], f"비활성 고정비 '{target_name}' 이름의 유령 탐지 항목: {ghost}"


def test_detected_fixed_kind_and_source_ids() -> None:
    """S31/S32: 원장 탐지 반복 고정비는 kind=DETECTED_FIXED 이고
    source_fixed_expense_id/source_loan_id/source_card_id 가 전부 None 이다
    (대응하는 입력 레코드가 없으므로). A 프로필은 loans 가 없어 원장 탐지
    대출이자 항목이 생기지 않으므로(대출 자체가 없음), 여기서는 kind 값과
    source_* 필드의 형태만 확인한다."""

    twin, _d, _gt = _gen("B_card_crunch")
    led = ledger_mod.normalize(twin)
    state = build_state(twin, led)

    detected = [c for c in state.committed if c.kind == "DETECTED_FIXED"]
    for item in detected:
        assert item.source_fixed_expense_id is None
        assert item.source_loan_id is None
        assert item.source_card_id is None


# ---------------------------------------------------------------------------
# 13. S32: source_fixed_expense_id/source_loan_id/source_card_id 가 채워짐
# ---------------------------------------------------------------------------


def test_committed_source_ids_populated_for_each_kind() -> None:
    twin, _d, _gt = _gen("B_card_crunch")
    led = ledger_mod.normalize(twin)
    state = build_state(twin, led)

    fixed_items = [c for c in state.committed if c.kind in ("UTILITY", "INSURANCE", "RENT")]
    assert fixed_items
    for item in fixed_items:
        assert item.source_fixed_expense_id is not None
        assert item.source_loan_id is None
        assert item.source_card_id is None

    loan_items = [c for c in state.committed if c.kind == "LOAN"]
    assert loan_items
    for item in loan_items:
        assert item.source_loan_id is not None
        assert item.source_fixed_expense_id is None
        assert item.source_card_id is None

    card_bill_items = [c for c in state.committed if c.kind == "CARD_BILL"]
    assert card_bill_items
    for item in card_bill_items:
        assert item.source_card_id is not None
        assert item.source_fixed_expense_id is None
        assert item.source_loan_id is None


# ---------------------------------------------------------------------------
# 14. S33: CardState.withdrawal_account_id 가 twin.cards 에서 그대로 옮겨온다
# ---------------------------------------------------------------------------


def test_card_state_withdrawal_account_id_matches_input() -> None:
    twin, _d, _gt = _gen("B_card_crunch")
    led = ledger_mod.normalize(twin)
    state = build_state(twin, led)

    card_by_id = {c.id: c for c in twin.cards}
    assert state.cards, "카드가 없으면 공허한 테스트"
    for card_state in state.cards:
        assert card_state.withdrawal_account_id == card_by_id[card_state.id].withdrawal_account_id


# ---------------------------------------------------------------------------
# 15. N5: card_billings 가 비어 있을 때 원장 기반 재구성 경로가 실제로 돌고,
#     card_billings 기반 재구성과 같은 결과를 낸다.
# ---------------------------------------------------------------------------


def test_reconstruct_issued_unpaid_from_ledger_matches_billing_based_path() -> None:
    """N5: `_reconstruct_issued_unpaid_from_billings` 는 이 카드의 `card_billings`
    가 하나도 없을 때만 `None` 을 돌려주고 `_reconstruct_issued_unpaid_from_ledger`
    로 넘어간다. `card_billings=[]` 로 만든 twin 에서는 반드시 이 경로가 실행된다.
    두 재구성 경로는 같은 현실(같은 원장)을 다르게 관찰할 뿐이므로 결과가
    (billing_date, amount) 집합으로 완전히 같아야 한다 - 이는 또한 "결제가
    원장에 CARD_BILL 로 이미 보이면 재구성하지 않는다"도 함께 확인한다(같은
    지 않으면 최소한 한쪽이 이미 결제된 청구서를 미결제로 잘못 남긴 것이다)."""

    twin, d, _gt = _gen("B_card_crunch")
    led = ledger_mod.normalize(twin)
    state_with_billings = build_state(twin, led)

    d2 = copy.deepcopy(d)
    d2["card_billings"] = []
    twin2 = TwinInput.model_validate(d2)
    led2 = ledger_mod.normalize(twin2)
    state_without_billings = build_state(twin2, led2)

    checked_any = False
    for card_id in (20, 21):
        with_billings = sorted(
            (b.billing_date, b.amount)
            for b in next(c for c in state_with_billings.cards if c.id == card_id).issued_unpaid
        )
        without_billings = sorted(
            (b.billing_date, b.amount)
            for b in next(
                c for c in state_without_billings.cards if c.id == card_id
            ).issued_unpaid
        )
        assert with_billings == without_billings, (
            f"card {card_id}: 원장 기반 재구성이 청구서 기반 결과와 다름 "
            f"({with_billings} != {without_billings})"
        )
        if with_billings:
            checked_any = True
    assert checked_any, "미결제 청구서가 하나도 없으면 공허한 테스트"


# ---------------------------------------------------------------------------
# 16. N6: PRIMARY 판정 2/3순위. 실제 원장 정규화 파이프라인에서 Flow.INCOME 은
#     항상 is_income 계좌에서만 나오므로(engine/ledger.py `_classify_flow`),
#     그런 계좌가 있으면 이미 2순위에서 걸린다 - 즉 3순위는 build_state 전체
#     파이프라인으로는 닿을 수 없다(불변 조건). 이 두 분기는 `_primary_account_id`
#     자체의 계약(주어진 twin/원장에서 PRIMARY 를 고르는 규칙)을 직접 검증한다.
# ---------------------------------------------------------------------------


def _account_dict(
    account_id: int, *, is_managed: bool = True, is_income: bool = False
) -> dict[str, object]:
    return {
        "id": account_id,
        "fin_account_no": f"110-{account_id:03d}",
        "bank_code": "004",
        "alias": f"계좌{account_id}",
        "is_managed": is_managed,
        "is_income": is_income,
        "balance": 0,
    }


def _minimal_twin(accounts: list[dict[str, object]]) -> TwinInput:
    payload = {
        "schema_version": "twin-input/1",
        "as_of": "2026-09-07",
        "user": {"id": 1},
        "envelopes": [{"id": eid, "name": name} for name, eid in ENVELOPE_IDS.items()],
        "subcategories": [
            {"id": sid, "envelope_id": eid, "name": name} for sid, eid, name in SUBCATEGORIES
        ],
        "accounts": accounts,
        "cards": [],
    }
    return TwinInput.model_validate(payload)


def test_primary_account_second_priority_is_income_account_without_cards() -> None:
    """SPEC 5.3 2순위: 카드가 없으면 PRIMARY 는 is_income 계좌."""

    twin = _minimal_twin(
        [
            _account_dict(1, is_managed=True, is_income=False),
            _account_dict(2, is_managed=True, is_income=True),
            _account_dict(3, is_managed=False, is_income=True),  # 비관리 계좌는 대상 제외
        ]
    )
    assert twin.cards == []

    primary_id = _primary_account_id(twin, ())
    assert primary_id == 2


def _income_tx(tx_id: int, tx_date: date, account_id: int) -> LedgerTx:
    return LedgerTx(
        id=tx_id,
        date=tx_date,
        time=time(9, 0, 0),
        account_id=account_id,
        card_id=None,
        signed_amount=1_000_000,
        flow=Flow.INCOME,
        envelope_id=None,
        subcategory_id=None,
        confidence=1.0,
        source="SEED",
        merchant_name_raw=None,
        exclude_tag=ExcludeTag.NONE,
        confirm_status=ConfirmStatus.CONFIRMED,
        origin_tx_id=tx_id,
        counterparty_account_id=None,
    )


def test_primary_account_third_priority_income_transaction_majority() -> None:
    """SPEC 5.3 3순위: 카드도 없고 is_income 계좌도 없으면 PRIMARY 는 INCOME
    거래가 가장 많은 계좌. `_classify_flow` 는 `account.is_income` 인 계좌에서만
    `Flow.INCOME` 을 만들므로(engine/ledger.py), 그런 계좌가 twin.accounts 에
    하나라도 있으면 `_primary_account_id` 의 2순위(`is_income` 계좌)가 먼저
    걸려 3순위에 닿지 못한다. 이 테스트는 `_primary_account_id` 를 원장
    정규화를 거치지 않은 합성 원장으로 직접 호출해 3순위 규칙 자체를 검증한다.
    """

    twin = _minimal_twin(
        [
            _account_dict(1, is_managed=True, is_income=False),
            _account_dict(2, is_managed=True, is_income=False),
        ]
    )
    assert twin.cards == []
    assert not any(a.is_income for a in twin.accounts)

    ledger_upto = (
        _income_tx(1, date(2026, 6, 25), account_id=2),
        _income_tx(2, date(2026, 7, 25), account_id=2),
        _income_tx(3, date(2026, 8, 25), account_id=2),
        _income_tx(4, date(2026, 6, 10), account_id=1),
    )
    primary_id = _primary_account_id(twin, ledger_upto)
    assert primary_id == 2


# ---------------------------------------------------------------------------
# 17. W6 준비(S42 예정): build_committed_queue 가 horizon_cap=365 까지 정상
#     동작한다 - 월 반복 고정비 12회, 카드대금(미청구)은 as_of 기준 1회만.
# ---------------------------------------------------------------------------


def test_build_committed_queue_horizon_cap_365_repeats_monthly_twelve_times() -> None:
    twin, _d, _gt = _gen("A_steady")
    led = ledger_mod.normalize(twin)
    state = build_state(twin, led)

    queue = build_committed_queue(twin, led, twin.as_of, state.cards, horizon_cap=365)

    rent_dues = sorted(c.due for c in queue if c.kind == "RENT")
    assert len(rent_dues) == 12, f"365일 안에 월세가 12회 반복돼야 함: {rent_dues}"
    for prev, nxt in itertools.pairwise(rent_dues):
        gap = (nxt - prev).days
        assert 27 <= gap <= 32, f"월세 due 간격이 매월 반복이 아님: {prev} -> {nxt} ({gap}일)"

    # 카드대금(미청구)은 "다음 발행" 단발 이벤트라 horizon_cap 을 늘려도 카드당
    # 최대 1건만 있어야 한다(반복 생성 회귀 방지).
    for card_state in state.cards:
        if card_state.unbilled <= 0:
            continue
        unbilled_items = [
            c
            for c in queue
            if c.kind == "CARD_BILL"
            and c.card_id == card_state.id
            and c.amount == card_state.unbilled
        ]
        assert len(unbilled_items) == 1
