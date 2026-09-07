"""`fdt/engine/ledger.py` 단위 테스트 (작업 ID W2, SPEC 5.2/3.3/5.3, PLAN §5.1).

전부 `tests/unit/fixtures_input.make_example_input()` / `example_input_dict_copy()`
를 바탕으로 거래를 손으로 추가해 만든다(생성기 산출물에 의존하지 않는다).
"""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from fdt.engine import ledger
from fdt.engine.errors import E_RECON, W_RECON, FdtError
from fdt.engine.schemas.input import TwinInput
from fdt.engine.taxonomy import ENVELOPE_IDS, Flow

from .fixtures_input import example_input_dict_copy, make_example_input

WAESIK = ENVELOPE_IDS["외식"]
CAFE_SUBCATEGORY_ID = 2  # (2, 외식, "카페")
FOOD_SUBCATEGORY_ID = 1  # (1, 외식, "음식점")


def _tx(
    tx_id: int,
    *,
    tx_type: str,
    tx_date: str,
    amount: int = 10000,
    account_id: int | None = 10,
    card_id: int | None = None,
    subcategory_id: int | None = None,
    tx_time: str = "12:00:00",
    confirm_status: str = "AUTO",
    exclude_tag: str = "NONE",
    status: str = "NORMAL",
    flow_hint: str | None = None,
    counterparty_account_id: int | None = None,
    merchant_name_raw: str | None = None,
    source: str = "SEED",
) -> dict:
    return {
        "id": tx_id,
        "source": source,
        "tx_type": tx_type,
        "account_id": account_id,
        "card_id": card_id,
        "merchant_id": None,
        "merchant_name_raw": merchant_name_raw,
        "amount": amount,
        "tx_date": tx_date,
        "tx_time": tx_time,
        "subcategory_id": subcategory_id,
        "confirm_status": confirm_status,
        "exclude_tag": exclude_tag,
        "status": status,
        "flow_hint": flow_hint,
        "counterparty_account_id": counterparty_account_id,
    }


def _build_twin(
    transactions: list[dict],
    *,
    as_of: str = "2026-09-30",
    extra_fixed_expenses: list[dict] | None = None,
    account_overrides: dict[int, dict] | None = None,
) -> TwinInput:
    data = example_input_dict_copy()
    data["as_of"] = as_of
    data["transactions"] = transactions
    if extra_fixed_expenses:
        data["fixed_expenses"].extend(extra_fixed_expenses)
    if account_overrides:
        for account in data["accounts"]:
            if account["id"] in account_overrides:
                account.update(account_overrides[account["id"]])
    return TwinInput.model_validate(data)


# ---------------------------------------------------------------------------
# 1. 취소 CARD 거래 -> SPEND(-)/REFUND(+) 두 건, 순액 0
# ---------------------------------------------------------------------------


def test_cancel_card_tx_produces_spend_and_refund_pair_net_zero():
    twin = _build_twin(
        [
            _tx(
                9001,
                tx_type="CARD",
                tx_date="2026-09-10",
                amount=5000,
                card_id=20,
                subcategory_id=CAFE_SUBCATEGORY_ID,
                status="CANCELED",
            )
        ]
    )
    led = ledger.normalize(twin)

    assert len(led) == 2
    by_id = {r.id: r for r in led}
    assert set(by_id) == {9001, -9001}

    spend = by_id[9001]
    refund = by_id[-9001]
    assert spend.flow == Flow.SPEND
    assert refund.flow == Flow.REFUND
    assert spend.signed_amount == -5000
    assert refund.signed_amount == 5000
    assert spend.origin_tx_id == 9001
    assert refund.origin_tx_id == 9001
    # CARD 거래는 account_id=None (SPEC 5.2 신규 규칙).
    assert spend.account_id is None
    assert refund.account_id is None
    assert spend.envelope_id == refund.envelope_id == WAESIK

    net = ledger.envelope_net_spend(led, date(2026, 9, 1), date(2026, 9, 30))
    assert net.get(WAESIK, 0) == 0


# ---------------------------------------------------------------------------
# 2. CARD_BILL 은 envelope None
# ---------------------------------------------------------------------------


