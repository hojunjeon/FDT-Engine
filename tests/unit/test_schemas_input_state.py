"""입력 / State / Behavior 스키마 단위 테스트 (작업 ID W0-B).

SPEC 3.2(TwinInput), 3.3(입력 검증), 5.1(State), 6장(Behavior) 을 따른다.
"""

from __future__ import annotations

import copy
from datetime import date

import pytest
from pydantic import ValidationError

from fdt.engine.errors import E_INPUT_DUP, E_INPUT_EMPTY, E_INPUT_REF, E_INPUT_TAXONOMY
from fdt.engine.schemas.behavior import Behavior, EnvelopeBehavior, ShockModel
from fdt.engine.schemas.input import TwinInput
from fdt.engine.schemas.state import (
    IncomeSchedule,
    State,
)
from fdt.engine.taxonomy import ENVELOPE_IDS, ENVELOPES

from .fixtures_input import example_input_dict, example_input_dict_copy, make_example_input


def _validation_error_message(exc_info: pytest.ExceptionInfo) -> str:
    return str(exc_info.value)


# ---------------------------------------------------------------------------
# TwinInput: 라운드트립
# ---------------------------------------------------------------------------


def test_twin_input_valid_example_roundtrip():
    twin = make_example_input()
    assert twin.schema_version == "twin-input/1"
    assert len(twin.envelopes) == 7
    assert len(twin.subcategories) == 22

    dumped = twin.model_dump(mode="json")
    twin2 = TwinInput.model_validate(dumped)
    dumped2 = twin2.model_dump(mode="json")

    assert dumped == dumped2


def test_twin_input_transactions_until_filters_future_tx():
    twin = make_example_input()
    # as_of 이전(2026-09-06)만: id 1001 만 남고 1002(2026-09-08)는 빠진다.
    until = twin.transactions_until(date(2026, 9, 7))
    ids = sorted(tx.id for tx in until)
    assert ids == [1001]

    until2 = twin.transactions_until(date(2026, 9, 8))
    ids2 = sorted(tx.id for tx in until2)
    assert ids2 == [1001, 1002]


# ---------------------------------------------------------------------------
# 검증 실패 4 케이스
# ---------------------------------------------------------------------------


def test_taxonomy_violation_wrong_envelope_name():
    data = example_input_dict_copy()
    data["envelopes"][0]["name"] = "존재하지않는봉투"

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_TAXONOMY in _validation_error_message(exc_info)


def test_taxonomy_violation_subcategory_dangling_envelope():
    data = example_input_dict_copy()
    data["subcategories"][0]["envelope_id"] = 999999

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_TAXONOMY in _validation_error_message(exc_info)


def test_ref_violation_card_withdrawal_account_missing():
    data = example_input_dict_copy()
    data["cards"][0]["withdrawal_account_id"] = 999999

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_REF in _validation_error_message(exc_info)


def test_ref_violation_fixed_expense_withdrawal_account_missing():
    data = example_input_dict_copy()
    data["fixed_expenses"][0]["withdrawal_account_id"] = 999999

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_REF in _validation_error_message(exc_info)


def test_ref_violation_transaction_account_and_card_missing():
    data = example_input_dict_copy()
    data["transactions"][0]["account_id"] = 999999

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_REF in _validation_error_message(exc_info)

    data2 = example_input_dict_copy()
    data2["transactions"][0]["card_id"] = 999999

    with pytest.raises(ValidationError) as exc_info2:
        TwinInput.model_validate(data2)

    assert E_INPUT_REF in _validation_error_message(exc_info2)


def test_dup_violation_same_id_different_content():
    data = example_input_dict_copy()
    dup = copy.deepcopy(data["transactions"][0])
    dup["amount"] = dup["amount"] + 1  # 내용만 다르게
    data["transactions"].append(dup)

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_DUP in _validation_error_message(exc_info)


def test_dup_same_id_same_content_collapses_to_one():
    data = example_input_dict_copy()
    dup = copy.deepcopy(data["transactions"][0])  # 완전히 동일한 내용
    data["transactions"].append(dup)

    twin = TwinInput.model_validate(data)
    ids = [tx.id for tx in twin.transactions]
    assert ids.count(1001) == 1
    # 원래 있던 다른 거래(1002)는 그대로 유지된다.
    assert 1002 in ids


