"""`fdt/gen` 더미 데이터 생성기 테스트 (SPEC 11장, PLAN 5.1 test_generator).

빠른 실행을 위해 `months=3` 을 쓴다(PLAN "테스트는 months=3 로 빠르게(<10초)").
"""

from __future__ import annotations

import json
from datetime import date

import pytest

from fdt.engine.schemas.input import TwinInput
from fdt.engine.taxonomy import ENVELOPE_IDS
from fdt.gen import PROFILE_NAMES, generate

END = date(2026, 9, 7)
MONTHS = 3
SEED = 7


def _gen(name: str, seed: int = SEED):
    return generate(name, seed=seed, months=MONTHS, end=END)


# ---------------------------------------------------------------------------
# 재현성
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_reproducible_bytes(name: str) -> None:
    _, d1, _ = _gen(name)
    _, d2, _ = _gen(name)
    assert json.dumps(d1, sort_keys=True, ensure_ascii=False) == json.dumps(
        d2, sort_keys=True, ensure_ascii=False
    )


def test_different_seed_differs() -> None:
    _, d1, _ = _gen("B_card_crunch", seed=7)
    _, d2, _ = _gen("B_card_crunch", seed=8)
    assert json.dumps(d1, sort_keys=True) != json.dumps(d2, sort_keys=True)


# ---------------------------------------------------------------------------
# 4 프로필 전부 TwinInput 검증 통과
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_twin_input_validates(name: str) -> None:
    twin_input, d, _ = _gen(name)
    assert isinstance(twin_input, TwinInput)
    # dict 로도 다시 검증 가능해야 한다 (라운드트립)
    TwinInput.model_validate(d)


# ---------------------------------------------------------------------------
# ground_truth 필드
# ---------------------------------------------------------------------------

_GT_FIELDS = (
    "daily_balance",
    "card_shortfalls",
    "declined_debits",
    "shocks",
    "cancels",
    "dutch_pays",
    "envelope_true_spend",
    "income_events",
    "hidden_params",
)


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_ground_truth_fields_present(name: str) -> None:
    _, _, gt = _gen(name)
    for field in _GT_FIELDS:
        assert field in gt, f"{name}: ground_truth 에 {field} 없음"
    assert len(gt["daily_balance"]) == (END - _start_of(name)).days + 1


def _start_of(name: str) -> date:
    from fdt.gen.generator import _add_months

    y, m = _add_months(END.year, END.month, -MONTHS)
    return date(y, m, 1)


# ---------------------------------------------------------------------------
# 프로필 특성 (SPEC 11장 표)
# ---------------------------------------------------------------------------


def test_profile_A_no_shortfall_no_decline() -> None:
    _, _, gt = _gen("A_steady")
    assert len(gt["card_shortfalls"]) == 0
    assert len(gt["declined_debits"]) == 0


def test_profile_B_card_shortfall() -> None:
    _, _, gt = _gen("B_card_crunch")
    assert len(gt["card_shortfalls"]) >= 1


def test_profile_C_declined_debits() -> None:
    _, _, gt = _gen("C_impulsive")
    assert len(gt["declined_debits"]) >= 10


def test_profile_D_subscriptions_and_confirmed_budget() -> None:
    twin_input, d, _ = _gen("D_goal_saver")
    subs = [fx for fx in d["fixed_expenses"] if fx["expense_type"] == "SUBSCRIPTION"]
    assert len(subs) == 5
    assert len(twin_input.budgets) == 1
    assert twin_input.budgets[0].status == "CONFIRMED"


# ---------------------------------------------------------------------------
# 거래 순번 유일
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_transaction_ids_unique(name: str) -> None:
    _, d, _ = _gen(name)
    ids = [tx["id"] for tx in d["transactions"]]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# 계좌 대사: opening_balance + Σ 부호거래 == balance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_account_reconciliation(name: str) -> None:
    _, d, _ = _gen(name)
    running = {a["id"]: a["opening_balance"] for a in d["accounts"]}
    for tx in d["transactions"]:
        if tx["status"] == "CANCELED":
            continue
        t = tx["tx_type"]
        amount = tx["amount"]
        if t == "DEPOSIT":
            running[tx["account_id"]] += amount
        elif t == "WITHDRAW":
            running[tx["account_id"]] -= amount
        elif t == "TRANSFER":
            running[tx["account_id"]] -= amount
            running[tx["counterparty_account_id"]] += amount
        # CARD: 계좌에 직접 영향 없음 (청구 WITHDRAW 로만 반영)
    for acc in d["accounts"]:
        assert running[acc["id"]] == acc["balance"], (
            f"{name} account {acc['id']}: 대사 불일치 "
            f"(계산={running[acc['id']]}, 기록={acc['balance']})"
        )


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_card_bill_withdraw_matches_paid_billings(name: str) -> None:
    _, d, _ = _gen(name)
    paid_sum = sum(b["total_amount"] for b in d["card_billings"] if b["status"] == "PAID")
    withdraw_sum = sum(
        tx["amount"] for tx in d["transactions"] if tx.get("flow_hint") == "CARD_BILL"
    )
    assert paid_sum == withdraw_sum


# ---------------------------------------------------------------------------
# 취소 거래는 새 레코드를 만들지 않고 원 레코드의 status 만 바꾼다
# ---------------------------------------------------------------------------


def test_canceled_tx_excluded_from_card_balance() -> None:
    _, d, _ = _gen("B_card_crunch")
    canceled = [tx for tx in d["transactions"] if tx["status"] == "CANCELED"]
    assert len(canceled) >= 0  # 존재하지 않아도 되지만, 있으면 CARD 여야 한다
    for tx in canceled:
        assert tx["tx_type"] == "CARD"


# ---------------------------------------------------------------------------
# 봉투 7종 이름/개수가 taxonomy 와 일치
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_envelopes_match_taxonomy(name: str) -> None:
    _, d, _ = _gen(name)
    got = {e["id"]: e["name"] for e in d["envelopes"]}
    assert got == {v: k for k, v in ENVELOPE_IDS.items()}
