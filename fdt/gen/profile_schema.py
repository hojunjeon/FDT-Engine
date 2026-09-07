"""생성기 프로필 YAML 검증 (리뷰 N10).

`fdt/gen/profiles/*.yaml` 을 그대로 신뢰하지 않고 pydantic 모델로 검증한다.
필수 파라미터가 없으면 여기서 명확한 `ValueError` 로 죽어야 하고(PLAN §8
"필수 파라미터 누락을 기본값으로 대체하지 않음"), 있어도 되는 선택 필드의
기본값은 이 모듈에서만 정의한다(생성기 쪽 `.get(..., 기본값)` 산발 금지).

이 모듈은 `fdt/engine` 의 taxonomy 만 참조한다(다른 `fdt.engine.*` 는
import 하지 않는다 - SPEC 11장 / PLAN Phase 1 아키텍처 규칙과 동일).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from fdt.engine.taxonomy import ENVELOPES, CardKind, FixedExpenseType, RepaymentType

_ENVELOPE_NAME_SET: frozenset[str] = frozenset(ENVELOPES)


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AccountCfg(_Base):
    id: int
    alias: str
    is_income: bool
    opening_balance: int
    managed: bool = True


class CardCfg(_Base):
    id: int
    alias: str | None = None
    kind: CardKind
    withdrawal_weekday: int = Field(ge=0, le=6)
    withdrawal_account_id: int


class IncomeCfg(_Base):
    type: Literal["SALARY", "IRREGULAR"]
    amount: int = Field(gt=0)
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    jitter_sigma: float = Field(default=0.0, ge=0)
    median_gap_days: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _check_type_fields(self) -> IncomeCfg:
        if self.type == "SALARY" and self.day_of_month is None:
            raise ValueError("income.type == SALARY 는 day_of_month 가 필수다")
        if self.type == "IRREGULAR" and self.median_gap_days is None:
            raise ValueError("income.type == IRREGULAR 는 median_gap_days 가 필수다")
        return self


class FixedExpenseCfg(_Base):
    id: int
    name: str
    expense_type: FixedExpenseType
    amount: int = Field(ge=0)
    is_variable: bool = False
    payment_day: int = Field(ge=1, le=31)
    withdrawal_account_id: int | None = None
    card_id: int | None = None

    @model_validator(mode="after")
    def _check_target(self) -> FixedExpenseCfg:
        if self.withdrawal_account_id is None and self.card_id is None:
            raise ValueError(
                f"fixed_expense {self.id}: withdrawal_account_id 또는 card_id 중 하나는 필수"
            )
        return self


class LoanCfg(_Base):
    id: int
    balance: int = Field(ge=0)
    annual_rate_pct: float = Field(ge=0)
    interest_day: int = Field(ge=1, le=31)
    withdrawal_account_id: int
    repayment: RepaymentType


class BudgetsCfg(_Base):
    confirmed: bool = False
    envelopes: dict[str, int]

    @model_validator(mode="after")
    def _check_envelopes(self) -> BudgetsCfg:
        missing = _ENVELOPE_NAME_SET - set(self.envelopes)
        if missing:
            raise ValueError(f"budgets.envelopes 에 봉투 누락: {sorted(missing)}")
        return self


class SpendingCfg(_Base):
    daily_rate: float = Field(ge=0)
    amount_mu: float
    amount_sigma: float = Field(gt=0)
    card_share: float = Field(ge=0, le=1)
    weekday_mult: list[float] = Field(min_length=7, max_length=7)


class ShockCfg(_Base):
    daily_prob: float = Field(ge=0, le=1)
    mu: float
    sigma: float = Field(gt=0)


class HiddenCfg(_Base):
    payday_boost: float = Field(default=1.0, gt=0)
    pre_payday_damp: float = Field(default=1.0, gt=0)
    # 스칼라(전 봉투 공통) 또는 봉투별 dict (리뷰 N4). 생성기가
    # `_build_elasticity_table` 로 항상 봉투별 dict 로 확장한다.
    elasticity: float | dict[str, float] = 1.0
    shock: ShockCfg
    cancel_prob: float = Field(default=0.0, ge=0, le=1)
    dutch_pay_prob: float = Field(default=0.0, ge=0, le=1)
    emergency_transfer_monthly: int = Field(default=0, ge=0)
    # 소비 거래 confirm_status 의 PENDING 확률 (리뷰 N5, SPEC S20).
    pending_ratio: float = Field(default=0.1, ge=0, le=1)

    @model_validator(mode="after")
    def _check_elasticity_keys(self) -> HiddenCfg:
        if isinstance(self.elasticity, dict):
            unknown = set(self.elasticity) - _ENVELOPE_NAME_SET
            if unknown:
                raise ValueError(f"hidden.elasticity 에 알 수 없는 봉투: {sorted(unknown)}")
        return self


class Profile(_Base):
    """프로필 YAML 최상위 모델 (리뷰 N10).

    `load_profile` 이 `Profile.model_validate(raw)` 로 검증한 뒤
    `model_dump(mode="json")` 로 되돌린 dict 를 생성기에 넘긴다. 이 왕복으로
    누락 필드는 여기서 정의한 기본값으로, 잘못된 값은 `ValueError` 로 걸러진다.
    """

    name: str
    description: str = ""
    accounts: list[AccountCfg] = Field(min_length=1)
    cards: list[CardCfg] = Field(default_factory=list)
    income: IncomeCfg
    fixed_expenses: list[FixedExpenseCfg] = Field(default_factory=list)
    loans: list[LoanCfg] = Field(default_factory=list)
    budgets: BudgetsCfg
    spending: dict[str, SpendingCfg]
    hidden: HiddenCfg

    @model_validator(mode="after")
    def _check_spending_envelopes(self) -> Profile:
        missing = _ENVELOPE_NAME_SET - set(self.spending)
        if missing:
            raise ValueError(f"spending 에 봉투 누락: {sorted(missing)}")
        return self

    @model_validator(mode="after")
    def _check_refs(self) -> Profile:
        account_ids = {a.id for a in self.accounts}
        card_ids = {c.id for c in self.cards}
        for card in self.cards:
            if card.withdrawal_account_id not in account_ids:
                raise ValueError(
                    f"card {card.id}: withdrawal_account_id {card.withdrawal_account_id} "
                    "가 accounts 에 없음"
                )
        for fx in self.fixed_expenses:
            if fx.withdrawal_account_id is not None and fx.withdrawal_account_id not in account_ids:
                raise ValueError(
                    f"fixed_expense {fx.id}: withdrawal_account_id "
                    f"{fx.withdrawal_account_id} 가 accounts 에 없음"
                )
            if fx.card_id is not None and fx.card_id not in card_ids:
                raise ValueError(f"fixed_expense {fx.id}: card_id {fx.card_id} 가 cards 에 없음")
        for loan in self.loans:
            if loan.withdrawal_account_id not in account_ids:
                raise ValueError(
                    f"loan {loan.id}: withdrawal_account_id {loan.withdrawal_account_id} "
                    "가 accounts 에 없음"
                )
        return self


def validate_profile(raw: dict[str, Any]) -> dict[str, Any]:
    """프로필 raw dict -> 검증된 dict (JSON 라운드트립, 기본값 채움).

    실패하면 pydantic `ValidationError`(내용은 `ValueError` 메시지 목록)를
    그대로 전파한다. `load_profile` 이 이 함수를 거친다.
    """

    model = Profile.model_validate(raw)
    return model.model_dump(mode="json")
