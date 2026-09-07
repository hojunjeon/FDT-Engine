"""전체 파이프라인 통합 테스트 (PLAN §5.4, §3 Phase 6, W13 소유).

`gen(3개월) -> build -> run 5모드 -> validate` 가 4 프로필에서 끝나는지
확인한다. 프로그램적 경로(함수 직접 호출)와 CLI 경로(`typer.testing.
CliRunner`, `fdt.cli.app`) 양쪽을 모두 검사한다 - CLI 경로는 실제 사용자
워크플로(`fdt gen` -> `fdt build` -> `fdt run` -> `fdt validate`)를 그대로
재현한다.

숫자 자체(리스크 확률, 잔액 등)는 K1 이 동시에 `simulate.py`/`state.py` 를
고치는 중이라 계속 바뀔 수 있으므로 단정하지 않는다 - `validate_result` 가
OK 를 내는지, 파이프라인이 예외 없이 끝나는지만 본다(작업 지시 4항).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from fdt.cli import app
from fdt.engine import build_engine
from fdt.engine.schemas.request import (
    ForecastParams,
    GoalParams,
    ModeRequest,
    OptimizeParams,
    RiskParams,
    WhatIfParams,
)
from fdt.engine.taxonomy import ENVELOPE_IDS, Mode
from fdt.gen import PROFILE_NAMES, generate
from fdt.tools.engine_io import load_engine, save_engine
from fdt.tools.validate import validate_result

runner = CliRunner()

_SEED = 7
_MONTHS = 3
_N_PATHS = 200
_HORIZON = 30
_DINING = ENVELOPE_IDS["외식"]


def _mode_requests() -> list[ModeRequest]:
    """SPEC 8장 5 모드 각각 최소한으로 유효한 `ModeRequest` 1건씩."""

    return [
        ModeRequest(
            mode=Mode.FORECAST,
            horizon_days=_HORIZON,
            n_paths=_N_PATHS,
            seed=42,
            params=ForecastParams(),
        ),
        ModeRequest(
            mode=Mode.WHATIF,
            horizon_days=_HORIZON,
            n_paths=_N_PATHS,
            seed=42,
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
            seed=42,
            params=GoalParams(goal_type="ENVELOPE_ADHERE"),
        ),
        ModeRequest(
            mode=Mode.RISK,
            horizon_days=_HORIZON,
            n_paths=_N_PATHS,
            seed=42,
            params=RiskParams(),
        ),
        ModeRequest(
            mode=Mode.OPTIMIZE,
            horizon_days=_HORIZON,
            n_paths=_N_PATHS,
            seed=42,
            params=OptimizeParams(objective="MIN_SHORTFALL_PROB"),
        ),
    ]


# ---------------------------------------------------------------------------
# 프로그램적 경로
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_gen_build_run5_validate_in_memory(profile: str, tmp_path: Path) -> None:
    twin, _twin_raw, _ground_truth = generate(profile, seed=_SEED, months=_MONTHS)
    engine = build_engine(twin)

    for req in _mode_requests():
        result = engine.run(req)
        assert result.status == "OK", (profile, req.mode, result.error)
        report = validate_result(result)
        assert report.ok, (profile, req.mode, report.errors)


def test_save_load_engine_roundtrip_run_matches(tmp_path: Path) -> None:
    """`save_engine -> load_engine -> run` 이 원본 엔진의 `run` 과
    `strip_volatile()` 기준으로 동일한 결과를 낸다 (PLAN §5.4)."""

    twin, _twin_raw, _ground_truth = generate("A_steady", seed=_SEED, months=_MONTHS)
    engine = build_engine(twin)

    engine_path = tmp_path / "A_steady.engine.json"
    save_engine(engine, engine_path)
    loaded = load_engine(engine_path)

    for req in _mode_requests():
        original = engine.run(req)
        via_loaded = loaded.run(req)
        assert original.status == via_loaded.status == "OK", req.mode
        assert original.strip_volatile() == via_loaded.strip_volatile(), req.mode


# ---------------------------------------------------------------------------
# CLI 경로(1 프로필): gen -> build -> run x 5 -> validate
# ---------------------------------------------------------------------------


def test_cli_gen_build_run5_validate(tmp_path: Path) -> None:
    profile = "A_steady"

    gen_out = tmp_path / "seed"
    gen_result = runner.invoke(
        app,
        [
            "gen",
            "--profile",
            profile,
            "--seed",
            str(_SEED),
            "--months",
            str(_MONTHS),
            "--out",
            str(gen_out),
        ],
    )
    assert gen_result.exit_code == 0, gen_result.output

    twin_input_path = gen_out / f"{profile}_{_SEED}" / "twin_input.json"
    assert twin_input_path.exists()

    engine_path = tmp_path / f"{profile}.engine.json"
    build_result = runner.invoke(
        app,
        ["build", "--input", str(twin_input_path), "--out", str(engine_path)],
    )
    assert build_result.exit_code == 0, build_result.output
    assert engine_path.exists()

    mode_params: list[tuple[str, dict]] = [
        ("FORECAST", {}),
        (
            "WHATIF",
            {
                "injections": [
                    {
                        "type": "SPEND",
                        "days_from_now": 5,
                        "amount": 50_000,
                        "envelope_id": _DINING,
                        "method": "CARD",
                    }
                ]
            },
        ),
        ("GOAL", {"goal_type": "ENVELOPE_ADHERE"}),
        ("RISK", {}),
        ("OPTIMIZE", {"objective": "MIN_SHORTFALL_PROB"}),
    ]

    for mode, params in mode_params:
        result_path = tmp_path / f"{profile}_{mode}.json"
        run_result = runner.invoke(
            app,
            [
                "run",
                "--engine",
                str(engine_path),
                "--mode",
                mode,
                "--horizon",
                str(_HORIZON),
                "--n-paths",
                str(_N_PATHS),
                "--seed",
                "42",
                "--params",
                json.dumps(params, ensure_ascii=False),
                "--out",
                str(result_path),
                "--validate",
            ],
        )
        assert run_result.exit_code == 0, (mode, run_result.output)
        assert "validate: ok" in run_result.output, (mode, run_result.output)
        assert result_path.exists()

        validate_result_cmd = runner.invoke(
            app, ["validate", "--result", str(result_path)]
        )
        assert validate_result_cmd.exit_code == 0, (mode, validate_result_cmd.output)
        assert "OK" in validate_result_cmd.output