def test_empty_violation_no_managed_account_or_card():
    data = example_input_dict_copy()
    for account in data["accounts"]:
        account["is_managed"] = False
    for card in data["cards"]:
        card["is_managed"] = False

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_EMPTY in _validation_error_message(exc_info)


def test_empty_violation_no_managed_account_even_with_managed_card():
    # 리뷰 N3: 관리 계좌 0개는 관리 카드 수와 합산하지 않고 그 자체로
    # E-INPUT-EMPTY 다 (§5.3 PRIMARY 계좌 결정에 관리 계좌가 필요).
    data = example_input_dict_copy()
    for account in data["accounts"]:
        account["is_managed"] = False
    assert any(card["is_managed"] for card in data["cards"])

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_EMPTY in _validation_error_message(exc_info)


# ---------------------------------------------------------------------------
# B1: taxonomy 완전 대조 (봉투 id<->이름, 세분류 매핑, 22종)
# ---------------------------------------------------------------------------


def test_taxonomy_violation_envelope_ids_reversed():
    # (가) 봉투 id 를 전부 역순(8-id)으로 뒤집으면, 이름 집합은 그대로라도
    # id<->이름 매핑이 taxonomy.ENVELOPE_IDS 와 달라져 조회 시 조용히 다른
    # 봉투를 가리킨다 (리뷰 B1). id 만 뒤집고 name 은 그대로 두면 EnvelopeDef
    # id 유일성은 유지된다(1..7 재배치이므로).
    data = example_input_dict_copy()
    for envelope in data["envelopes"]:
        envelope["id"] = 8 - envelope["id"]
    # subcategories 도 새 envelope id 를 참조하도록 맞춰야 참조 오류가 아니라
    # taxonomy 매핑 오류로 걸린다(그렇지 않으면 E_INPUT_REF 이전에 이미
    # taxonomy 검사가 실패해도 무방하지만, 이 케이스는 envelopes 자체의
    # id<->이름 불일치를 확인하는 것이 목적이다).
    for sub in data["subcategories"]:
        sub["envelope_id"] = 8 - sub["envelope_id"]

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_TAXONOMY in _validation_error_message(exc_info)


def test_taxonomy_violation_subcategory_wrong_envelope_mapping():
    # (나) subcategories[0].envelope_id 를 1(외식) -> 5(쇼핑) 처럼 실제
    # taxonomy 매핑과 다르게 바꾸면, id 는 여전히 envelopes 안에 있어도
    # taxonomy.SUBCATEGORIES 와 (id, envelope_id, name) 집합이 달라진다.
    data = example_input_dict_copy()
    first_sub = data["subcategories"][0]
    assert first_sub["id"] == 1
    assert first_sub["envelope_id"] == ENVELOPE_IDS["외식"]
    first_sub["envelope_id"] = ENVELOPE_IDS["쇼핑"]

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_TAXONOMY in _validation_error_message(exc_info)


def test_taxonomy_violation_only_21_subcategories():
    # (다) 세분류를 21종으로 줄이면(1종 누락) 개수·집합 대조에서 실패한다.
    data = example_input_dict_copy()
    assert len(data["subcategories"]) == 22
    data["subcategories"].pop()

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_TAXONOMY in _validation_error_message(exc_info)


# ---------------------------------------------------------------------------
# N2: transactions 외 배열의 id 중복 검사 (같은 id, 다른 내용 -> E-INPUT-DUP)
# ---------------------------------------------------------------------------


def test_dup_violation_accounts_same_id_different_content():
    data = example_input_dict_copy()
    dup = copy.deepcopy(data["accounts"][0])
    dup["balance"] = dup["balance"] + 1
    data["accounts"].append(dup)

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_DUP in _validation_error_message(exc_info)


def test_dup_violation_cards_same_id_different_content():
    data = example_input_dict_copy()
    dup = copy.deepcopy(data["cards"][0])
    dup["withdrawal_weekday"] = (dup["withdrawal_weekday"] + 1) % 7
    data["cards"].append(dup)

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_DUP in _validation_error_message(exc_info)