def test_card_bill_matched_by_fixed_expense_has_no_envelope():
    fixed_card_bill = {
        "id": 41,
        "name": "KB 체크 카드대금",
        "expense_type": "CARD_BILL",
        "amount": 183500,
        "is_variable": False,
        "payment_day": 9,
        "withdrawal_account_id": 10,
        "card_id": None,
        "active": True,
    }
    twin = _build_twin(
        [
            _tx(
                9002,
                tx_type="WITHDRAW",
                tx_date="2026-09-09",
                amount=183500,
                account_id=10,
                card_id=None,
            )
        ],
        extra_fixed_expenses=[fixed_card_bill],
    )
    led = ledger.normalize(twin)

    assert len(led) == 1
    record = led[0]
    assert record.flow == Flow.CARD_BILL
    assert record.envelope_id is None
    assert record.account_id == 10
    assert record.signed_amount == -183500


def test_card_bill_matched_by_merchant_name_keyword():
    twin = _build_twin(
        [
            _tx(
                9003,
                tx_type="WITHDRAW",
                tx_date="2026-09-09",
                amount=999999,
                account_id=10,
                merchant_name_raw="KB국민카드 카드대금 출금",
            )
        ]
    )
    led = ledger.normalize(twin)
    assert len(led) == 1
    assert led[0].flow == Flow.CARD_BILL
    assert led[0].envelope_id is None


# ---------------------------------------------------------------------------
# 3. 봉투 순지출 합산 규칙: EMERGENCY/CARRYOVER 제외, DUTCH 입금은 +
# ---------------------------------------------------------------------------


def test_envelope_net_spend_excludes_emergency_and_carryover_includes_dutch():
    twin = _build_twin(
        [
            _tx(
                9101,
                tx_type="WITHDRAW",
                tx_date="2026-09-10",
                amount=1000,
                subcategory_id=FOOD_SUBCATEGORY_ID,
                exclude_tag="NONE",
            ),
            _tx(
                9102,
                tx_type="WITHDRAW",
                tx_date="2026-09-10",
                amount=5000,
                subcategory_id=FOOD_SUBCATEGORY_ID,
                exclude_tag="EMERGENCY",
            ),
            _tx(
                9103,
                tx_type="WITHDRAW",
                tx_date="2026-09-10",
                amount=3000,
                subcategory_id=FOOD_SUBCATEGORY_ID,
                exclude_tag="CARRYOVER",
            ),
            _tx(
                9104,
                tx_type="DEPOSIT",
                tx_date="2026-09-10",
                amount=1000,
                account_id=11,  # is_income=False 계좌 -> REFUND
                subcategory_id=FOOD_SUBCATEGORY_ID,
                exclude_tag="DUTCH",
            ),
        ]
    )
    led = ledger.normalize(twin)
    flows = {r.origin_tx_id: r.flow for r in led}
    assert flows[9101] == Flow.SPEND
    assert flows[9104] == Flow.REFUND

    net = ledger.envelope_net_spend(led, date(2026, 9, 1), date(2026, 9, 30))
    # NONE(-1000) + DUTCH(+1000) 만 반영되고 EMERGENCY/CARRYOVER 는 제외되므로
    # 순지출은 0 이어야 한다. 만약 제외 규칙이 없다면 -1000-5000-3000+1000=-8000
    # 이 되어 abs=8000 이 나온다.
    assert net.get(WAESIK, 0) == 0


# ---------------------------------------------------------------------------
# 4. flow_hint 우선 (분류 순서 1~5 건너뜀)
# ---------------------------------------------------------------------------


def test_flow_hint_overrides_classification_order():
    # counterparty_account_id 가 내 계좌라 원래는 TRANSFER_INTERNAL 로 판정될
    # 거래지만, flow_hint=SPEND 가 있으면 그대로 SPEND 로 기록되고 상대 계좌
    # 레코드도 추가되지 않는다.
    twin = _build_twin(
        [
            _tx(
                9201,
                tx_type="TRANSFER",
                tx_date="2026-09-10",
                amount=2000,
                subcategory_id=FOOD_SUBCATEGORY_ID,
                counterparty_account_id=11,
                flow_hint="SPEND",
            )
        ]
    )
    led = ledger.normalize(twin)
    assert len(led) == 1
    record = led[0]
    assert record.flow == Flow.SPEND
    assert record.signed_amount == -2000
    assert record.envelope_id == WAESIK


