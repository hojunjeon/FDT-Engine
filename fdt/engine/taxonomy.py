"""봉투(envelope) 세분류(subcategory) 체계와 엔진 전역 상수.

SPEC.md 1장(범위), 2장(용어), 3.2(스키마), 5.2(흐름 판정), 7.2(하루 처리 순서)를
따른다. 이 모듈의 공개 이름은 다른 구현자가 그대로 import 하는 계약이다.
값이나 이름을 바꾸려면 SPEC 을 먼저 고친다.
"""

from __future__ import annotations

from enum import StrEnum

# ---------------------------------------------------------------------------
# 7대 소비 봉투 (SPEC 2장 "봉투", 요구사항명세 봉투/세분류 표)
# 순서 고정: id 는 아래 튜플의 인덱스+1 이다.
# ---------------------------------------------------------------------------

ENVELOPES: tuple[str, ...] = (
    "외식",
    "교통비",
    "의료·건강",
    "취미·여가",
    "쇼핑",
    "편의점·마트·잡화",
    "기타",
)

ENVELOPE_IDS: dict[str, int] = {name: idx + 1 for idx, name in enumerate(ENVELOPES)}

OTHER_ENVELOPE_ID: int = ENVELOPE_IDS["기타"]

# ---------------------------------------------------------------------------
# 22종 세분류. (subcategory_id, envelope_id, name)
# ---------------------------------------------------------------------------

SUBCATEGORIES: tuple[tuple[int, int, str], ...] = (
    (1, ENVELOPE_IDS["외식"], "음식점"),
    (2, ENVELOPE_IDS["외식"], "카페"),
    (3, ENVELOPE_IDS["외식"], "배달"),
    (4, ENVELOPE_IDS["외식"], "주점"),
    (5, ENVELOPE_IDS["교통비"], "대중교통"),
    (6, ENVELOPE_IDS["교통비"], "택시"),
    (7, ENVELOPE_IDS["교통비"], "주유"),
    (8, ENVELOPE_IDS["의료·건강"], "병원·약국"),
    (9, ENVELOPE_IDS["의료·건강"], "운동·헬스"),
    (10, ENVELOPE_IDS["취미·여가"], "영화·공연·전시"),
    (11, ENVELOPE_IDS["취미·여가"], "스포츠 관람"),
    (12, ENVELOPE_IDS["취미·여가"], "게임·콘텐츠"),
    (13, ENVELOPE_IDS["취미·여가"], "여행·숙박"),
    (14, ENVELOPE_IDS["쇼핑"], "패션·잡화"),
    (15, ENVELOPE_IDS["쇼핑"], "뷰티"),
    (16, ENVELOPE_IDS["쇼핑"], "온라인 쇼핑"),
    (17, ENVELOPE_IDS["편의점·마트·잡화"], "편의점"),
    (18, ENVELOPE_IDS["편의점·마트·잡화"], "마트"),
    (19, ENVELOPE_IDS["편의점·마트·잡화"], "생활용품"),
    (20, ENVELOPE_IDS["기타"], "교육"),
    (21, ENVELOPE_IDS["기타"], "해외 결제"),
    (22, ENVELOPE_IDS["기타"], "경조사·기타"),
)

_SUBCATEGORY_TO_ENVELOPE: dict[int, int] = {
    sub_id: envelope_id for sub_id, envelope_id, _name in SUBCATEGORIES
}

# ---------------------------------------------------------------------------
# 필수/유연 봉투 (SPEC 8.4 protect_essential, 8.6 유연 봉투 감액 후보)
# ---------------------------------------------------------------------------

ESSENTIAL_ENVELOPES: frozenset[str] = frozenset({"교통비", "의료·건강", "편의점·마트·잡화"})

FLEXIBLE_ENVELOPES: frozenset[str] = frozenset(set(ENVELOPES) - ESSENTIAL_ENVELOPES)


def envelope_of(subcategory_id: int | None) -> int:
    """세분류 id -> 봉투 id. 없거나 미등록이면 기타(OTHER_ENVELOPE_ID) 로 본다.

    SPEC 3.3 "봉투 7종·세분류->봉투 매핑 누락" 은 taxonomy 자체의 정합성
    검사이고, 이 함수는 개별 거래의 subcategory_id 가 null 이거나 알 수 없는
    값일 때의 처리(SPEC 5.2의 5번, "null 이면 기타")를 담당한다.
    """

    if subcategory_id is None:
        return OTHER_ENVELOPE_ID
    return _SUBCATEGORY_TO_ENVELOPE.get(subcategory_id, OTHER_ENVELOPE_ID)


# ---------------------------------------------------------------------------
# 거래 성격 / 유형 열거형 (SPEC 2장, 3.2, 5.2)
# ---------------------------------------------------------------------------


class Flow(StrEnum):
    """거래 성격 (SPEC 2장 "흐름")."""

    INCOME = "INCOME"
    FIXED = "FIXED"
    CARD_BILL = "CARD_BILL"
    TRANSFER_INTERNAL = "TRANSFER_INTERNAL"
    REFUND = "REFUND"
    SPEND = "SPEND"


class FixedExpenseType(StrEnum):
    """고정비 유형 (SPEC 3.2 fixed_expenses.expense_type)."""

    RENT = "RENT"
    SUBSCRIPTION = "SUBSCRIPTION"
    CARD_BILL = "CARD_BILL"
    LOAN = "LOAN"
    UTILITY = "UTILITY"
    INSURANCE = "INSURANCE"
    TELECOM = "TELECOM"


class TxType(StrEnum):
    """거래 유형 (SPEC 3.2 transactions.tx_type)."""

    CARD = "CARD"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    TRANSFER = "TRANSFER"


class ExcludeTag(StrEnum):
    """봉투 차감 제외 태그 (SPEC 3.2, 5.2)."""

    NONE = "NONE"
    DUTCH = "DUTCH"
    SELF_TRANSFER = "SELF_TRANSFER"
    EMERGENCY = "EMERGENCY"
    CARRYOVER = "CARRYOVER"


class ConfirmStatus(StrEnum):
    """거래 확정 상태 (SPEC 3.2 transactions.confirm_status)."""

    AUTO = "AUTO"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"


class TxStatus(StrEnum):
    """거래 상태 (SPEC 3.2 transactions.status)."""

    NORMAL = "NORMAL"
    CANCELED = "CANCELED"


class CardKind(StrEnum):
    """카드 종류 (SPEC 3.2 cards.kind)."""

    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class RepaymentType(StrEnum):
    """대출 상환 방식 (SPEC 3.2 loans.repayment)."""

    INTEREST_ONLY = "INTEREST_ONLY"
    AMORTIZING = "AMORTIZING"


class Mode(StrEnum):
    """엔진 실행 모드 5종 (SPEC 8장)."""

    FORECAST = "FORECAST"
    WHATIF = "WHATIF"
    GOAL = "GOAL"
    RISK = "RISK"
    OPTIMIZE = "OPTIMIZE"


# ---------------------------------------------------------------------------
# 카드 청구 상수 (SPEC 7.2 하루 처리 순서 3~4단계, 15.A 부록 예시)
# ---------------------------------------------------------------------------

# 청구서 발행 요일. 0=월요일(python date.weekday() 기준), 07:30 발행.
# 카드별 withdrawal_weekday 에 출금 16:00 시도, 미결제 청구서는 이후 매일
# 16:00 재시도(성공할 때까지, 재시도 횟수 제한 없음). SPEC 15.A 부록 참조.
BILLING_ISSUE_WEEKDAY: int = 0
