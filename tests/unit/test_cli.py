"""CLI 서브커맨드 단위 테스트 (SPEC 10장, PLAN 5.1 test_cli, W5 완료 조건).

`typer.testing.CliRunner` 로 `build` -> `inspect` -> `run`(미구현 모드라
ERROR 기대) 을 잇달아 실행해 종료 코드를 확인한다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from fdt.cli import app

runner = CliRunner()

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SEED_TWIN_INPUT = _REPO_ROOT / "data" / "seed" / "A_steady_7" / "twin_input.json"


def test_build_then_inspect_then_run_forecast_ok(tmp_path: Path) -> None:
    """W7 재개: FORECAST 러너가 등록됐으므로 `fdt run` 이 OK 로 끝난다
    (이전엔 모드 러너가 하나도 없어 E-MODE-NOT_IMPLEMENTED 를 기대했다)."""

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
            "--validate",
        ],
    )
    assert run_result.exit_code == 0, run_result.output
    assert result_path.exists()

    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert result_payload["status"] == "OK"
    assert result_payload["facts"], "FORECAST 결과에 facts 가 비어 있다"
    assert result_payload["viz"], "FORECAST 결과에 viz 가 비어 있다"


def test_run_error_mode_still_exits_one_and_writes_error_json(tmp_path: Path) -> None:
    """아직 등록 안 된 모드(GOAL/OPTIMIZE)는 여전히 E-MODE-NOT_IMPLEMENTED,
    종료 코드 1 이어야 한다 - `run` 이 FORECAST/RISK/WHATIF 를 구현했다고
    이 경로 자체가 사라지면 안 된다."""

    engine_path = tmp_path / "A.engine.json"
    build_result = runner.invoke(
        app, ["build", "--input", str(_SEED_TWIN_INPUT), "--out", str(engine_path)]
    )
    assert build_result.exit_code == 0, build_result.output

    from fdt.engine.modes import MODE_RUNNERS, load_all
    from fdt.engine.taxonomy import Mode

    load_all()
    not_yet_implemented = [m for m in Mode if m not in MODE_RUNNERS]
    if not not_yet_implemented:
        pytest.skip("다섯 모드가 전부 등록됐다(다른 작업자 완료) - 이 케이스는 검증할 게 없다")
    mode = not_yet_implemented[0]

    # `E-MODE-NOT_IMPLEMENTED` 는 `ModeRequest` 자체가 파싱된 뒤(모드별
    # params 검증을 통과한 뒤)에야 도달하는 코드다 - GOAL/OPTIMIZE 는 필수
    # params 가 있어(§8.4/8.6) 최소한의 유효 params 를 채워 넣어야 그
    # 경로(러너 미등록)를 실제로 검증할 수 있다.
    default_params: dict[str, str] = {
        "GOAL": '{"goal_type":"ENVELOPE_ADHERE"}',
        "OPTIMIZE": '{"objective":"MIN_SHORTFALL_PROB"}',
    }
    params_json = default_params.get(mode.value, "{}")

    result_path = tmp_path / "err.json"
    run_result = runner.invoke(
        app,
        [
            "run",
            "--engine",
            str(engine_path),
            "--mode",
            mode.value,
            "--params",
            params_json,
            "--out",
            str(result_path),
        ],
    )
    assert run_result.exit_code == 1, run_result.output
    assert "E-MODE-NOT_IMPLEMENTED" in run_result.output

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
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["status"] == "ERROR"
    assert payload["error"]["code"]
    assert not engine_path.exists()


def _build_engine(tmp_path: Path) -> Path:
    engine_path = tmp_path / "A.engine.json"
    build_result = runner.invoke(
        app,
        ["build", "--input", str(_SEED_TWIN_INPUT), "--out", str(engine_path)],
    )
    assert build_result.exit_code == 0, build_result.output
    return engine_path


def test_run_invalid_params_json_exits_one_with_req_invalid(tmp_path: Path) -> None:
    engine_path = _build_engine(tmp_path)
    result_path = tmp_path / "out.json"

    result = runner.invoke(
        app,
        [
            "run",
            "--engine",
            str(engine_path),
            "--mode",
            "FORECAST",
            "--params",
            "{oops",
            "--out",
            str(result_path),
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "ERROR"
    assert payload["error"]["code"] == "E-REQ-INVALID"
    assert not result_path.exists()


def test_run_missing_params_file_exits_one(tmp_path: Path) -> None:
    engine_path = _build_engine(tmp_path)
    result_path = tmp_path / "out.json"

    result = runner.invoke(
        app,
        [
            "run",
            "--engine",
            str(engine_path),
            "--mode",
            "FORECAST",
            "--params-file",
            str(tmp_path / "does_not_exist.json"),
            "--out",
            str(result_path),
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "ERROR"
    assert not result_path.exists()


def test_build_input_schema_violation_exits_one_with_input_ref(tmp_path: Path) -> None:
    twin = json.loads(_SEED_TWIN_INPUT.read_text(encoding="utf-8"))
    # 카드가 참조하는 계좌를 지워 E-INPUT-REF 를 유발한다.
    referenced_account_ids = {c["withdrawal_account_id"] for c in twin["cards"]}
    twin["accounts"] = [a for a in twin["accounts"] if a["id"] not in referenced_account_ids]

    broken_input = tmp_path / "broken_twin_input.json"
    broken_input.write_text(json.dumps(twin, ensure_ascii=False), encoding="utf-8")

    engine_path = tmp_path / "A.engine.json"
    result = runner.invoke(
        app,
        ["build", "--input", str(broken_input), "--out", str(engine_path)],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "ERROR"
    assert payload["error"]["code"] == "E-INPUT-REF"
    assert not engine_path.exists()


def test_run_goal_mode_missing_params_exits_one_with_req_missing(tmp_path: Path) -> None:
    engine_path = _build_engine(tmp_path)
    result_path = tmp_path / "out.json"

    result = runner.invoke(
        app,
        [
            "run",
            "--engine",
            str(engine_path),
            "--mode",
            "GOAL",
            "--out",
            str(result_path),
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "ERROR"
    # 정규식 코드 추출 없이, ModeRequest 검증기가 던진 FdtError 를 그대로
    # extract_errors() 로 복원한 코드여야 한다 (리뷰 N4).
    assert payload["error"]["code"] == "E-REQ-MISSING"
    assert not result_path.exists()


def test_run_horizon_and_n_paths_out_of_range_reports_both_errors(tmp_path: Path) -> None:
    engine_path = _build_engine(tmp_path)
    result_path = tmp_path / "out.json"

    result = runner.invoke(
        app,
        [
            "run",
            "--engine",
            str(engine_path),
            "--mode",
            "FORECAST",
            "--horizon",
            "400",
            "--n-paths",
            "50",
            "--out",
            str(result_path),
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "ERROR"
    assert payload["error"]["code"] == "E-REQ-RANGE"
    errors = payload["error"]["details"]["errors"]
    assert len(errors) == 2
    assert {e["code"] for e in errors} == {"E-REQ-RANGE"}
    assert not result_path.exists()


# ---------------------------------------------------------------------------
# `fdt validate` / `fdt render` (SPEC 10장, PLAN Phase 6 - 이전에는 미구현)
# ---------------------------------------------------------------------------


def _run_forecast(tmp_path: Path, name: str = "out.json") -> Path:
    engine_path = _build_engine(tmp_path)
    result_path = tmp_path / name
    result = runner.invoke(
        app,
        [
            "run",
            "--engine",
            str(engine_path),
            "--mode",
            "FORECAST",
            "--horizon",
            "30",
            "--out",
            str(result_path),
        ],
    )
    assert result.exit_code == 0, result.output
    return result_path


def test_validate_subcommand_passes_for_ok_result(tmp_path: Path) -> None:
    result_path = _run_forecast(tmp_path)

    validate_result_cli = runner.invoke(app, ["validate", "--result", str(result_path)])

    assert validate_result_cli.exit_code == 0, validate_result_cli.output
    assert "OK" in validate_result_cli.output


def test_validate_subcommand_fails_on_tampered_caption(tmp_path: Path) -> None:
    result_path = _run_forecast(tmp_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["viz"][0]["caption"] = "부족 확률은 999%다."
    result_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    validate_result_cli = runner.invoke(app, ["validate", "--result", str(result_path)])

    assert validate_result_cli.exit_code == 1, validate_result_cli.output
    assert "999" in validate_result_cli.output


def test_validate_subcommand_missing_file_reports_error(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.json"

    result = runner.invoke(app, ["validate", "--result", str(missing)])

    assert result.exit_code == 1, result.output


def test_render_subcommand_writes_png_files(tmp_path: Path) -> None:
    result_path = _run_forecast(tmp_path)
    out_dir = tmp_path / "png"

    render_result_cli = runner.invoke(
        app, ["render", "--result", str(result_path), "--out", str(out_dir)]
    )

    assert render_result_cli.exit_code == 0, render_result_cli.output
    pngs = list(out_dir.glob("*.png"))
    assert pngs, "PNG 파일이 하나도 안 만들어졌다"
    for png in pngs:
        assert png.stat().st_size > 0
