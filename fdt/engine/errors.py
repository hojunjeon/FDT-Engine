"""엔진 오류·경고 코드 (SPEC 3.3 입력 검증, 8.1 모드 요청 검증).

`fdt/engine/**` 는 이 모듈의 코드만으로 실패를 표현한다. 순수 파이썬 예외
메시지에 임의 문자열을 쓰지 않는다.

리뷰 N1·N22·S39: pydantic validator 안에서 `ValueError(f"{CODE}: ...")` 로
코드를 메시지 문자열에 태우던 옛 관례 대신, `FdtError(code=..., message=...,
details=...)` 를 그대로 던진다. `FdtError` 가 `ValueError` 의 서브클래스라
pydantic 이 여느 `ValueError` 와 똑같이 잡아 `ValidationError` 로 감싸고,
pydantic v2 는 원 예외 객체를 `ValidationError.errors(include_context=True)`
의 각 항목 `ctx["error"]` 에 그대로 보존한다. `extract_errors()` 가 이
`ctx["error"]` 를 우선 사용해 코드 손실 없이 구조화된 `FdtError` 목록을
복원한다(정규식으로 메시지를 파싱하지 않는다).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import ValidationError


class FdtError(ValueError):
    """엔진 내부에서 발생하는 검증·계약 위반 오류.

    code 는 아래 상수 중 하나(또는 그 확장)여야 한다. message 가 비어 있으면
    MESSAGES 의 기본 한국어 메시지를 쓴다. `ValueError` 를 상속해 pydantic
    validator 안에서 던져도 다른 `ValueError` 와 동일하게 `ValidationError`
    로 감싸진다(N1·S39).
    """

    def __init__(
        self,
        code: str,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.details = details or {}
        self.message = message or MESSAGES.get(code, code)
        super().__init__(f"{self.code}: {self.message}")


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
E_REQ_INVALID = "E-REQ-INVALID"
E_ENGINE_ID_MISMATCH = "E-ENGINE-ID-MISMATCH"
E_ENGINE_LOAD = "E-ENGINE-LOAD"
E_MODE_NOT_IMPLEMENTED = "E-MODE-NOT_IMPLEMENTED"

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
    E_REQ_INVALID: "모드 요청 파라미터 검증에 실패했다",
    E_ENGINE_ID_MISMATCH: "저장된 engine_id 와 로드 시점 재계산 결과가 다르다",
    E_ENGINE_LOAD: "엔진 파일을 불러오지 못했다",
    E_MODE_NOT_IMPLEMENTED: "요청한 모드는 아직 구현되지 않았다",
    W_INPUT_FUTURE_TX: "as_of 이후 날짜의 거래가 있어 무시했다",
    W_RECON: "계좌 대사 차액이 있다",
    W_INPUT_SHORT_HISTORY: "거래 이력이 28일 미만이라 Behavior 기본값 비중을 높였다",
    W_FIXED_VARIABLE_UNKNOWN: "변동형 고정비의 금액을 원장에서 추정하지 못해 0원으로 처리했다",
}

# ---------------------------------------------------------------------------
# ValidationError -> FdtError 구조화 변환 (N1·N22·S39)
# ---------------------------------------------------------------------------

# pydantic v2 내장 오류 `type` -> 엔진 코드. 여기 없는 타입은 전부
# `E_REQ_INVALID` 로 떨어진다(그 외 범주는 코드가 세분화될 이유가 없다).
_PYDANTIC_TYPE_TO_CODE: dict[str, str] = {
    "missing": E_REQ_MISSING,
    "greater_than": E_REQ_RANGE,
    "greater_than_equal": E_REQ_RANGE,
    "less_than": E_REQ_RANGE,
    "less_than_equal": E_REQ_RANGE,
    "too_long": E_REQ_RANGE,
    "too_short": E_REQ_RANGE,
    "string_pattern_mismatch": E_REQ_RANGE,
    "literal_error": E_REQ_RANGE,
    "enum": E_REQ_RANGE,
}


def extract_errors(exc: ValidationError) -> list[FdtError]:
    """`pydantic.ValidationError` -> `list[FdtError]` (N1·N22·S39).

    각 오류 항목의 `ctx["error"]` 가 우리가 던진 `FdtError` 그대로면(검증
    지점이 `FdtError(code=...)` 를 던진 경우) 그것을 그대로 쓴다. 아니면
    pydantic 내장 오류(`missing`, 범위류 등)를 `_PYDANTIC_TYPE_TO_CODE` 로
    매핑하고, 매핑에 없으면 `E_REQ_INVALID` 로 떨어진다. **메시지 문자열을
    정규식으로 파싱하지 않는다** - 코드는 항상 `ctx["error"]`(구조화된 예외
    객체) 또는 pydantic 이 이미 구조화해 준 `type` 필드에서만 얻는다.

    각 `FdtError.details` 에는 최소한 `loc`(필드 경로)가 들어가고, pydantic
    이 `input` 을 제공하면 그것도 담는다.
    """

    out: list[FdtError] = []
    for err in exc.errors(include_context=True):
        loc = list(err["loc"])
        ctx = err.get("ctx") or {}
        original = ctx.get("error")
        if isinstance(original, FdtError):
            merged_details = {"loc": loc, **original.details}
            out.append(
                FdtError(code=original.code, message=original.message, details=merged_details)
            )
            continue

        code = _PYDANTIC_TYPE_TO_CODE.get(err["type"], E_REQ_INVALID)
        details: dict[str, Any] = {"loc": loc}
        if "input" in err:
            details["input"] = err["input"]
        out.append(FdtError(code=code, message=err["msg"], details=details))

    return out
