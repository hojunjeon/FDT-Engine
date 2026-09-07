"""엔진 오류·경고 코드 (SPEC 3.3 입력 검증, 8.1 모드 요청 검증).

`fdt/engine/**` 는 이 모듈의 코드만으로 실패를 표현한다. 순수 파이썬 예외
메시지에 임의 문자열을 쓰지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class FdtError(Exception):
    """엔진 내부에서 발생하는 검증·계약 위반 오류.

    code 는 아래 상수 중 하나(또는 그 확장)여야 한다. message 가 비어 있으면
    MESSAGES 의 기본 한국어 메시지를 쓴다.
    """

    def __init__(self, code: str, message: str | None = None, details: dict[str, Any] | None = None):
        self.code = code
        self.details = details or {}
        self.message = message or MESSAGES.get(code, code)
        super().__init__(f"[{self.code}] {self.message}")


@dataclass
class FdtWarning:
    """엔진이 결과에 실어 보내는 경고 한 건 (Engine.meta.warnings, State 등)."""

    code: str
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.message:
            self.message = MESSAGES.get(self.code, self.code)


# ---------------------------------------------------------------------------
# 오류 코드 (MUST, SPEC 3.3 / 8.1)
# ---------------------------------------------------------------------------

E_INPUT_TAXONOMY = "E-INPUT-TAXONOMY"
E_INPUT_REF = "E-INPUT-REF"
E_INPUT_DUP = "E-INPUT-DUP"
E_INPUT_EMPTY = "E-INPUT-EMPTY"
E_RECON = "E-RECON"
E_REQ_MISSING = "E-REQ-MISSING"
E_REQ_RANGE = "E-REQ-RANGE"
E_ENGINE_ID_MISMATCH = "E-ENGINE-ID-MISMATCH"

# ---------------------------------------------------------------------------
# 경고 코드 (SPEC 3.3, 5.4, 6장)
# ---------------------------------------------------------------------------

W_INPUT_FUTURE_TX = "W-INPUT-FUTURE_TX"
W_RECON = "W-RECON"
W_INPUT_SHORT_HISTORY = "W-INPUT-SHORT_HISTORY"
W_FIXED_VARIABLE_UNKNOWN = "W-FIXED-VARIABLE-UNKNOWN"

MESSAGES: dict[str, str] = {
    E_INPUT_TAXONOMY: "봉투 7종 또는 세분류-봉투 매핑이 taxonomy 와 일치하지 않는다",
    E_INPUT_REF: "참조하는 id 가 입력 배열에 없다",
    E_INPUT_DUP: "같은 id 에 서로 다른 내용의 항목이 중복됐다",
    E_INPUT_EMPTY: "관리 대상(is_managed) 계좌 또는 카드가 하나도 없다",
    E_RECON: "계좌 대사 차액이 있다(strict 모드)",
    E_REQ_MISSING: "모드 요청에 필수 파라미터가 빠졌다",
    E_REQ_RANGE: "모드 요청 파라미터가 허용 범위를 벗어났다",
    E_ENGINE_ID_MISMATCH: "저장된 engine_id 와 로드 시점 재계산 결과가 다르다",
    W_INPUT_FUTURE_TX: "as_of 이후 날짜의 거래가 있어 무시했다",
    W_RECON: "계좌 대사 차액이 있다",
    W_INPUT_SHORT_HISTORY: "거래 이력이 28일 미만이라 Behavior 기본값 비중을 높였다",
    W_FIXED_VARIABLE_UNKNOWN: "변동형 고정비의 금액을 원장에서 추정하지 못해 0원으로 처리했다",
}
