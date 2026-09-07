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
    (2) 내 계좌가 상대편인 거래(구조 변환, N7)는 그 계좌에 + 레코드를 하나
        더 만든다. 이 레코드의 id 는 `원본id * 10 + 1` 이다(결정론적 규칙,
        원본 id 와 절대 겹치지 않도록 자릿수를 늘린다).
    두 경우 모두 `origin_tx_id` 는 항상 원본 `transactions[].id` 를 가리킨다.

    `counterparty_account_id` (S22 준비, W3 State 의 반복 자기이체 탐지가
    사용할 필드): 원 레코드에서는 거래 상대 계좌(`transactions[].
    counterparty_account_id` 를 그대로 물려받음), 구조 변환으로 생긴 상대
    레코드에서는 원 레코드의 계좌(`transactions[].account_id`)를 가리킨다.
    상대 계좌가 없거나(일반 SPEND 등) 카드 거래라 `account_id` 가 `None` 인
    경우는 `None` 이다.
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
    counterparty_account_id: int | None


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
    4. `tx_type == DEPOSIT` -> `exclude_tag == DUTCH` 면 계좌와 무관하게
       REFUND(봉투 +). 아니면 `is_income` 계좌면 INCOME, 아니면 REFUND.
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
    """거래 한 건 -> 레코드 목록 (SPEC 5.2, N7 반영: 구조 변환과 흐름 라벨 분리).

    두 단계로 나눈다.

    1. 흐름 라벨(`flow`) 결정: `flow_hint` 가 있으면 그것을 그대로 쓰고,
       없으면 `_classify_flow` 의 판정 순서 2~5 를 따른다(규칙 1의 취소
       판정은 라벨이 아니라 구조 변환이라 여기 포함하지 않는다).
    2. 구조 변환: `status == CANCELED and tx_type == CARD` 인 거래는
       `flow_hint` 유무와 무관하게 항상 SPEND(-)/REFUND(+) 두 건으로
       나뉜다(1 단계에서 정한 라벨은 그 두 건에 그대로 적용된다 - 기본값은
       SPEND/REFUND). 그 외 거래는 `_build_records_for_flow` 가 만들며,
       `counterparty_account_id` 가 내 계좌면(구조 조건) `flow_hint` 유무와
       무관하게 상대 계좌 레코드가 항상 추가된다.
    """

    if tx.status == TxStatus.CANCELED and tx.tx_type == TxType.CARD:
        return _build_cancel_pair(tx, tx.flow_hint)

    flow = tx.flow_hint if tx.flow_hint is not None else _classify_flow(tx, twin, account_ids)
    return _build_records_for_flow(tx, flow, account_ids)