def test_dup_violation_card_billings_same_id_different_content():
    data = example_input_dict_copy()
    dup = copy.deepcopy(data["card_billings"][0])
    dup["total_amount"] = dup["total_amount"] + 1
    data["card_billings"].append(dup)

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_DUP in _validation_error_message(exc_info)


def test_dup_violation_fixed_expenses_same_id_different_content():
    data = example_input_dict_copy()
    dup = copy.deepcopy(data["fixed_expenses"][0])
    dup["amount"] = dup["amount"] + 1
    data["fixed_expenses"].append(dup)

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_DUP in _validation_error_message(exc_info)


def test_dup_violation_loans_same_id_different_content():
    data = example_input_dict_copy()
    dup = copy.deepcopy(data["loans"][0])
    dup["balance"] = dup["balance"] + 1
    data["loans"].append(dup)

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_DUP in _validation_error_message(exc_info)


def test_dup_violation_envelopes_same_id_different_content():
    # taxonomy 검사보다 dedup 이 먼저 실행되므로(순서 주의), 틀린 이름의
    # 중복을 먼저 두고 올바른 항목을 뒤에 두면 최종 이름 매핑은 taxonomy 와
    # 맞지만(따라서 taxonomy 오류로 새지 않고) dedup 단계에서 내용이 다른
    # 같은 id 중복으로 걸린다.
    data = example_input_dict_copy()
    correct = next(e for e in data["envelopes"] if e["id"] == ENVELOPE_IDS["외식"])
    wrong_dup = copy.deepcopy(correct)
    wrong_dup["name"] = "존재하지않는이름"
    data["envelopes"].insert(0, wrong_dup)

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_DUP in _validation_error_message(exc_info)


def test_dup_violation_subcategories_same_id_different_content():
    # envelopes 케이스와 동일한 이유로, 최종 집합이 taxonomy 와 일치하도록
    # 틀린 중복을 앞에 두고 올바른 항목을 뒤에 둔다.
    data = example_input_dict_copy()
    correct = data["subcategories"][0]
    assert correct["id"] == 1
    wrong_dup = copy.deepcopy(correct)
    wrong_dup["name"] = "존재하지않는세분류"
    data["subcategories"].insert(0, wrong_dup)

    with pytest.raises(ValidationError) as exc_info:
        TwinInput.model_validate(data)

    assert E_INPUT_DUP in _validation_error_message(exc_info)


def test_future_transaction_does_not_fail_validation():
    # example_input_dict 는 이미 as_of(2026-09-07) 이후 거래(1002, 09-08)를
    # 포함하지만 검증은 통과해야 한다 (SPEC 3.3: 경고만, 오류 아님).
    data = example_input_dict()
    twin = TwinInput.model_validate(data)
    assert any(tx.id == 1002 for tx in twin.transactions)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def _example_income_schedule() -> dict:
    return {
        "next_date": "2026-09-25",
        "expected": 2870000,
        "irregular": False,
        "median_gap_days": 30,
    }


def _example_state_dict() -> dict:
    return {
        "as_of": "2026-09-07",
        "accounts": [
            {"id": 10, "role": "PRIMARY", "balance": 1830000},
            {"id": 11, "role": "EMERGENCY", "balance": 350000},
        ],
        "liquidity": 1830000,
        "emergency_fund": 350000,
        "cards": [
            {
                "id": 20,
                "withdrawal_weekday": 1,
                "unbilled": 92300,
                "issued_unpaid": [{"billing_date": "2026-09-01", "amount": 183500}],
            }
        ],
        "committed": [
            {
                "kind": "RENT",
                "name": "월세",
                "due": "2026-09-25",
                "amount": 700000,
                "certainty": 1.0,
                "account_id": 10,
                "card_id": None,
            }
        ],
        "envelopes": [
            {
                "envelope_id": ENVELOPE_IDS[name],
                "name": name,
                "budget": 300000 if name == "외식" else 0,
                "spent": 212400 if name == "외식" else 0,
                "remaining": 87600 if name == "외식" else 0,
                "budget_source": "CONFIRMED" if name == "외식" else "ENGINE",
            }
            for name in ENVELOPES
        ],
        "income": _example_income_schedule(),
        "indicators": {
            "spend_7d_avg": 41200.0,
            "spend_90d_avg": 36800.0,
            "acceleration": 1.12,
            "unconfirmed_count": 3,
        },
        "cycle": {
            "budget_cycle_start": "2026-09-01",
            "budget_cycle_end": "2026-09-30",
            "progress": 0.233,
        },
    }


