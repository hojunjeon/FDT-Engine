"""`fdt validate` 의 코어 함수 (SPEC 9장, 14 R7, PLAN Phase 6).

`validate_result()` 는 이미 만들어진 `EngineResult`(또는 그 dict 표현)를
검사해 `ValidationReport` 를 낸다. 검사 항목은:

(a) `EngineResult` 스키마 자체(파싱 실패 = 오류). 이 과정에서 렌더러 종속
    키·값(color, px, 라이브러리명)도 `Viz` 모델의 `model_validator` 가 함께
    걸러낸다.
(b) 모드별 필수 facts key 존재 + importance == 1(§9.4 무조건 필수) +
    조건부 필수(결과에 해당 데이터가 있을 때만 요구, N17).
(c) 모드별 필수 viz kind 존재 + priority == 1.
(d) `title`·`caption`·`annotations[].label`·`data.*.{label,name,detail}`
    의 모든 숫자 토큰이 facts 표기 집합과 **정확히 일치**(집합 대 집합
    비교, B9/S59) - 서수·계수(1위/3개/2건/10번째)는 예외.
(e) line_band x/y/band 길이 일치, step_bars 스택 합 == total(±1원),
    gauge thresholds 오름차순, table columns key ⊂ rows key.
(f) status=ERROR 면 result/facts/viz 가 없어야 한다.

이 모듈은 `fdt/tools/` 에 있으므로 파일 I/O 를 해도 되지만(SPEC §4.2),
`validate_result()` 자체는 순수 함수다 - I/O 는 CLI(`fdt validate`)가 한다.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fdt.engine.errors import extract_errors
from fdt.engine.schemas.result import EngineResult, GaugeViz, LineBandViz, StepBarsViz, TableViz
from fdt.engine.taxonomy import Mode

# ---------------------------------------------------------------------------
# 모드별 필수 facts / viz (SPEC 9.4)
# ---------------------------------------------------------------------------

MODE_REQUIRED_FACTS: dict[Mode, tuple[str, ...]] = {
    Mode.FORECAST: (
        "end_balance_median",
        "min_balance_median",
        "min_balance_date",
        "shortfall_prob",
    ),
    Mode.WHATIF: (
        "delta_min_balance",
        "delta_shortfall_prob",
        "verdict",
        "branch_min_balance_date",
    ),
    Mode.GOAL: ("feasible", "achieve_prob", "gap_median", "reduction_ratio", "plan_achieve_prob"),
    Mode.RISK: ("risk_score", "level", "worst_day", "expected_shortfall", "safe_to_spend_today"),
    Mode.OPTIMIZE: ("baseline_shortfall_prob",),
}

MODE_REQUIRED_VIZ_KINDS: dict[Mode, tuple[str, ...]] = {
    Mode.FORECAST: ("line_band", "progress_bars", "event_timeline"),
    Mode.WHATIF: ("line_band", "delta_bars"),
    Mode.GOAL: ("gauge", "step_bars", "line_band"),
    Mode.RISK: ("gauge", "table", "event_timeline"),
    Mode.OPTIMIZE: ("ranked_bars", "delta_bars"),
}

# N17: §9.4 는 몇몇 필수 facts 를 "결과에 그 데이터가 있을 때만" 요구한다
# (FORECAST 소진 예상 봉투, RISK 최고 위험 결제, OPTIMIZE 1위 행동). 이전에는
# `MODE_REQUIRED_FACTS` 가 이 3개를 아예 검사하지 않아 `facts.py` 가 회귀해도
# 잡히지 않았다. 각 항목은 (조건 함수, 조건이 참일 때 요구하는 fact key 들)
# 이다 - 조건 함수는 파싱된 모드별 result 를 받는다.
MODE_CONDITIONAL_REQUIRED_FACTS: dict[Mode, tuple[tuple[Any, tuple[str, ...]], ...]] = {
    Mode.FORECAST: (
        (
            lambda r: any(e.exhaust_date_median is not None for e in r.envelopes),
            ("envelope_exhaust_date_1",),
        ),
    ),
    Mode.RISK: (
        (
            lambda r: bool(r.payment_risks),
            ("payment_risk_due_1", "payment_risk_amount_1", "payment_risk_fail_prob_1"),
        ),
    ),
    Mode.OPTIMIZE: (
        (lambda r: bool(r.ranked), ("top_action_label", "top_action_delta")),
    ),
}

_NUMBER_TOKEN_RE = re.compile(r"[+-]?\d[\d,\.]*")

# B9/S59: 서수·계수(1위, 3개, 2건, 10번째)는 오케스트레이터 결정으로 facts
# 등록 대상에서 제외한다(§9.3 예외) - 그 숫자를 뺀 나머지만 정확 일치로
# 검사한다. 이 정규식이 매치한 부분 문자열을 검사 대상 텍스트에서 먼저
# 제거해 "1위" 의 "1" 이 facts 표기에 없어도 통과시킨다.
_ORDINAL_COUNT_RE = re.compile(r"\d+(?:위|개|건|번째)")

# 렌더러 종속 키(라이브러리명 6종)·값(hex 색상 코드, rgb(, Npx)은
# `fdt.engine.schemas.result._VizBase._no_forbidden_keys` 모델 검증기가 이미
# `Viz` 파싱 시점에 재귀로 검사한다(`encoding.color`처럼 SPEC 9.3이 정의한
# 정당한 인코딩 키 이름은 여기서 다시 금지하지 않는다 - 그 값이 실제 색상
# 코드/픽셀/라이브러리명일 때만 걸린다). `validate_result` 는 그 결과(파싱 실패
# = 오류)를 그대로 반영하고, 아래는 그 외 모드별·구조적 계약만 추가로 본다.


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _check_required_facts(result_obj: EngineResult, errors: list[str]) -> None:
    mode = result_obj.meta.mode
    fact_by_key = {f.key: f for f in result_obj.facts}
    for key in MODE_REQUIRED_FACTS.get(mode, ()):
        fact = fact_by_key.get(key)
        if fact is None:
            errors.append(f"필수 fact 누락: {key} (mode={mode.value})")
        elif fact.importance != 1:
            errors.append(f"필수 fact {key} 의 importance 가 1 이 아니다 (mode={mode.value})")

    # N17: 조건부 필수(결과에 해당 데이터가 있을 때만).
    result = result_obj.result
    if result is None:
        return
    for condition, keys in MODE_CONDITIONAL_REQUIRED_FACTS.get(mode, ()):
        if not condition(result):
            continue
        for key in keys:
            if key not in fact_by_key:
                errors.append(f"필수 fact 누락(조건부): {key} (mode={mode.value})")


def _check_required_viz(result_obj: EngineResult, errors: list[str]) -> None:
    mode = result_obj.meta.mode
    priority1_kinds = {v.kind for v in result_obj.viz if v.priority == 1}
    for kind in MODE_REQUIRED_VIZ_KINDS.get(mode, ()):
        if kind not in priority1_kinds:
            errors.append(f"필수 viz 누락: {kind} (mode={mode.value}, priority=1)")


def _normalize_number_token(token: str) -> str:
    """쉼표를 제거해 "19100" 과 "19,100" 을 같은 토큰으로 본다(B9 거짓 양성 제거)."""

    return token.replace(",", "")


def _number_token_set(text: str) -> set[str]:
    stripped = _ORDINAL_COUNT_RE.sub(" ", text)
    return {_normalize_number_token(tok) for tok in _NUMBER_TOKEN_RE.findall(stripped)}


def _iter_named_strings(data: Any, path: str = "") -> list[tuple[str, str]]:
    """`data`(viz.data 를 dict 로 덤프한 것)를 재귀 순회하며 key 가
    label/name/detail 인 문자열 값을 전부 낸다 (B9/S59 검사 범위 확장:
    `data.*.{label,name,detail}`)."""

    out: list[tuple[str, str]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            sub_path = f"{path}.{key}" if path else str(key)
            if key in ("label", "name", "detail") and isinstance(value, str):
                out.append((sub_path, value))
            else:
                out.extend(_iter_named_strings(value, sub_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            out.extend(_iter_named_strings(item, f"{path}[{i}]"))
    return out


def _check_caption_numbers(result_obj: EngineResult, errors: list[str]) -> None:
    """`title`·`caption`·`annotations[].label`·`data.*.{label,name,detail}`
    의 숫자 토큰이 facts 표기의 숫자 토큰 집합과 **정확히 일치**하는지
    검사한다 (B9/S59).

    이전에는 표기를 이어붙인 문자열에 `in` 으로 부분 문자열 검색을 했다 -
    "37점" 의 "37" 이 "1,370,000원" 의 부분 문자열이라는 이유로 통과하는 등
    검사가 사실상 무력화됐다(한 자리 숫자는 거의 항상 통과). 이제 양쪽을
    각각 숫자 토큰 **집합**으로 만들어(쉼표 제거로 정규화) 정확히 포함되는지
    본다. 순위·개수 같은 서수/계수(`_ORDINAL_COUNT_RE`)는 예외로 제외한다
    (§9.3, "1위"/"3개"/"2건"/"10번째" 는 오케스트레이터가 정한 값이라 facts
    에 넣지 않는다).
    """

    fact_tokens: set[str] = set()
    for f in result_obj.facts:
        for rendering in f.allowed_renderings:
            fact_tokens.update(_number_token_set(rendering))

    def _check_text(source: str, where: str) -> None:
        for token in _number_token_set(source):
            if token not in fact_tokens:
                errors.append(f"{where} 의 숫자 '{token}' 가 facts 표기 집합에 없다: {source!r}")

    for v in result_obj.viz:
        _check_text(v.title, f"viz {v.id} title")
        for ann in v.annotations:
            _check_text(ann.label, f"viz {v.id} annotation")
        _check_text(v.caption, f"viz {v.id} caption")
        data_dump = v.data.model_dump(mode="json") if hasattr(v.data, "model_dump") else {}
        for field_path, text in _iter_named_strings(data_dump):
            _check_text(text, f"viz {v.id} data.{field_path}")


def _check_structure(result_obj: EngineResult, errors: list[str]) -> None:
    for v in result_obj.viz:
        if isinstance(v, LineBandViz):
            data = v.data
            lengths = {len(data.x), len(data.band.lower), len(data.band.upper)}
            for series in data.series:
                lengths.add(len(series.y))
            if len(lengths) > 1:
                errors.append(f"viz {v.id}(line_band) 길이 불일치: {sorted(lengths)}")
        elif isinstance(v, StepBarsViz):
            step_data = v.data
            step_lengths = {len(step_data.x), len(step_data.total)}
            for stack in step_data.stacks:
                step_lengths.add(len(stack.y))
            if len(step_lengths) > 1:
                errors.append(f"viz {v.id}(step_bars) 길이 불일치: {sorted(step_lengths)}")
            else:
                for i, total in enumerate(step_data.total):
                    stacked_sum = sum(stack.y[i] for stack in step_data.stacks)
                    if abs(stacked_sum - total) > 1:
                        errors.append(
                            f"viz {v.id}(step_bars) index {i} "
                            f"스택 합({stacked_sum}) != total({total})"
                        )
        elif isinstance(v, GaugeViz):
            thresholds = v.data.thresholds
            if thresholds != sorted(thresholds):
                errors.append(f"viz {v.id}(gauge) thresholds 가 오름차순이 아니다: {thresholds}")
        elif isinstance(v, TableViz):
            table_data = v.data
            col_keys = {c.key for c in table_data.columns}
            for i, row in enumerate(table_data.rows):
                missing = col_keys - set(row.keys())
                if missing:
                    errors.append(f"viz {v.id}(table) row {i} 에 컬럼 키 누락: {sorted(missing)}")


def validate_result(obj: dict | EngineResult) -> ValidationReport:
    """`EngineResult`(또는 그 dict) 를 검사해 `ValidationReport` 를 낸다."""

    errors: list[str] = []
    warnings: list[str] = []

    if isinstance(obj, EngineResult):
        result_obj = obj
    else:
        try:
            result_obj = EngineResult.model_validate(obj)
        except ValidationError as exc:
            for fdt_error in extract_errors(exc):
                errors.append(f"{fdt_error.code}: {fdt_error.message}")
            return ValidationReport(ok=False, errors=errors, warnings=warnings)

    if result_obj.status == "ERROR":
        if result_obj.result is not None:
            errors.append("status=ERROR 인데 result 가 있다 (SPEC 9.1)")
        if result_obj.facts:
            errors.append("status=ERROR 인데 facts 가 있다 (SPEC 9.1)")
        if result_obj.viz:
            errors.append("status=ERROR 인데 viz 가 있다 (SPEC 9.1)")
        return ValidationReport(ok=not errors, errors=errors, warnings=warnings)

    _check_required_facts(result_obj, errors)
    _check_required_viz(result_obj, errors)
    _check_caption_numbers(result_obj, errors)
    _check_structure(result_obj, errors)

    return ValidationReport(ok=not errors, errors=errors, warnings=warnings)


__all__ = [
    "MODE_CONDITIONAL_REQUIRED_FACTS",
    "MODE_REQUIRED_FACTS",
    "MODE_REQUIRED_VIZ_KINDS",
    "ValidationReport",
    "validate_result",
]
