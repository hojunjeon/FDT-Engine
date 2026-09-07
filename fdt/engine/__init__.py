"""숫자를 만드는 유일한 곳. 외부 I/O 및 LLM 의존성이 없다 (SPEC 4.2).

`build_engine`, `Engine`, `ModeRequest`, `EngineResult`, `TwinInput` 을
공개 API 로 재노출한다(SPEC 4장, PLAN Phase 2 W5).
"""

from fdt.engine.engine import Engine, EngineBuildMeta, build_engine
from fdt.engine.schemas.input import TwinInput
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.schemas.result import EngineResult

__all__ = [
    "Engine",
    "EngineBuildMeta",
    "EngineResult",
    "ModeRequest",
    "TwinInput",
    "build_engine",
]
