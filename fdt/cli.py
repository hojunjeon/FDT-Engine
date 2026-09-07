"""FDT 테스트용 CLI (SPEC 10장).

이번 단계(W0-C)에서는 `schema` 서브커맨드만 구현한다. `gen/build/run/
inspect/render/validate` 는 이후 다른 작업자가 이 typer 앱에 추가한다.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import typer

from fdt.gen import DEFAULT_END, DEFAULT_MONTHS, PROFILE_NAMES, write_profile
from fdt.tools.schema_export import export_json_schemas

app = typer.Typer(help="FDT 엔진 테스트용 CLI")


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


if __name__ == "__main__":
    app()
