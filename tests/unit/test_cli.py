"""CLI 서브커맨드 단위 테스트 (SPEC 10장, PLAN 5.1 test_cli, W5 완료 조건).

`typer.testing.CliRunner` 로 `build` -> `inspect` -> `run`(미구현 모드라
ERROR 기대) 을 잇달아 실행해 종료 코드를 확인한다.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from fdt.cli import app

runner = CliRunner()

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SEED_TWIN_INPUT = _REPO_ROOT / "data" / "seed" / "A_steady_7" / "twin_input.json"


def test_build_then_inspect_then_run_error(tmp_path: Path) -> None:
    engine_path = tmp_path / "A.engine.json"

    build_result = runner.invoke(
        app,
        [
            "build",
            "--input",
            str(_SEED_TWIN_INPUT),
            "--out",
            str(engine_path),
        ],
    )
    assert build_result.exit_code == 0, build_result.output
    assert engine_path.exists()

    inspect_result = runner.invoke(app, ["inspect", "--engine", str(engine_path)])
    assert inspect_result.exit_code == 0, inspect_result.output
    assert "State" in inspect_result.output
    assert "Behavior" in inspect_result.output

    result_path = tmp_path / "A_forecast.json"
    run_result = runner.invoke(
        app,
        [
            "run",
            "--engine",
            str(engine_path),
            "--mode",
            "FORECAST",
            "--horizon",
            "30",
            "--n-paths",
            "200",
            "--seed",
            "42",
            "--out",
            str(result_path),
        ],
    )
    # 이번 단계는 모드 러너가 없어 status=ERROR 로 끝나야 하고, CLI 는 그 경우
    # 종료 코드 1 을 낸다(모드가 실제로 구현되면 이 기대치는 W7~W10 이 고친다).
    assert run_result.exit_code == 1, run_result.output
    assert "E-MODE-NOT_IMPLEMENTED" in run_result.output
    assert result_path.exists()

    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert result_payload["status"] == "ERROR"
    assert result_payload["error"]["code"] == "E-MODE-NOT_IMPLEMENTED"


def test_build_with_invalid_as_of_exits_one_with_req_range(tmp_path: Path) -> None:
    engine_path = tmp_path / "A.engine.json"

    result = runner.invoke(
        app,
        [
            "build",
            "--input",
            str(_SEED_TWIN_INPUT),
            "--out",
            str(engine_path),
            "--as-of",
            "not-a-date",
        ],
    )

    assert result.exit_code == 1
    assert "E-REQ-RANGE" in result.output
    assert not engine_path.exists()


def test_run_missing_mode_exits_two(tmp_path: Path) -> None:
    engine_path = tmp_path / "A.engine.json"
    build_result = runner.invoke(
        app,
        ["build", "--input", str(_SEED_TWIN_INPUT), "--out", str(engine_path)],
    )
    assert build_result.exit_code == 0, build_result.output

    result_path = tmp_path / "out.json"
    result = runner.invoke(
        app,
        ["run", "--engine", str(engine_path), "--horizon", "30", "--out", str(result_path)],
    )

    assert result.exit_code == 2
    assert not result_path.exists()


def test_inspect_output_is_utf8_and_contains_korean(tmp_path: Path) -> None:
    engine_path = tmp_path / "A.engine.json"
    build_result = runner.invoke(
        app,
        ["build", "--input", str(_SEED_TWIN_INPUT), "--out", str(engine_path)],
    )
    assert build_result.exit_code == 0, build_result.output

    result = runner.invoke(app, ["inspect", "--engine", str(engine_path)])
    assert result.exit_code == 0
    assert "봉투" in result.output
    assert "유동성" in result.output


def test_build_missing_input_file_reports_error(tmp_path: Path) -> None:
    engine_path = tmp_path / "A.engine.json"
    result = runner.invoke(
        app,
        [
            "build",
            "--input",
            str(tmp_path / "does_not_exist.json"),
            "--out",
            str(engine_path),
        ],
    )
    assert result.exit_code != 0
