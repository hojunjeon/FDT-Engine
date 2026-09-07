"""시뮬레이션 결과의 JSON 친화적 조각 (SPEC 7.3).

`SimulationResult` 자신(`fdt/engine/simulate.py`)은 numpy ndarray 를 그대로
들고 있어 pydantic 모델로 두지 않는다(직렬화가 필요 없는 엔진 내부 계약).
여기에는 그 결과를 사람이 읽거나 JSON 으로 내보낼 때 쓰는 하위 조각만 둔다:
`stats()` 가 반환하는 `PathStats`, `payment_risks()` 가 반환하는
`PaymentRisk`, `event_log` 원소 `DayEvents`(그 안의 `Event`).

공개 이름(다른 작업 ID, 특히 W7 FORECAST/RISK 가 import 하는 계약):
`Event`, `DayEvents`, `PathStats`, `PaymentRisk`.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


class Event(_Base):
    """하루치 사건 한 건 (SPEC 7.2 8단계 "event_log[k] 에 (kind, amount,
    성공 경로 비율) 기록", SPEC 7.3 `DayEvents`).

    `kind` 은 `Committed.kind` 값 또는 `"INCOME"`/`"CARD_BILL"`/사용자 주입
    타입 문자열이다(자유 문자열로 둔다 - 주입 7종과 약정 8종을 하나의
    리터럴로 강제하면 W7/W8 이 새 kind 를 추가할 때마다 이 스키마를 고쳐야
    한다).
    """

    kind: str
    name: str
    amount: int
    success_ratio: float = Field(ge=0.0, le=1.0)
    source_fixed_expense_id: int | None = None
    source_loan_id: int | None = None
    source_card_id: int | None = None


class DayEvents(_Base):
    date: date
    events: list[Event] = Field(default_factory=list)


class PathStats(_Base):
    """`SimulationResult.stats()` (SPEC 7.3).

    `economic=False` 로 부르면 `median`/`p10`/`p90`/`mean`/`min_balance`/
    `end_balance_median` 은 실제 잔액(`balances`) 기준이고, `economic=True`
    면 경제 잔액(`economic`) 기준이다. `shortfall_prob`/`card_shortfall_prob`/
    `first_shortfall_date_median` 은 SPEC 7.2 8단계 정의상 항상 **실제
    잔액**(`liquidity < 0`) 기준이라 `economic` 플래그와 무관하게 같다.
    """

    dates: list[date]
    median: list[int]
    p10: list[int]
    p90: list[int]
    mean: list[float]
    min_balance: int
    min_balance_date: date
    end_balance_median: int
    shortfall_prob: float = Field(ge=0.0, le=1.0)
    card_shortfall_prob: float = Field(ge=0.0, le=1.0)
    first_shortfall_date_median: date | None = None
    envelope_spend_median: dict[int, int] = Field(default_factory=dict)
    # W6 구현 결정(보고 참조): "그 봉투가 어느 한 예산 주기에서라도 예산을
    # 넘긴 경로 비율"과 "그 넘긴 시점의 중앙값 날짜"로 정의한다(SPEC 7.3 은
    # 이름만 정의하고 정확한 통계 정의는 남겨 두었다). 근거: 시뮬레이터가
    # 유일하게 아는 것은 매달 리셋되는 누적 지출(`_month_spent`)이 예산을
    # 넘는 시점뿐이고, 이는 FORECAST 의 "이번 달 봉투 소진" 계산과도
    # 자연스럽게 맞물린다.
    envelope_overrun_prob: dict[int, float] = Field(default_factory=dict)
    envelope_exhaust_date_median: dict[int, date | None] = Field(default_factory=dict)


class PaymentRisk(_Base):
    """`SimulationResult.payment_risks()` 원소 (SPEC 7.3, 8.5)."""

    due: date
    kind: str
    name: str
    amount: int
    fail_prob: float = Field(ge=0.0, le=1.0)
    median_balance_before: int
    source_fixed_expense_id: int | None = None
    source_loan_id: int | None = None
    source_card_id: int | None = None
