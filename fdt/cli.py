"""FDT 테스트용 CLI (SPEC 10장).

이번 단계(W0-C)에서는 `schema` 서브커맨드만 구현한다. `gen/build/run/
inspect/render/validate` 는 이후 다른 작업자가 이 typer 앱에 추가한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer

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


if __name__ == "__main__":
    app()
