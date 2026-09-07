"""아키텍처 테스트 (SPEC 4.2 불변 원칙, PLAN Phase 0 완료 조건).

fdt/engine/** 전체를 읽어 다음을 검사한다.
(a) 금지 import (LLM/HTTP/비결정 난수·시각 라이브러리)가 없다.
(b) 금지 문자열("ground_truth", "hidden_params", "yaml")이 없다(순환 검증 금지,
    엔진이 생성기의 정답/숨김 파라미터를 읽지 않는다는 증거).
(c) taxonomy 상수 개수가 SPEC 1장/3장 표와 일치한다(봉투 7, 세분류 22,
    필수 ∪ 유연 = 전체 7종).

아직 만들어지지 않은 경로는 glob 결과 기준으로 건너뛴다(파일이 없으면 검사할
대상도 없다).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_ROOT / "fdt" / "engine"

# (a) 금지 import. 모듈 경계에서만 매칭되도록 줄 단위 정규식을 쓴다.
_FORBIDDEN_IMPORT_PATTERNS = [
    re.compile(r"^\s*import\s+openai\b"),
    re.compile(r"^\s*from\s+openai\b"),
    re.compile(r"^\s*import\s+anthropic\b"),
    re.compile(r"^\s*from\s+anthropic\b"),
    re.compile(r"^\s*import\s+ollama\b"),
    re.compile(r"^\s*from\s+ollama\b"),
    re.compile(r"^\s*import\s+requests\b"),
    re.compile(r"^\s*from\s+requests\b"),
    re.compile(r"^\s*import\s+httpx\b"),
    re.compile(r"^\s*from\s+httpx\b"),
    re.compile(r"^\s*import\s+random\b"),
    re.compile(r"^\s*from\s+random\b"),
    re.compile(r"^\s*import\s+time\b"),
    re.compile(r"^\s*from\s+time\b"),
]

# (b) 금지 문자열. 어디에 나오든(주석 포함) 위반으로 본다. 순환 검증 금지가
# 목적이므로 코드가 아니라도 실수로 남은 참조를 잡아야 한다.
_FORBIDDEN_SUBSTRINGS = ["ground_truth", "hidden_params", "yaml"]


def _engine_py_files() -> list[Path]:
    if not ENGINE_DIR.exists():
        return []
    return sorted(ENGINE_DIR.rglob("*.py"))


def test_no_forbidden_imports_in_engine():
    violations: list[str] = []
    for path in _engine_py_files():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in _FORBIDDEN_IMPORT_PATTERNS:
                if pattern.match(line):
                    violations.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")
    assert not violations, "fdt/engine/ 에 금지 import 발견:\n" + "\n".join(violations)


def test_no_forbidden_strings_in_engine():
    violations: list[str] = []
    for path in _engine_py_files():
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for token in _FORBIDDEN_SUBSTRINGS:
            if token.lower() in lowered:
                violations.append(f"{path.relative_to(REPO_ROOT)}: '{token}' 포함")
    assert not violations, "fdt/engine/ 에 금지 문자열 발견:\n" + "\n".join(violations)


def test_taxonomy_constants_match_spec():
    from fdt.engine.taxonomy import (
        ENVELOPE_IDS,
        ENVELOPES,
        ESSENTIAL_ENVELOPES,
        FLEXIBLE_ENVELOPES,
        SUBCATEGORIES,
    )

    assert len(ENVELOPES) == 7, "봉투는 7종이어야 한다 (SPEC 1/2/3장)"
    assert len(SUBCATEGORIES) == 22, "세분류는 22종이어야 한다 (SPEC 3.2)"
    assert len(ENVELOPE_IDS) == 7
    assert set(ENVELOPE_IDS.keys()) == set(ENVELOPES)
    assert set(ENVELOPE_IDS.values()) == set(range(1, 8))

    assert len(ESSENTIAL_ENVELOPES) == 3
    assert len(FLEXIBLE_ENVELOPES) == 4
    assert ESSENTIAL_ENVELOPES.isdisjoint(FLEXIBLE_ENVELOPES)
    assert ESSENTIAL_ENVELOPES | FLEXIBLE_ENVELOPES == set(ENVELOPES)

    sub_ids = [sub_id for sub_id, _env_id, _name in SUBCATEGORIES]
    assert sub_ids == list(range(1, 23)), "세분류 id 는 1..22 연속이어야 한다"

    envelope_ids_used = {env_id for _sub_id, env_id, _name in SUBCATEGORIES}
    assert envelope_ids_used == set(range(1, 8)), "모든 봉투가 세분류 매핑을 가져야 한다"


def test_errors_module_has_all_codes():
    from fdt.engine import errors

    required_codes = [
        "E_INPUT_TAXONOMY",
        "E_INPUT_REF",
        "E_INPUT_DUP",
        "E_INPUT_EMPTY",
        "E_RECON",
        "E_REQ_MISSING",
        "E_REQ_RANGE",
        "E_ENGINE_ID_MISMATCH",
        "W_INPUT_FUTURE_TX",
        "W_RECON",
        "W_INPUT_SHORT_HISTORY",
        "W_FIXED_VARIABLE_UNKNOWN",
    ]
    for name in required_codes:
        assert hasattr(errors, name), f"errors.py 에 {name} 상수가 없다"
        code_value = getattr(errors, name)
        assert code_value in errors.MESSAGES, f"MESSAGES 에 {code_value} 기본 메시지가 없다"
