"""`ModeRequest`/`EngineResult` 스키마 단위 테스트 (작업 ID W0-C).

SPEC 8장(모드 계약), 9장(출력 계약), 15.C(viz 예시)를 검증한다.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from fdt.engine.schemas.export import export_json_schemas
from fdt.engine.schemas.request import (
    BudgetChangeInjection,
    GoalParams,
    ModeRequest,
    OptimizeParams,
    RiskParams,
    SpendInjection,
    WhatIfParams,
)
from fdt.engine.schemas.result import (
    AccelerationAlert,
    ColumnSpec,
    ConcerningTxAlert,
    EngineError,
    EngineMeta,
    EngineResult,
    GaugeData,
    GaugeEncoding,
    GaugeViz,
    Health,
    PaymentRisk,
    RiskResult,
    TableData,
    TableViz,
)
from fdt.engine.taxonomy import Mode


# ---------------------------------------------------------------------------
# 공용 헬퍼
# ---------------------------------------------------------------------------


def _meta(mode: Mode, seed: int = 42, n_paths: int = 200, horizon_days: int = 30, elapsed_ms: int = 812) -> EngineMeta:
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
    req = ModeRequest(mode=Mode.FORECAST, params={"include_envelopes": True, "include_events": True})
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


def test_mode_params_mismatch_is_req_missing():
    with pytest.raises(ValueError, match="E-REQ-MISSING"):
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


def test_viz_encoding_with_color_key_fails():
    with pytest.raises(ValidationError):
        GaugeViz(
            id="risk",
            title="t",
            priority=1,
            data=GaugeData(value=1, level="SAFE"),
            encoding={"unit": "점", "color": "#ff0000"},
        )


def test_viz_table_row_with_color_key_fails():
    with pytest.raises(ValidationError):
        TableViz(
            id="t",
            title="t",
            priority=1,
            data=TableData(
                columns=[ColumnSpec(key="a", label="a")],
                rows=[{"a": 1, "color": "red"}],
            ),
        )


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


def test_engine_result_ok_requires_result():
    with pytest.raises(ValidationError):
        EngineResult(
            meta=_meta(Mode.RISK),
            request=_risk_request(),
            result=None,
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
