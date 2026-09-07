"""아키텍처 테스트 (SPEC 4.2 불변 원칙, PLAN Phase 0 완료 조건).

fdt/engine/** 전체를 읽어 다음을 검사한다.
(a) 금지 import (LLM/HTTP/비결정 난수·시각 라이브러리)가 없다. 정규식이 아니라
    `ast.parse` 로 Import/ImportFrom/Call 노드를 순회해 다음을 잡는다(리뷰
    20260907_W0.md N9):
      - `import os, requests` 같은 한 줄 다중 import
      - `import sys; import httpx` 같은 세미콜론 뒤 import
      - `importlib.import_module(...)` / `__import__(...)` 동적 import
      - `hash(...)` 호출(SPEC §4.2-2 가 명시적으로 금지한 시드 방식)
      - `from numpy import random`, `numpy.random.seed(...)` 같은 numpy 전역 RNG
    `time` 은 SPEC §4.2-2(리뷰 S12) 에 따라 `time.perf_counter` 호출만 허용한다.
    그 외 `time.*` 호출, `import time` 이외의 time 심볼 import(`from time import
    time` 등)는 전부 금지한다. `elapsed_ms` 계측용 `perf_counter` 만 예외.
(b) 금지 문자열("ground_truth", "hidden_params", "yaml")이 없다(순환 검증 금지,
    엔진이 생성기의 정답/숨김 파라미터를 읽지 않는다는 증거). 이 검사는
    대소문자 무시 전체 문자열(주석·docstring 포함) 검색이다 - 예를 들어
    "YAML 설정을 읽지 않는다" 같은 정당한 설명 주석도 걸린다. 함정이므로
    엔진 코드/주석에 이 세 단어를 아예 쓰지 않는 방식으로 피해야 한다.
(c) taxonomy 상수 개수가 SPEC 1장/3장 표와 일치한다(봉투 7, 세분류 22,
    필수+유연 합집합 = 전체 7종).
(d) `fdt/engine/**` 소스에 파일 쓰기·표준출력이 없다(SPEC §4.2 "엔진 코어는
    외부 I/O 없음", 리뷰 B5). `open(`, `.write_text(`, `.write_bytes(`,
    `print(`, `sys.stdout`, `sys.stderr` 를 문자열 검색으로 잡는다.

아직 만들어지지 않은 경로는 glob 결과 기준으로 건너뛴다(파일이 없으면 검사할
대상도 없다). 다만 `_engine_py_files()` 가 빈 리스트를 돌려주면(디렉터리 이름이
바뀌거나 경로가 틀어진 경우) 테스트가 조용히 통과해버리는 "공허한 통과"를
막기 위해 `test_engine_dir_is_not_empty` 가 최소 파일 수를 강제한다.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_ROOT / "fdt" / "engine"

# 루트 모듈 이름 기준 금지 목록 (SPEC §4.2-1).
_FORBIDDEN_ROOT_MODULES = {
    "openai",
    "anthropic",
    "ollama",
    "requests",
    "httpx",
    "random",
}

# 호출 형태로 우회하는 동적 import·비결정 함수 (SPEC §4.2-2).
_FORBIDDEN_CALL_NAMES = {
    "import_module",  # importlib.import_module(...)
    "__import__",
    "hash",
}

# (b) 금지 문자열. 어디에 나오든(주석 포함) 위반으로 본다. 순환 검증 금지가
# 목적이므로 코드가 아니라도 실수로 남은 참조를 잡아야 한다.
# 함정: 대소문자 무시 + 부분 문자열 검색이라 "야믈"이 아니라 "yaml" 이 들어간
# 정상적인 한글 설명(예: "YAML 설정 파일") 도 걸린다. 엔진 코드/주석에 이
# 단어들을 쓰지 마라.
_FORBIDDEN_SUBSTRINGS = ["ground_truth", "hidden_params", "yaml"]

# (d) 엔진 코어 안에서 금지되는 I/O 흔적 문자열 (SPEC §4.2, 리뷰 B5).
_FORBIDDEN_IO_SUBSTRINGS = [
    "open(",
    ".write_text(",
    ".write_bytes(",
    "print(",
    "sys.stdout",
    "sys.stderr",
]


def _engine_py_files() -> list[Path]:
    if not ENGINE_DIR.exists():
        return []
    return sorted(ENGINE_DIR.rglob("*.py"))


def test_engine_dir_is_not_empty():
    files = _engine_py_files()
    assert len(files) >= 5, (
        "엔진 파일을 하나도(또는 너무 적게) 스캔하지 못했다 - ENGINE_DIR 경로가 "
        f"틀어졌을 수 있다: {ENGINE_DIR}"
    )


def _root_module_name(module: str | None) -> str:
    if not module:
        return ""
    return module.split(".")[0]


def _check_ast_violations(path: Path, tree: ast.AST) -> list[str]:
    violations: list[str] = []
    try:
        rel = path.relative_to(REPO_ROOT)
    except ValueError:
        # 회귀 테스트가 실제 저장소에 없는 가상 경로를 넘기는 경우.
        rel = path

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = _root_module_name(alias.name)
                if root in _FORBIDDEN_ROOT_MODULES:
                    violations.append(f"{rel}:{node.lineno}: import {alias.name}")
                if root == "time" and alias.name != "time":
                    # "import time" 자체는 perf_counter 호출용으로 허용.
                    # "import time.something" 형태는 없지만 방어적으로 남김.
                    violations.append(f"{rel}:{node.lineno}: import {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            root = _root_module_name(node.module)
            if root in _FORBIDDEN_ROOT_MODULES:
                names = ", ".join(alias.name for alias in node.names)
                violations.append(f"{rel}:{node.lineno}: from {node.module} import {names}")
            if root == "numpy":
                for alias in node.names:
                    if alias.name == "random":
                        violations.append(
                            f"{rel}:{node.lineno}: from {node.module} import random "
                            "(numpy 전역 RNG 금지, default_rng(seed) 만 허용)"
                        )
            if root == "time":
                # `from time import perf_counter` 만 허용. time() 등은 금지.
                for alias in node.names:
                    if alias.name != "perf_counter":
                        violations.append(
                            f"{rel}:{node.lineno}: from time import {alias.name} "
                            "(perf_counter 외 time 심볼 금지)"
                        )

        elif isinstance(node, ast.Call):
            func = node.func
            call_name = None
            if isinstance(func, ast.Name):
                call_name = func.id
            elif isinstance(func, ast.Attribute):
                call_name = func.attr

            if call_name in _FORBIDDEN_CALL_NAMES:
                violations.append(f"{rel}:{node.lineno}: {call_name}(...) 호출 금지")

            # time.<anything>() 은 perf_counter 만 허용.
            if isinstance(func, ast.Attribute) and call_name is not None:
                value = func.value
                is_time_call = (
                    isinstance(value, ast.Name)
                    and value.id == "time"
                    and call_name != "perf_counter"
                )
                if is_time_call:
                    violations.append(
                        f"{rel}:{node.lineno}: time.{call_name}(...) 호출 금지 "
                        "(time.perf_counter() 만 허용)"
                    )
                # numpy.random.seed(...) / np.random.seed(...) 류 전역 RNG 금지.
                if (
                    call_name == "seed"
                    and isinstance(value, ast.Attribute)
                    and value.attr == "random"
                ):
                    violations.append(
                        f"{rel}:{node.lineno}: {ast.dump(func)} - numpy 전역 시드 금지 "
                        "(default_rng(seed) 만 허용)"
                    )

    return violations


def test_no_forbidden_imports_in_engine():
    violations: list[str] = []
    for path in _engine_py_files():
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        violations.extend(_check_ast_violations(path, tree))
    assert not violations, "fdt/engine/ 에 금지 import/호출 발견:\n" + "\n".join(violations)


def test_forbidden_import_ast_check_catches_bypass_cases():
    """리뷰가 실측한 우회 사례 2건이 AST 검사로는 잡히는지 확인하는 회귀 테스트."""

    src_one_line = "import os, requests\n"
    tree_one_line = ast.parse(src_one_line)
    fake_path = Path("fdt/engine/_regression_one_line.py")
    violations_one_line = _check_ast_violations(fake_path, tree_one_line)
    assert any("requests" in v for v in violations_one_line), (
        "한 줄 다중 import(`import os, requests`) 를 잡지 못했다"
    )

    src_semicolon = "import sys; import httpx\n"
    tree_semicolon = ast.parse(src_semicolon)
    violations_semicolon = _check_ast_violations(
        Path("fdt/engine/_regression_semicolon.py"), tree_semicolon
    )
    assert any("httpx" in v for v in violations_semicolon), (
        "세미콜론 뒤 import(`import sys; import httpx`) 를 잡지 못했다"
    )


def test_perf_counter_is_allowed_but_other_time_calls_are_not():
    src_ok = "import time\n\nt0 = time.perf_counter()\n"
    tree_ok = ast.parse(src_ok)
    violations_ok = _check_ast_violations(Path("fdt/engine/_regression_perf_counter.py"), tree_ok)
    assert not violations_ok, f"time.perf_counter() 는 허용되어야 하는데 걸렸다: {violations_ok}"

    src_bad = "from time import time\n\nt0 = time()\n"
    tree_bad = ast.parse(src_bad)
    violations_bad = _check_ast_violations(Path("fdt/engine/_regression_time_time.py"), tree_bad)
    assert violations_bad, "`from time import time` 는 잡혀야 하는데 통과했다"


def test_no_forbidden_strings_in_engine():
    violations: list[str] = []
    for path in _engine_py_files():
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for token in _FORBIDDEN_SUBSTRINGS:
            if token.lower() in lowered:
                violations.append(f"{path.relative_to(REPO_ROOT)}: '{token}' 포함")
    assert not violations, "fdt/engine/ 에 금지 문자열 발견:\n" + "\n".join(violations)


def test_no_file_io_or_stdio_in_engine():
    """SPEC §4.2 '엔진 코어는 외부 I/O 없음' (리뷰 B5).

    `fdt/engine/**` 소스에 `open(`, `.write_text(`, `.write_bytes(`, `print(`,
    `sys.stdout`, `sys.stderr` 가 없어야 한다. 파일 쓰기·콘솔 출력은
    `fdt/tools/`, `fdt/cli.py` 등 엔진 밖에서만 한다.
    """

    violations: list[str] = []
    for path in _engine_py_files():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for token in _FORBIDDEN_IO_SUBSTRINGS:
                if token in line:
                    violations.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")
    assert not violations, "fdt/engine/ 에 금지된 I/O 흔적 발견:\n" + "\n".join(violations)


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
