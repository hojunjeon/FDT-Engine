"""엔진 파일 저장·복원 (SPEC 4.1 `Engine.save`/`Engine.load`).

`fdt/engine/**` 는 파일 I/O 를 하지 않으므로(SPEC §4.2-7), `Engine.to_dict()`/
`Engine.from_dict()` 가 만든 순수 dict 를 실제로 디스크에 쓰고 읽는 일은
여기(`fdt/tools/`)에 둔다. SPEC 문서의 `Engine.save(path)`/`Engine.load(path)`
표기는 이 모듈의 `save_engine`/`load_engine` 을 가리킨다.
"""

from __future__ import annotations

import json
from pathlib import Path

from fdt.engine.engine import Engine
from fdt.engine.errors import E_ENGINE_LOAD, FdtError

__all__ = ["load_engine", "save_engine"]


def save_engine(engine: Engine, path: str | Path) -> None:
    """`engine.to_dict()` 를 JSON 파일로 쓴다(UTF-8)."""

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(engine.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_engine(path: str | Path) -> Engine:
    """`save_engine` 이 쓴 JSON 파일을 다시 `Engine` 으로 만든다.

    파일이 없거나 JSON 파싱에 실패하면 `FdtError(E-ENGINE-LOAD)`. 내용은
    맞지만 `engine_id` 가 twin 재계산과 다르면 `Engine.from_dict` 가
    `FdtError(E-ENGINE-ID-MISMATCH)` 를 그대로 전파한다.
    """

    in_path = Path(path)
    try:
        raw = in_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except OSError as exc:
        raise FdtError(
            code=E_ENGINE_LOAD,
            message=f"엔진 파일을 읽을 수 없다: {in_path}",
            details={"path": str(in_path), "reason": str(exc)},
        ) from exc
    except json.JSONDecodeError as exc:
        raise FdtError(
            code=E_ENGINE_LOAD,
            message=f"엔진 파일이 올바른 JSON 이 아니다: {in_path}",
            details={"path": str(in_path), "reason": str(exc)},
        ) from exc

    try:
        return Engine.from_dict(data)
    except (KeyError, TypeError, ValueError) as exc:
        # engine_id 불일치(FdtError)는 그대로 전파한다. 그 외 형태가 깨진
        # 데이터(필수 키 누락 등)만 E-ENGINE-LOAD 로 감싼다.
        raise FdtError(
            code=E_ENGINE_LOAD,
            message=f"엔진 파일 내용이 올바르지 않다: {in_path}",
            details={"path": str(in_path), "reason": str(exc)},
        ) from exc
