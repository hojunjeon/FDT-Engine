"""`fdt/tools/validate.py` 단위 테스트 (작업 ID W11a, SPEC 9장, 14 R7).

정상 케이스(5 모드 각각 validate 통과)와 부정 케이스(캡션 숫자 변조, color 키,
길이 불일치, 필수 fact 누락)가 실제로 실패하는지 검사한다.
"""

from __future__ import annotations

import pytest

from fdt.engine.taxonomy import Mode
from fdt.tools.validate import validate_result
from tests.unit.test_facts import RESULT_BUILDERS, _meta, _request, build_ok_result


@pytest.mark.parametrize("mode", list(Mode))
def test_valid_result_passes_for_all_modes(mode: Mode):
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    report = validate_result(engine_result)
    assert report.ok, report.errors
    assert report.errors == []


@pytest.mark.parametrize("mode", list(Mode))
def test_valid_result_passes_as_dict_too(mode: Mode):
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    report = validate_result(dumped)
    assert report.ok, report.errors


def test_error_status_with_result_is_rejected():
    mode = Mode.FORECAST
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    dumped["status"] = "ERROR"
    dumped["error"] = {"code": "E-TEST", "message": "test", "details": {}}
    # status=ERROR 인데 result/facts/viz 가 남아있다 -> EngineResult 파싱 단계에서부터
    # 이미 SPEC 9.1 모델 검증(@model_validator _check_status)에 걸린다.
    report = validate_result(dumped)
    assert not report.ok
    assert report.errors


def test_error_status_clean_is_ok():
    dumped = {
        "schema_version": "engine-result/1",
        "meta": _meta(Mode.FORECAST).model_dump(mode="json"),
        "request": _request(Mode.FORECAST).model_dump(mode="json"),
        "result": None,
        "facts": [],
        "viz": [],
        "status": "ERROR",
        "error": {"code": "E-TEST", "message": "테스트 오류", "details": {}},
    }
    report = validate_result(dumped)
    assert report.ok, report.errors


def test_caption_number_tampering_fails():
    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    # caption 에 facts 표기에 없는 숫자를 끼워 넣는다.
    dumped["viz"][0]["caption"] = "위험 점수는 999점이다."
    report = validate_result(dumped)
    assert not report.ok
    assert any("999" in e for e in report.errors)


def test_annotation_label_number_tampering_fails():
    mode = Mode.FORECAST
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    line_band = next(v for v in dumped["viz"] if v["kind"] == "line_band")
    line_band["annotations"] = [{"type": "point", "label": "최저점 777777원"}]
    report = validate_result(dumped)
    assert not report.ok
    assert any("777777" in e for e in report.errors)


def test_forbidden_hex_color_value_fails_at_parse():
    # "color" 자체는 event_timeline 의 정당한 encoding 키(SPEC 9.3)라 금지어가
    # 아니다. 실제 hex 색상 코드 값이 caption 에 섞이면 `Viz` 모델의
    # `_no_forbidden_keys` 검증기가 파싱 단계에서부터 막아야 한다.
    mode = Mode.FORECAST
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    dumped["viz"][0]["caption"] = "이 선의 색은 #ff0000 이다."
    report = validate_result(dumped)
    assert not report.ok


def test_forbidden_library_name_value_fails_at_parse():
    mode = Mode.FORECAST
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    dumped["viz"][0]["caption"] = "matplotlib 으로 그렸다."
    report = validate_result(dumped)
    assert not report.ok


def test_line_band_length_mismatch_fails():
    mode = Mode.FORECAST
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    line_band = next(v for v in dumped["viz"] if v["kind"] == "line_band")
    line_band["data"]["band"]["lower"] = line_band["data"]["band"]["lower"][:-1]
    report = validate_result(dumped)
    assert not report.ok
    assert any("길이 불일치" in e for e in report.errors)


def test_missing_required_fact_fails():
    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    dumped["facts"] = [f for f in dumped["facts"] if f["key"] != "risk_score"]
    report = validate_result(dumped)
    assert not report.ok
    assert any("risk_score" in e for e in report.errors)


def test_required_fact_present_but_wrong_importance_fails():
    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    for f in dumped["facts"]:
        if f["key"] == "risk_score":
            f["importance"] = 2
    report = validate_result(dumped)
    assert not report.ok
    assert any("importance" in e for e in report.errors)


def test_missing_required_viz_kind_fails():
    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    dumped["viz"] = [v for v in dumped["viz"] if v["kind"] != "gauge"]
    report = validate_result(dumped)
    assert not report.ok
    assert any("gauge" in e for e in report.errors)


def test_step_bars_stack_sum_mismatch_fails():
    mode = Mode.GOAL
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    step_bars = next(v for v in dumped["viz"] if v["kind"] == "step_bars")
    step_bars["data"]["total"][0] = step_bars["data"]["total"][0] + 999999
    report = validate_result(dumped)
    assert not report.ok
    assert any("스택 합" in e for e in report.errors)


def test_gauge_thresholds_not_ascending_fails():
    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    gauge = next(v for v in dumped["viz"] if v["kind"] == "gauge")
    gauge["data"]["thresholds"] = [50, 20]
    report = validate_result(dumped)
    assert not report.ok
    assert any("오름차순" in e for e in report.errors)


def test_table_row_missing_column_key_fails():
    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    table = next(v for v in dumped["viz"] if v["kind"] == "table")
    del table["data"]["rows"][0]["fail_prob"]
    report = validate_result(dumped)
    assert not report.ok
    assert any("컬럼 키 누락" in e for e in report.errors)


def test_malformed_schema_fails_gracefully_without_raising():
    report = validate_result({"schema_version": "engine-result/1", "status": "OK"})
    assert not report.ok
    assert report.errors
