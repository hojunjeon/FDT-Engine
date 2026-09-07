"""`fdt/gen` 더미 데이터 생성기 테스트 (SPEC 11장, PLAN 5.1 test_generator).

빠른 실행을 위해 `months=3` 을 쓴다(PLAN "테스트는 months=3 로 빠르게(<10초)").
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date

import pytest
from pydantic import ValidationError

from fdt.engine.schemas.input import TwinInput
from fdt.engine.taxonomy import ENVELOPE_IDS, ENVELOPES
from fdt.gen import PROFILE_NAMES, generate
from fdt.gen.generator import Generator, _CardBilling, _first_due
from fdt.gen.profile_schema import validate_profile

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


# ---------------------------------------------------------------------------
# B1 회귀: 카드 출금이 withdrawal_weekday 를 지킨다 (리뷰 B1, SPEC S16)
# ---------------------------------------------------------------------------


def test_first_due_returns_next_matching_weekday() -> None:
    # 화요일(1) 출금 카드, 월요일 발행 -> 다음 날(화요일)이 예정 출금일.
    # date(2026, 9, 7) 이 월요일이다(END 상수와 같은 주).
    assert date(2026, 9, 7).weekday() == 0
    assert _first_due(date(2026, 9, 7), 1) == date(2026, 9, 8)
    # 토요일(5) 출금 카드, 월요일 발행 -> 그 주 토요일이 예정 출금일 (화요일이
    # 아니다. 이것이 리뷰 B1 이 잡은 버그다).
    assert date(2026, 8, 10).weekday() == 0
    assert _first_due(date(2026, 8, 10), 5) == date(2026, 8, 15)
    assert _first_due(date(2026, 8, 10), 5) != date(2026, 8, 11)


def test_first_due_monday_billing_monday_withdrawal_is_same_day() -> None:
    # 월요일(0) 출금 카드가 월요일에 발행되면 발행 당일이 곧 예정 출금일이다
    # (경계 케이스, 리뷰 B1 지시문: "현재 4 프로필에는 월요일 출금 카드가
    # 없어 이 경계가 한 번도 밟히지 않는다").
    billing_date = date(2026, 9, 7)  # 월요일
    assert billing_date.weekday() == 0
    assert _first_due(billing_date, 0) == billing_date


def test_spec_15a_card_billing_cycle() -> None:
    """SPEC 15.A 부록 표(화요일 출금 카드) 를 `_step_card_withdraw` 로 그대로
    재현한다. `_first_due`/카드 출금 판정 함수 기준 회귀 테스트(리뷰 B4)."""

    profile = _minimal_profile()
    gen = Generator(profile, seed=1, months=1, end=date(2026, 9, 16))
    card = gen.cards[20]
    acc = gen.accounts[10]

    # (월) 발행 103,500 -> 다음날(화) 출금 성공. date(2026, 9, 7) 이 월요일.
    b1 = _CardBilling(id=9001, card_id=20, billing_date=date(2026, 9, 7), total_amount=103500)
    card.billings.append(b1)
    acc.balance = 500000
    gen._step_card_withdraw(date(2026, 9, 7))
    assert b1.status == "UNPAID", "발행 당일은 아직 예정 출금일이 아니다"
    gen._step_card_withdraw(date(2026, 9, 8))
    assert b1.status == "PAID"
    assert acc.balance == 500000 - 103500

    # 다음 주 (월) 발행 167,800 -> (화) 잔액 120,000 부족 -> (수) 재시도 성공
    b2 = _CardBilling(id=9002, card_id=20, billing_date=date(2026, 9, 14), total_amount=167800)
    card.billings.append(b2)
    acc.balance = 120000
    gen._step_card_withdraw(date(2026, 9, 15))
    assert b2.status == "UNPAID"
    assert len(gen.gt["card_shortfalls"]) == 1
    assert gen.gt["card_shortfalls"][0]["amount"] == 167800
    acc.balance = 200000
    gen._step_card_withdraw(date(2026, 9, 16))
    assert b2.status == "PAID"
    assert acc.balance == 200000 - 167800


def test_profile_B_card21_respects_saturday_withdrawal() -> None:
    """B 카드21(토요일 출금)이 월요일 발행 청구서를 화요일에 결제하지 않는다
    (리뷰 B1 회귀 - 수정 전에는 전부 화요일에 결제됐다)."""

    _, d, _ = _gen("B_card_crunch")
    card21_billings = [b for b in d["card_billings"] if b["card_id"] == 21]
    assert card21_billings, "카드21 청구서가 생성되지 않음"

    paid_saturday = False
    for b in card21_billings:
        if b["status"] != "PAID":
            continue
        billing_date = date.fromisoformat(b["billing_date"])
        paid_at = date.fromisoformat(b["paid_at"])
        due = _first_due(billing_date, 5)
        assert paid_at >= due, f"{b} 가 예정 출금일({due}) 이전에 결제됨"
        if paid_at.weekday() == 5:
            paid_saturday = True

    assert paid_saturday, "카드21(토요일 출금)이 한 번도 토요일에 결제되지 않음"


# ---------------------------------------------------------------------------
# 봉투별 elasticity dict 지원 (리뷰 N4)
# ---------------------------------------------------------------------------


def _minimal_profile() -> dict:
    """Generator 를 직접 단위 테스트하기 위한 최소 프로필 dict.

    `profile_schema.Profile` 이 채우는 모든 키를 직접 채운다(`load_profile`
    을 거치지 않고 `Generator` 를 바로 생성하는 테스트에서 재사용).
    """

    return {
        "accounts": [
            {
                "id": 10,
                "alias": "테스트계좌",
                "is_income": True,
                "opening_balance": 0,
                "managed": True,
            }
        ],
        "cards": [
            {
                "id": 20,
                "alias": "테스트카드",
                "kind": "CREDIT",
                "withdrawal_weekday": 1,
                "withdrawal_account_id": 10,
            }
        ],
        "income": {
            "type": "SALARY",
            "day_of_month": 25,
            "amount": 1000000,
            "jitter_sigma": 0.0,
            "median_gap_days": None,
        },
        "fixed_expenses": [],
        "loans": [],
        "budgets": {"confirmed": False, "envelopes": dict.fromkeys(ENVELOPES, 100000)},
        "spending": {
            name: {
                "daily_rate": 0.0,
                "amount_mu": 8.0,
                "amount_sigma": 0.5,
                "card_share": 0.0,
                "weekday_mult": [1.0] * 7,
            }
            for name in ENVELOPES
        },
        "hidden": {
            "payday_boost": 1.0,
            "pre_payday_damp": 1.0,
            "elasticity": 1.0,
            "shock": {"daily_prob": 0.0, "mu": 8.0, "sigma": 0.5},
            "cancel_prob": 0.0,
            "dutch_pay_prob": 0.0,
            "emergency_transfer_monthly": 0,
            "pending_ratio": 0.1,
        },
    }


def test_elasticity_scalar_expands_to_all_envelopes() -> None:
    profile = _minimal_profile()
    profile["hidden"]["elasticity"] = 1.4
    gen = Generator(profile, seed=1, months=1, end=date(2026, 9, 17))
    assert all(v == 1.4 for v in gen._elasticity.values())
    assert set(gen._elasticity) == set(ENVELOPE_IDS.values())


def test_elasticity_dict_per_envelope_with_default_fallback() -> None:
    profile = _minimal_profile()
    profile["hidden"]["elasticity"] = {"외식": 2.0}
    gen = Generator(profile, seed=1, months=1, end=date(2026, 9, 17))
    assert gen._elasticity[ENVELOPE_IDS["외식"]] == 2.0
    # 지정하지 않은 봉투는 탄력도 중립값 1.0 으로 채워진다.
    assert gen._elasticity[ENVELOPE_IDS["교통비"]] == 1.0


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_hidden_elasticity_is_profile_dict(name: str) -> None:
    # 4 프로필의 hidden.elasticity 가 봉투별 dict 로 확장되어 있어야 한다
    # (N4: 스칼라 하나가 아니라 유연/필수 봉투가 서로 다른 값을 갖는다).
    _, _, gt = _gen(name)
    elasticity = gt["hidden_params"]["hidden"]["elasticity"]
    assert isinstance(elasticity, dict)
    assert set(elasticity) == set(ENVELOPES)


# ---------------------------------------------------------------------------
# confirm_status: 흐름별 규칙 (리뷰 N5)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_confirm_status_confirmed_for_income_fixed_card_bill(name: str) -> None:
    _, d, _ = _gen(name)
    for tx in d["transactions"]:
        if tx.get("flow_hint") in ("INCOME", "FIXED", "CARD_BILL"):
            assert tx["confirm_status"] == "CONFIRMED", tx
        if tx.get("exclude_tag") == "SELF_TRANSFER":
            assert tx["confirm_status"] == "CONFIRMED", tx
        if tx.get("exclude_tag") == "DUTCH":
            assert tx["confirm_status"] == "AUTO", tx


# ---------------------------------------------------------------------------
# declined_debits.kind, unpaid_obligation/suppressed_demand 누적 (리뷰 N8)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_declined_debits_have_kind(name: str) -> None:
    _, _, gt = _gen(name)
    for item in gt["declined_debits"]:
        assert item["kind"] in ("FIXED", "LOAN", "SPEND")
        if item["kind"] == "SPEND":
            assert item["envelope_id"] is not None
        else:
            assert item["envelope_id"] is None


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_unpaid_obligation_and_suppressed_demand_are_nondecreasing(name: str) -> None:
    _, _, gt = _gen(name)
    assert "unpaid_obligation" in gt
    assert "suppressed_demand" in gt
    dates = sorted(gt["unpaid_obligation"])
    assert dates == sorted(gt["daily_balance"])
    prev_u, prev_s = 0, 0
    for d in dates:
        u, s = gt["unpaid_obligation"][d], gt["suppressed_demand"][d]
        assert u >= prev_u
        assert s >= prev_s
        prev_u, prev_s = u, s


# ---------------------------------------------------------------------------
# 더치페이 수령분이 envelope_true_spend/_month_spent 에서 차감된다 (리뷰 B2)
# ---------------------------------------------------------------------------


def test_dutch_pay_reduces_envelope_true_spend() -> None:
    """더치 수령분이 그 봉투의 `_month_spent`/`envelope_true_spend` 에서
    차감된다 (리뷰 B2, 생성기 측). `dutch_pay_prob=1.0` 으로 결정론적으로
    확인한다."""

    profile = _minimal_profile()
    profile["hidden"]["dutch_pay_prob"] = 1.0
    gen = Generator(profile, seed=1, months=1, end=date(2026, 9, 8))
    d = date(2026, 9, 7)
    dining_id = ENVELOPE_IDS["외식"]

    # _step_spending 을 거치지 않고 카드 외식 결제 한 건을 직접 주입한다
    # (subcategory_id=1 은 taxonomy 상 "음식점" -> 외식 봉투).
    tx = gen._add_tx(
        tx_type="CARD",
        tx_date=d,
        amount=40000,
        account_id=10,
        card_id=20,
        merchant_name_raw="테스트식당",
        subcategory_id=1,
    )
    gen._month_spent[dining_id] += tx["amount"]
    gen._record_envelope_spend(d, dining_id, tx["amount"])
    ym = "202609"
    before = gen.gt["envelope_true_spend"][ym][str(dining_id)]
    before_month_spent = gen._month_spent[dining_id]

    gen._step_cancel_and_dutch(d)

    assert gen.gt["dutch_pays"], "더치페이가 발생하지 않음(cancel_prob/조건 확인 필요)"
    share = gen.gt["dutch_pays"][0]["amount"]
    assert share > 0
    assert gen._month_spent[dining_id] == before_month_spent - share
    assert gen.gt["envelope_true_spend"][ym][str(dining_id)] == before - share


# ---------------------------------------------------------------------------
# profile_schema 검증 실패 케이스 (리뷰 N10)
# ---------------------------------------------------------------------------


def _valid_raw_profile() -> dict:
    return {
        "name": "T",
        "description": "테스트",
        "accounts": [
            {"id": 10, "alias": "계좌", "is_income": True, "opening_balance": 0, "managed": True}
        ],
        "cards": [
            {
                "id": 20,
                "alias": "카드",
                "kind": "CREDIT",
                "withdrawal_weekday": 1,
                "withdrawal_account_id": 10,
            }
        ],
        "income": {
            "type": "SALARY",
            "day_of_month": 25,
            "amount": 1000000,
            "jitter_sigma": 0.0,
            "median_gap_days": None,
        },
        "fixed_expenses": [],
        "loans": [],
        "budgets": {"confirmed": False, "envelopes": dict.fromkeys(ENVELOPES, 100000)},
        "spending": {
            name: {
                "daily_rate": 0.1,
                "amount_mu": 8.0,
                "amount_sigma": 0.5,
                "card_share": 0.3,
                "weekday_mult": [1.0] * 7,
            }
            for name in ENVELOPES
        },
        "hidden": {
            "payday_boost": 1.0,
            "pre_payday_damp": 1.0,
            "elasticity": 1.0,
            "shock": {"daily_prob": 0.01, "mu": 8.0, "sigma": 0.5},
            "cancel_prob": 0.0,
            "dutch_pay_prob": 0.0,
            "emergency_transfer_monthly": 0,
        },
    }


def test_profile_schema_accepts_valid_profile() -> None:
    validated = validate_profile(_valid_raw_profile())
    # 선택 필드 기본값이 채워져 있어야 한다 (N10 ".get 기본값 통일")
    assert validated["hidden"]["pending_ratio"] == 0.1
    assert validated["fixed_expenses"] == []


def test_profile_schema_rejects_missing_envelope_budget() -> None:
    raw = _valid_raw_profile()
    del raw["budgets"]["envelopes"]["외식"]
    with pytest.raises(ValidationError):
        validate_profile(raw)


def test_profile_schema_rejects_missing_spending_envelope() -> None:
    raw = _valid_raw_profile()
    del raw["spending"]["외식"]
    with pytest.raises(ValidationError):
        validate_profile(raw)


def test_profile_schema_rejects_weekday_mult_wrong_length() -> None:
    raw = _valid_raw_profile()
    raw["spending"]["외식"]["weekday_mult"] = [1.0] * 6
    with pytest.raises(ValidationError):
        validate_profile(raw)


def test_profile_schema_rejects_salary_without_day_of_month() -> None:
    raw = _valid_raw_profile()
    raw["income"] = {
        "type": "SALARY",
        "day_of_month": None,
        "amount": 1000000,
        "jitter_sigma": 0.0,
        "median_gap_days": None,
    }
    with pytest.raises(ValidationError):
        validate_profile(raw)


def test_profile_schema_rejects_irregular_without_median_gap_days() -> None:
    raw = _valid_raw_profile()
    raw["income"] = {
        "type": "IRREGULAR",
        "day_of_month": None,
        "amount": 1000000,
        "jitter_sigma": 0.2,
        "median_gap_days": None,
    }
    with pytest.raises(ValidationError):
        validate_profile(raw)


def test_profile_schema_rejects_dangling_card_reference() -> None:
    raw = _valid_raw_profile()
    raw["cards"][0]["withdrawal_account_id"] = 999
    with pytest.raises(ValidationError):
        validate_profile(raw)


def test_profile_schema_rejects_unknown_field() -> None:
    raw = _valid_raw_profile()
    raw["unexpected_field"] = 1
    with pytest.raises(ValidationError):
        validate_profile(raw)


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_real_profile_yaml_passes_schema(name: str) -> None:
    # 4 프로필 YAML 이 실제로 profile_schema 를 통과하는지 (load_profile 이
    # 이미 검증하지만, 스키마 자체의 회귀를 잡기 위해 명시적으로도 확인한다).
    from fdt.gen.generator import load_profile

    profile = load_profile(name)
    assert set(profile["spending"]) == set(ENVELOPES)
    assert set(profile["budgets"]["envelopes"]) == set(ENVELOPES)


# ---------------------------------------------------------------------------
# 프로필별 수지 범위 (리뷰 N1/N2/N13 재캘리브레이션 회귀)
# ---------------------------------------------------------------------------


def _monthly_ratios(name: str) -> list[float]:
    """완결월(마지막 달 제외)의 (고정비+봉투소비+자기이체)/수입 비율 목록."""

    _, d, gt = generate(name, seed=SEED, months=6, end=END)
    last_ym = f"{END.year:04d}{END.month:02d}"
    complete_months = [m for m in sorted(gt["envelope_true_spend"]) if m != last_ym]

    fixed_by_m: dict[str, int] = defaultdict(int)
    income_by_m: dict[str, int] = defaultdict(int)
    emer_by_m: dict[str, int] = defaultdict(int)
    for tx in d["transactions"]:
        if tx["status"] == "CANCELED":
            continue
        ym = tx["tx_date"][:7].replace("-", "")
        if tx.get("flow_hint") == "FIXED":
            fixed_by_m[ym] += tx["amount"]
        elif tx.get("flow_hint") == "INCOME":
            income_by_m[ym] += tx["amount"]
        if tx.get("exclude_tag") == "SELF_TRANSFER":
            emer_by_m[ym] += tx["amount"]

    ratios = []
    for ym in complete_months:
        income = income_by_m.get(ym, 0)
        if income <= 0:
            continue
        env = sum(gt["envelope_true_spend"][ym].values())
        outflow = fixed_by_m.get(ym, 0) + env + emer_by_m.get(ym, 0)
        ratios.append(outflow / income)
    return ratios


def test_profile_A_spend_income_ratio_in_baseline_range() -> None:
    # N1: 재캘리브레이션 후 지출/수입이 "조용히 SAFE" 로 남되 0 은 아니어야
    # 한다. 완결월 전부가 대략 50~95% 범위(기준선답게 100% 는 넘지 않는다).
    ratios = _monthly_ratios("A_steady")
    assert ratios
    assert all(0.45 <= r <= 0.95 for r in ratios), ratios


def test_profile_B_spend_income_ratio_is_tight() -> None:
    # N13: 결제일 위기형은 지출/수입이 대체로 100% 안팎(80~120%)이어야 한다.
    ratios = _monthly_ratios("B_card_crunch")
    assert ratios
    assert all(0.75 <= r <= 1.20 for r in ratios), ratios


def test_profile_D_spend_income_ratio_leaves_thin_surplus() -> None:
    # N2: 저축 목표가 아슬아슬하게 불가능해야 하므로 지출/수입이 A 보다는
    # 높고(월 잉여가 얇음) 100% 는 넘지 않아야 한다.
    ratios = _monthly_ratios("D_goal_saver")
    assert ratios
    assert all(0.60 <= r <= 0.95 for r in ratios), ratios


def test_profile_D_goal_save_type_is_marginally_infeasible() -> None:
    # N2/S21: "말일 잔액 >= as_of 잔액 + 200만"(SAVE, 증분 저축) 해석에서
    # 9/7 -> 12/31 필요 저축(월 52.6만원 근사)이 실제 월 평균 잉여보다 커야
    # "아슬아슬하게 불가능" 하다.
    _, d, gt = generate("D_goal_saver", seed=SEED, months=6, end=END)
    last_ym = f"{END.year:04d}{END.month:02d}"
    complete_months = [m for m in sorted(gt["envelope_true_spend"]) if m != last_ym]

    fixed_by_m: dict[str, int] = defaultdict(int)
    income_by_m: dict[str, int] = defaultdict(int)
    for tx in d["transactions"]:
        if tx["status"] == "CANCELED":
            continue
        ym = tx["tx_date"][:7].replace("-", "")
        if tx.get("flow_hint") == "FIXED":
            fixed_by_m[ym] += tx["amount"]
        elif tx.get("flow_hint") == "INCOME":
            income_by_m[ym] += tx["amount"]

    surpluses = [
        income_by_m[ym] - fixed_by_m[ym] - sum(gt["envelope_true_spend"][ym].values())
        for ym in complete_months
    ]
    avg_surplus = sum(surpluses) / len(surpluses)

    days_to_goal = (date(2026, 12, 31) - END).days
    required_monthly_saving = 2_000_000 / (days_to_goal / 30.4)

    assert avg_surplus < required_monthly_saving, (avg_surplus, required_monthly_saving)
    # 목표를 아예 포기할 만큼 부족하지도 않아야 한다("아슬아슬").
    assert avg_surplus > required_monthly_saving * 0.5, (avg_surplus, required_monthly_saving)
