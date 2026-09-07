"""`viz.py` 단위 테스트 (작업 ID W11a, SPEC 9.3, 9.4).

5 모드 각각 합성 result(=`test_facts.py` 의 빌더 재사용)로 `build_viz()` 를
호출해 SPEC 9.4 필수 kind(priority 1), data 길이 일관, annotations 라벨 숫자
⊂ facts, 금지 키(color/px/library) 없음을 검사한다.
"""

from __future__ import annotations

import pytest

from fdt.engine.facts import build_facts
from fdt.engine.schemas.result import EngineResult
from fdt.engine.taxonomy import Mode
from fdt.engine.viz import build_viz
from tests.unit.test_facts import (
    AS_OF,
    RESULT_BUILDERS,
    _forecast_result,
    _goal_result,
    _optimize_result,
    _risk_result,
    _whatif_result,
    build_ok_result,
)

REQUIRED_VIZ_KINDS = {
    Mode.FORECAST: {"line_band", "progress_bars", "event_timeline"},
    Mode.WHATIF: {"line_band", "delta_bars"},
    Mode.GOAL: {"gauge", "step_bars", "line_band"},
    Mode.RISK: {"gauge", "table", "event_timeline"},
    Mode.OPTIMIZE: {"ranked_bars", "delta_bars"},
}


def _fact_renderings(mode: Mode, result) -> set[str]:
    facts = build_facts(mode, result, as_of=AS_OF)
    out: set[str] = set()
    for f in facts:
        out.update(f.allowed_renderings)
    return out


@pytest.mark.parametrize("mode", list(Mode))
def test_required_viz_kinds_present_with_priority_1(mode: Mode):
    result = RESULT_BUILDERS[mode]()
    facts = build_facts(mode, result, as_of=AS_OF)
    viz = build_viz(mode, result, facts, as_of=AS_OF)
    priority1_kinds = {v.kind for v in viz if v.priority == 1}
    assert REQUIRED_VIZ_KINDS[mode] <= priority1_kinds


@pytest.mark.parametrize("mode", list(Mode))
def test_annotation_and_caption_numbers_are_subset_of_facts(mode: Mode):
    import re

    result = RESULT_BUILDERS[mode]()
    facts = build_facts(mode, result, as_of=AS_OF)
    viz = build_viz(mode, result, facts, as_of=AS_OF)
    blob = " ".join(_fact_renderings(mode, result))
    token_re = re.compile(r"[+-]?\d[\d,\.]*")
    for v in viz:
        for ann in v.annotations:
            for token in token_re.findall(ann.label):
                assert token in blob, f"{mode}:{v.id} annotation 라벨의 '{token}' 이 facts 에 없다"
        for token in token_re.findall(v.caption):
            assert token in blob, f"{mode}:{v.id} caption 의 '{token}' 이 facts 에 없다"


def test_forecast_line_band_lengths_consistent():
    result = _forecast_result()
    facts = build_facts(Mode.FORECAST, result, as_of=AS_OF)
    viz = build_viz(Mode.FORECAST, result, facts, as_of=AS_OF)
    line_band = next(v for v in viz if v.kind == "line_band")
    n = len(line_band.data.x)
    assert len(line_band.data.band.lower) == n
    assert len(line_band.data.band.upper) == n
    for series in line_band.data.series:
        assert len(series.y) == n


def test_whatif_line_band_has_two_series():
    result = _whatif_result()
    facts = build_facts(Mode.WHATIF, result, as_of=AS_OF)
    viz = build_viz(Mode.WHATIF, result, facts, as_of=AS_OF)
    line_band = next(v for v in viz if v.kind == "line_band")
    assert len(line_band.data.series) == 2
    names = {s.name for s in line_band.data.series}
    assert names == {"기준", "분기"}


def test_goal_step_bars_stack_sum_matches_total():
    result = _goal_result()
    facts = build_facts(Mode.GOAL, result, as_of=AS_OF)
    viz = build_viz(Mode.GOAL, result, facts, as_of=AS_OF)
    step_bars = next(v for v in viz if v.kind == "step_bars")
    for i, total in enumerate(step_bars.data.total):
        stacked = sum(s.y[i] for s in step_bars.data.stacks)
        assert abs(stacked - total) <= 1


def test_risk_gauge_thresholds_ascending_and_matches_level():
    result = _risk_result()
    facts = build_facts(Mode.RISK, result, as_of=AS_OF)
    viz = build_viz(Mode.RISK, result, facts, as_of=AS_OF)
    gauge = next(v for v in viz if v.kind == "gauge")
    assert gauge.data.thresholds == sorted(gauge.data.thresholds)
    assert gauge.data.level == result.level
    assert gauge.data.value == result.risk_score


def test_risk_table_rows_have_all_column_keys():
    result = _risk_result()
    facts = build_facts(Mode.RISK, result, as_of=AS_OF)
    viz = build_viz(Mode.RISK, result, facts, as_of=AS_OF)
    table = next(v for v in viz if v.kind == "table")
    col_keys = {c.key for c in table.data.columns}
    for row in table.data.rows:
        assert col_keys <= set(row.keys())


def test_optimize_ranked_bars_matches_result_ranked_length():
    result = _optimize_result()
    facts = build_facts(Mode.OPTIMIZE, result, as_of=AS_OF)
    viz = build_viz(Mode.OPTIMIZE, result, facts, as_of=AS_OF)
    ranked_bars = next(v for v in viz if v.kind == "ranked_bars")
    assert len(ranked_bars.data.items) == len(result.ranked)


def test_no_forbidden_library_names_or_color_codes_anywhere():
    # "color" 는 event_timeline 의 정당한 encoding 키(SPEC 9.3, `color:"fail_prob"`)
    # 이므로 금지어가 아니다. 여기서는 실제 렌더러 종속 흔적(라이브러리명·hex
    # 색상 코드·rgb(·Npx)만 검사한다.
    import re as _re

    hex_re = _re.compile(r"#[0-9a-fA-F]{6}\b")
    px_re = _re.compile(r"\d+px\b")
    for mode, builder in RESULT_BUILDERS.items():
        result = builder()
        facts = build_facts(mode, result, as_of=AS_OF)
        viz = build_viz(mode, result, facts, as_of=AS_OF)
        for v in viz:
            blob = str(v.model_dump(mode="json"))
            for banned in ("matplotlib", "plotly", "vega", "chart.js", "recharts"):
                assert banned not in blob.lower(), f"{mode}:{v.id} 에 라이브러리명 '{banned}' 발견"
            assert not hex_re.search(blob), f"{mode}:{v.id} 에 hex 색상 코드가 있다"
            assert not px_re.search(blob), f"{mode}:{v.id} 에 px 값이 있다"


def test_engine_result_ok_round_trips_for_all_modes():
    for mode in Mode:
        result = RESULT_BUILDERS[mode]()
        engine_result = build_ok_result(mode, result)
        dumped = engine_result.model_dump(mode="json")
        again = EngineResult.model_validate(dumped)
        assert again == engine_result