# ---------------------------------------------------------------------------
# 5. 고정비 매칭 허용 오차(±10%/±3일) 경계
# ---------------------------------------------------------------------------


def test_fixed_expense_amount_tolerance_boundary():
    # RENT: amount=700000, payment_day=25 (기존 fixture fixed_expense id=40).
    ok = _tx(9301, tx_type="WITHDRAW", tx_date="2026-09-25", amount=770000)  # +10% 경계, 매칭
    bad = _tx(9302, tx_type="WITHDRAW", tx_date="2026-09-25", amount=770001)  # 경계 초과
    twin = _build_twin([ok, bad])
    led = ledger.normalize(twin)
    flows = {r.origin_tx_id: r.flow for r in led}
    assert flows[9301] == Flow.FIXED
    assert flows[9302] == Flow.SPEND


def test_fixed_expense_payment_day_tolerance_boundary():
    ok = _tx(9401, tx_type="WITHDRAW", tx_date="2026-09-28", amount=700000)  # diff=3, 매칭
    bad = _tx(9402, tx_type="WITHDRAW", tx_date="2026-09-29", amount=700000)  # diff=4, 불일치
    twin = _build_twin([ok, bad])
    led = ledger.normalize(twin)
    flows = {r.origin_tx_id: r.flow for r in led}
    assert flows[9401] == Flow.FIXED
    assert flows[9402] == Flow.SPEND


# ---------------------------------------------------------------------------
# 6. TRANSFER_INTERNAL 두 레코드
# ---------------------------------------------------------------------------


def test_transfer_internal_creates_counterparty_record():
    twin = _build_twin(
        [
            _tx(
                9501,
                tx_type="TRANSFER",
                tx_date="2026-09-10",
                amount=50000,
                account_id=10,
                counterparty_account_id=11,
            )
        ]
    )
    led = ledger.normalize(twin)
    assert len(led) == 2
    by_id = {r.id: r for r in led}
    assert set(by_id) == {9501, 95011}  # 9501*10+1

    main = by_id[9501]
    counter = by_id[95011]
    assert main.flow == Flow.TRANSFER_INTERNAL
    assert counter.flow == Flow.TRANSFER_INTERNAL
    assert main.account_id == 10
    assert main.signed_amount == -50000
    assert counter.account_id == 11
    assert counter.signed_amount == 50000
    assert main.envelope_id is None
    assert counter.envelope_id is None
    assert counter.origin_tx_id == 9501


# ---------------------------------------------------------------------------
# 7. as_of 필터: 뒤 날짜 거래 제외
# ---------------------------------------------------------------------------


def test_as_of_filters_future_transactions():
    twin = make_example_input()
    led = ledger.normalize(twin)
    # fixtures_input 의 tx 1002 는 2026-09-08(as_of=2026-09-07 이후) 이라 제외돼야 한다.
    ids = {r.origin_tx_id for r in led}
    assert 1001 in ids
    assert 1002 not in ids
    assert ledger.future_tx_count(twin) == 1


def test_normalize_as_of_argument_overrides_twin_as_of():
    twin = make_example_input()
    led = ledger.normalize(twin, as_of=date(2026, 9, 8))
    ids = {r.origin_tx_id for r in led}
    assert 1002 in ids


# ---------------------------------------------------------------------------
# 8. account_balance_at: opening_balance 있음/없음 두 경로
# ---------------------------------------------------------------------------


def test_account_balance_at_with_opening_balance():
    twin = _build_twin(
        [
            _tx(9601, tx_type="WITHDRAW", tx_date="2026-09-03", amount=200000, account_id=10),
        ],
        as_of="2026-09-07",
        account_overrides={10: {"opening_balance": 1000000, "balance": 800000}},
    )
    led = ledger.normalize(twin)

    # twin.as_of 시점: opening + 그 이하 전부 반영.
    assert ledger.account_balance_at(twin, led, 10, date(2026, 9, 7)) == 800000
    # 거래 이전 시점: 아직 반영 안 됨.
    assert ledger.account_balance_at(twin, led, 10, date(2026, 9, 2)) == 1000000


