"""원장 정규화·흐름 판정·대사 (SPEC 5.2 "원장 정규화와 흐름 판정", 3.3 계좌
대사, 5.3 잔액 규칙).

`TwinInput.transactions` 를 불변 `LedgerTx` 튜플로 바꾼다. 이 모듈이 내는
`LedgerTx` 는 이후 State/Behavior/Simulate 가 유일하게 신뢰하는 거래 원장이다
(SPEC 4.2-4 "ledger 는 생성 후 변경 불가").

공개 함수 (다른 작업 ID 가 import 하는 계약):

- `normalize(twin, as_of=None) -> tuple[LedgerTx, ...]`
- `envelope_net_spend(ledger, start, end) -> dict[int, int]`
- `account_balance_at(twin, ledger, account_id, as_of) -> int`
- `reconcile(twin, ledger, *, strict=False) -> list[FdtWarning]`
- `history_days(ledger) -> int`
- `future_tx_count(twin) -> int`
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, time

from fdt.engine.errors import E_RECON, W_RECON, FdtError, FdtWarning
from fdt.engine.schemas.input import FixedExpenseIn, TransactionIn, TwinInput
from fdt.engine.taxonomy import (
    OTHER_ENVELOPE_ID,
    ConfirmStatus,
    ExcludeTag,
    FixedExpenseType,
    Flow,
    TxStatus,
    TxType,
    envelope_of,
)

# ---------------------------------------------------------------------------
# 고정비 매칭 허용 오차 (SPEC 5.2, 규칙 3)
# ---------------------------------------------------------------------------

FIXED_AMOUNT_TOLERANCE_PCT: float = 0.10
FIXED_PAYMENT_DAY_TOLERANCE_DAYS: int = 3
CARD_BILL_MERCHANT_KEYWORD: str = "카드대금"

# 봉투 차감에서 제외하는 태그 (SPEC 5.2 "원장 규칙 NFR-BGT-01").
_ENVELOPE_EXCLUDED_TAGS: frozenset[ExcludeTag] = frozenset(
    {ExcludeTag.EMERGENCY, ExcludeTag.CARRYOVER}
)

# 봉투를 가지는 흐름(SPEND/REFUND) 만 confidence 규칙(SPEC 5.2 규칙 5)을 적용.
_ENVELOPE_BEARING_FLOWS: frozenset[Flow] = frozenset({Flow.SPEND, Flow.REFUND})

_CONFIRM_STATUS_CONFIDENCE: dict[ConfirmStatus, float] = {
    ConfirmStatus.CONFIRMED: 1.0,
    ConfirmStatus.AUTO: 0.8,
    ConfirmStatus.PENDING: 0.5,
}


@dataclass(frozen=True, slots=True)
class LedgerTx:
    """정규화·분류된 원장 한 줄 (SPEC 5.2, 4.2-4 불변).

    `id` 는 대부분 원본 `transactions[].id` 와 같다. 예외 둘:
    (1) 취소(CANCELED) CARD 거래는 SPEND(-)/REFUND(+) 두 건으로 나뉘고, SPEND
        건은 원본 id 를, REFUND 건은 `-원본id` 를 쓴다(이력 보존, 순액 0).
    (2) TRANSFER_INTERNAL 로 판정되고 상대 계좌가 내 계좌면, 그 계좌에 +
        레코드를 하나 더 만든다. 이 레코드의 id 는 `원본id * 10 + 1` 이다
        (결정론적 규칙, 원본 id 와 절대 겹치지 않도록 자릿수를 늘린다).
    두 경우 모두 `origin_tx_id` 는 항상 원본 `transactions[].id` 를 가리킨다.
    """

    id: int
    date: date
    time: time
    account_id: int | None
    card_id: int | None
    signed_amount: int
    flow: Flow
    envelope_id: int | None
    subcategory_id: int | None
    confidence: float
    source: str
    merchant_name_raw: str | None
    exclude_tag: ExcludeTag
    confirm_status: ConfirmStatus
    origin_tx_id: int


# ---------------------------------------------------------------------------
# normalize()
# ---------------------------------------------------------------------------


def normalize(twin: TwinInput, as_of: date | None = None) -> tuple[LedgerTx, ...]:
    """`TwinInput.transactions` -> 정규화된 불변 원장 (SPEC 5.2).

    `as_of` 를 생략하면 `twin.as_of` 를 쓴다. `as_of` 이하 날짜의 거래만
    쓴다(SPEC 2장 as_of, 3.3 W-INPUT-FUTURE_TX - 이후 거래는 여기서 조용히
    걸러지고 무시된다. 경고 발행은 `future_tx_count`/엔진 상위 계층 몫이다).

    정렬은 (date, time, id) 이다. 흐름 판정은 `flow_hint` 가 있으면 그것을
    그대로 쓰고(SPEC 5.2 "흐름 판정 순서"), 없으면 아래 순서를 따른다.

    1. `status == CANCELED` 인 CARD 거래 -> SPEND(-)/REFUND(+) 두 건.
    2. `exclude_tag == SELF_TRANSFER` 또는 상대 계좌가 내 계좌 -> TRANSFER_INTERNAL.
    3. 고정비/카드대금 매칭 -> FIXED / CARD_BILL.
    4. `tx_type == DEPOSIT` -> `is_income` 계좌면 INCOME, 아니면 REFUND.
    5. 나머지 CARD/WITHDRAW -> SPEND.
    """

    effective_as_of = as_of if as_of is not None else twin.as_of
    account_ids = {account.id for account in twin.accounts}

    ordered_txs = sorted(
        (tx for tx in twin.transactions if tx.tx_date <= effective_as_of),
        key=lambda tx: (tx.tx_date, tx.tx_time, tx.id),
    )

    records: list[LedgerTx] = []
    for tx in ordered_txs:
        records.extend(_normalize_one(tx, twin, account_ids))

    records.sort(key=lambda r: (r.date, r.time, r.id))
    return tuple(records)


def _normalize_one(
    tx: TransactionIn, twin: TwinInput, account_ids: set[int]
) -> list[LedgerTx]:
    if tx.flow_hint is not None:
        return _build_records_for_flow(tx, tx.flow_hint, account_ids)

    if tx.status == TxStatus.CANCELED and tx.tx_type == TxType.CARD:
        return _build_cancel_pair(tx)

    if tx.exclude_tag == ExcludeTag.SELF_TRANSFER or (
        tx.counterparty_account_id is not None and tx.counterparty_account_id in account_ids
    ):
        return _build_records_for_flow(tx, Flow.TRANSFER_INTERNAL, account_ids)

    matched_fixed = _match_fixed_expense(tx, twin)
    if matched_fixed is not None:
        if matched_fixed.expense_type == FixedExpenseType.CARD_BILL:
            return _build_records_for_flow(tx, Flow.CARD_BILL, account_ids)
        return _build_records_for_flow(tx, Flow.FIXED, account_ids)

    if tx.merchant_name_raw is not None and CARD_BILL_MERCHANT_KEYWORD in tx.merchant_name_raw:
        return _build_records_for_flow(tx, Flow.CARD_BILL, account_ids)

    if tx.tx_type == TxType.DEPOSIT:
        account = _account_by_id(twin, tx.account_id)
        if account is not None and account.is_income:
            return _build_records_for_flow(tx, Flow.INCOME, account_ids)
        return _build_records_for_flow(tx, Flow.REFUND, account_ids)

    return _build_records_for_flow(tx, Flow.SPEND, account_ids)


def _account_by_id(twin: TwinInput, account_id: int | None):
    if account_id is None:
        return None
    for account in twin.accounts:
        if account.id == account_id:
            return account
    return None


def _signed_amount(flow: Flow, amount: int) -> int:
    if flow in (Flow.INCOME, Flow.REFUND):
        return amount
    # SPEND / FIXED / CARD_BILL / TRANSFER_INTERNAL 은 전부 차감(-)이다. 내
    # 계좌로 들어오는 TRANSFER_INTERNAL 상대편 레코드는 이 함수를 거치지
    # 않고 `_build_records_for_flow` 에서 별도로 부호를 뒤집는다.
    return -amount


def _envelope_and_confidence(
    flow: Flow, subcategory_id: int | None, confirm_status: ConfirmStatus
) -> tuple[int | None, float]:
    if flow not in _ENVELOPE_BEARING_FLOWS:
        return None, 1.0
    if subcategory_id is None:
        return OTHER_ENVELOPE_ID, 0.3
    return envelope_of(subcategory_id), _CONFIRM_STATUS_CONFIDENCE[confirm_status]


def _card_tx_account_id(tx: TransactionIn) -> int | None:
    # SPEC 5.2 신규 규칙: "카드(CARD) 거래는 account_id=None(계좌 잔액에
    # 영향 없음, 카드대금 출금 시 반영)". CARD 승인은 unbilled 만 올리고
    # 계좌 잔액은 나중 CARD_BILL(WITHDRAW) 이 깎을 때만 바뀐다.
    if tx.tx_type == TxType.CARD:
        return None
    return tx.account_id


def _build_records_for_flow(
    tx: TransactionIn, flow: Flow, account_ids: set[int]
) -> list[LedgerTx]:
    envelope_id, confidence = _envelope_and_confidence(flow, tx.subcategory_id, tx.confirm_status)
    signed_amount = _signed_amount(flow, tx.amount)

    main = LedgerTx(
        id=tx.id,
        date=tx.tx_date,
        time=tx.tx_time,
        account_id=_card_tx_account_id(tx),
        card_id=tx.card_id,
        signed_amount=signed_amount,
        flow=flow,
        envelope_id=envelope_id,
        subcategory_id=tx.subcategory_id,
        confidence=confidence,
        source=tx.source,
        merchant_name_raw=tx.merchant_name_raw,
        exclude_tag=tx.exclude_tag,
        confirm_status=tx.confirm_status,
        origin_tx_id=tx.id,
    )
    records = [main]

    if (
        flow == Flow.TRANSFER_INTERNAL
        and tx.counterparty_account_id is not None
        and tx.counterparty_account_id in account_ids
    ):
        # 결정론적 상대 계좌 레코드 id 규칙: origin_tx_id * 10 + 1. 원본
        # transactions[].id 가 int 인 한 절대 원본 id 와 겹치지 않는다.
        counterparty = LedgerTx(
            id=tx.id * 10 + 1,
            date=tx.tx_date,
            time=tx.tx_time,
            account_id=tx.counterparty_account_id,
            card_id=None,
            signed_amount=tx.amount,
            flow=Flow.TRANSFER_INTERNAL,
            envelope_id=None,
            subcategory_id=None,
            confidence=1.0,
            source=tx.source,
            merchant_name_raw=tx.merchant_name_raw,
            exclude_tag=tx.exclude_tag,
            confirm_status=tx.confirm_status,
            origin_tx_id=tx.id,
        )
        records.append(counterparty)

    return records


def _build_cancel_pair(tx: TransactionIn) -> list[LedgerTx]:
    # SPEC 5.2 규칙 1: 원 승인 SPEND(-) 와 같은 시각 REFUND(+) 두 건, 이력
    # 보존·순액 0. 둘 다 같은 봉투/confidence 를 써야 envelope_net_spend 가
    # 정확히 상쇄된다.
    envelope_id, confidence = _envelope_and_confidence(
        Flow.SPEND, tx.subcategory_id, tx.confirm_status
    )
    account_id = _card_tx_account_id(tx)

    spend = LedgerTx(
        id=tx.id,
        date=tx.tx_date,
        time=tx.tx_time,
        account_id=account_id,
        card_id=tx.card_id,
        signed_amount=-tx.amount,
        flow=Flow.SPEND,
        envelope_id=envelope_id,
        subcategory_id=tx.subcategory_id,
        confidence=confidence,
        source=tx.source,
        merchant_name_raw=tx.merchant_name_raw,
        exclude_tag=tx.exclude_tag,
        confirm_status=tx.confirm_status,
        origin_tx_id=tx.id,
    )
    refund = LedgerTx(
        id=-tx.id,
        date=tx.tx_date,
        time=tx.tx_time,
        account_id=account_id,
        card_id=tx.card_id,
        signed_amount=tx.amount,
        flow=Flow.REFUND,
        envelope_id=envelope_id,
        subcategory_id=tx.subcategory_id,
        confidence=confidence,
        source=tx.source,
        merchant_name_raw=tx.merchant_name_raw,
        exclude_tag=tx.exclude_tag,
        confirm_status=tx.confirm_status,
        origin_tx_id=tx.id,
    )
    return [spend, refund]


# ---------------------------------------------------------------------------
# 고정비/카드대금 매칭 (SPEC 5.2 규칙 3)
# ---------------------------------------------------------------------------


def _match_fixed_expense(tx: TransactionIn, twin: TwinInput) -> FixedExpenseIn | None:
    for fx in twin.fixed_expenses:
        if not fx.active:
            continue
        account_matches = (
            fx.withdrawal_account_id is not None
            and tx.account_id == fx.withdrawal_account_id
        )
        card_matches = fx.card_id is not None and tx.card_id == fx.card_id
        if not (account_matches or card_matches):
            continue
        if not _amount_within_tolerance(tx.amount, fx.amount):
            continue
        if not _payment_day_within_tolerance(tx.tx_date, fx.payment_day):
            continue
        return fx
    return None


def _amount_within_tolerance(amount: int, fixed_amount: int) -> bool:
    if fixed_amount == 0:
        return amount == 0
    return abs(amount - fixed_amount) <= fixed_amount * FIXED_AMOUNT_TOLERANCE_PCT


def _clamped_month_date(year: int, month: int, day: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def _payment_day_within_tolerance(tx_date: date, payment_day: int) -> bool:
    candidates: list[date] = []
    for delta in (-1, 0, 1):
        month = tx_date.month + delta
        year = tx_date.year
        if month == 0:
            month, year = 12, year - 1
        elif month == 13:
            month, year = 1, year + 1
        candidates.append(_clamped_month_date(year, month, payment_day))
    diff = min(abs((tx_date - candidate).days) for candidate in candidates)
    return diff <= FIXED_PAYMENT_DAY_TOLERANCE_DAYS


# ---------------------------------------------------------------------------
# 봉투 순지출 (SPEC 5.2 "원장 규칙 NFR-BGT-01")
# ---------------------------------------------------------------------------


def envelope_net_spend(
    ledger: tuple[LedgerTx, ...], start: date, end: date
) -> dict[int, int]:
    """봉투별 순지출 = |Σ(SPEND + REFUND(봉투 있는 것))|, [start, end] 양끝 포함.

    `exclude_tag ∈ {EMERGENCY, CARRYOVER}` 는 제외한다. DUTCH 입금(REFUND)은
    제외 대상이 아니므로 그대로 합산돼 순지출을 줄인다(SPEC 5.2). 취소 거래는
    SPEND(-amount)+REFUND(+amount) 가 같은 봉투로 상쇄돼 0이 된다.
    """

    totals: dict[int, int] = {}
    for record in ledger:
        if record.envelope_id is None:
            continue
        if record.flow not in (Flow.SPEND, Flow.REFUND):
            continue
        if record.exclude_tag in _ENVELOPE_EXCLUDED_TAGS:
            continue
        if not (start <= record.date <= end):
            continue
        totals[record.envelope_id] = totals.get(record.envelope_id, 0) + record.signed_amount

    return {envelope_id: abs(total) for envelope_id, total in totals.items()}


# ---------------------------------------------------------------------------
# 계좌 잔액 역산/전진 계산 (SPEC 5.3 "잔액")
# ---------------------------------------------------------------------------


def account_balance_at(
    twin: TwinInput, ledger: tuple[LedgerTx, ...], account_id: int, as_of: date
) -> int:
    """`as_of` 시점의 계좌 잔액. 홀드아웃 평가(as_of < twin.as_of)의 핵심.

    `opening_balance` 가 있으면 전진 계산: `opening + Σ(as_of 이하 원장)`.
    없으면 as_of(twin.as_of) 잔액에서 역산: `balance - Σ(as_of 초과, twin.as_of
    이하 원장)`.
    """

    account = None
    for candidate in twin.accounts:
        if candidate.id == account_id:
            account = candidate
            break
    if account is None:
        raise FdtError(
            code="E-INPUT-REF",
            message=f"account_balance_at: account {account_id} 없음",
            details={"account_id": account_id},
        )

    if account.opening_balance is not None:
        total = sum(
            record.signed_amount
            for record in ledger
            if record.account_id == account_id and record.date <= as_of
        )
        return account.opening_balance + total

    total = sum(
        record.signed_amount
        for record in ledger
        if record.account_id == account_id and as_of < record.date <= twin.as_of
    )
    return account.balance - total


# ---------------------------------------------------------------------------
# 대사 (SPEC 3.3 계좌 대사)
# ---------------------------------------------------------------------------


def reconcile(
    twin: TwinInput, ledger: tuple[LedgerTx, ...], *, strict: bool = False
) -> list[FdtWarning]:
    """계좌별 `opening_balance + Σ원장(≤ twin.as_of) == balance` 검사.

    `opening_balance` 가 없는 계좌는 대사 대상이 아니다(건너뛴다). 불일치가
    있으면 `strict=False` 일 때 `W-RECON` 경고(계좌 id·기대값·실제값·차액
    포함)를 모아 반환하고, `strict=True` 면 첫 불일치에서 바로
    `FdtError(E-RECON)` 을 던진다.
    """

    warnings: list[FdtWarning] = []
    for account in twin.accounts:
        if account.opening_balance is None:
            continue
        expected = account.opening_balance + sum(
            record.signed_amount
            for record in ledger
            if record.account_id == account.id and record.date <= twin.as_of
        )
        actual = account.balance
        diff = actual - expected
        if diff == 0:
            continue
        details = {
            "account_id": account.id,
            "expected": expected,
            "actual": actual,
            "diff": diff,
        }
        if strict:
            raise FdtError(code=E_RECON, details=details)
        warnings.append(FdtWarning(code=W_RECON, details=details))

    return warnings


# ---------------------------------------------------------------------------
# 이력 길이 / 미래 거래 수 (SPEC 3.3 W-INPUT-SHORT_HISTORY, W-INPUT-FUTURE_TX)
# ---------------------------------------------------------------------------


def history_days(ledger: tuple[LedgerTx, ...]) -> int:
    """원장이 덮는 일수(최초~최후 거래일, 양끝 포함). 원장이 비면 0."""

    if not ledger:
        return 0
    dates = [record.date for record in ledger]
    return (max(dates) - min(dates)).days + 1


def future_tx_count(twin: TwinInput) -> int:
    """`as_of` 이후 날짜의 거래 수 (엔진이 W-INPUT-FUTURE_TX 를 낼 때 쓴다)."""

    return sum(1 for tx in twin.transactions if tx.tx_date > twin.as_of)
