"""4 프로필(생성기 산출물)로 원장을 검증하는 게이트 테스트 (리뷰 B4, N12).

PLAN Phase 1 완료 조건 "4 프로필 대사 차액 0" 과 "봉투 월 순지출 ==
`envelope_true_spend`" 는 리뷰 이전까지 어떤 테스트에도 존재하지 않았다
(`test_generator.py:137-158` 는 `ledger.normalize`/`reconcile` 을 호출하지
않고 생성기 dict 를 테스트가 자체 규칙으로 다시 합산할 뿐이었다). 이 파일은
`fdt.gen.generator.generate()` 로 만든 실제 `TwinInput` 을
`fdt.engine.ledger` 에 직접 통과시켜, 원장 계층이 실제로 대사·봉투 순지출과
일치하는지를 고정한다(리뷰 B4 지시문 1~8, N12, B2 회귀 10 그대로).

`months=3, seed=7` 로 고정해 6개월 생성보다 훨씬 빠르게(<15초) 돈다. 이
테스트는 평가 코드이므로 `ground_truth` 를 읽어도 되지만(SPEC 11장,
"엔진 코드는 ground_truth 를 읽지 않는다"), `fdt/engine/**` 자체는 여기서도
`ground_truth` 를 참조하지 않는다 - 이 파일이 참조할 뿐이다.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta

import pytest

from fdt.engine import ledger
from fdt.engine.taxonomy import ENVELOPE_IDS, Flow
from fdt.gen import PROFILE_NAMES, generate
from fdt.gen.generator import _first_due

END = date(2026, 9, 7)
MONTHS = 3
SEED = 7

_ALL_ENVELOPE_IDS = tuple(ENVELOPE_IDS.values())


def _gen(name: str, *, omit_opening_balance: bool = False):
    return generate(
        name, seed=SEED, months=MONTHS, end=END, omit_opening_balance=omit_opening_balance
    )


def _completed_months(gt: dict, as_of: date) -> list[tuple[date, date]]:
    """`ground_truth.envelope_true_spend` 의 키 중 완결 월(1일~말일 모두
    `as_of` 이전)만 골라 (월초, 월말) 쌍으로 반환한다."""

    out = []
    for ym in gt["envelope_true_spend"]:
        year, month = int(ym[:4]), int(ym[4:6])
        last_day = calendar.monthrange(year, month)[1]
        month_end = date(year, month, last_day)
        if month_end > as_of:
            continue
        out.append((date(year, month, 1), month_end))
    return out


# ---------------------------------------------------------------------------
# 1. 대사: ledger.reconcile == [] 및 계좌별 opening_balance + Σsigned == balance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_reconcile_empty_and_account_arithmetic(name: str) -> None:
    twin, _d, _gt = _gen(name)
    led = ledger.normalize(twin)

    warnings = ledger.reconcile(twin, led)
    assert warnings == [], f"{name}: 대사 경고 존재 {warnings}"

    for acc in twin.accounts:
        assert acc.opening_balance is not None, f"{name}: opening_balance 없음"
        total = sum(record.signed_amount for record in led if record.account_id == acc.id)
        assert acc.opening_balance + total == acc.balance, (
            f"{name} 계좌 {acc.id}: opening={acc.opening_balance} + "
            f"Σ{total} != balance={acc.balance}"
        )


# ---------------------------------------------------------------------------
# 2. 완결 월 봉투 순지출 == ground_truth.envelope_true_spend (0 봉투 통일)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_envelope_net_spend_matches_ground_truth(name: str) -> None:
    twin, _d, gt = _gen(name)
    led = ledger.normalize(twin)

    completed = _completed_months(gt, twin.as_of)
    assert completed, f"{name}: 완결 월이 없음(months=3 로도 최소 2개월은 완결돼야 함)"

    for month_start, month_end in completed:
        ym = f"{month_start.year:04d}{month_start.month:02d}"
        computed = ledger.envelope_net_spend(led, month_start, month_end)
        expected_raw = gt["envelope_true_spend"][ym]
        expected = {int(k): v for k, v in expected_raw.items()}

        # 0 인 봉투 취급을 양쪽에서 통일: 7 봉투 키를 전부 채운다.
        computed_full = {eid: computed.get(eid, 0) for eid in _ALL_ENVELOPE_IDS}
        expected_full = {eid: expected.get(eid, 0) for eid in _ALL_ENVELOPE_IDS}

        assert computed_full == expected_full, (
            f"{name} {ym}: 원장 순지출 {computed_full} != ground_truth {expected_full}"
        )


# ---------------------------------------------------------------------------
# 3. account_balance_at(as_of - 30일) == ground_truth.daily_balance (전 계좌)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_account_balance_at_matches_daily_balance(name: str) -> None:
    twin, _d, gt = _gen(name)
    led = ledger.normalize(twin)

    as_of_minus_30 = twin.as_of - timedelta(days=30)
    day_snapshot = gt["daily_balance"][as_of_minus_30.isoformat()]

    for acc in twin.accounts:
        computed = ledger.account_balance_at(twin, led, acc.id, as_of_minus_30)
        expected = day_snapshot[str(acc.id)]
        assert computed == expected, (
            f"{name} 계좌 {acc.id} @ {as_of_minus_30}: 원장 역/전진 계산 {computed} != "
            f"ground_truth {expected}"
        )


# ---------------------------------------------------------------------------
# 4. CARD_BILL 출금 합 == PAID 청구서 합
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_card_bill_ledger_sum_matches_paid_billings(name: str) -> None:
    twin, d, _gt = _gen(name)
    led = ledger.normalize(twin)

    ledger_sum = sum(-record.signed_amount for record in led if record.flow == Flow.CARD_BILL)
    paid_sum = sum(b["total_amount"] for b in d["card_billings"] if b["status"] == "PAID")
    assert ledger_sum == paid_sum, (
        f"{name}: 원장 CARD_BILL 합 {ledger_sum} != PAID 청구서 합 {paid_sum}"
    )


# ---------------------------------------------------------------------------
# 5. 취소 거래마다 원장 레코드 2건, 합 0
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_canceled_transactions_produce_two_zero_sum_records(name: str) -> None:
    twin, d, _gt = _gen(name)
    led = ledger.normalize(twin)

    canceled_ids = [tx["id"] for tx in d["transactions"] if tx["status"] == "CANCELED"]
    assert canceled_ids, f"{name}: 취소 거래가 하나도 없음(고정 시드에서는 있어야 함)"

    for tx_id in canceled_ids:
        records = [r for r in led if r.origin_tx_id == tx_id]
        assert len(records) == 2, f"{name} 취소거래 {tx_id}: 레코드 {len(records)}건(2건이어야 함)"
        assert sum(r.signed_amount for r in records) == 0, (
            f"{name} 취소거래 {tx_id}: 순액이 0 이 아님 {[r.signed_amount for r in records]}"
        )


# ---------------------------------------------------------------------------
# 6. 원장 INCOME 합 == Σ ground_truth.income_events.amount
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_income_ledger_sum_matches_income_events(name: str) -> None:
    twin, _d, gt = _gen(name)
    led = ledger.normalize(twin)

    ledger_income_sum = sum(record.signed_amount for record in led if record.flow == Flow.INCOME)
    gt_income_sum = sum(event["amount"] for event in gt["income_events"])
    assert ledger_income_sum == gt_income_sum, (
        f"{name}: 원장 INCOME 합 {ledger_income_sum} != income_events 합 {gt_income_sum}"
    )


# ---------------------------------------------------------------------------
# 8. B 카드21(토요일 출금) CARD_BILL 출금이 전부 예정 출금일 이후(원장 관점,
#    리뷰 B1 회귀 - 월요일 발행 청구서를 화요일에 결제하지 않음)
# ---------------------------------------------------------------------------


def test_b_card21_ledger_card_bill_respects_saturday_withdrawal() -> None:
    twin, d, _gt = _gen("B_card_crunch")
    led = ledger.normalize(twin)

    card21 = next(c for c in twin.cards if c.id == 21)
    assert card21.withdrawal_weekday == 5, "프로필이 바뀌어 카드21이 더 이상 토요일 출금이 아님"
    expected_merchant = f"카드대금 {card21.card_name}"

    ledger_card21_bills = [
        r for r in led if r.flow == Flow.CARD_BILL and r.merchant_name_raw == expected_merchant
    ]
    paid_billings = [
        b for b in d["card_billings"] if b["card_id"] == 21 and b["status"] == "PAID"
    ]
    assert len(ledger_card21_bills) == len(paid_billings), (
        f"원장 CARD_BILL(카드21) {len(ledger_card21_bills)}건 != "
        f"PAID 청구서 {len(paid_billings)}건"
    )

    paid_saturday = False
    for billing in paid_billings:
        due = _first_due(date.fromisoformat(billing["billing_date"]), 5)
        paid_at = date.fromisoformat(billing["paid_at"])
        assert paid_at >= due, f"{billing}: 예정 출금일({due}) 이전에 결제됨"
        if paid_at.weekday() == 5:
            paid_saturday = True

        matching = [r for r in ledger_card21_bills if r.date == paid_at]
        assert matching, f"원장에 {paid_at} 결제 레코드가 없음: {billing}"

    assert paid_saturday, "카드21(토요일 출금)이 원장 관점으로 한 번도 토요일에 결제되지 않음"

    # B1 회귀의 핵심: "월요일 발행 -> 화요일이면 곧 연체" 로 잘못 판정하던
    # 버그는 첫 시도를 항상 화요일에 하게 만들었다. 예정 출금일(토요일) 전에
    # 시도된 레코드가 없어야 한다(이미 위에서 paid_at >= due 로 검증했지만,
    # 원장 레코드 자체에서도 직접 확인한다 - 매일 재시도 규칙(SPEC 7.2
    # 4단계)상 due 이후 결제일은 토요일이 아닐 수도 있으므로 "화요일 금지"가
    # 아니라 "due 이전 금지" 가 올바른 불변식이다).
    billing_by_id = {b["id"]: b for b in d["card_billings"] if b["card_id"] == 21}
    for record in ledger_card21_bills:
        due_dates = [
            _first_due(date.fromisoformat(b["billing_date"]), 5)
            for b in billing_by_id.values()
            if b["status"] == "PAID" and date.fromisoformat(b["paid_at"]) == record.date
        ]
        assert due_dates, f"원장 레코드 {record.date} 에 대응하는 청구서를 찾지 못함"
        assert all(record.date >= due for due in due_dates)


# ---------------------------------------------------------------------------
# 9. N12: opening_balance 없는 프로필에서 account_balance_at 역산 경로 검증
# ---------------------------------------------------------------------------


def test_n12_account_balance_at_backward_path_without_opening_balance() -> None:
    twin, _d, gt = _gen("A_steady", omit_opening_balance=True)
    led = ledger.normalize(twin)

    for acc in twin.accounts:
        assert acc.opening_balance is None, "omit_opening_balance=True 인데 채워져 있음"

    warnings = ledger.reconcile(twin, led)
    assert warnings == [], f"reconcile 이 비어있지 않음: {warnings}"

    as_of_minus_30 = twin.as_of - timedelta(days=30)
    day_snapshot = gt["daily_balance"][as_of_minus_30.isoformat()]
    for acc in twin.accounts:
        computed = ledger.account_balance_at(twin, led, acc.id, as_of_minus_30)
        expected = day_snapshot[str(acc.id)]
        assert computed == expected, (
            f"계좌 {acc.id} @ {as_of_minus_30}: 역산 경로 {computed} != ground_truth {expected}"
        )


# ---------------------------------------------------------------------------
# 10. B2 회귀: DUTCH 입금이 REFUND 이고 envelope_id 가 있음 (B, C)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["B_card_crunch", "C_impulsive"])
def test_b2_regression_dutch_deposits_are_refund_with_envelope(name: str) -> None:
    twin, _d, _gt = _gen(name)
    led = ledger.normalize(twin)

    dutch_records = [r for r in led if r.exclude_tag.value == "DUTCH"]
    for record in dutch_records:
        assert record.flow == Flow.REFUND, f"{name}: DUTCH 입금이 REFUND 가 아님({record.flow})"
        assert record.envelope_id is not None, f"{name}: DUTCH 입금에 envelope_id 가 없음"


def test_b2_regression_dutch_present_in_c_impulsive() -> None:
    """`months=3, seed=7` 고정 파라미터에서 더치페이가 실제로 발생하는지
    확인해, 위 회귀 테스트가 공허하게 통과하지 않도록 한다(C 프로필에서
    2건 발생함을 확인했다)."""

    twin, _d, _gt = _gen("C_impulsive")
    led = ledger.normalize(twin)
    dutch_records = [r for r in led if r.exclude_tag.value == "DUTCH"]
    assert len(dutch_records) >= 1, "고정 시드에서 더치페이가 하나도 발생하지 않음"
