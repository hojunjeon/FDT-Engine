"""State(t) 빌드 (SPEC 5장).

`TwinInput` + 정규화된 원장(`fdt.engine.ledger.normalize` 산출물)에서 어느
시점(`as_of`)의 스냅샷 `State` 를 계산한다. 이 모듈은 **원장만** 읽는다 -
생성기 패키지를 import 하지 않고, 프로필 설정 파일이나 정답 데이터를
참조하지 않는다(SPEC 4.2 불변 원칙, 11장 "엔진 코드는 정답 데이터를 읽지
않는다").

공개 함수 (다른 작업 ID 가 import 하는 계약):

- `build_state(twin, ledger, *, as_of=None, budgets_override=None, income=None,
  horizon_cap=90, account_balances=None) -> State`
- `build_state_with_warnings(..., account_balances=None) -> tuple[State, list[FdtWarning]]`
  (`account_balances`: 리뷰 B1 대응. `{account_id: balance}` 를 주면 그 계좌는
  `ledger_mod.account_balance_at` 재계산 없이 그 값을 그대로 쓴다. 홀드아웃
  빌드에서 원장이 `as_of` 로 잘린 뒤 `account_balance_at` 의 역산 분기가
  깨지는 문제를 우회하기 위해 `build_engine`(H1)이 원장을 자르기 전에 계산한
  잔액을 여기로 주입한다.)
- `build_committed_queue(twin, ledger, as_of, cards, horizon_cap=90) -> list[Committed]`
- `propose_budgets(ledger, as_of) -> dict[int, int]`

수입 일정(`IncomeSchedule`)은 이 모듈이 추정하지 않는다. `income` 인자로
주입받은 값을 그대로 쓰고, 주입이 없으면 "수입 없음" 기본값을 쓴다(중복
구현 금지, Behavior 담당 작업이 원장에서 추정한 값을 엔진 빌드 단계가
넘겨준다).
"""

from __future__ import annotations

import calendar
import math
import statistics
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from fdt.engine import ledger as ledger_mod
from fdt.engine.errors import W_FIXED_VARIABLE_UNKNOWN, FdtWarning
from fdt.engine.ledger import LedgerTx
from fdt.engine.schemas.input import CardIn, FixedExpenseIn, LoanIn, TwinInput
from fdt.engine.schemas.state import (
    AccountState,
    CardState,
    Committed,
    Cycle,
    EnvelopeState,
    IncomeSchedule,
    Indicators,
    IssuedBilling,
    State,
)
from fdt.engine.taxonomy import (
    ENVELOPE_IDS,
    ConfirmStatus,
    FixedExpenseType,
    Flow,
    RepaymentType,
)

__all__ = [
    "build_committed_queue",
    "build_state",
    "build_state_with_warnings",
    "propose_budgets",
]

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

_DEFAULT_HORIZON_CAP = 90
_CARD_BILL_KEYWORD = "카드대금"

# SPEC 5.4 표 1행에서 fixed_expenses -> 약정 큐로 직접 옮기는 유형(카드대금은
# 카드 상태에서 별도로 다루고, 대출은 loans[] 에서 다룬다).
_AccountRole = Literal["PRIMARY", "EMERGENCY", "OTHER"]
_BudgetSource = Literal["CONFIRMED", "PROPOSED", "ENGINE"]

_FixedRowKind = Literal["RENT", "UTILITY", "INSURANCE", "TELECOM", "SUBSCRIPTION"]

_FIXED_ROW_KIND_MAP: dict[FixedExpenseType, _FixedRowKind] = {
    FixedExpenseType.RENT: "RENT",
    FixedExpenseType.UTILITY: "UTILITY",
    FixedExpenseType.INSURANCE: "INSURANCE",
    FixedExpenseType.TELECOM: "TELECOM",
    FixedExpenseType.SUBSCRIPTION: "SUBSCRIPTION",
}

# 원장 탐지 반복 고정비에 붙일 kind. 리뷰 B3/S31: 이전에는 Committed.kind
# 열거형에 전용 값이 없어(SPEC 5.1) SUBSCRIPTION 으로 매핑했는데, 그 결과
# loans[]/fixed_expenses 에서 이미 만든 항목과 (kind, name, due, amount) dedup
# 키가 겹치지 않아 대출이자·관리비가 "구독료"로 이중 계상됐다. 이제
# Committed.kind 에 DETECTED_FIXED 전용 값을 추가했으므로 그것을 쓴다.
_DETECTED_FIXED_KIND: Literal["DETECTED_FIXED"] = "DETECTED_FIXED"