def _classify_flow(tx: TransactionIn, twin: TwinInput, account_ids: set[int]) -> Flow:
    """`flow_hint` 가 없을 때의 흐름 판정 순서 2~5 (SPEC 5.2).

    규칙 1(취소 CARD 거래 분할)은 구조 변환이라 `_normalize_one` 에서 별도로
    처리하고 여기서는 다루지 않는다.
    """

    if tx.exclude_tag == ExcludeTag.SELF_TRANSFER or (
        tx.counterparty_account_id is not None and tx.counterparty_account_id in account_ids
    ):
        return Flow.TRANSFER_INTERNAL

    matched_fixed = _match_fixed_expense(tx, twin)
    if matched_fixed is not None:
        if matched_fixed.expense_type == FixedExpenseType.CARD_BILL:
            return Flow.CARD_BILL
        return Flow.FIXED

    if tx.merchant_name_raw is not None and CARD_BILL_MERCHANT_KEYWORD in tx.merchant_name_raw:
        return Flow.CARD_BILL

    if tx.tx_type == TxType.DEPOSIT:
        if tx.exclude_tag == ExcludeTag.DUTCH:
            # SPEC 5.2 규칙 4: "그 외 DEPOSIT 은 REFUND(더치페이 입금 포함,
            # exclude_tag == DUTCH 면 해당 봉투에 +)". DUTCH 는 입금 계좌의
            # is_income 과 무관하게 항상 REFUND(봉투 +) 다(B2).
            return Flow.REFUND
        account = _account_by_id(twin, tx.account_id)
        if account is not None and account.is_income:
            return Flow.INCOME
        return Flow.REFUND

    return Flow.SPEND


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
    # SPEC 5.2 `LedgerTx` 정의 (S25 제안 반영 예정): "tx_type == CARD 인
    # 거래의 LedgerTx.account_id 는 None 이다. 카드 승인은 계좌 잔액에 영향이
    # 없고 CARD_BILL 출금에서만 반영된다(§3.3 계좌 대사의 전제)". CARD 승인은
    # unbilled 만 올리고 계좌 잔액은 나중 CARD_BILL(WITHDRAW) 이 깎을 때만
    # 바뀐다.
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
        counterparty_account_id=tx.counterparty_account_id,
    )
    records = [main]

    if tx.counterparty_account_id is not None and tx.counterparty_account_id in account_ids:
        # 구조 변환(N7): 내 계좌가 상대편인 거래는 상대 계좌 레코드가 항상
        # 추가된다 - `flow_hint` 유무·값과 무관하다. `flow` 라벨은 그대로
        # 물려받되(라벨만 덮어쓰는 규칙), signed_amount 는 이중 기록을 위해
        # 항상 main 의 반대 부호(+tx.amount)로 고정한다. 결정론적 상대 계좌
        # 레코드 id 규칙: origin_tx_id * 10 + 1. 원본 transactions[].id 가
        # int 인 한 절대 원본 id 와 겹치지 않는다.
        counterparty = LedgerTx(
            id=tx.id * 10 + 1,
            date=tx.tx_date,
            time=tx.tx_time,
            account_id=tx.counterparty_account_id,
            card_id=None,
            signed_amount=tx.amount,
            flow=flow,
            envelope_id=None,
            subcategory_id=None,
            confidence=1.0,
            source=tx.source,
            merchant_name_raw=tx.merchant_name_raw,
            exclude_tag=tx.exclude_tag,
            confirm_status=tx.confirm_status,
            origin_tx_id=tx.id,
            # 상대 레코드에서는 "상대"가 원 레코드의 계좌다.
            counterparty_account_id=tx.account_id,
        )
        records.append(counterparty)

    return records


def _build_cancel_pair(tx: TransactionIn, flow_hint: Flow | None) -> list[LedgerTx]:
    # SPEC 5.2 규칙 1: 원 승인 SPEND(-) 와 같은 시각 REFUND(+) 두 건, 이력
    # 보존·순액 0. 이 구조 변환은 `flow_hint` 유무와 무관하게 항상 실행된다
    # (N7). `flow_hint` 가 없으면 기본 라벨 SPEND/REFUND 를 쓰고, 있으면 두
    # 레코드의 라벨을 그 값으로 덮어쓴다(구조 - 부호 -tx.amount/+tx.amount -
    # 는 라벨과 무관하게 고정).
    spend_flow = flow_hint if flow_hint is not None else Flow.SPEND
    refund_flow = flow_hint if flow_hint is not None else Flow.REFUND
    account_id = _card_tx_account_id(tx)

    spend_envelope_id, spend_confidence = _envelope_and_confidence(
        spend_flow, tx.subcategory_id, tx.confirm_status
    )
    refund_envelope_id, refund_confidence = _envelope_and_confidence(
        refund_flow, tx.subcategory_id, tx.confirm_status
    )

    spend = LedgerTx(
        id=tx.id,
        date=tx.tx_date,
        time=tx.tx_time,
        account_id=account_id,
        card_id=tx.card_id,
        signed_amount=-tx.amount,
        flow=spend_flow,
        envelope_id=spend_envelope_id,
        subcategory_id=tx.subcategory_id,
        confidence=spend_confidence,
        source=tx.source,
        merchant_name_raw=tx.merchant_name_raw,
        exclude_tag=tx.exclude_tag,
        confirm_status=tx.confirm_status,
        origin_tx_id=tx.id,
        counterparty_account_id=tx.counterparty_account_id,
    )
    refund = LedgerTx(
        id=-tx.id,
        date=tx.tx_date,
        time=tx.tx_time,
        account_id=account_id,
        card_id=tx.card_id,
        signed_amount=tx.amount,
        flow=refund_flow,
        envelope_id=refund_envelope_id,
        subcategory_id=tx.subcategory_id,
        confidence=refund_confidence,
        source=tx.source,
        merchant_name_raw=tx.merchant_name_raw,
        exclude_tag=tx.exclude_tag,
        confirm_status=tx.confirm_status,
        origin_tx_id=tx.id,
        counterparty_account_id=tx.counterparty_account_id,
    )
    return [spend, refund]


