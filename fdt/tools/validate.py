"""`fdt validate` 의 코어 함수 (SPEC 9장, 14 R7, PLAN Phase 6).

`validate_result()` 는 이미 만들어진 `EngineResult`(또는 그 dict 표현)를
검사해 `ValidationReport` 를 낸다. 검사 항목은:

(a) `EngineResult` 스키마 자체(파싱 실패 = 오류). 이 과정에서 렌더러 종속
    키·값(color, px, 라이브러리명)도 `Viz` 모델의 `model_validator` 가 함께
    걸러낸다.
(b) 모드별 필수 facts key 존재 + importance == 1.
(c) 모드별 필수 viz kind 존재 + priority == 1.
(d) viz annotations 라벨·caption 의 모든 숫자 토큰이 facts 표기 집합에 포함.
(e) line_band x/y/band 길이 일치, step_bars 스택 합 == total(±1원),
    gauge thresholds 오름차순, table columns key ⊂ rows key.
(f) status=ERROR 면 result/facts/viz 가 없어야 한다.

이 모듈은 `fdt/tools/` 에 있으므로 파일 I/O 를 해도 되지만(SPEC §4.2),
`validate_result()` 자체는 순수 함수다 - I/O 는 CLI(`fdt validate`)가 한다.
"""

from __future__ import annotations

import re

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

_NUMBER_TOKEN_RE = re.compile(r"[+-]?\d[\d,\.]*")

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


def _check_required_viz(result_obj: EngineResult, errors: list[str]) -> None:
    mode = result_obj.meta.mode
    priority1_kinds = {v.kind for v in result_obj.viz if v.priority == 1}
    for kind in MODE_REQUIRED_VIZ_KINDS.get(mode, ()):
        if kind not in priority1_kinds:
            errors.append(f"필수 viz 누락: {kind} (mode={mode.value}, priority=1)")


def _check_caption_numbers(result_obj: EngineResult, errors: list[str]) -> None:
    """annotations 라벨·caption 의 숫자 토큰이 facts 표기에 포함되는지 검사 (R7).

    한국어 단위 결합 표기("1만 9천원" 등)도 포함해 부분 문자열 일치로
    검사한다(SPEC 14 R7 지시). 토큰 하나가 facts 의 `allowed_renderings`
    전체를 이어붙인 문자열 어딘가에 부분 문자열로 나타나면 통과시킨다.
    """

    blob = " ".join(r for f in result_obj.facts for r in f.allowed_renderings)

    def _check_text(source: str, where: str) -> None:
        for token in _NUMBER_TOKEN_RE.findall(source):
            if token not in blob:
                errors.append(f"{where} 의 숫자 '{token}' 가 facts 표기 집합에 없다: {source!r}")

    for v in result_obj.viz:
        for ann in v.annotations:
            _check_text(ann.label, f"viz {v.id} annotation")
        _check_text(v.caption, f"viz {v.id} caption")


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


__all__ = ["MODE_REQUIRED_FACTS", "MODE_REQUIRED_VIZ_KINDS", "ValidationReport", "validate_result"]