# 대출 원리금균등(AMORTIZING) 상환액 계산에 쓰는 가정 상환 개월수.
# `LoanIn` 스키마에 잔여 상환 개월(term)이 없어(SPEC 3.2) 표준 연금 공식을
# 그대로 쓸 수 없다. 3년(36개월) 할부를 기본 가정으로 둔다(구현 결정, 보고서에
# 명시. 실제 서비스 연동 시 스키마에 term 필드를 추가해야 정확해진다).
_AMORTIZING_ASSUMED_TERM_MONTHS = 36

_REPEAT_GAP_MIN_DAYS = 25
_REPEAT_GAP_MAX_DAYS = 35
_TRANSFER_AMOUNT_TOLERANCE_PCT = 0.10


# ---------------------------------------------------------------------------
# 날짜 헬퍼
# ---------------------------------------------------------------------------


def _clamped_month_date(year: int, month: int, day: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def _add_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _first_weekday_on_or_after(d: date, weekday: int) -> date:
    delta = (weekday - d.weekday()) % 7
    return d + timedelta(days=delta)


def _monthly_due_dates(anchor_day: int, as_of: date, horizon_cap: int) -> list[date]:
    """`anchor_day`(1~31, 말일 보정)가 매달 돌아오는 날짜 중
    `(as_of, as_of+horizon_cap]` 안에 드는 것 전부(SPEC 5.4 "매월 반복")."""

    end = as_of + timedelta(days=horizon_cap)
    year, month = as_of.year, as_of.month
    candidate = _clamped_month_date(year, month, anchor_day)
    if candidate <= as_of:
        year, month = _add_month(year, month)
        candidate = _clamped_month_date(year, month, anchor_day)

    dates: list[date] = []
    while candidate <= end:
        dates.append(candidate)
        year, month = _add_month(year, month)
        candidate = _clamped_month_date(year, month, anchor_day)
    return dates


def _month_bounds(d: date) -> tuple[date, date]:
    start = d.replace(day=1)
    last_day = calendar.monthrange(d.year, d.month)[1]
    end = date(d.year, d.month, last_day)
    return start, end


# ---------------------------------------------------------------------------
# 원장 필터 (SPEC "모든 원장 접근은 t.date <= as_of")
# ---------------------------------------------------------------------------


def _ledger_until(ledger: tuple[LedgerTx, ...], as_of: date) -> tuple[LedgerTx, ...]:
    return tuple(r for r in ledger if r.date <= as_of)


# ---------------------------------------------------------------------------
# 계좌 역할 (SPEC 5.3 PRIMARY/EMERGENCY)
# ---------------------------------------------------------------------------


def _primary_account_id(twin: TwinInput, ledger_until: tuple[LedgerTx, ...]) -> int:
    managed_ids = {a.id for a in twin.accounts if a.is_managed}

    card_counts: dict[int, int] = {}
    for card in twin.cards:
        if card.withdrawal_account_id not in managed_ids:
            continue
        card_counts[card.withdrawal_account_id] = card_counts.get(card.withdrawal_account_id, 0) + 1
    if card_counts:
        top = max(card_counts.values())
        return min(aid for aid, cnt in card_counts.items() if cnt == top)

    income_accounts = sorted(a.id for a in twin.accounts if a.is_income and a.id in managed_ids)
    if income_accounts:
        return income_accounts[0]

    income_counts: dict[int, int] = {}
    for record in ledger_until:
        if record.flow == Flow.INCOME and record.account_id in managed_ids:
            income_counts[record.account_id] = income_counts.get(record.account_id, 0) + 1
    if income_counts:
        top = max(income_counts.values())
        return min(aid for aid, cnt in income_counts.items() if cnt == top)

    # 관리 계좌는 최소 1개 있음을 입력 검증(E-INPUT-EMPTY)이 보장한다.
    return min(managed_ids)


def _build_accounts_and_balances(
    twin: TwinInput,
    ledger: tuple[LedgerTx, ...],
    as_of: date,
    account_balances: dict[int, int] | None = None,
) -> tuple[list[AccountState], int, int]:
    """계좌별 잔액과 PRIMARY/EMERGENCY 역할을 계산한다.

    `account_balances` 가 주어지면(H1 `build_engine` 홀드아웃 경로) 그 계좌의
    잔액은 자체 역산(`ledger_mod.account_balance_at`) 대신 그대로 신뢰한다.
    `build_engine` 이 원장을 `as_of` 로 자른 뒤에는 `account_balance_at` 의
    `opening_balance is None` 역산 분기가 잘린 구간을 못 봐 항상 0을 빼는
    문제(리뷰 B1)가 있어, 호출자가 원장이 잘리기 전에 계산한 잔액을 주입할 수
    있게 한다.
    """

    ledger_upto = _ledger_until(ledger, as_of)
    primary_id = _primary_account_id(twin, ledger_upto)

    accounts: list[AccountState] = []
    liquidity = 0
    emergency_fund = 0
    for account in twin.accounts:
        if account_balances is not None and account.id in account_balances:
            balance = account_balances[account.id]
        else:
            balance = ledger_mod.account_balance_at(twin, ledger, account.id, as_of)
        role: _AccountRole
        if not account.is_managed:
            role = "OTHER"
        elif account.id == primary_id:
            role = "PRIMARY"
            liquidity = balance
        else:
            role = "EMERGENCY"
            emergency_fund += balance
        accounts.append(AccountState(id=account.id, role=role, balance=balance))

    return accounts, liquidity, emergency_fund


# ---------------------------------------------------------------------------
# 카드 상태 (SPEC 5.3 unbilled/issued_unpaid)
# ---------------------------------------------------------------------------

_UNBILLED_FLOWS: frozenset[Flow] = frozenset({Flow.SPEND, Flow.FIXED, Flow.REFUND})


def _cycle_start(as_of: date) -> date:
    return as_of - timedelta(days=as_of.weekday())


def _card_unbilled(ledger_upto: tuple[LedgerTx, ...], card_id: int, as_of: date) -> int:
    start = _cycle_start(as_of)
    total = 0
    for record in ledger_upto:
        if record.card_id != card_id:
            continue
        if record.flow not in _UNBILLED_FLOWS:
            continue
        if not (start <= record.date <= as_of):
            continue
        total += record.signed_amount
    return -total


def _reconstruct_issued_unpaid_from_billings(
    twin: TwinInput, card_id: int, as_of: date
) -> list[IssuedBilling] | None:
    """`card_billings` 기반 재구성. 이 카드의 청구서가 하나도 없으면 `None`.

    S28: SPEC 5.3 문구는 `card_billings[status=UNPAID, billing_date <= as_of]`
    라고 적었지만, `status` 는 `twin.as_of`(현재) 시점의 값이라 그보다 앞선
    홀드아웃 `as_of` 에서는 쓸 수 없다(나중에 결제된 청구서가 `status=PAID` 로
    보여 미결제를 놓친다). 그 시점 기준 미결제인지는 `paid_at` 으로 판정해야
    정확하다 - `paid_at is None or paid_at > as_of`. 홀드아웃 재구성 실측
    검증(리뷰 W3~W5, `test_holdout_issued_unpaid_reconstruction_matches_billing_status`)
    은 이 판정이 옳음을 확인했다.
    """

    billings = [b for b in twin.card_billings if b.card_id == card_id]
    if not billings:
        return None

    unpaid: list[IssuedBilling] = []
    for billing in billings:
        if billing.billing_date > as_of:
            continue
        if billing.paid_at is None or billing.paid_at > as_of:
            unpaid.append(
                IssuedBilling(billing_date=billing.billing_date, amount=billing.total_amount)
            )
    unpaid.sort(key=lambda b: b.billing_date)
    return unpaid


def _reconstruct_issued_unpaid_from_ledger(
    ledger_upto: tuple[LedgerTx, ...],
    card: CardIn,
    as_of: date,
) -> list[IssuedBilling]:
    """`card_billings` 가 이 카드에 전혀 없을 때의 원장 기반 재구성(SPEC 5.3).

    생성기의 주 단위 청구 발행 규칙(월요일 발행, 직전 주 승인 합)을 그대로
    되짚는다. 발행된 각 주간 청구서에 대응하는 `CARD_BILL` 출금 레코드가
    원장에 없으면 미결제로 본다.
    """

    account_id = card.withdrawal_account_id
    keyword = f"{_CARD_BILL_KEYWORD} {card.card_name}"

    card_dates = sorted({r.date for r in ledger_upto if r.card_id == card.id})
    if not card_dates:
        return []

    first_monday = card_dates[0] - timedelta(days=card_dates[0].weekday())
    unpaid: list[IssuedBilling] = []

    monday = first_monday + timedelta(days=7)
    while monday <= as_of:
        week_start, week_end = monday - timedelta(days=7), monday - timedelta(days=1)
        total = 0
        for record in ledger_upto:
            if record.card_id != card.id or record.flow not in _UNBILLED_FLOWS:
                continue
            if week_start <= record.date <= week_end:
                total += record.signed_amount
        amount = -total
        if amount > 0:
            due = _first_weekday_on_or_after(monday, card.withdrawal_weekday)
            paid = any(
                record.account_id == account_id
                and record.flow == Flow.CARD_BILL
                and record.merchant_name_raw == keyword
                and record.date >= due
                and -record.signed_amount == amount
                for record in ledger_upto
            )
            if not paid:
                unpaid.append(IssuedBilling(billing_date=monday, amount=amount))
        monday += timedelta(days=7)

    return unpaid


def _build_cards(twin: TwinInput, ledger: tuple[LedgerTx, ...], as_of: date) -> list[CardState]:
    ledger_upto = _ledger_until(ledger, as_of)
    cards: list[CardState] = []
    for card in twin.cards:
        unbilled = _card_unbilled(ledger_upto, card.id, as_of)
        issued_unpaid = _reconstruct_issued_unpaid_from_billings(twin, card.id, as_of)
        if issued_unpaid is None:
            issued_unpaid = _reconstruct_issued_unpaid_from_ledger(ledger_upto, card, as_of)
        cards.append(
            CardState(
                id=card.id,
                withdrawal_weekday=card.withdrawal_weekday,
                withdrawal_account_id=card.withdrawal_account_id,  # S33
                unbilled=unbilled,
                issued_unpaid=issued_unpaid,
            )
        )
    return cards


# ---------------------------------------------------------------------------
# 약정 큐 (SPEC 5.4)
# ---------------------------------------------------------------------------


@dataclass
class _QueueBuildResult:
    items: list[Committed]
    warnings: list[FdtWarning]


def _fixed_expense_amount(
    ledger_upto: tuple[LedgerTx, ...],
    fx: FixedExpenseIn,
) -> tuple[int, list[FdtWarning]]:
    if not fx.is_variable:
        return fx.amount, []

    matches = [
        record
        for record in ledger_upto
        if record.flow == Flow.FIXED
        and record.merchant_name_raw == fx.name
        and (
            (fx.card_id is not None and record.card_id == fx.card_id)
            or (
                fx.withdrawal_account_id is not None
                and record.account_id == fx.withdrawal_account_id
            )
        )
    ]
    matches.sort(key=lambda r: r.date, reverse=True)
    recent = matches[:3]
    if not recent:
        # N20: SPEC R6 의 facts `unknown_variable_fixed` 를 만들려면 이름·유형·
        # 계좌·카드까지 필요하다. `fixed_expense_id` 만으로는 W8/facts 단계가
        # twin 을 다시 뒤져야 한다.
        return 0, [
            FdtWarning(
                code=W_FIXED_VARIABLE_UNKNOWN,
                details={
                    "fixed_expense_id": fx.id,
                    "name": fx.name,
                    "expense_type": fx.expense_type.value,
                    "withdrawal_account_id": fx.withdrawal_account_id,
                    "card_id": fx.card_id,
                },
            )
        ]

    amounts = [abs(r.signed_amount) for r in recent]
    return round(statistics.median(amounts)), []


def _loan_monthly_amount(loan: LoanIn, loan_rate_delta_bp: int) -> int:
    adjusted_rate_pct = loan.annual_rate_pct + loan_rate_delta_bp / 100
    monthly_rate = adjusted_rate_pct / 100 / 12
    interest = round(loan.balance * monthly_rate / 10) * 10

    if loan.repayment != RepaymentType.AMORTIZING:
        return int(interest)

    n = _AMORTIZING_ASSUMED_TERM_MONTHS
    if monthly_rate == 0:
        payment = loan.balance / n
    else:
        payment = loan.balance * monthly_rate / (1 - (1 + monthly_rate) ** (-n))
    return int(round(payment / 10) * 10)


def _fixed_expense_queue_items(
    twin: TwinInput,
    ledger_upto: tuple[LedgerTx, ...],
    as_of: date,
    horizon_cap: int,
) -> _QueueBuildResult:
    items: list[Committed] = []
    warnings: list[FdtWarning] = []

    for fx in twin.fixed_expenses:
        if not fx.active or fx.expense_type not in _FIXED_ROW_KIND_MAP:
            continue
        amount, fx_warnings = _fixed_expense_amount(ledger_upto, fx)
        warnings.extend(fx_warnings)
        certainty = 0.8 if fx.is_variable else 1.0
        for due in _monthly_due_dates(fx.payment_day, as_of, horizon_cap):
            items.append(
                Committed(
                    kind=_FIXED_ROW_KIND_MAP[fx.expense_type],
                    name=fx.name,
                    due=due,
                    amount=amount,
                    certainty=certainty,
                    account_id=fx.withdrawal_account_id,
                    card_id=fx.card_id,
                    source_fixed_expense_id=fx.id,
                )
            )
    return _QueueBuildResult(items, warnings)


def _loan_queue_items(
    twin: TwinInput, as_of: date, horizon_cap: int
) -> list[Committed]:
    items: list[Committed] = []
    delta_bp = twin.externals.loan_rate_delta_bp
    for loan in twin.loans:
        amount = _loan_monthly_amount(loan, delta_bp)
        for due in _monthly_due_dates(loan.interest_day, as_of, horizon_cap):
            items.append(
                Committed(
                    kind="LOAN",
                    name="대출이자",
                    due=due,
                    amount=amount,
                    certainty=1.0,
                    account_id=loan.withdrawal_account_id,
                    card_id=None,
                    source_loan_id=loan.id,
                )
            )
    return items


def _card_queue_items(
    twin: TwinInput, as_of: date, cards: list[CardState]
) -> list[Committed]:
    items: list[Committed] = []
    card_by_id = {c.id: c for c in twin.cards}

    for card_state in cards:
        card = card_by_id.get(card_state.id)
        if card is None:
            continue
        name = f"{_CARD_BILL_KEYWORD} {card.card_name}"

        if card_state.unbilled > 0:
            next_monday = _cycle_start(as_of) + timedelta(days=7)
            due = _first_weekday_on_or_after(next_monday, card.withdrawal_weekday)
            items.append(
                Committed(
                    kind="CARD_BILL",
                    name=name,
                    due=due,
                    amount=card_state.unbilled,
                    certainty=0.9,
                    account_id=card.withdrawal_account_id,
                    card_id=card.id,
                    source_card_id=card.id,
                )
            )

        for billing in card_state.issued_unpaid:
            due = _first_weekday_on_or_after(billing.billing_date, card.withdrawal_weekday)
            if due <= as_of:
                # S40: 예정 출금일이 이미 지났으면(연체) as_of+1 로 당긴다. §7.2
                # 4단계는 카드 출금을 매일 재시도하므로, 다음 영업일(as_of+1)에
                # 다시 시도하는 것으로 표현하는 편이 "다음 withdrawal_weekday"
                # 까지 그대로 기다리는 것보다 그 재시도 규칙과 정합한다.
                due = as_of + timedelta(days=1)
            items.append(
                Committed(
                    kind="CARD_BILL",
                    name=name,
                    due=due,
                    amount=billing.amount,
                    certainty=1.0,
                    account_id=card.withdrawal_account_id,
                    card_id=card.id,
                    source_card_id=card.id,
                )
            )
    return items


def _known_recurring_names(
    twin: TwinInput,
) -> tuple[dict[int, set[str]], dict[int, set[str]]]:
    """B3/S30/S31: 원장 탐지 반복 고정비가 만들지 말아야 할 (계좌 또는 카드,
    이름) 집합. `fixed_expenses`(대출이자는 loans[] 에서 별도로 큐에 들어가고,
    카드대금은 cards[] 에서 별도로 들어간다)와 같은 이름·같은 계좌/카드로
    원장에 `FIXED` 레코드가 남아 있으면, 그 이름을 원장 탐지가 다시 잡아
    `LOAN 대출이자` + `SUBSCRIPTION/DETECTED_FIXED 대출이자` 처럼 이중 계상하게
    된다(리뷰 B3 실측: B 프로필 대출이자 68,000원이 매달 두 번 잡힘).

    `fixed_expenses` 는 `active` 여부와 무관하게 전부 포함한다 - 비활성화되거나
    개명된 뒤에도 활성 시절의 `FIXED` 레코드가 원장에 남아 있어, `active` 로
    걸러내면 정확히 그 시점에 유령 항목이 생긴다.
    """

    by_account: dict[int, set[str]] = {}
    by_card: dict[int, set[str]] = {}

    def _add_account(account_id: int | None, name: str) -> None:
        if account_id is not None:
            by_account.setdefault(account_id, set()).add(name)

    def _add_card(card_id: int | None, name: str) -> None:
        if card_id is not None:
            by_card.setdefault(card_id, set()).add(name)

    for fx in twin.fixed_expenses:
        _add_account(fx.withdrawal_account_id, fx.name)
        _add_card(fx.card_id, fx.name)
    for loan in twin.loans:
        _add_account(loan.withdrawal_account_id, "대출이자")
    for card in twin.cards:
        card_bill_name = f"{_CARD_BILL_KEYWORD} {card.card_name}"
        _add_account(card.withdrawal_account_id, card_bill_name)
        _add_card(card.id, card_bill_name)

    return by_account, by_card


def _detected_fixed_queue_items(
    twin: TwinInput, ledger_upto: tuple[LedgerTx, ...], as_of: date, horizon_cap: int
) -> list[Committed]:
    excluded_by_account, excluded_by_card = _known_recurring_names(twin)

    groups: dict[tuple[int | None, int | None, str], list[LedgerTx]] = {}
    for record in ledger_upto:
        if record.flow != Flow.FIXED:
            continue
        name = record.merchant_name_raw
        if name is None:
            continue
        if record.account_id is not None and name in excluded_by_account.get(
            record.account_id, ()
        ):
            continue
        if record.card_id is not None and name in excluded_by_card.get(record.card_id, ()):
            continue
        key = (record.account_id, record.card_id, name)
        groups.setdefault(key, []).append(record)

    items: list[Committed] = []
    for (account_id, card_id, name), records in groups.items():
        records.sort(key=lambda r: r.date)
        dates = [r.date for r in records]
        if len(dates) < 2:
            continue
        gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        if not any(_REPEAT_GAP_MIN_DAYS <= g <= _REPEAT_GAP_MAX_DAYS for g in gaps):
            continue

        recent = records[-3:]
        amount = round(statistics.median([abs(r.signed_amount) for r in recent]))
        last_date = dates[-1]
        for due in _monthly_due_dates(last_date.day, as_of, horizon_cap):
            items.append(
                Committed(
                    kind=_DETECTED_FIXED_KIND,
                    name=name,
                    due=due,
                    amount=amount,
                    certainty=0.9,
                    account_id=account_id,
                    card_id=card_id,
                )
            )
    return items


def _detected_self_transfer_queue_items(
    ledger_upto: tuple[LedgerTx, ...], as_of: date, horizon_cap: int
) -> list[Committed]:
    groups: dict[tuple[int, int], list[LedgerTx]] = {}
    for record in ledger_upto:
        if record.flow != Flow.TRANSFER_INTERNAL:
            continue
        if record.signed_amount >= 0:
            continue  # 출금 레코드만(상대 계좌 쪽 + 레코드는 제외)
        if record.account_id is None or record.counterparty_account_id is None:
            continue
        key = (record.account_id, record.counterparty_account_id)
        groups.setdefault(key, []).append(record)

    items: list[Committed] = []
    for (account_id, _counterparty_id), records in groups.items():
        records.sort(key=lambda r: r.date)
        median_amount = statistics.median([abs(r.signed_amount) for r in records])
        clustered = [
            r
            for r in records
            if abs(abs(r.signed_amount) - median_amount)
            <= median_amount * _TRANSFER_AMOUNT_TOLERANCE_PCT
        ]
        if len(clustered) < 2:
            continue
        dates = [r.date for r in clustered]
        gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        if not any(_REPEAT_GAP_MIN_DAYS <= g <= _REPEAT_GAP_MAX_DAYS for g in gaps):
            continue

        recent = clustered[-3:]
        amount = round(statistics.median([abs(r.signed_amount) for r in recent]))
        last_date = dates[-1]
        name = clustered[-1].merchant_name_raw or "자기이체"
        for due in _monthly_due_dates(last_date.day, as_of, horizon_cap):
            items.append(
                Committed(
                    kind="SELF_TRANSFER",
                    name=name,
                    due=due,
                    amount=amount,
                    certainty=0.9,
                    account_id=account_id,
                    card_id=None,
                )
            )
    return items


def _dedup_committed(items: list[Committed]) -> list[Committed]:
    """SPEC 5.4 "동일 (kind, name, due) 는 하나". 여기서는 `amount` 도 키에
    더한다 - 같은 카드의 서로 다른 미결제 청구서 두 건이 (연체로 인해) 우연히
    같은 보정된 due(as_of+1)로 겹칠 수 있는데, 그 둘은 금액이 달라 실제로는
    서로 다른 의무다. `amount` 없이 (kind,name,due) 만 쓰면 이 경우 하나가
    부당하게 사라진다(구현 결정, 보고서에 명시)."""

    seen: set[tuple[str, str, date, int]] = set()
    out: list[Committed] = []
    for item in items:
        key = (item.kind, item.name, item.due, item.amount)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def build_committed_queue(
    twin: TwinInput,
    ledger: tuple[LedgerTx, ...],
    as_of: date,
    cards: list[CardState],
    horizon_cap: int = _DEFAULT_HORIZON_CAP,
) -> list[Committed]:
    """약정 큐 (SPEC 5.4). 경고는 버려진다 - 경고까지 필요하면
    `build_state_with_warnings` 를 쓴다."""

    result = _build_committed_queue_with_warnings(twin, ledger, as_of, cards, horizon_cap)
    return result.items


def _build_committed_queue_with_warnings(
    twin: TwinInput,
    ledger: tuple[LedgerTx, ...],
    as_of: date,
    cards: list[CardState],
    horizon_cap: int,
) -> _QueueBuildResult:
    ledger_upto = _ledger_until(ledger, as_of)

    fixed_result = _fixed_expense_queue_items(twin, ledger_upto, as_of, horizon_cap)
    items: list[Committed] = list(fixed_result.items)
    items.extend(_loan_queue_items(twin, as_of, horizon_cap))
    items.extend(_card_queue_items(twin, as_of, cards))
    items.extend(_detected_fixed_queue_items(twin, ledger_upto, as_of, horizon_cap))
    items.extend(_detected_self_transfer_queue_items(ledger_upto, as_of, horizon_cap))

    return _QueueBuildResult(_dedup_committed(items), fixed_result.warnings)


# ---------------------------------------------------------------------------
# 예산 (SPEC 5.5 propose_budgets, 5.3 봉투 예산 우선순위)
# ---------------------------------------------------------------------------


def _round_up_to_10000(amount: float) -> int:
    return max(10_000, math.ceil(amount / 10_000) * 10_000)


def _completed_months(ledger_upto: tuple[LedgerTx, ...], as_of: date) -> list[tuple[date, date]]:
    if not ledger_upto:
        return []
    earliest = min(r.date for r in ledger_upto)
    out: list[tuple[date, date]] = []
    year, month = earliest.year, earliest.month
    while True:
        start, end = _month_bounds(date(year, month, 1))
        if end > as_of:
            break
        out.append((start, end))
        if year == as_of.year and month == as_of.month:
            break
        year, month = _add_month(year, month)
    return out


def propose_budgets(ledger: tuple[LedgerTx, ...], as_of: date) -> dict[int, int]:
    """엔진 예산 제안 (SPEC 5.5). 완결 월 3개월 이상 중앙값, 1~2개월 평균,
    0개월은 최근 28일 순지출 x 30/28. 만원 올림, 하한 10,000원."""

    ledger_upto = _ledger_until(ledger, as_of)
    completed = _completed_months(ledger_upto, as_of)
    envelope_ids = list(ENVELOPE_IDS.values())

    proposals: dict[int, int] = {}
    if len(completed) >= 3:
        per_month = [
            ledger_mod.envelope_net_spend(ledger_upto, start, end) for start, end in completed
        ]
        for envelope_id in envelope_ids:
            values = [m.get(envelope_id, 0) for m in per_month]
            proposals[envelope_id] = _round_up_to_10000(statistics.median(values))
    elif len(completed) >= 1:
        per_month = [
            ledger_mod.envelope_net_spend(ledger_upto, start, end) for start, end in completed
        ]
        for envelope_id in envelope_ids:
            values = [m.get(envelope_id, 0) for m in per_month]
            proposals[envelope_id] = _round_up_to_10000(sum(values) / len(values))
    else:
        window_start = as_of - timedelta(days=27)
        totals = ledger_mod.envelope_net_spend(ledger_upto, window_start, as_of)
        for envelope_id in envelope_ids:
            proposals[envelope_id] = _round_up_to_10000(totals.get(envelope_id, 0) * 30 / 28)

    return proposals


def _envelope_states(
    twin: TwinInput,
    ledger: tuple[LedgerTx, ...],
    as_of: date,
    budgets_override: dict[int, int] | None,
) -> list[EnvelopeState]:
    ledger_upto = _ledger_until(ledger, as_of)
    month_start, _month_end = _month_bounds(as_of)
    spent_by_envelope = ledger_mod.envelope_net_spend(ledger_upto, month_start, as_of)

    budget_month = f"{as_of.year:04d}{as_of.month:02d}"
    confirmed_by_envelope: dict[int, int] = {}
    proposed_by_envelope: dict[int, int] = {}
    for budget in twin.budgets:
        if budget.budget_month != budget_month:
            continue
        for env in budget.envelopes:
            if env.confirmed_amount is not None:
                confirmed_by_envelope[env.envelope_id] = env.confirmed_amount
            if env.proposed_amount is not None:
                proposed_by_envelope[env.envelope_id] = env.proposed_amount

    engine_proposals: dict[int, int] | None = None

    envelopes: list[EnvelopeState] = []
    for name, envelope_id in ENVELOPE_IDS.items():
        source: _BudgetSource
        if budgets_override is not None and envelope_id in budgets_override:
            budget_amount = budgets_override[envelope_id]
            source = "CONFIRMED"
        elif envelope_id in confirmed_by_envelope:
            budget_amount = confirmed_by_envelope[envelope_id]
            source = "CONFIRMED"
        elif envelope_id in proposed_by_envelope:
            budget_amount = proposed_by_envelope[envelope_id]
            source = "PROPOSED"
        else:
            if engine_proposals is None:
                engine_proposals = propose_budgets(ledger, as_of)
            budget_amount = engine_proposals[envelope_id]
            source = "ENGINE"

        spent = spent_by_envelope.get(envelope_id, 0)
        envelopes.append(
            EnvelopeState(
                envelope_id=envelope_id,
                name=name,
                budget=budget_amount,
                spent=spent,
                remaining=budget_amount - spent,
                budget_source=source,
            )
        )
    return envelopes


# ---------------------------------------------------------------------------
# 지표 (SPEC 5.3)
# ---------------------------------------------------------------------------


def _indicators(ledger: tuple[LedgerTx, ...], as_of: date) -> Indicators:
    ledger_upto = _ledger_until(ledger, as_of)
    if ledger_upto:
        earliest = min(r.date for r in ledger_upto)
        history_days_available = (as_of - earliest).days + 1
    else:
        history_days_available = 0

    def _window_avg(max_days: int) -> float:
        if history_days_available <= 0:
            return 0.0
        days = min(history_days_available, max_days)
        window_start = as_of - timedelta(days=days - 1)
        totals = ledger_mod.envelope_net_spend(ledger_upto, window_start, as_of)
        total = sum(totals.values())
        return total / days

    spend_7d_avg = _window_avg(7)
    spend_90d_avg = _window_avg(90)
    acceleration = spend_7d_avg / max(spend_90d_avg, 1000.0)

    month_start, _month_end = _month_bounds(as_of)
    unconfirmed_count = sum(
        1
        for record in ledger_upto
        if record.flow == Flow.SPEND
        and record.confirm_status == ConfirmStatus.PENDING
        and month_start <= record.date <= as_of
    )

    return Indicators(
        spend_7d_avg=spend_7d_avg,
        spend_90d_avg=spend_90d_avg,
        acceleration=acceleration,
        unconfirmed_count=unconfirmed_count,
    )


def _cycle(as_of: date) -> Cycle:
    start, end = _month_bounds(as_of)
    last_day = end.day
    return Cycle(
        budget_cycle_start=start,
        budget_cycle_end=end,
        progress=as_of.day / last_day,
    )


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

_DEFAULT_INCOME = IncomeSchedule(next_date=None, expected=0, irregular=True, median_gap_days=None)


def build_state_with_warnings(
    twin: TwinInput,
    ledger: tuple[LedgerTx, ...],
    *,
    as_of: date | None = None,
    budgets_override: dict[int, int] | None = None,
    income: IncomeSchedule | None = None,
    horizon_cap: int = _DEFAULT_HORIZON_CAP,
    account_balances: dict[int, int] | None = None,
) -> tuple[State, list[FdtWarning]]:
    """State(t) 를 만든다 (SPEC 5장).

    `account_balances` (리뷰 B1 대응, H1 계약): 주어지면 그 계좌들의 잔액은
    `ledger_mod.account_balance_at` 로 다시 계산하지 않고 그대로 신뢰한다.
    `build_engine` 이 `as_of` 로 원장을 잘라내면(홀드아웃) `account_balance_at`
    의 `opening_balance is None` 역산 분기가 잘려나간 구간을 보지 못해 항상
    0을 빼는 문제가 있으므로, 호출자가 원장을 자르기 전에 계산한 잔액을 여기로
    주입해 우회한다. `None`(기본값)이면 기존 동작(원장에서 직접 계산)과 같다.
    """

    effective_as_of = as_of if as_of is not None else twin.as_of

    accounts, liquidity, emergency_fund = _build_accounts_and_balances(
        twin, ledger, effective_as_of, account_balances
    )
    cards = _build_cards(twin, ledger, effective_as_of)
    queue_result = _build_committed_queue_with_warnings(
        twin, ledger, effective_as_of, cards, horizon_cap
    )
    envelopes = _envelope_states(twin, ledger, effective_as_of, budgets_override)
    indicators = _indicators(ledger, effective_as_of)
    cycle = _cycle(effective_as_of)

    state = State(
        as_of=effective_as_of,
        accounts=accounts,
        liquidity=liquidity,
        emergency_fund=emergency_fund,
        cards=cards,
        committed=queue_result.items,
        envelopes=envelopes,
        income=income if income is not None else _DEFAULT_INCOME,
        indicators=indicators,
        cycle=cycle,
    )
    return state, queue_result.warnings


def build_state(
    twin: TwinInput,
    ledger: tuple[LedgerTx, ...],
    *,
    as_of: date | None = None,
    budgets_override: dict[int, int] | None = None,
    income: IncomeSchedule | None = None,
    horizon_cap: int = _DEFAULT_HORIZON_CAP,
    account_balances: dict[int, int] | None = None,
) -> State:
    state, _warnings = build_state_with_warnings(
        twin,
        ledger,
        as_of=as_of,
        budgets_override=budgets_override,
        income=income,
        horizon_cap=horizon_cap,
        account_balances=account_balances,
    )
    return state
