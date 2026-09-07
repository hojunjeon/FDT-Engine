"""JSON Schema 내보내기 (PLAN Phase 0, SPEC 10장 `fdt schema`).

에이전트·프론트 팀과 공유하기 위해 핵심 pydantic 모델의
`model_json_schema()` 를 `<name>.schema.json` 파일로 저장한다.

이 모듈은 `fdt/engine/**` 밖(`fdt/tools/`)에 둔다. 파일 쓰기를 하므로
SPEC §4.2 "엔진 코어는 외부 I/O 없음" 을 지키기 위함이다(원래
`fdt/engine/schemas/export.py` 에 있었으나 리뷰 B5 지시로 이동됨).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from fdt.engine.schemas.behavior import Behavior
from fdt.engine.schemas.input import TwinInput
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.schemas.result import EngineResult
from fdt.engine.schemas.state import State


def export_json_schemas(out_dir: Path) -> list[Path]:
    """핵심 모델의 JSON Schema 를 `out_dir` 에 `<name>.schema.json` 으로 쓴다.

    반환값은 실제로 쓰인 파일 경로 목록이다.
    """

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    models: list[tuple[str, type[BaseModel]]] = [
        ("TwinInput", TwinInput),
        ("State", State),
        ("Behavior", Behavior),
        ("ModeRequest", ModeRequest),
        ("EngineResult", EngineResult),
    ]

    written: list[Path] = []
    for name, model in models:
        schema = model.model_json_schema()
        path = out_dir / f"{name}.schema.json"
        path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        written.append(path)

    return written
