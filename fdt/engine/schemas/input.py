"""입력 계약 `TwinInput` (SPEC 3장).

KeyFin ERD 테이블을 그대로 JSON 배열로 옮긴 형태를 1급 입력으로 삼는다. 이
모듈은 `fdt.engine.taxonomy` 의 공개 상수/열거형만 신뢰하고 그 값을 다시
정의하지 않는다 (SPEC 4.2 불변 원칙, PLAN Phase 0 병렬 규칙).

검증 오류는 전부 `FdtError(code=..., details=...)` 로 낸다(N1·S39: 예전에는
`ValueError(f"<코드>: 상세")` 로 코드를 메시지 문자열에 태웠으나, `FdtError`
가 `ValueError` 의 서브클래스라 pydantic 은 여전히 이를 잡아
`ValidationError` 로 감싼다 - 다만 이제는 `ValidationError.errors(
include_context=True)[i]["ctx"]["error"]` 로 원 `FdtError` 를 그대로 꺼낼 수
있어, `fdt.engine.errors.extract_errors()` 가 메시지 정규식 파싱 없이 코드를
복원한다). 코드 문자열 자체는 `fdt.engine.errors` 의 상수를 그대로 쓴다.
"""

from __future__ import annotations

from datetime import date, time
from typing import Any, Literal, NoReturn, TypeVar

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, model_validator

from fdt.engine.errors import E_INPUT_DUP, E_INPUT_EMPTY, E_INPUT_REF, E_INPUT_TAXONOMY, FdtError
from fdt.engine.taxonomy import (
    ENVELOPE_IDS,
    ENVELOPES,
    SUBCATEGORIES,
    CardKind,
    ConfirmStatus,
    ExcludeTag,
    FixedExpenseType,
    Flow,
    RepaymentType,
    TxStatus,
    TxType,
)

_ENVELOPE_NAME_SET: frozenset[str] = frozenset(ENVELOPES)
_ENVELOPE_ID_TO_NAME: dict[int, str] = {v: k for k, v in ENVELOPE_IDS.items()}
_SUBCATEGORY_SET: frozenset[tuple[int, int, str]] = frozenset(SUBCATEGORIES)

_HasId = TypeVar("_HasId", bound=BaseModel)


def _fail(code: str, message: str, details: dict[str, Any] | None = None) -> NoReturn:
    raise FdtError(code=code, message=message, details=details)


def _dedup_by_id(items: list[_HasId], label: str) -> list[_HasId]:
    """SPEC 3.1 "모든 배열은 id 유일" 을 배열 종류에 상관없이 강제한다.

    같은 id·같은 내용의 항목은 처음 것만 남기고, 같은 id·다른 내용이면
    `E-INPUT-DUP` 를 던진다. `items` 의 원소는 `id: int` 필드를 가진 pydantic
    모델이어야 한다.
    """

    by_id: dict[Any, _HasId] = {}
    deduped: list[_HasId] = []
    for item in items:
        item_id = item.id  # type: ignore[attr-defined]
        existing = by_id.get(item_id)
        if existing is None:
            by_id[item_id] = item
            deduped.append(item)
            continue
        if existing == item:
            continue
        _fail(
            E_INPUT_DUP,
            f"{label} {item_id} 가 서로 다른 내용으로 중복됨",
            details={"label": label, "id": item_id},
        )
    return deduped


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


# ---------------------------------------------------------------------------
# 사용자 (SPEC 3.2 user / user_profiles)
# ---------------------------------------------------------------------------


class UserInfo(_Base):
    id: int
    # SPEC 예시는 값이 채워져 있지만, employment_status/income_band 를 엔진의
    # 어떤 계산도 참조하지 않는다(§5~§8 어디에도 등장하지 않음). 어댑터가
    # 데이터를 못 채우는 경우를 위해 선택 필드로 완화한다.
    employment_status: str | None = None
    income_band: str | None = None
    birth_date: date | None = None


