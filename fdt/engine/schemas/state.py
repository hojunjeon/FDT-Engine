"""State(t) 스키마 (SPEC 5.1).

이 모듈은 State 의 형태만 정의한다. State 를 실제로 계산하는 로직(PRIMARY/
EMERGENCY 판정, 약정 큐, 예산 소스 우선순위, 지표 산출 등, SPEC 5.2~5.5)은
`engine/state.py`(다른 작업 ID 소유)가 담당한다.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


# ---------------------------------------------------------------------------
# 계좌 / 카드
# ---------------------------------------------------------------------------


class AccountState(_Base):
    id: int
    role: Literal["PRIMARY", "EMERGENCY", "OTHER"]
    balance: int


class IssuedBilling(_Base):
    billing_date: date
    amount: int


class CardState(_Base):
    id: int
    withdrawal_weekday: int = Field(ge=0, le=6)
    unbilled: int
    issued_unpaid: list[IssuedBilling] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 약정 큐 (SPEC 5.4)
# ---------------------------------------------------------------------------


class Committed(_Base):
    kind: Literal[
        "RENT",
        "SUBSCRIPTION",
        "CARD_BILL",
        "LOAN",
        "UTILITY",
        "INSURANCE",
        "TELECOM",
    ]
    name: str
    due: date
    amount: int
    certainty: float = Field(ge=0, le=1)
    account_id: int | None = None
    card_id: int | None = None


# ---------------------------------------------------------------------------
# 봉투 상태 (SPEC 5.1, 5.5 budget_source 우선순위)
# ---------------------------------------------------------------------------


class EnvelopeState(_Base):
    envelope_id: int
    name: str
    budget: int
    spent: int
    remaining: int
    budget_source: Literal["CONFIRMED", "PROPOSED", "ENGINE"]


# ---------------------------------------------------------------------------
# 수입 일정 (SPEC 5.3, 6장 표 마지막 행) - Behavior 도 재사용하므로 여기서
# 정의하고 behavior.py 가 import 한다.
# ---------------------------------------------------------------------------


class IncomeSchedule(_Base):
    next_date: date | None = None
    expected: int
    irregular: bool
    median_gap_days: int | None = None


# ---------------------------------------------------------------------------
# 지표 / 예산 주기
# ---------------------------------------------------------------------------


class Indicators(_Base):
    spend_7d_avg: float
    spend_90d_avg: float
    acceleration: float
    unconfirmed_count: int = Field(ge=0)


class Cycle(_Base):
    budget_cycle_start: date
    budget_cycle_end: date
    progress: float = Field(ge=0, le=1)


# ---------------------------------------------------------------------------
# 최상위 State
# ---------------------------------------------------------------------------


class State(_Base):
    as_of: date
    accounts: list[AccountState]
    liquidity: int
    emergency_fund: int
    cards: list[CardState] = Field(default_factory=list)
    committed: list[Committed] = Field(default_factory=list)
    envelopes: list[EnvelopeState]
    income: IncomeSchedule
    indicators: Indicators
    cycle: Cycle

    def envelope_by_id(self, envelope_id: int) -> EnvelopeState | None:
        for env in self.envelopes:
            if env.envelope_id == envelope_id:
                return env
        return None

    def committed_between(self, start: date, end: date) -> list[Committed]:
        return [c for c in self.committed if start <= c.due <= end]