def test_state_roundtrip():
    state = State.model_validate(_example_state_dict())
    dumped = state.model_dump(mode="json")
    state2 = State.model_validate(dumped)
    assert dumped == state2.model_dump(mode="json")


def test_state_helper_methods():
    state = State.model_validate(_example_state_dict())

    env = state.envelope_by_id(ENVELOPE_IDS["외식"])
    assert env is not None
    assert env.name == "외식"
    assert state.envelope_by_id(-1) is None

    committed = state.committed_between(date(2026, 9, 1), date(2026, 9, 30))
    assert len(committed) == 1
    assert committed[0].kind == "RENT"

    none_committed = state.committed_between(date(2026, 10, 1), date(2026, 10, 31))
    assert none_committed == []


def test_state_model_copy_deep_is_independent():
    state = State.model_validate(_example_state_dict())
    forked = state.model_copy(deep=True)

    forked.liquidity = 999
    forked.accounts[0].balance = -1
    forked.envelopes[0].spent = 123456

    assert state.liquidity == 1830000
    assert state.accounts[0].balance == 1830000
    assert state.envelopes[0].spent != 123456


# ---------------------------------------------------------------------------
# Behavior
# ---------------------------------------------------------------------------


def _example_behavior_dict(weekday_mult=None) -> dict:
    weekday_mult = weekday_mult or [1.0] * 7
    return {
        "as_of": "2026-09-07",
        "window_days": 90,
        "envelopes": [
            {
                "envelope_id": ENVELOPE_IDS[name],
                "daily_rate": 0.3,
                "weekday_mult": list(weekday_mult),
                "amount_mu": 9.2,
                "amount_sigma": 0.6,
                "card_share": 0.8,
                "elasticity": 1.0,
                "n_obs": 20,
            }
            for name in ENVELOPES
        ],
        "payday_boost": 1.3,
        "shock": {"daily_prob": 0.01, "mu": 11.5, "sigma": 0.6},
        "income": _example_income_schedule(),
    }


def test_behavior_roundtrip():
    behavior = Behavior.model_validate(_example_behavior_dict())
    dumped = behavior.model_dump(mode="json")
    behavior2 = Behavior.model_validate(dumped)
    assert dumped == behavior2.model_dump(mode="json")
    assert len(behavior.envelopes) == 7


def test_behavior_weekday_mult_all_ones_passes():
    behavior = Behavior.model_validate(_example_behavior_dict(weekday_mult=[1.0] * 7))
    for env in behavior.envelopes:
        assert env.weekday_mult == [1.0] * 7


def test_behavior_weekday_mult_non_uniform_but_mean_one_passes():
    # 평균은 1 인데 값은 제각각인 경우도 통과해야 한다.
    mult = [0.5, 1.5, 1.0, 1.0, 1.0, 1.2, 0.8]
    assert abs(sum(mult) / 7 - 1.0) < 1e-9
    behavior = Behavior.model_validate(_example_behavior_dict(weekday_mult=mult))
    assert behavior.envelopes[0].weekday_mult == mult


def test_envelope_behavior_weekday_mult_mean_violation_raises():
    bad_mult = [2.0] * 7  # 평균 2.0, 1.0 이 아님
    with pytest.raises(ValidationError):
        EnvelopeBehavior.model_validate(
            {
                "envelope_id": 1,
                "daily_rate": 0.1,
                "weekday_mult": bad_mult,
                "amount_mu": 9.0,
                "amount_sigma": 0.5,
                "card_share": 0.5,
                "elasticity": 1.0,
                "n_obs": 10,
            }
        )


def test_shock_model_and_income_schedule_direct():
    shock = ShockModel.model_validate({"daily_prob": 0.02, "mu": 11.0, "sigma": 0.5})
    assert shock.daily_prob == 0.02

    income = IncomeSchedule.model_validate(_example_income_schedule())
    assert income.expected == 2870000

    no_income = IncomeSchedule.model_validate(
        {"next_date": None, "expected": 0, "irregular": True, "median_gap_days": None}
    )
    assert no_income.next_date is None
    assert no_income.median_gap_days is None
