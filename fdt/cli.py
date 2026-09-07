"""FDT 테스트용 CLI (SPEC 10장).

`schema`, `gen` 에 이어 이번 단계(W5)는 `build`, `inspect`, `run` 골격을
더한다. `render`/`validate` 는 이후 다른 작업자(W12)가 추가한다.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import typer
from pydantic import ValidationError

from fdt.engine.engine import build_engine
from fdt.engine.errors import E_REQ_INVALID, E_REQ_RANGE, FdtError
from fdt.engine.schemas.input import TwinInput
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.taxonomy import ENVELOPE_IDS
from fdt.gen import DEFAULT_END, DEFAULT_MONTHS, PROFILE_NAMES, write_profile
from fdt.tools.engine_io import load_engine, save_engine
from fdt.tools.schema_export import export_json_schemas

app = typer.Typer(help="FDT 엔진 테스트용 CLI")

_ENVELOPE_NAME_BY_ID: dict[int, str] = {idx: name for name, idx in ENVELOPE_IDS.items()}
_ERROR_CODE_RE = re.compile(r"\bE-[A-Z]+(?:-[A-Z_]+)+\b")


def _echo_error(code: str, message: str, details: dict[str, Any] | None = None) -> None:
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    payload: dict[str, Any] = {"status": "ERROR", "error": error}
    typer.echo(json.dumps(payload, ensure_ascii=False))


def _extract_error_code(message: str, default: str) -> str:
    """CLI 표시용 최선 노력 코드 추출.

    SPEC §9.1 은 `EngineResult.error.code` 를 pydantic 메시지 파싱으로
    채우지 말라고 한다(엔진 결과 계약). 이 함수는 그 계약과 무관한
    CLI 종료 코드 표시 편의용이며, 정규식으로 못 찾으면 `default` 를 쓴다.
    """

    match = _ERROR_CODE_RE.search(message)
    return match.group(0) if match else default


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

    twin = TwinInput.model_validate_json(input.read_text(encoding="utf-8"))

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
                f"미결제(issued_unpaid)={_format_krw(issued)}건수={len(card.issued_unpaid)}"
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
) -> None:
    """ModeRequest 를 만들어 `Engine.run()` 을 호출한다 (SPEC 8~10장).

    이번 단계(W5)는 `fdt.engine.modes.MODE_RUNNERS` 가 비어 있어 모든 모드가
    `E-MODE-NOT_IMPLEMENTED` 로 끝난다. 결과 JSON 은 항상 `out` 에 쓰고,
    `status=ERROR` 면 종료 코드 1 을 반환한다.
    """

    try:
        eng = load_engine(engine)
    except FdtError as exc:
        _echo_error(exc.code, exc.message, exc.details)
        raise typer.Exit(code=1) from exc

    if params_file is not None:
        params_raw = json.loads(params_file.read_text(encoding="utf-8"))
    elif params is not None:
        params_raw = json.loads(params)
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
        code = _extract_error_code(str(exc), E_REQ_INVALID)
        _echo_error(code, str(exc))
        raise typer.Exit(code=1) from exc

    result = eng.run(request)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if result.status == "ERROR":
        assert result.error is not None
        typer.echo(f"ERROR {result.error.code}: {result.error.message}")
        raise typer.Exit(code=1)

    typer.echo(f"wrote {out}")


if __name__ == "__main__":
    app()