def test_account_balance_at_without_opening_balance_reverses_from_balance():
    twin = _build_twin(
        [
            _tx(9701, tx_type="WITHDRAW", tx_date="2026-09-06", amount=5600, account_id=10),
        ],
        as_of="2026-09-07",
        account_overrides={10: {"opening_balance": None, "balance": 1830000}},
    )
    led = ledger.normalize(twin)

    # as_of(twin.as_of) 시점 그대로.
    assert ledger.account_balance_at(twin, led, 10, date(2026, 9, 7)) == 1830000
    # 거래(9/6) 이전인 9/5 시점은 역산: balance - Σ(9/5 초과 ~ 9/7 이하) = 1830000 - (-5600).
    assert ledger.account_balance_at(twin, led, 10, date(2026, 9, 5)) == 1835600


# ---------------------------------------------------------------------------
# 9. reconcile: 정상 / 불일치 / strict
# ---------------------------------------------------------------------------


def test_reconcile_matches_when_opening_balance_consistent():
    twin = _build_twin(
        [
            _tx(9801, tx_type="WITHDRAW", tx_date="2026-09-03", amount=200000, account_id=10),
        ],
        as_of="2026-09-07",
        account_overrides={10: {"opening_balance": 1000000, "balance": 800000}},
    )
    led = ledger.normalize(twin)
    assert ledger.reconcile(twin, led) == []


def test_reconcile_reports_warning_on_mismatch():
    twin = _build_twin(
        [
            _tx(9901, tx_type="WITHDRAW", tx_date="2026-09-03", amount=200000, account_id=10),
        ],
        as_of="2026-09-07",
        # 실제 잔액이 기대값(800000)과 10000원 어긋난다.
        account_overrides={10: {"opening_balance": 1000000, "balance": 810000}},
    )
    led = ledger.normalize(twin)
    warnings = ledger.reconcile(twin, led)
    assert len(warnings) == 1
    warning = warnings[0]
    assert warning.code == W_RECON
    assert warning.details["account_id"] == 10
    assert warning.details["expected"] == 800000
    assert warning.details["actual"] == 810000
    assert warning.details["diff"] == 10000


def test_reconcile_strict_raises_fdt_error_on_mismatch():
    twin = _build_twin(
        [
            _tx(9902, tx_type="WITHDRAW", tx_date="2026-09-03", amount=200000, account_id=10),
        ],
        as_of="2026-09-07",
        account_overrides={10: {"opening_balance": 1000000, "balance": 810000}},
    )
    led = ledger.normalize(twin)
    with pytest.raises(FdtError) as exc_info:
        ledger.reconcile(twin, led, strict=True)
    assert exc_info.value.code == E_RECON


# ---------------------------------------------------------------------------
# 10. 정렬 안정성 (date, time, id)
# ---------------------------------------------------------------------------


def test_normalize_sorts_by_date_time_id_regardless_of_input_order():
    txs = [
        _tx(9950, tx_type="WITHDRAW", tx_date="2026-09-12", tx_time="09:00:00"),
        _tx(9910, tx_type="WITHDRAW", tx_date="2026-09-10", tx_time="09:00:00"),
        _tx(9911, tx_type="WITHDRAW", tx_date="2026-09-10", tx_time="08:00:00"),
        _tx(9920, tx_type="WITHDRAW", tx_date="2026-09-11", tx_time="09:00:00"),
    ]
    twin = _build_twin(txs)
    led = ledger.normalize(twin)
    ids_in_order = [r.origin_tx_id for r in led]
    assert ids_in_order == [9911, 9910, 9920, 9950]

    # 같은 입력을 다시 정규화해도 바이트/순서 동일(재현성).
    led_again = ledger.normalize(twin)
    assert led == led_again


# ---------------------------------------------------------------------------
# 11. LedgerTx frozen
# ---------------------------------------------------------------------------


def test_ledger_tx_is_frozen():
    twin = _build_twin(
        [_tx(9990, tx_type="WITHDRAW", tx_date="2026-09-10", amount=1000)]
    )
    led = ledger.normalize(twin)
    record = led[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.signed_amount = -9999  # type: ignore[misc]
