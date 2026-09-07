"""`fdt/tools/render.py` 단위 테스트 (작업 ID J4, SPEC 9.3, 10장, §6.3).

합성 result(=`test_facts.py` 의 빌더 재사용) 로 8종 viz kind 가 전부 PNG
한 장씩(파일 크기 > 0)으로 그려지는지, 그리고 4 프로필(엔진 fixture) x 5
모드 = 20 결과를 실제로 `engine.run()` 해 렌더한 PNG 도 전부 만들어지는지
검사한다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fdt.engine.engine import Engine
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.taxonomy import Mode
from fdt.tools.render import render_result, render_viz
from tests.unit.test_facts import AS_OF, RESULT_BUILDERS, build_ok_result

ALL_VIZ_KINDS = {
    "line_band",
    "event_timeline",
    "gauge",
    "progress_bars",
    "delta_bars",
    "step_bars",
    "ranked_bars",
    "table",
}


@pytest.mark.parametrize("mode", list(Mode))
def test_render_viz_writes_nonempty_png_for_every_kind(mode: Mode, tmp_path: Path) -> None:
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    seen_kinds = set()
    for v in engine_result.viz:
        out_path = render_viz(v, tmp_path)
        assert out_path.exists()
        assert out_path.stat().st_size > 0, f"{mode}:{v.id} PNG 가 비어 있다"
        seen_kinds.add(v.kind)
    assert seen_kinds  # 최소 한 종류는 그려졌다


def test_all_eight_viz_kinds_render_across_modes(tmp_path: Path) -> None:
    """5 모드를 합치면 SPEC 9.3 의 8종 kind 가 전부 등장하고, 전부 렌더된다."""

    seen_kinds: set[str] = set()
    for mode in Mode:
        result = RESULT_BUILDERS[mode]()
        engine_result = build_ok_result(mode, result)
        for v in engine_result.viz:
            out_path = render_viz(v, tmp_path)
            assert out_path.stat().st_size > 0
            seen_kinds.add(v.kind)
    assert seen_kinds == ALL_VIZ_KINDS, seen_kinds


def test_render_result_from_json_file(tmp_path: Path) -> None:
    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    result_path = tmp_path / "result.json"
    result_path.write_text(engine_result.model_dump_json(), encoding="utf-8")

    out_dir = tmp_path / "png"
    written = render_result(result_path, out_dir)

    assert written, "RISK 결과에 viz 가 있는데 PNG 가 하나도 안 만들어졌다"
    for path in written:
        assert path.exists()
        assert path.stat().st_size > 0


def test_render_result_error_status_writes_nothing(tmp_path: Path) -> None:
    dumped: dict[str, object] = {
        "schema_version": "engine-result/1",
        "meta": {
            "engine_id": "a3f9c1d2e4b5",
            "as_of": AS_OF.isoformat(),
            "mode": "FORECAST",
            "seed": 42,
            "n_paths": 200,
            "horizon_days": 30,
            "elapsed_ms": 10,
            "engine_version": "0.1.0",
            "warnings": [],
        },
        "request": {
            "mode": "FORECAST",
            "horizon_days": 30,
            "n_paths": 200,
            "seed": 42,
            "params": {},
        },
        "result": None,
        "facts": [],
        "viz": [],
        "status": "ERROR",
        "error": {"code": "E-TEST", "message": "테스트 오류", "details": {}},
    }
    result_path = tmp_path / "error.json"
    import json

    result_path.write_text(json.dumps(dumped, ensure_ascii=False), encoding="utf-8")

    written = render_result(result_path, tmp_path / "png")
    assert written == []


# ---------------------------------------------------------------------------
# 엔진 fixture(4 프로필) x 5 모드 = 20 결과 렌더
# ---------------------------------------------------------------------------


def _request_for(mode: Mode) -> ModeRequest:
    params: dict[str, object]
    if mode is Mode.WHATIF:
        params = {
            "injections": [
                {
                    "type": "SPEND",
                    "days_from_now": 1,
                    "amount": 150000,
                    "envelope_id": 5,
                    "method": "CARD",
                }
            ]
        }
    elif mode is Mode.GOAL:
        params = {
            "goal_type": "BALANCE",
            "target_amount": 2_000_000,
            "target_date": "2026-12-31",
        }
    elif mode is Mode.OPTIMIZE:
        params = {"objective": "MIN_SHORTFALL_PROB"}
    else:
        params = {}
    return ModeRequest(
        mode=mode, horizon_days=30, n_paths=200, seed=42, params=params  # type: ignore[arg-type]
    )


def test_render_20_results_from_engine_fixtures(
    engines_3m: dict[str, Engine], tmp_path: Path
) -> None:
    """4 프로필 x 5 모드 = 20 결과를 실제로 `engine.run()` 해 렌더한다.

    PLAN Phase 6 완료 조건 "렌더 20 세트 PNG 생성" 을 3개월 fixture 규모로
    확인한다(6개월 골든 세트는 통합 테스트가 별도로 다룬다).
    """

    total_png = 0
    for name, engine in engines_3m.items():
        for mode in Mode:
            req = _request_for(mode)
            result = engine.run(req)
            assert result.status == "OK", (name, mode, result.error)
            out_dir = tmp_path / name / mode.value
            written = render_result_from_engine_result(result, out_dir)
            assert written, f"{name}:{mode} 결과에서 PNG 가 하나도 안 만들어졌다"
            for path in written:
                assert path.stat().st_size > 0
            total_png += len(written)
    assert total_png > 0


def render_result_from_engine_result(result, out_dir: Path):
    from fdt.tools.render import render_viz

    out_dir.mkdir(parents=True, exist_ok=True)
    return [render_viz(v, out_dir) for v in result.viz]
