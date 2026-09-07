"""`fdt/tools/validate.py` 단위 테스트 (작업 ID W11a/J4, SPEC 9장, 14 R7).

정상 케이스(5 모드 각각 validate 통과)와 부정 케이스(캡션 숫자 변조, color 키,
길이 불일치, 필수 fact 누락)가 실제로 실패하는지 검사한다. B9/S59 이후로는
부분 문자열 매칭 우회(항목 7-4 실측: "37점" 이 "1,370,000원" 때문에 통과,
"1위" 가 우연히 통과) 가 더 이상 통하지 않는지, 서수/계수 예외("1위")는
여전히 통과하는지도 검사한다.
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


# ---------------------------------------------------------------------------
# B9/S59: 부분 문자열 매칭 우회 회귀 고정
# ---------------------------------------------------------------------------


def test_substring_coincidence_no_longer_passes_37_vs_1370000():
    """항목 7-4 실측: 이전 구현은 "37점" 의 "37" 이 facts 표기 "1,370,000원"
    의 부분 문자열이라는 이유만으로 통과시켰다. 토큰 집합 정확 일치로
    바꾸면 "37" 이 facts 어디에도 독립 토큰으로 없으면 실패해야 한다."""

    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    # facts 에 "37" 을 독립 토큰으로 내는 것을 전부 지운다(risk_score=37 등).
    dumped["facts"] = [f for f in dumped["facts"] if "37" not in f["key"]]
    for f in dumped["facts"]:
        f["allowed_renderings"] = [r for r in f["allowed_renderings"] if "37" not in r]
    # 그런데 facts 어딘가에 "1,370,000원" 처럼 "37" 을 부분 문자열로 담은
    # 표기를 하나 심어둔다 - 이전 구현이라면 이것만으로 "37" 이 통과했다.
    dumped["facts"][0]["allowed_renderings"].append("1,370,000원")
    dumped["viz"][0]["caption"] = "위험 점수는 37점이다."
    report = validate_result(dumped)
    assert not report.ok
    assert any("37" in e for e in report.errors), report.errors


def test_ordinal_rank_exception_1st_passes_even_without_matching_fact():
    """B9/S59 서수 예외: "1위" 는 순위 표현이라 facts 등록 없이 통과해야
    한다(오케스트레이터 결정, §9.3 예외) - 단 "1" 이 다른 숫자와 우연히
    맞아떨어져서가 아니라 "위" 접미사 규칙 자체가 면제하는지 확인한다."""

    import re

    mode = Mode.OPTIMIZE
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    token_re = re.compile(r"[+-]?\d[\d,\.]*")

    def _has_standalone_1(rendering: str) -> bool:
        return any(tok.replace(",", "") == "1" for tok in token_re.findall(rendering))

    # facts 표기 어디에도 "1" 이 독립 토큰으로 없도록 만든다(부분 문자열이
    # 아니라 정확한 토큰 기준 - "31%" 같은 표기는 그대로 둔다).
    for f in dumped["facts"]:
        f["allowed_renderings"] = [r for r in f["allowed_renderings"] if not _has_standalone_1(r)]
    ranked_bars = next(v for v in dumped["viz"] if v["kind"] == "ranked_bars")
    ranked_bars["caption"] = "1위 행동을 확인하라."
    report = validate_result(dumped)
    assert report.ok, report.errors


def test_missing_date_fact_9wol_16il_fails():
    """"9월 16일" 처럼 날짜 fact 가 등록돼 있지 않으면, 그 문장 안의 "9"·
    "16" 은 다른 숫자와 우연히 맞아떨어지지 않는 한 실패해야 한다."""

    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    # 날짜 관련 fact(worst_day 등)를 전부 지워 "9"/"16" 표기가 남지 않게 한다.
    dumped["facts"] = [
        f
        for f in dumped["facts"]
        if not any(tok in r for r in f["allowed_renderings"] for tok in ("9월", "16"))
    ]
    dumped["viz"][0]["caption"] = "9월 16일에 결제가 몰려 있다."
    report = validate_result(dumped)
    assert not report.ok
    assert any(("9" in e or "16" in e) for e in report.errors), report.errors


def test_comma_normalization_removes_false_positive():
    """B9 거짓 양성 제거: facts 표기가 "19,100원" 뿐이어도, caption 에
    쉼표 없는 "19100" 을 쓰면(같은 값의 다른 표기) 쉼표 정규화로 통과해야
    한다."""

    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    fact = next(f for f in dumped["facts"] if f["key"] == "safe_to_spend_today")
    assert "19,100원" in fact["allowed_renderings"]
    dumped["viz"][0]["caption"] = "오늘 19100원까지는 써도 된다."
    report = validate_result(dumped)
    assert report.ok, report.errors


def test_title_number_not_in_facts_fails():
    """B9/S59 검사 범위 확장: `title` 도 이제 검사한다."""

    mode = Mode.FORECAST
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    dumped["viz"][0]["title"] = "45일 잔액 예측"
    report = validate_result(dumped)
    assert not report.ok
    assert any("45" in e for e in report.errors), report.errors


def test_data_detail_field_number_not_in_facts_fails():
    """B9/S59 검사 범위 확장: `data.*.detail` 도 이제 검사한다(항목 7-1
    "ranked_bars.data.items.detail" 결함 - 재발 방지 회귀)."""

    mode = Mode.OPTIMIZE
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    ranked_bars = next(v for v in dumped["viz"] if v["kind"] == "ranked_bars")
    ranked_bars["data"]["items"][0]["detail"] = "이번 달 이미 사용 999999원"
    report = validate_result(dumped)
    assert not report.ok
    assert any("999999" in e for e in report.errors), report.errors


# ---------------------------------------------------------------------------
# N17: 조건부 필수 facts (결과에 데이터가 있을 때만)
# ---------------------------------------------------------------------------


def test_forecast_conditional_envelope_exhaust_fact_required_when_present():
    mode = Mode.FORECAST
    result = RESULT_BUILDERS[mode]()
    assert any(e.exhaust_date_median is not None for e in result.envelopes)
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    dumped["facts"] = [f for f in dumped["facts"] if f["key"] != "envelope_exhaust_date_1"]
    report = validate_result(dumped)
    assert not report.ok
    assert any("envelope_exhaust_date_1" in e for e in report.errors), report.errors


def test_risk_conditional_worst_payment_risk_fact_required_when_present():
    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    assert result.payment_risks
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    dumped["facts"] = [f for f in dumped["facts"] if f["key"] != "payment_risk_due_1"]
    report = validate_result(dumped)
    assert not report.ok
    assert any("payment_risk_due_1" in e for e in report.errors), report.errors


def test_optimize_conditional_top_action_facts_required_when_ranked_present():
    mode = Mode.OPTIMIZE
    result = RESULT_BUILDERS[mode]()
    assert result.ranked
    engine_result = build_ok_result(mode, result)
    dumped = engine_result.model_dump(mode="json")
    dumped["facts"] = [f for f in dumped["facts"] if f["key"] != "top_action_delta"]
    report = validate_result(dumped)
    assert not report.ok
    assert any("top_action_delta" in e for e in report.errors), report.errors
