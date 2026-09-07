"""`ModeRequest`/`EngineResult` 스키마 단위 테스트 (작업 ID W0-C).

SPEC 8장(모드 계약), 9장(출력 계약), 15.C(viz 예시)를 검증한다.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from fdt.engine.schemas.request import (
    BudgetChangeInjection,
    FixedChangeInjection,
    GoalParams,
    ModeRequest,
    OptimizeParams,
    RiskParams,
    SpendInjection,
    WhatIfParams,
)
from fdt.engine.schemas.result import (
    AccelerationAlert,
    AppliedAction,
    BranchSummary,
    ColumnSpec,
    ConcerningTxAlert,
    DeltaBarsData,
    DeltaBarsViz,
    DeltaItem,
    EngineError,
    EngineMeta,
    EngineResult,
    EventPoint,
    EventTimelineData,
    EventTimelineViz,
    FirstShortfallDate,
    ForecastResult,
    GaugeData,
    GaugeEncoding,
    GaugeViz,
    Health,
    OptimizeBaseline,
    OptimizeResult,
    OverrideSpec,
    PaymentRisk,
    PointStat,
    RankedAction,
    RiskResult,
    TableData,
    TableViz,
    TrajectorySummary,
    WhatIfDelta,
    WhatIfResult,
)
from fdt.engine.taxonomy import Mode
from fdt.tools.schema_export import export_json_schemas

# ---------------------------------------------------------------------------
# 공용 헬퍼
# ---------------------------------------------------------------------------


def _meta(
    mode: Mode,
    seed: int = 42,
    n_paths: int = 200,
    horizon_days: int = 30,
    elapsed_ms: int = 812,
) -> EngineMeta:
    return EngineMeta(
        engine_id="a3f9c1d2e4b5",
        as_of=date(2026, 9, 7),
        mode=mode,
        seed=seed,
        n_paths=n_paths,
        horizon_days=horizon_days,
        elapsed_ms=elapsed_ms,
        engine_version="0.1.0",
        warnings=[],
    )


def _dates(n: int) -> list[date]:
    return [date(2026, 9, 7 + i) for i in range(n)]


# ---------------------------------------------------------------------------
# 1. 5 모드 유효 요청 왕복
# ---------------------------------------------------------------------------


def test_forecast_request_roundtrip():
    req = ModeRequest(
        mode=Mode.FORECAST,
        params={"include_envelopes": True, "include_events": True},
    )
    dumped = req.model_dump(mode="json")
    again = ModeRequest.model_validate(dumped)
    assert again == req
    assert req.horizon_days == 30 and req.n_paths == 1000 and req.seed == 42


def test_whatif_request_roundtrip():
    req = ModeRequest(
        mode=Mode.WHATIF,
        params={
            "injections": [
                {
                    "type": "SPEND",
                    "days_from_now": 3,
                    "amount": 150000,
                    "envelope_id": 5,
                    "method": "CARD",
                }
            ]
        },
    )
    dumped = req.model_dump(mode="json")
    again = ModeRequest.model_validate(dumped)
    assert again == req
    assert isinstance(req.params, WhatIfParams)
    assert isinstance(req.params.injections[0], SpendInjection)


def test_goal_request_roundtrip():
    req = ModeRequest(
        mode=Mode.GOAL,
        params={
            "goal_type": "BALANCE",
            "target_amount": 2000000,
            "target_date": "2026-12-31",
            "protect_essential": True,
        },
    )
    dumped = req.model_dump(mode="json")
    again = ModeRequest.model_validate(dumped)
    assert again == req


def test_risk_request_roundtrip():
    req = ModeRequest(mode=Mode.RISK, params={"recent_tx_ids": [1001, 1002]})
    dumped = req.model_dump(mode="json")
    again = ModeRequest.model_validate(dumped)
    assert again == req
    assert isinstance(req.params, RiskParams)


def test_optimize_request_roundtrip():
    req = ModeRequest(
        mode=Mode.OPTIMIZE,
        params={
            "objective": "MIN_SHORTFALL_PROB",
            "candidates": "AUTO",
            "max_actions": 3,
            "constraints": {
                "protect_essential": True,
                "max_cut_ratio": 0.5,
                "allow_emergency_draw": False,
            },
        },
    )
    dumped = req.model_dump(mode="json")
    again = ModeRequest.model_validate(dumped)
    assert again == req
    assert isinstance(req.params, OptimizeParams)


def test_optimize_reach_goal_requires_goal():
    with pytest.raises(ValueError, match="E-REQ-MISSING"):
        ModeRequest(
            mode=Mode.OPTIMIZE,
            params={"objective": "REACH_GOAL", "candidates": "AUTO"},
        )


# ---------------------------------------------------------------------------
# 2. 오류 케이스
# ---------------------------------------------------------------------------


def test_mode_params_mismatch_is_rejected():
    # B2: mode 로 params 클래스를 먼저 확정해 파싱하므로, WHATIF 모양의 params 를
    # FORECAST 에 보내면 ForecastParams 자체의 검증(미지 필드 금지)으로 즉시 실패한다.
    with pytest.raises(ValidationError):
        ModeRequest(
            mode=Mode.FORECAST,
            params={
                "injections": [
                    {
                        "type": "SPEND",
                        "days_from_now": 1,
                        "amount": 1000,
                        "envelope_id": 1,
                        "method": "CARD",
                    }
                ]
            },
        )


def test_risk_empty_params_dict_parses_as_risk_params():
    # B2 위반 1 회귀: {"mode":"RISK","params":{}} 는 유효한 요청이다
    # (recent_tx_ids 는 선택 필드, 비면 as_of 당일 SPEND 전부 - SPEC 8.5).
    req = ModeRequest(mode=Mode.RISK, params={})
    assert isinstance(req.params, RiskParams)
    assert req.params.recent_tx_ids == []


def test_whatif_empty_params_dict_is_req_missing_injections():
    # B2 위반 2 회귀: {"mode":"WHATIF","params":{}} 는 injections 누락으로
    # E-REQ-MISSING 이어야 한다(엉뚱한 타입 메시지가 아니라).
    with pytest.raises(ValueError, match="E-REQ-MISSING"):
        ModeRequest(mode=Mode.WHATIF, params={})


def test_horizon_out_of_range_is_req_range():
    with pytest.raises(ValueError, match="E-REQ-RANGE"):
        ModeRequest(
            mode=Mode.FORECAST,
            horizon_days=400,
            params={"include_envelopes": True, "include_events": True},
        )


def test_goal_missing_target_date_is_req_missing():
    with pytest.raises(ValueError, match="E-REQ-MISSING"):
        GoalParams(goal_type="BALANCE", target_amount=2000000)


def test_goal_envelope_adhere_forbids_targets():
    with pytest.raises(ValueError, match="E-REQ-MISSING"):
        GoalParams(goal_type="ENVELOPE_ADHERE", target_amount=1)


def test_spend_injection_card_id_optional_defaults_none():
    # N4: `method=CARD` 가 항상 첫 카드로 가던 문제 - `card_id` 로 특정
    # 카드를 지정할 수 있다(생략하면 기존 동작대로 None, simulate.py 가
    # 하위 호환으로 처리한다, J1 소유).
    without = SpendInjection(days_from_now=1, amount=1000, envelope_id=1, method="CARD")
    assert without.card_id is None

    with_card = SpendInjection(
        days_from_now=1, amount=1000, envelope_id=1, method="CARD", card_id=21
    )
    assert with_card.card_id == 21
    dumped = with_card.model_dump(mode="json")
    again = SpendInjection.model_validate(dumped)
    assert again == with_card


def test_spend_injection_both_on_and_days_from_now_fails():
    with pytest.raises(ValueError, match="E-REQ-MISSING"):
        SpendInjection(
            on=date(2026, 9, 10),
            days_from_now=3,
            amount=1000,
            envelope_id=1,
            method="CARD",
        )


def test_spend_injection_neither_on_nor_days_from_now_fails():
    with pytest.raises(ValueError, match="E-REQ-MISSING"):
        SpendInjection(amount=1000, envelope_id=1, method="CARD")


def test_amount_over_limit_is_req_range():
    with pytest.raises(ValueError, match="E-REQ-RANGE"):
        SpendInjection(
            days_from_now=1,
            amount=1_000_000_000_001,
            envelope_id=1,
            method="CARD",
        )


def test_budget_change_amount_over_limit_is_req_range():
    with pytest.raises(ValueError, match="E-REQ-RANGE"):
        BudgetChangeInjection(envelope_id=1, new_budget=2_000_000_000_000)


def test_fixed_change_missing_from_is_req_missing():
    # B3: `from`(적용 시작일)이 빠지면 기본값(None)으로 조용히 통과하지 않고
    # E-REQ-MISSING 이어야 한다 (SPEC 8.3 표 `FIXED_CHANGE.from`).
    with pytest.raises(ValueError, match="E-REQ-MISSING"):
        FixedChangeInjection(fixed_expense_id=40, new_amount=500000)


def test_fixed_change_with_from_succeeds():
    inj = FixedChangeInjection(fixed_expense_id=40, new_amount=500000, **{"from": "2026-10-01"})
    assert inj.from_ == date(2026, 10, 1)


# ---------------------------------------------------------------------------
# 3. SPEC 15.C viz 예시
# ---------------------------------------------------------------------------


def test_viz_gauge_example_from_spec_15c():
    viz = GaugeViz(
        id="risk",
        title="30일 결제 부족 위험",
        priority=1,
        data=GaugeData(value=37, min=0, max=100, thresholds=[20, 50], level="WARNING"),
        encoding=GaugeEncoding(unit="점"),
        caption="위험 점수 37점, 주의 단계.",
    )
    assert viz.kind == "gauge"
    assert viz.data.value == 37


def test_viz_table_example_from_spec_15c():
    viz = TableViz(
        id="payments",
        title="결제일별 부족 확률",
        priority=1,
        data=TableData(
            columns=[
                ColumnSpec(key="due", label="결제일", unit="date"),
                ColumnSpec(key="name", label="항목"),
                ColumnSpec(key="amount", label="금액", unit="KRW"),
                ColumnSpec(key="fail_prob", label="부족 확률", unit="%"),
            ],
            rows=[
                {
                    "due": "2026-09-16",
                    "name": "KB 체크 카드대금",
                    "amount": 175000,
                    "fail_prob": 35,
                }
            ],
        ),
        annotations=[{"type": "point", "x": "2026-09-16", "label": "가장 위험한 결제일"}],
        caption="9월 16일 카드대금 17만 5천원의 부족 확률이 35%로 가장 높다.",
    )
    assert viz.kind == "table"
    assert viz.data.rows[0]["amount"] == 175000


def test_event_timeline_encoding_color_is_fail_prob():
    # B4: SPEC 9.3 표는 event_timeline encoding 필드명을 `color` 로 못박는다.
    viz = EventTimelineViz(
        id="events",
        title="결제·수입 이벤트",
        priority=1,
        data=EventTimelineData(
            events=[
                EventPoint(
                    date=date(2026, 9, 9),
                    kind="CARD_BILL",
                    name="KB 체크",
                    amount=183500,
                    fail_prob=0.02,
                )
            ]
        ),
    )
    assert viz.encoding.color == "fail_prob"


def test_delta_bars_encoding_with_hex_color_value_fails():
    # B4: 키 검사가 아니라 값 검사. 렌더러 종속 색상 코드는 어느 키에 있든 거부한다.
    with pytest.raises(ValidationError):
        DeltaBarsViz(
            id="d",
            title="t",
            priority=1,
            data=DeltaBarsData(items=[DeltaItem(name="a", base=1, branch=2, delta=1, unit="KRW")]),
            encoding={"stroke": "#ff0000"},
        )


def test_viz_caption_mentioning_library_name_fails():
    with pytest.raises(ValidationError):
        GaugeViz(
            id="risk",
            title="t",
            priority=1,
            data=GaugeData(value=1, level="SAFE"),
            encoding=GaugeEncoding(unit="점"),
            caption="matplotlib 으로 렌더",
        )


def test_viz_encoding_with_color_key_fails():
    with pytest.raises(ValidationError):
        GaugeViz(
            id="risk",
            title="t",
            priority=1,
            data=GaugeData(value=1, level="SAFE"),
            encoding={"unit": "점", "color": "#ff0000"},
        )


def test_viz_table_row_with_hex_color_value_fails():
    # B4: 키 이름이 아니라 값(hex 색상 코드)이 렌더러 종속이라 거부된다.
    with pytest.raises(ValidationError):
        TableViz(
            id="t",
            title="t",
            priority=1,
            data=TableData(
                columns=[ColumnSpec(key="a", label="a")],
                rows=[{"a": 1, "stroke": "#ff0000"}],
            ),
        )


def test_ranked_action_wraps_injection_with_cut_ratio():
    # S9: RankedAction.actions 의 원소는 list[dict] 가 아니라
    # AppliedAction(injection: Injection, cut_ratio?, label?) 이다.
    action = RankedAction(
        rank=1,
        actions=[
            AppliedAction(
                injection={
                    "type": "BUDGET_CHANGE",
                    "envelope_id": 5,
                    "new_budget": 280000,
                },
                cut_ratio=0.3,
            )
        ],
        effect={"shortfall_prob": 0.12, "delta": -0.19, "end_balance_median": 1010000},
        feasibility_note="이번 달 이미 사용 21만원, 남은 한도 7만원",
    )
    assert isinstance(action.actions[0].injection, BudgetChangeInjection)
    assert action.actions[0].cut_ratio == 0.3

    dumped = action.model_dump(mode="json")
    again = RankedAction.model_validate(dumped)
    assert again == action


def test_applied_action_wraps_override_instead_of_injection():
    # S57: `AppliedAction` 은 §8.6.1 4번째 AUTO 후보(카드 출금 요일 변경)를
    # `injection` 대신 `override`(신규 `OverrideSpec`)로 담을 수 있다.
    action = AppliedAction(
        override=OverrideSpec(card_id=20, weekday=5),
        label="카드 20 출금 요일을 토요일로 변경",
    )
    assert action.injection is None
    assert isinstance(action.override, OverrideSpec)
    assert action.override.type == "CARD_WITHDRAWAL_WEEKDAY"

    dumped = action.model_dump(mode="json")
    again = AppliedAction.model_validate(dumped)
    assert again == action


def test_applied_action_requires_exactly_one_of_injection_or_override():
    with pytest.raises(ValidationError, match="정확히 하나"):
        AppliedAction()  # 둘 다 없음

    with pytest.raises(ValidationError, match="정확히 하나"):
        AppliedAction(
            injection={
                "type": "BUDGET_CHANGE",
                "envelope_id": 5,
                "new_budget": 280000,
            },
            override=OverrideSpec(card_id=20, weekday=5),
        )  # 둘 다 있음


def test_override_spec_weekday_out_of_range_rejected():
    with pytest.raises(ValidationError):
        OverrideSpec(card_id=20, weekday=7)


def _optimize_baseline() -> OptimizeBaseline:
    return OptimizeBaseline(
        shortfall_prob=0.31, card_shortfall_prob=0.37, end_balance_median=780000
    )


def test_optimize_result_notes_and_n_paths_used_roundtrip():
    # N11: 후보 0개 -> ranked=[], notes 에 이유. N14: 실제로 시뮬을 돌린
    # n_paths(하향값 포함)를 결과 자체에 싣는다.
    result = OptimizeResult(
        objective="MIN_SHORTFALL_PROB",
        baseline=_optimize_baseline(),
        ranked=[],
        recommended=None,
        evaluated=0,
        sim_calls=1,
        notes=["적용 가능한 후보가 없다"],
        n_paths_used=400,
    )
    assert result.notes == ["적용 가능한 후보가 없다"]
    assert result.n_paths_used == 400

    dumped = result.model_dump(mode="json")
    again = OptimizeResult.model_validate(dumped)
    assert again == result


def test_optimize_result_notes_defaults_empty():
    result = OptimizeResult(
        objective="MIN_SHORTFALL_PROB",
        baseline=_optimize_baseline(),
        ranked=[],
        recommended=None,
        evaluated=0,
        sim_calls=1,
        n_paths_used=1000,
    )
    assert result.notes == []


def test_whatif_result_branch_level_optional_roundtrip():
    # J2 용: RISK.health.level 과 같은 3단 등급. 옵션이라 생략하면 None.
    summary = BranchSummary(
        trajectory=TrajectorySummary(median=[1.0], p10=[1.0], p90=[1.0]),
        min_point=PointStat(date=date(2026, 9, 10), median_balance=100),
        end_point=PointStat(date=date(2026, 9, 10), median_balance=100),
        shortfall_prob=0.1,
        card_shortfall_prob=0.1,
    )
    delta = WhatIfDelta(
        min_balance=0,
        end_balance=0,
        shortfall_prob=0.0,
        card_shortfall_prob=0.0,
        first_shortfall_date=FirstShortfallDate(),
    )
    without = WhatIfResult(base=summary, branch=summary, delta=delta, verdict="OK")
    assert without.branch_level is None

    with_level = WhatIfResult(
        base=summary, branch=summary, delta=delta, verdict="CAUTION", branch_level="WARNING"
    )
    assert with_level.branch_level == "WARNING"
    dumped = with_level.model_dump(mode="json")
    again = WhatIfResult.model_validate(dumped)
    assert again == with_level


# ---------------------------------------------------------------------------
# 4. EngineResult OK/ERROR, strip_volatile, fact_renderings
# ---------------------------------------------------------------------------


def _risk_request() -> ModeRequest:
    return ModeRequest(mode=Mode.RISK, n_paths=200, params={"recent_tx_ids": []})


def _risk_result() -> RiskResult:
    return RiskResult(
        risk_score=37,
        level="WARNING",
        shortfall_prob=0.31,
        card_shortfall_prob=0.37,
        worst_day=date(2026, 9, 16),
        expected_shortfall=142000,
        payment_risks=[
            PaymentRisk(
                due=date(2026, 9, 16),
                kind="CARD_BILL",
                name="KB 체크",
                amount=175000,
                fail_prob=0.35,
                median_balance_before=161000,
            )
        ],
        alerts=[
            AccelerationAlert(severity="WARNING", ratio=1.42),
            ConcerningTxAlert(
                severity="DANGER",
                tx_id=1001,
                amount=250000,
                envelope_id=5,
                remaining_before=200000,
                threshold=100000,
            ),
        ],
        safe_to_spend_today=19100,
        health=Health(score=58, level="WARNING", coverage=0.61, adherence=0.72, risk=0.63),
    )


def _forecast_result() -> ForecastResult:
    dates = _dates(2)
    return ForecastResult(
        trajectory={
            "dates": dates,
            "median": [1.0, 2.0],
            "p10": [0.0, 1.0],
            "p90": [2.0, 3.0],
            "mean": [1.0, 2.0],
        },
        economic={"median": [1.0, 2.0], "p10": [0.0, 1.0], "p90": [2.0, 3.0]},
        min_point={"date": dates[0], "median_balance": 118000},
        end_point={"date": dates[1], "median_balance": 2013000},
        shortfall_prob=0.09,
        card_shortfall_prob=0.04,
    )


def test_engine_result_ok_requires_result():
    with pytest.raises(ValidationError):
        EngineResult(
            meta=_meta(Mode.RISK),
            request=_risk_request(),
            result=None,
            status="OK",
        )


def test_engine_result_mode_result_type_mismatch_is_rejected():
    # N4: meta.mode=RISK 인데 result 가 ForecastResult 인 조합은 거부돼야 한다.
    with pytest.raises(ValidationError):
        EngineResult(
            meta=_meta(Mode.RISK),
            request=_risk_request(),
            result=_forecast_result(),
            status="OK",
        )


def test_engine_result_error_requires_error_and_no_result():
    with pytest.raises(ValidationError):
        EngineResult(
            meta=_meta(Mode.RISK),
            request=_risk_request(),
            result=_risk_result(),
            status="ERROR",
            error=EngineError(code="E-REQ-RANGE", message="x"),
        )

    ok_error = EngineResult(
        meta=_meta(Mode.RISK),
        request=_risk_request(),
        result=None,
        status="ERROR",
        error=EngineError(code="E-REQ-RANGE", message="x"),
    )
    assert ok_error.status == "ERROR"
    assert ok_error.result is None


def test_engine_result_ok_roundtrip_and_strip_volatile():
    facts = [
        {
            "key": "risk_score",
            "label": "위험 점수",
            "value": 37,
            "unit": "점",
            "precision": 0,
            "allowed_renderings": ["37", "37점"],
            "importance": 1,
            "hint": "level=WARNING",
        },
        {
            "key": "safe_to_spend_today",
            "label": "오늘 안심 소비 한도",
            "value": 19100,
            "unit": "KRW",
            "precision": -2,
            "allowed_renderings": ["19,100원", "1만 9천원", "1.9만원", "약 2만원"],
            "importance": 1,
        },
    ]
    viz = [
        {
            "kind": "gauge",
            "id": "risk",
            "title": "30일 결제 부족 위험",
            "priority": 1,
            "data": {"value": 37, "min": 0, "max": 100, "thresholds": [20, 50], "level": "WARNING"},
            "encoding": {"unit": "점"},
            "caption": "위험 점수 37점, 주의 단계.",
        }
    ]
    result = EngineResult(
        meta=_meta(Mode.RISK),
        request=_risk_request(),
        result=_risk_result(),
        facts=facts,
        viz=viz,
        status="OK",
    )

    dumped = result.model_dump(mode="json")
    again = EngineResult.model_validate(dumped)
    assert again == result

    stripped = result.strip_volatile()
    assert "elapsed_ms" not in stripped["meta"]

    # elapsed_ms 만 다른 결과는 strip_volatile 이후 동일해야 한다(재현성 비교).
    result2 = result.model_copy(update={"meta": _meta(Mode.RISK, elapsed_ms=999)})
    assert result.strip_volatile() == result2.strip_volatile()

    renderings = result.fact_renderings()
    assert renderings == {
        "37",
        "37점",
        "19,100원",
        "1만 9천원",
        "1.9만원",
        "약 2만원",
    }


# ---------------------------------------------------------------------------
# 5. export_json_schemas
# ---------------------------------------------------------------------------


def test_export_json_schemas_writes_valid_json(tmp_path: Path):
    out_dir = tmp_path / "schemas"
    written = export_json_schemas(out_dir)

    assert written, "적어도 한 개 이상의 스키마 파일이 써져야 한다"
    names = {p.name for p in written}
    assert "ModeRequest.schema.json" in names
    assert "EngineResult.schema.json" in names

    for path in written:
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert "$defs" in data or "properties" in data