# ---------------------------------------------------------------------------
# 봉투 / 세분류 (taxonomy 와 이름 집합·매핑이 일치해야 함, TwinInput 검증에서 확인)
# ---------------------------------------------------------------------------


class EnvelopeDef(_Base):
    id: int
    name: str


class SubcategoryDef(_Base):
    id: int
    envelope_id: int
    name: str


# ---------------------------------------------------------------------------
# 계좌 / 카드 / 카드 청구
# ---------------------------------------------------------------------------


class AccountIn(_Base):
    id: int
    fin_account_no: str
    bank_code: str
    alias: str
    is_managed: bool
    is_income: bool
    balance: int
    opening_balance: int | None = None


class CardIn(_Base):
    id: int
    issuer_code: str
    card_name: str
    kind: CardKind
    withdrawal_account_id: int
    withdrawal_weekday: int = Field(ge=0, le=6)
    is_managed: bool


class CardBillingIn(_Base):
    id: int
    card_id: int
    billing_date: date
    total_amount: NonNegativeInt
    status: Literal["UNPAID", "PAID"]
    paid_at: date | None = None


# ---------------------------------------------------------------------------
# 고정비 / 대출
# ---------------------------------------------------------------------------


class FixedExpenseIn(_Base):
    id: int
    name: str
    expense_type: FixedExpenseType
    amount: NonNegativeInt
    is_variable: bool
    payment_day: int = Field(ge=1, le=31)
    withdrawal_account_id: int | None = None
    card_id: int | None = None
    active: bool


class LoanIn(_Base):
    id: int
    balance: NonNegativeInt
    annual_rate_pct: float = Field(ge=0)
    interest_day: int = Field(ge=1, le=31)
    withdrawal_account_id: int
    repayment: RepaymentType


# ---------------------------------------------------------------------------
# 예산
# ---------------------------------------------------------------------------


class BudgetEnvelopeIn(_Base):
    envelope_id: int
    proposed_amount: NonNegativeInt | None = None
    confirmed_amount: NonNegativeInt | None = None


class BudgetIn(_Base):
    budget_month: str = Field(pattern=r"^\d{6}$")
    status: Literal["CONFIRMED", "PROPOSED"]
    envelopes: list[BudgetEnvelopeIn] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 거래
# ---------------------------------------------------------------------------


class TransactionIn(_Base):
    id: int
    source: Literal["SEED", "LIVE"]
    tx_type: TxType
    account_id: int | None = None
    card_id: int | None = None
    merchant_id: int | None = None
    merchant_name_raw: str | None = None
    amount: int = Field(gt=0)
    tx_date: date
    tx_time: time
    subcategory_id: int | None = None
    confirm_status: ConfirmStatus
    exclude_tag: ExcludeTag = ExcludeTag.NONE
    status: TxStatus = TxStatus.NORMAL
    flow_hint: Flow | None = None
    counterparty_account_id: int | None = None


# ---------------------------------------------------------------------------
# 외부 변수
# ---------------------------------------------------------------------------


class Externals(_Base):
    price_index_mult: float = Field(default=1.0, gt=0)
    loan_rate_delta_bp: int = 0
    income_growth_pct: float = 0.0


# ---------------------------------------------------------------------------
# 최상위 입력
# ---------------------------------------------------------------------------