# ---------------------------------------------------------------------------
# 고정비/카드대금 매칭 (SPEC 5.2 규칙 3)
# ---------------------------------------------------------------------------


def _match_fixed_expense(tx: TransactionIn, twin: TwinInput) -> FixedExpenseIn | None:
    """고정비 후보 매칭 (SPEC 5.2 규칙 3, S17 반영).

    `subcategory_id` 가 있는 거래는 소비로 보고 고정비 후보에서 제외한다
    (세분류가 붙었다는 것은 사람이 분류한 소비라는 뜻). 단
    `fixed_expenses.name == merchant_name_raw` 로 정확히 같으면 이 가드를
    우회해 예외적으로 매칭한다(LIVE 데이터에서 세분류가 붙은 고정비가 들어올
    수 있다). 계좌 매칭(`withdrawal_account_id`)은 `tx_type ∈ {WITHDRAW,
    TRANSFER}` 에만 적용한다 - CARD 거래는 카드 승인이라 계좌형 고정비와
    같은 계좌를 공유할 뿐 별개의 소비이기 쉽다. `tx_type == CARD` 는
    `fixed_expenses.card_id` 와만 매칭한다(B3).
    """

    for fx in twin.fixed_expenses:
        if not fx.active:
            continue

        name_matches = tx.merchant_name_raw is not None and tx.merchant_name_raw == fx.name
        if tx.subcategory_id is not None and not name_matches:
            continue

        account_matches = (
            fx.withdrawal_account_id is not None
            and tx.tx_type in (TxType.WITHDRAW, TxType.TRANSFER)
            and tx.account_id == fx.withdrawal_account_id
        )
        card_matches = (
            fx.card_id is not None
            and tx.tx_type == TxType.CARD
            and tx.card_id == fx.card_id
        )
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
    """봉투별 순지출 = -(Σ(SPEND + REFUND(봉투 있는 것))), [start, end] 양끝 포함.

    SPEND 는 `signed_amount` 가 음수이므로 부호를 반전해 "지출은 양수" 로
    맞춘다. `exclude_tag ∈ {EMERGENCY, CARRYOVER}` 는 제외한다. DUTCH
    입금(REFUND)은 제외 대상이 아니므로 그대로 합산돼 순지출을 줄인다(SPEC
    5.2). 취소 거래는 SPEND(-amount)+REFUND(+amount) 가 같은 봉투로 상쇄돼
    0이 된다.

    한 달의 DUTCH REFUND 합이 SPEND 합을 넘으면(더치 정산 수령이 실제 지출을
    초과) 결과는 **음수**일 수 있다(N9). `abs()` 로 부호를 삼키면 안 된다 -
    State 의 `remaining = budget - spent` 는 `spent` 가 음수여도 그대로
    성립한다(남은 예산이 더 커진다).
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

    return {envelope_id: -total for envelope_id, total in totals.items()}


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
