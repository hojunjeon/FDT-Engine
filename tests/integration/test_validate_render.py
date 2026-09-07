"""렌더 · validate 통합 테스트 (PLAN §5.4, §3 Phase 6, W13 소유).

전반부: 4 프로필 x 5 모드 = 20 개 `engine.run()` 결과를 실제로
`fdt.tools.render.render_result` 로 렌더해 PNG 파일이(존재하고 크기 > 0)
전부 만들어지는지 확인한다(§6.3 QA 렌더 체크리스트의 전제 조건).

후반부: 일부러 깨뜨린 viz(길이 불일치, facts 표기 밖 숫자를 담은 caption)를
`validate_result` 가 실제로 잡아내는지 확인한다(SPEC 14 R7, 리뷰 B9).
`tests/unit/test_facts.py::RESULT_BUILDERS`/`build_ok_result` 로 합성한
결과를 그대로 변형해 쓴다 - facts/viz 스키마 자체는 W11 소유이고 이 파일은
그 산출물을 깨뜨려서 검사기만 시험한다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fdt.engine import Engine
from fdt.engine.schemas.request import (
    ForecastParams,
    GoalParams,
    ModeRequest,
    OptimizeParams,
    RiskParams,
    WhatIfParams,
)
from fdt.engine.schemas.result import LineBandViz
from fdt.engine.taxonomy import ENVELOPE_IDS, Mode
from fdt.tools.render import render_result
from fdt.tools.validate import validate_result
from tests.unit.test_facts import RESULT_BUILDERS, build_ok_result

_N_PATHS = 200
_HORIZON = 30
_DINING = ENVELOPE_IDS["외식"]

_PROFILES = ("A_steady", "B_card_crunch", "C_impulsive", "D_goal_saver")


def _mode_requests() -> list[ModeRequest]:
    return [
        ModeRequest(
            mode=Mode.FORECAST, horizon_days=_HORIZON, n_paths=_N_PATHS, params=ForecastParams()
        ),
        ModeRequest(
            mode=Mode.WHATIF,
            horizon_days=_HORIZON,
            n_paths=_N_PATHS,
            params=WhatIfParams(
                injections=[
                    {
                        "type": "SPEND",
                        "days_from_now": 5,
                        "amount": 50_000,
                        "envelope_id": _DINING,
                        "method": "CARD",
                    }
                ]
            ),
        ),
        ModeRequest(
            mode=Mode.GOAL,
            horizon_days=_HORIZON,
            n_paths=_N_PATHS,
            params=GoalParams(goal_type="ENVELOPE_ADHERE"),
        ),
        ModeRequest(mode=Mode.RISK, horizon_days=_HORIZON, n_paths=_N_PATHS, params=RiskParams()),
        ModeRequest(
            mode=Mode.OPTIMIZE,
            horizon_days=_HORIZON,
            n_paths=_N_PATHS,
            params=OptimizeParams(objective="MIN_SHORTFALL_PROB"),
        ),
    ]


# ---------------------------------------------------------------------------
# 20 결과 렌더 -> PNG(크기 > 0)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile", _PROFILES)
def test_render_all_5_modes_produces_nonempty_png(
    profile: str, engines_3m: dict[str, Engine], tmp_path: Path
) -> None:
    engine = engines_3m[profile]
    out_dir = tmp_path / profile
    written_total = 0

    for req in _mode_requests():
        result = engine.run(req)
        assert result.status == "OK", (profile, req.mode, result.error)
        report = validate_result(result)
        assert report.ok, (profile, req.mode, report.errors)

        result_path = tmp_path / f"{profile}_{req.mode.value}.json"
        result_path.write_text(result.model_dump_json(), encoding="utf-8")

        written = render_result(result_path, out_dir)
        assert written, (profile, req.mode, "PNG 가 하나도 안 만들어졌다")
        for path in written:
            assert path.exists()
            assert path.stat().st_size > 0, (profile, req.mode, path)
        written_total += len(written)

    assert written_total > 0


# ---------------------------------------------------------------------------
# 잘못된 viz -> validate 가 잡는다
# ---------------------------------------------------------------------------


def test_validate_catches_line_band_length_mismatch() -> None:
    mode = Mode.FORECAST
    result_obj = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result_obj)

    line_band = next(v for v in engine_result.viz if isinstance(v, LineBandViz))
    # x 는 그대로 두고 band.lower 만 한 칸 짧게 만들어 길이 불일치를 만든다.
    line_band.data.band.lower = line_band.data.band.lower[:-1]

    report = validate_result(engine_result)
    assert not report.ok
    assert any("길이 불일치" in err for err in report.errors), report.errors


def test_validate_catches_caption_number_outside_facts() -> None:
    mode = Mode.RISK
    result_obj = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result_obj)

    victim = engine_result.viz[0]
    # facts 의 allowed_renderings 어디에도 없을 만큼 특이한 숫자를 caption 에 심는다.
    victim.caption = f"{victim.caption} 참고: 987654321원 초과 시 주의"

    report = validate_result(engine_result)
    assert not report.ok
    assert any("facts 표기 집합에 없다" in err for err in report.errors), report.errors