class TwinInput(_Base):
    schema_version: Literal["twin-input/1"]
    as_of: date
    user: UserInfo
    envelopes: list[EnvelopeDef]
    subcategories: list[SubcategoryDef]
    accounts: list[AccountIn]
    cards: list[CardIn] = Field(default_factory=list)
    card_billings: list[CardBillingIn] = Field(default_factory=list)
    fixed_expenses: list[FixedExpenseIn] = Field(default_factory=list)
    loans: list[LoanIn] = Field(default_factory=list)
    budgets: list[BudgetIn] = Field(default_factory=list)
    transactions: list[TransactionIn] = Field(default_factory=list)
    externals: Externals = Field(default_factory=Externals)

    # -- 검증 (SPEC 3.3) ----------------------------------------------------
    # 순서 중요: dedup 을 가장 먼저 실행해 완전 동일한 중복 항목을 1건으로
    # 정리한 뒤에 taxonomy/참조/empty 검사를 한다. 그렇지 않으면 "같은 id·
    # 같은 내용" 중복(정상적으로 1건으로 접혀야 함)이 taxonomy 의 개수/집합
    # 비교에서 원본 배열 길이 때문에 그릇된 오류로 잡힌다.

    @model_validator(mode="after")
    def _dedup_all_arrays(self) -> TwinInput:
        # SPEC 3.1 "모든 배열은 id 유일": 같은 id·같은 내용은 1건으로 정리,
        # 같은 id·다른 내용은 E-INPUT-DUP (리뷰 N2, transactions 전용이던
        # 검사를 모든 id 배열 공통 헬퍼로 확장한다).
        self.accounts = _dedup_by_id(self.accounts, "account")
        self.cards = _dedup_by_id(self.cards, "card")
        self.card_billings = _dedup_by_id(self.card_billings, "card_billing")
        self.fixed_expenses = _dedup_by_id(self.fixed_expenses, "fixed_expense")
        self.loans = _dedup_by_id(self.loans, "loan")
        self.envelopes = _dedup_by_id(self.envelopes, "envelope")
        self.subcategories = _dedup_by_id(self.subcategories, "subcategory")
        self.transactions = _dedup_by_id(self.transactions, "transaction")
        return self

    @model_validator(mode="after")
    def _validate_taxonomy(self) -> TwinInput:
        # (1) 봉투 id<->이름이 taxonomy.ENVELOPE_IDS 를 뒤집은 것과 완전히
        # 같아야 한다. 이름 집합만 맞고 id 가 뒤바뀌면(예: 역순) 겉보기엔
        # 통과하지만 engine/ledger.py 의 taxonomy.envelope_of() 조회가 조용히
        # 틀린 봉투를 가리키게 된다 (SPEC 3.3, 리뷰 B1).
        got_envelopes = {e.id: e.name for e in self.envelopes}
        if got_envelopes != _ENVELOPE_ID_TO_NAME:
            mismatched = sorted(
                eid
                for eid in set(got_envelopes) | set(_ENVELOPE_ID_TO_NAME)
                if got_envelopes.get(eid) != _ENVELOPE_ID_TO_NAME.get(eid)
            )
            _fail(
                E_INPUT_TAXONOMY,
                f"envelopes 의 id<->이름이 taxonomy.ENVELOPE_IDS 와 "
                f"일치하지 않는다 (불일치 id: {mismatched}, "
                f"받은 값: {sorted(got_envelopes.items())})",
                details={"mismatched_ids": mismatched},
            )

        # (2) 세분류는 22종이어야 하고 (id, envelope_id, name) 집합이
        # taxonomy.SUBCATEGORIES 와 완전히 같아야 한다.
        got_subs = {(s.id, s.envelope_id, s.name) for s in self.subcategories}
        if len(self.subcategories) != len(SUBCATEGORIES) or got_subs != _SUBCATEGORY_SET:
            missing = sorted(_SUBCATEGORY_SET - got_subs)
            extra = sorted(got_subs - _SUBCATEGORY_SET)
            _fail(
                E_INPUT_TAXONOMY,
                f"subcategories 가 taxonomy.SUBCATEGORIES(22종) 와 "
                f"일치하지 않는다 (누락: {missing}, 불일치/초과: {extra})",
                details={"missing": missing, "extra": extra},
            )
        return self

    @model_validator(mode="after")
    def _validate_references(self) -> TwinInput:
        account_ids = {a.id for a in self.accounts}
        card_ids = {c.id for c in self.cards}

        for card in self.cards:
            if card.withdrawal_account_id not in account_ids:
                _fail(
                    E_INPUT_REF,
                    f"card {card.id} -> account {card.withdrawal_account_id} 없음",
                    details={
                        "ref_from": "card",
                        "ref_from_id": card.id,
                        "ref_to": "account",
                        "ref_to_id": card.withdrawal_account_id,
                    },
                )

        for fx in self.fixed_expenses:
            if fx.withdrawal_account_id is not None and fx.withdrawal_account_id not in account_ids:
                _fail(
                    E_INPUT_REF,
                    f"fixed_expense {fx.id} -> account {fx.withdrawal_account_id} 없음",
                    details={
                        "ref_from": "fixed_expense",
                        "ref_from_id": fx.id,
                        "ref_to": "account",
                        "ref_to_id": fx.withdrawal_account_id,
                    },
                )
            if fx.card_id is not None and fx.card_id not in card_ids:
                _fail(
                    E_INPUT_REF,
                    f"fixed_expense {fx.id} -> card {fx.card_id} 없음",
                    details={
                        "ref_from": "fixed_expense",
                        "ref_from_id": fx.id,
                        "ref_to": "card",
                        "ref_to_id": fx.card_id,
                    },
                )

        for loan in self.loans:
            if loan.withdrawal_account_id not in account_ids:
                _fail(
                    E_INPUT_REF,
                    f"loan {loan.id} -> account {loan.withdrawal_account_id} 없음",
                    details={
                        "ref_from": "loan",
                        "ref_from_id": loan.id,
                        "ref_to": "account",
                        "ref_to_id": loan.withdrawal_account_id,
                    },
                )

        for billing in self.card_billings:
            if billing.card_id not in card_ids:
                _fail(
                    E_INPUT_REF,
                    f"card_billing {billing.id} -> card {billing.card_id} 없음",
                    details={
                        "ref_from": "card_billing",
                        "ref_from_id": billing.id,
                        "ref_to": "card",
                        "ref_to_id": billing.card_id,
                    },
                )

        for tx in self.transactions:
            if tx.account_id is not None and tx.account_id not in account_ids:
                _fail(
                    E_INPUT_REF,
                    f"transaction {tx.id} -> account {tx.account_id} 없음",
                    details={
                        "ref_from": "transaction",
                        "ref_from_id": tx.id,
                        "ref_to": "account",
                        "ref_to_id": tx.account_id,
                    },
                )
            if tx.card_id is not None and tx.card_id not in card_ids:
                _fail(
                    E_INPUT_REF,
                    f"transaction {tx.id} -> card {tx.card_id} 없음",
                    details={
                        "ref_from": "transaction",
                        "ref_from_id": tx.id,
                        "ref_to": "card",
                        "ref_to_id": tx.card_id,
                    },
                )
            if (
                tx.counterparty_account_id is not None
                and tx.counterparty_account_id not in account_ids
            ):
                _fail(
                    E_INPUT_REF,
                    f"transaction {tx.id} -> account(counterparty) "
                    f"{tx.counterparty_account_id} 없음",
                    details={
                        "ref_from": "transaction",
                        "ref_from_id": tx.id,
                        "ref_to": "account",
                        "ref_to_id": tx.counterparty_account_id,
                    },
                )

        return self

    @model_validator(mode="after")
    def _validate_not_empty(self) -> TwinInput:
        # 관리 대상 계좌 0개는 카드 수와 합산하지 않고 그 자체로 오류다
        # (SPEC 3.3, §5.3 PRIMARY 계좌 결정에 관리 계좌가 필요, 리뷰 N3).
        managed_accounts = sum(1 for a in self.accounts if a.is_managed)
        if managed_accounts == 0:
            _fail(E_INPUT_EMPTY, "is_managed 계좌가 하나도 없음")
        return self

    # -- 헬퍼 -----------------------------------------------------------

    def transactions_until(self, as_of: date) -> list[TransactionIn]:
        """as_of(포함) 이하 날짜의 거래만 반환한다 (SPEC 2장 as_of, 3.3).

        as_of 이후 거래는 입력 검증 대상이 아니다(§3.3 W-INPUT-FUTURE_TX 로
        경고만 내고 무시). State/Behavior 는 이 헬퍼로 걸러낸 목록만 써야
        한다.
        """

        return [tx for tx in self.transactions if tx.tx_date <= as_of]
