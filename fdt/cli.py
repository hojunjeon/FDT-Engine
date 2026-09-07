"""FDT 테스트용 CLI (SPEC 10장).

`schema`, `gen`, `build`, `inspect`, `run` 에 이어 `validate`(독립 서브커맨드)
와 `render`(viz -> PNG, 개발·QA 전용)를 더해 SPEC 10장의 7개 서브커맨드가
모두 갖춰졌다.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any

import typer
from pydantic import ValidationError

from fdt.engine.engine import build_engine
from fdt.engine.errors import E_REQ_INVALID, E_REQ_RANGE, FdtError, extract_errors
from fdt.engine.schemas.input import TwinInput
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.taxonomy import ENVELOPE_IDS
from fdt.eval.backtest import run_backtest
from fdt.eval.calibration import run_calibration
from fdt.eval.monotonic import run_monotonic
from fdt.eval.perf import run_perf
from fdt.eval.report import write_json_reports, write_markdown_report
from fdt.gen import DEFAULT_END, DEFAULT_MONTHS, PROFILE_NAMES, write_profile
from fdt.tools.engine_io import load_engine, save_engine
from fdt.tools.render import render_result
from fdt.tools.schema_export import export_json_schemas
from fdt.tools.validate import validate_result

app = typer.Typer(help="FDT 엔진 테스트용 CLI")
eval_app = typer.Typer(help="평가 도구 (SPEC 12장, PLAN §3 Phase 7)")
app.add_typer(eval_app, name="eval")

_ENVELOPE_NAME_BY_ID: dict[int, str] = {idx: name for name, idx in ENVELOPE_IDS.items()}


def _echo_error(code: str, message: str, details: dict[str, Any] | None = None) -> None:
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    payload: dict[str, Any] = {"status": "ERROR", "error": error}
    typer.echo(json.dumps(payload, ensure_ascii=False))


def _echo_validation_error(exc: ValidationError) -> None:
    """`pydantic.ValidationError` -> 구조화 오류 JSON (리뷰 N4·S39).

    `fdt.engine.errors.extract_errors()` 로 코드 손실 없이 복원한 뒤(정규식
    파싱 없음), 첫 오류를 대표(`error.code`/`error.message`)로 삼고 전부를
    `error.details.errors` 에 싣는다.
    """

    errors = extract_errors(exc)
    first = errors[0]
    error_list = [
        {"code": err.code, "message": err.message, "loc": err.details.get("loc", [])}
        for err in errors
    ]
    _echo_error(first.code, first.message, {"errors": error_list})


@contextmanager
def _cli_error_guard() -> Iterator[None]:
    """서브커맨드 최상위 안전망 (리뷰 N2·N3·N4, 요구사항 5).

    개별 호출부에서 이미 더 구체적인 코드로 잡은 경우 이 지점까지 오지
    않는다. 여기까지 올라오는 `FdtError`/`ValidationError`/`OSError`/
    `json.JSONDecodeError` 는 예상치 못한 경로(예: 엔진 파일 쓰기 실패)이며,
    트레이스백 대신 구조화된 오류 JSON + 종료 코드 1 로 끝낸다. 그 외
    예외(버그)는 여기서 잡지 않고 그대로 전파한다.
    """

    try:
        yield
    except typer.Exit:
        raise
    except FdtError as exc:
        _echo_error(exc.code, exc.message, exc.details)
        raise typer.Exit(code=1) from exc
    except ValidationError as exc:
        _echo_validation_error(exc)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        _echo_error(E_REQ_INVALID, f"JSON 파싱 실패: {exc}")
        raise typer.Exit(code=1) from exc
    except OSError as exc:
        _echo_error(E_REQ_INVALID, f"파일 처리 중 오류: {exc}")
        raise typer.Exit(code=1) from exc


@app.callback()
def _main() -> None:
    """FDT 엔진 테스트용 CLI. 서브커맨드는 아래를 본다.

    콘솔 스크립트(`fdt`)와 `python -m fdt.cli` 양쪽에서 항상 실행되므로,
    한글 출력이 깨지지 않도록 여기서 UTF-8 을 강제한다(SPEC §10).
    """

    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass


@app.command()
def schema(
    out: Path = typer.Option(  # noqa: B008
        Path("schemas"), "--out", help="JSON Schema 를 저장할 디렉터리"
    ),
) -> None:
    """핵심 pydantic 모델을 JSON Schema 로 내보낸다."""

    written = export_json_schemas(out)
    for path in written:
        typer.echo(f"wrote {path}")
    typer.echo(f"{len(written)} schema file(s) written to {out}")


@app.command()
def gen(
    profile: str = typer.Option(
        ..., "--profile", help="프로필 이름(A_steady 등) 또는 'all'"
    ),
    seed: int = typer.Option(..., "--seed", help="난수 시드"),
    months: int = typer.Option(DEFAULT_MONTHS, "--months", help="생성 개월 수"),
    end: str = typer.Option(
        DEFAULT_END.isoformat(), "--end", help="as_of(기준일), YYYY-MM-DD"
    ),
    out: Path = typer.Option(  # noqa: B008
        Path("data/seed"), "--out", help="출력 루트 디렉터리"
    ),
    omit_opening_balance: bool = typer.Option(
        False,
        "--omit-opening-balance",
        help="accounts[].opening_balance 를 null 로 내보낸다(역산 경로 검증용, 리뷰 N12)",
    ),
) -> None:
    """프로필 YAML + 시드 -> TwinInput + ground_truth (SPEC 11장).

    `data/<out>/<profile>_<seed>/` 에 twin_input.json, ground_truth.json,
    profile.yaml 을 쓴다. `--profile all` 이면 SPEC 11장의 4 프로필을 전부
    생성한다.
    """

    end_date = date.fromisoformat(end)
    names = list(PROFILE_NAMES) if profile == "all" else [profile]
    for name in names:
        out_dir = write_profile(
            name,
            out,
            seed=seed,
            months=months,
            end=end_date,
            omit_opening_balance=omit_opening_balance,
        )
        typer.echo(f"generated {name} (seed={seed}) -> {out_dir}")


@app.command()
def build(
    input: Path = typer.Option(..., "--input", help="TwinInput JSON 경로"),  # noqa: B008
    out: Path = typer.Option(..., "--out", help="Engine JSON 을 쓸 경로"),  # noqa: B008
    as_of: str | None = typer.Option(
        None, "--as-of", help="빌드 기준일 YYYY-MM-DD (기본: twin.as_of)"
    ),
    strict: bool = typer.Option(
        False, "--strict", help="계좌 대사 불일치를 경고 대신 오류로 처리"
    ),
) -> None:
    """TwinInput -> Engine, 파일로 저장 (SPEC 10장, 4.1)."""

    with _cli_error_guard():
        try:
            input_text = input.read_text(encoding="utf-8")
        except OSError as exc:
            _echo_error(E_REQ_INVALID, f"입력 파일을 읽을 수 없다: {input} ({exc})")
            raise typer.Exit(code=1) from exc

        try:
            twin = TwinInput.model_validate_json(input_text)
        except ValidationError as exc:
            # JSON 파싱 실패(`json_invalid`)와 스키마/참조 위반(E-INPUT-*) 을
            # 모두 여기서 잡는다: pydantic 은 두 경우 다 ValidationError 로
            # 감싼다 (리뷰 N3).
            _echo_validation_error(exc)
            raise typer.Exit(code=1) from exc

        as_of_date: date | None = None
        if as_of is not None:
            try:
                as_of_date = date.fromisoformat(as_of)
            except ValueError as exc:
                _echo_error(E_REQ_RANGE, f"--as-of 가 올바른 날짜(YYYY-MM-DD)가 아니다: {as_of}")
                raise typer.Exit(code=1) from exc

        try:
            engine = build_engine(twin, as_of=as_of_date, strict=strict)
        except FdtError as exc:
            _echo_error(exc.code, exc.message, exc.details)
            raise typer.Exit(code=1) from exc

        save_engine(engine, out)
        typer.echo(f"built engine {engine.meta.engine_id} (as_of={engine.meta.as_of}) -> {out}")
        for warning in engine.meta.warnings:
            typer.echo(f"warning: {warning.code} - {warning.message}")


def _format_krw(amount: int) -> str:
    return f"{amount:,}원"


def _print_state_summary(engine) -> None:
    state = engine.state
    typer.echo(f"as_of: {state.as_of}")
    typer.echo("계좌:")
    for account in state.accounts:
        typer.echo(f"  [{account.id}] {account.role}: {_format_krw(account.balance)}")
    typer.echo(f"유동성(liquidity): {_format_krw(state.liquidity)}")
    typer.echo(f"비상금(emergency_fund): {_format_krw(state.emergency_fund)}")

    if state.cards:
        typer.echo("카드:")
        for card in state.cards:
            issued = sum(bill.amount for bill in card.issued_unpaid)
            typer.echo(
                f"  [{card.id}] 미청구(unbilled)={_format_krw(card.unbilled)} "
                f"미결제(issued_unpaid)={_format_krw(issued)} 건수={len(card.issued_unpaid)}"
            )

    typer.echo("봉투(예산/사용/잔여):")
    for env in state.envelopes:
        typer.echo(
            f"  {env.name}: 예산={_format_krw(env.budget)} 사용={_format_krw(env.spent)} "
            f"잔여={_format_krw(env.remaining)} 출처={env.budget_source}"
        )

    typer.echo("약정 큐(상위 10건):")
    for item in sorted(state.committed, key=lambda c: c.due)[:10]:
        typer.echo(f"  {item.due} {item.kind} {item.name} {_format_krw(item.amount)}")

    income = state.income
    typer.echo(
        f"수입 일정: 다음={income.next_date} 예상={_format_krw(income.expected)} "
        f"불규칙={income.irregular} 평균간격={income.median_gap_days}일"
    )

    ind = state.indicators
    typer.echo(
        f"지표: 7일평균={_format_krw(int(ind.spend_7d_avg))} "
        f"90일평균={_format_krw(int(ind.spend_90d_avg))} 가속도={ind.acceleration:.2f} "
        f"미확정건수={ind.unconfirmed_count}"
    )


def _print_behavior_summary(engine) -> None:
    behavior = engine.behavior
    typer.echo(f"window_days: {behavior.window_days}")
    typer.echo("봉투별 행동:")
    for env in behavior.envelopes:
        name = _ENVELOPE_NAME_BY_ID.get(env.envelope_id, str(env.envelope_id))
        typer.echo(
            f"  {name}: daily_rate={env.daily_rate:.3f} mu={env.amount_mu:.2f} "
            f"card_share={env.card_share:.2f} elasticity={env.elasticity:.2f}"
        )
    typer.echo(
        f"payday_boost={behavior.payday_boost:.2f} pre_payday_damp={behavior.pre_payday_damp:.2f}"
    )
    shock = behavior.shock
    typer.echo(
        f"shock: daily_prob={shock.daily_prob:.4f} mu={shock.mu:.2f} sigma={shock.sigma:.2f}"
    )


@app.command()
def inspect(
    engine: Path = typer.Option(..., "--engine", help="Engine JSON 경로"),  # noqa: B008
) -> None:
    """State/Behavior 요약 표 출력 (SPEC 10장)."""

    with _cli_error_guard():
        try:
            eng = load_engine(engine)
        except FdtError as exc:
            _echo_error(exc.code, exc.message, exc.details)
            raise typer.Exit(code=1) from exc

        typer.echo("=== State ===")
        _print_state_summary(eng)
        typer.echo("")
        typer.echo("=== Behavior ===")
        _print_behavior_summary(eng)


@app.command(name="run")
def run_mode(
    engine: Path = typer.Option(..., "--engine", help="Engine JSON 경로"),  # noqa: B008
    mode: str = typer.Option(..., "--mode", help="FORECAST|WHATIF|GOAL|RISK|OPTIMIZE"),
    horizon: int = typer.Option(30, "--horizon", help="horizon_days"),
    n_paths: int = typer.Option(1000, "--n-paths", help="n_paths"),
    seed: int = typer.Option(42, "--seed", help="난수 시드"),
    params: str | None = typer.Option(None, "--params", help="params JSON 문자열"),
    params_file: Path | None = typer.Option(  # noqa: B008
        None, "--params-file", help="params JSON 파일 경로"
    ),
    out: Path = typer.Option(..., "--out", help="EngineResult JSON 을 쓸 경로"),  # noqa: B008
    validate: bool = typer.Option(
        False, "--validate", help="결과를 `fdt/tools/validate.py` 로 검사하고 실패 시 종료 코드 1"
    ),
) -> None:
    """ModeRequest 를 만들어 `Engine.run()` 을 호출한다 (SPEC 8~10장).

    등록된 모드(FORECAST/RISK/WHATIF, 이후 GOAL/OPTIMIZE)는 `status=OK` 로
    끝나고, 아직 러너가 없는 모드는 `E-MODE-NOT_IMPLEMENTED` 로 끝난다.
    결과 JSON 은 항상 `out` 에 쓰고, `status=ERROR` 면 종료 코드 1 을
    반환한다. `--validate` 를 주면 `status=OK` 인 결과에 한해
    `fdt.tools.validate.validate_result()` 로 필수 facts/viz·구조를 추가로
    검사하고, 검사가 실패하면(`ValidationReport.ok=False`) 종료 코드 1 로
    끝낸다(SPEC 14 R7, PLAN Phase 6).
    """

    with _cli_error_guard():
        try:
            eng = load_engine(engine)
        except FdtError as exc:
            _echo_error(exc.code, exc.message, exc.details)
            raise typer.Exit(code=1) from exc

        if params_file is not None:
            try:
                params_text = params_file.read_text(encoding="utf-8")
            except OSError as exc:
                _echo_error(
                    E_REQ_INVALID, f"--params-file 을 읽을 수 없다: {params_file} ({exc})"
                )
                raise typer.Exit(code=1) from exc
            try:
                params_raw = json.loads(params_text)
            except json.JSONDecodeError as exc:
                _echo_error(E_REQ_INVALID, f"--params-file JSON 파싱 실패: {exc}")
                raise typer.Exit(code=1) from exc
        elif params is not None:
            try:
                params_raw = json.loads(params)
            except json.JSONDecodeError as exc:
                _echo_error(E_REQ_INVALID, f"--params JSON 파싱 실패: {exc}")
                raise typer.Exit(code=1) from exc
        else:
            params_raw = {}

        try:
            request = ModeRequest.model_validate(
                {
                    "mode": mode,
                    "horizon_days": horizon,
                    "n_paths": n_paths,
                    "seed": seed,
                    "params": params_raw,
                }
            )
        except ValidationError as exc:
            _echo_validation_error(exc)
            raise typer.Exit(code=1) from exc

        result = eng.run(request)

        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            # QA-102: by_alias=True 필요 - FixedChangeInjection.from_ 이
            # SPEC 계약대로 "from" 키로 나가야 한다 (result.to_json_dict).
            json.dumps(result.to_json_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if result.status == "ERROR":
            assert result.error is not None
            typer.echo(f"ERROR {result.error.code}: {result.error.message}")
            raise typer.Exit(code=1)

        if validate:
            report = validate_result(result)
            if not report.ok:
                for err in report.errors:
                    typer.echo(f"validate: {err}")
                typer.echo(f"wrote {out} (validate 실패)")
                raise typer.Exit(code=1)
            typer.echo("validate: ok")

        typer.echo(f"wrote {out}")


@app.command()
def validate(
    result: Path = typer.Option(..., "--result", help="EngineResult JSON 경로"),  # noqa: B008
) -> None:
    """`EngineResult` JSON 을 읽어 `fdt/tools/validate.py` 로 검사한다 (SPEC 10장).

    스키마·필수 facts/viz·annotations·caption 숫자(§9.3 R7) 등을 검사하고
    오류 목록을 출력한다. 통과하면 종료 코드 0, 실패하면(또는 파일을 읽거나
    파싱할 수 없으면) 종료 코드 1.
    """

    with _cli_error_guard():
        try:
            result_text = result.read_text(encoding="utf-8")
        except OSError as exc:
            _echo_error(E_REQ_INVALID, f"결과 파일을 읽을 수 없다: {result} ({exc})")
            raise typer.Exit(code=1) from exc

        try:
            result_raw = json.loads(result_text)
        except json.JSONDecodeError as exc:
            _echo_error(E_REQ_INVALID, f"결과 JSON 파싱 실패: {exc}")
            raise typer.Exit(code=1) from exc

        report = validate_result(result_raw)
        for warning in report.warnings:
            typer.echo(f"warning: {warning}")
        if not report.ok:
            for err in report.errors:
                typer.echo(f"error: {err}")
            typer.echo(f"validate {result}: FAIL ({len(report.errors)}건)")
            raise typer.Exit(code=1)
        typer.echo(f"validate {result}: OK")


@app.command()
def render(
    result: Path = typer.Option(..., "--result", help="EngineResult JSON 경로"),  # noqa: B008
    out: Path = typer.Option(..., "--out", help="PNG 를 쓸 디렉터리"),  # noqa: B008
) -> None:
    """`EngineResult` 의 viz 8종을 PNG 로 그린다 (SPEC 10장, §6.3 - 개발·QA 전용).

    `fdt/tools/render.py::render_result` 를 그대로 호출한다. `matplotlib` 로
    그리며, 렌더러 독립이어야 하는 `fdt/engine/**` 는 이 커맨드가 부르지
    않는다(`viz` 명세는 이미 `result` JSON 안에 들어있다).
    """

    with _cli_error_guard():
        written = render_result(result, out)
        for path in written:
            typer.echo(f"wrote {path}")
        typer.echo(f"{len(written)} PNG file(s) written to {out}")


def _parse_seeds(seeds: str) -> list[int]:
    return [int(s.strip()) for s in seeds.split(",") if s.strip()]


_DEFAULT_SEEDS = "1,3,5,7,11"


@eval_app.command("backtest")
def eval_backtest(
    seeds: str = typer.Option(_DEFAULT_SEEDS, "--seeds", help="쉼표로 구분한 데이터 시드 목록"),
    n_paths: int = typer.Option(1000, "--n-paths", help="시뮬레이션 경로 수"),
    out: Path = typer.Option(Path("data/eval"), "--out", help="출력 디렉터리"),  # noqa: B008
) -> None:
    """홀드아웃 백테스트(SPEC §12 sMAPE·커버리지)를 돌려 `data/eval/backtest.json` 을 쓴다."""

    with _cli_error_guard():
        report = run_backtest(list(PROFILE_NAMES), _parse_seeds(seeds), n_paths=n_paths)
        written = write_json_reports(out, backtest=report)
        for path in written:
            typer.echo(f"wrote {path}")


@eval_app.command("calibration")
def eval_calibration(
    seeds: str = typer.Option("1,2,3,4,5", "--seeds", help="쉼표로 구분한 데이터 시드 목록"),
    n_paths: int = typer.Option(1000, "--n-paths", help="시뮬레이션 경로 수"),
    out: Path = typer.Option(Path("data/eval"), "--out", help="출력 디렉터리"),  # noqa: B008
) -> None:
    """리스크 캘리브레이션(ECE·Brier)을 돌려 `data/eval/calibration.json` 을 쓴다."""

    with _cli_error_guard():
        report = run_calibration(list(PROFILE_NAMES), _parse_seeds(seeds), n_paths=n_paths)
        written = write_json_reports(out, calibration=report)
        for path in written:
            typer.echo(f"wrote {path}")


@eval_app.command("monotonic")
def eval_monotonic(
    n_paths: int = typer.Option(1000, "--n-paths", help="시뮬레이션 경로 수"),
    out: Path = typer.Option(Path("data/eval"), "--out", help="출력 디렉터리"),  # noqa: B008
) -> None:
    """WHATIF 단조성 위반 수를 세어 `data/eval/monotonic.json` 을 쓴다."""

    with _cli_error_guard():
        report = run_monotonic(list(PROFILE_NAMES), n_paths=n_paths)
        written = write_json_reports(out, monotonic=report)
        for path in written:
            typer.echo(f"wrote {path}")


@eval_app.command("perf")
def eval_perf(
    n_paths: int = typer.Option(1000, "--n-paths", help="시뮬레이션 경로 수"),
    out: Path = typer.Option(Path("data/eval"), "--out", help="출력 디렉터리"),  # noqa: B008
) -> None:
    """SPEC §12 성능 5 항목 + 재현성을 측정해 `data/eval/perf.json` 을 쓴다."""

    with _cli_error_guard():
        report = run_perf(n_paths=n_paths)
        written = write_json_reports(out, perf=report)
        for path in written:
            typer.echo(f"wrote {path}")


@eval_app.command("all")
def eval_all(
    seeds: str = typer.Option(_DEFAULT_SEEDS, "--seeds", help="쉼표로 구분한 데이터 시드 목록"),
    n_paths: int = typer.Option(1000, "--n-paths", help="시뮬레이션 경로 수"),
    out: Path = typer.Option(Path("data/eval"), "--out", help="출력 디렉터리"),  # noqa: B008
) -> None:
    """백테스트·캘리브레이션·단조성·성능을 전부 돌려 `docs/EVAL_REPORT.md` 를 쓴다."""

    with _cli_error_guard():
        seed_list = _parse_seeds(seeds)
        profiles = list(PROFILE_NAMES)

        typer.echo("running backtest...")
        backtest = run_backtest(profiles, seed_list, n_paths=n_paths)
        typer.echo("running calibration...")
        calibration_seeds = [1, 2, 3, 4, 5]
        calibration = run_calibration(profiles, calibration_seeds, n_paths=n_paths)
        typer.echo("running monotonic...")
        monotonic = run_monotonic(profiles, n_paths=n_paths)
        typer.echo("running perf...")
        perf = run_perf(n_paths=n_paths)

        written = write_json_reports(
            out, backtest=backtest, calibration=calibration, monotonic=monotonic, perf=perf
        )
        for path in written:
            typer.echo(f"wrote {path}")

        md_path = write_markdown_report(
            Path("docs/EVAL_REPORT.md"),
            backtest=backtest,
            calibration=calibration,
            monotonic=monotonic,
            perf=perf,
        )
        typer.echo(f"wrote {md_path}")


if __name__ == "__main__":
    app()
