"""`TwinInput` 예시 픽스처 (SPEC 3.2 예시 JSON 기반, taxonomy 상수로 생성).

`test_schemas_input_state.py` 및 이후 다른 단위 테스트가 재사용할 수 있도록
분리했다 (작업 ID W0-B 소유).
"""

from __future__ import annotations

import copy
from typing import Any

from fdt.engine.schemas.input import TwinInput
from fdt.engine.taxonomy import ENVELOPE_IDS, ENVELOPES, SUBCATEGORIES

AS_OF = "2026-09-07"


def example_input_dict() -> dict[str, Any]:
    """SPEC 3.2 예시와 값이 대응하는 완전한 TwinInput JSON(dict)."""

    envelopes = [{"id": ENVELOPE_IDS[name], "name": name} for name in ENVELOPES]
    subcategories = [
        {"id": sub_id, "envelope_id": env_id, "name": name}
        for sub_id, env_id, name in SUBCATEGORIES
    ]

    return {
        "schema_version": "twin-input/1",
        "as_of": AS_OF,
        "user": {
            "id": 1,
            "employment_status": "EMPLOYED",
            "income_band": None,
            "birth_date": None,
        },
        "envelopes": envelopes,
        "subcategories": subcategories,
        "accounts": [
            {
                "id": 10,
                "fin_account_no": "0011234567890123",
                "bank_code": "001",
                "alias": "월급통장",
                "is_managed": True,
                "is_income": True,
                "balance": 1830000,
                "opening_balance": None,
            },
            {
                "id": 11,
                "fin_account_no": "0011234567890999",
                "bank_code": "001",
                "alias": "비상금통장",
                "is_managed": True,
                "is_income": False,
                "balance": 350000,
                "opening_balance": None,
            },
        ],
        "cards": [
            {
                "id": 20,
                "issuer_code": "1001",
                "card_name": "KB 체크",
                "kind": "CREDIT",
                "withdrawal_account_id": 10,
                "withdrawal_weekday": 1,
                "is_managed": True,
            }
        ],
        "card_billings": [
            {
                "id": 30,
                "card_id": 20,
                "billing_date": "2026-09-01",
                "total_amount": 183500,
                "status": "UNPAID",
                "paid_at": None,
            }
        ],
        "fixed_expenses": [
            {
                "id": 40,
                "name": "월세",
                "expense_type": "RENT",
                "amount": 700000,
                "is_variable": False,
                "payment_day": 25,
                "withdrawal_account_id": 10,
                "card_id": None,
                "active": True,
            }
        ],
        "loans": [
            {
                "id": 50,
                "balance": 12000000,
                "annual_rate_pct": 6.8,
                "interest_day": 15,
                "withdrawal_account_id": 10,
                "repayment": "INTEREST_ONLY",
            }
        ],
        "budgets": [
            {
                "budget_month": "202609",
                "status": "CONFIRMED",
                "envelopes": [
                    {
                        "envelope_id": ENVELOPE_IDS["외식"],
                        "proposed_amount": 350000,
                        "confirmed_amount": 300000,
                    }
                ],
            }
        ],
        "transactions": [
            {
                "id": 1001,
                "source": "SEED",
                "tx_type": "CARD",
                "account_id": 10,
                "card_id": 20,
                "merchant_id": 7,
                "merchant_name_raw": "스타벅스",
                "amount": 5600,
                "tx_date": "2026-09-06",
                "tx_time": "13:20:00",
                "subcategory_id": 2,
                "confirm_status": "AUTO",
                "exclude_tag": "NONE",
                "status": "NORMAL",
                "flow_hint": None,
                "counterparty_account_id": None,
            },
            {
                # as_of(2026-09-07) 이후 거래. 검증은 통과해야 하고
                # transactions_until 로만 걸러진다 (SPEC 3.3).
                "id": 1002,
                "source": "SEED",
                "tx_type": "CARD",
                "account_id": 10,
                "card_id": 20,
                "merchant_id": 8,
                "merchant_name_raw": "이마트",
                "amount": 32000,
                "tx_date": "2026-09-08",
                "tx_time": "19:00:00",
                "subcategory_id": 18,
                "confirm_status": "AUTO",
                "exclude_tag": "NONE",
                "status": "NORMAL",
                "flow_hint": None,
                "counterparty_account_id": None,
            },
        ],
        "externals": {
            "price_index_mult": 1.0,
            "loan_rate_delta_bp": 0,
            "income_growth_pct": 0.0,
        },
    }


def make_example_input() -> TwinInput:
    return TwinInput.model_validate(example_input_dict())


def example_input_dict_copy() -> dict[str, Any]:
    """변형 테스트용으로 안전하게 변경할 수 있는 깊은 복사본."""

    return copy.deepcopy(example_input_dict())
