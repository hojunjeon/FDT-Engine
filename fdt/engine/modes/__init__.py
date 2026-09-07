"""모드 러너 레지스트리 (SPEC 8장, 4.2-5 "다섯 모드는 모두 `simulate()` 하나를
호출한다").

`Engine.run()` 은 이 딕셔너리에서 `req.mode` 로 러너를 찾아 호출한다. 이번
단계(W5)에는 모드 구현이 하나도 없으므로 빈 채로 시작하고, 각 모드 작업
(W7~W10)이 자신의 러너를 여기에 등록한다.

러너 시그니처: `Callable[[Engine, ModeRequest], ResultUnion]`. `Engine` 은
순환 import 를 피하기 위해 타입체크 시점에만 import 한다.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from fdt.engine.schemas.request import ModeRequest
from fdt.engine.schemas.result import ResultUnion
from fdt.engine.taxonomy import Mode

if TYPE_CHECKING:
    from fdt.engine.engine import Engine

ModeRunner = Callable[["Engine", ModeRequest], ResultUnion]

MODE_RUNNERS: dict[Mode, ModeRunner] = {}

__all__ = ["MODE_RUNNERS", "ModeRunner"]
