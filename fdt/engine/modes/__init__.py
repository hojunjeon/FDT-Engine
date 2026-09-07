"""모드 러너 레지스트리 (SPEC 8장, 4.2-5 "다섯 모드는 모두 `simulate()` 하나를
호출한다").

`Engine.run()` 은 이 딕셔너리에서 `req.mode` 로 러너를 찾아 호출한다.
`register(mode)` 데코레이터로 각 모드 모듈(`forecast.py`, `whatif.py`,
`goal.py`, `risk.py`, `optimize.py`)이 자신의 러너를 등록한다. 등록 자체는
그 모듈이 import 될 때 일어나므로, `load_all()` 이 `fdt.engine.modes.*` 의
모든 서브모듈을 한 번 훑어 import 해야 레지스트리가 채워진다(동적 로드 -
이 `__init__.py` 는 모듈 이름을 하드코딩하지 않는다. 각 작업자가 새 모드
파일을 추가해도 이 파일을 고칠 필요가 없다).

`Engine.run()` 은 첫 호출에서 `load_all()` 을 부른다(멱등 - 이미 로드됐으면
아무 일도 하지 않는다).

러너 시그니처: `Callable[[Engine, ModeRequest], ResultUnion]`. `Engine` 은
순환 import 를 피하기 위해 타입체크 시점에만 import 한다.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from fdt.engine.errors import FdtError
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.schemas.result import ResultUnion
from fdt.engine.taxonomy import Mode

if TYPE_CHECKING:
    from fdt.engine.engine import Engine

ModeRunner = Callable[["Engine", ModeRequest], ResultUnion]

MODE_RUNNERS: dict[Mode, ModeRunner] = {}

_F = TypeVar("_F", bound=ModeRunner)

_loaded = False

__all__ = ["MODE_RUNNERS", "ModeRunner", "load_all", "register"]


def register(mode: Mode) -> Callable[[_F], _F]:
    """`@register(Mode.WHATIF)` 데코레이터: 모드 러너를 `MODE_RUNNERS` 에 등록한다.

    같은 모드가 두 번 등록되면(예: 모듈이 실수로 두 러너를 같은 모드에
    붙임) `FdtError(E-MODE-DUPLICATE)` 를 던진다 - 이는 사용자 입력이 아니라
    프로그래밍 오류이므로 개발 중(임포트 시점)에 바로 드러나야 한다.
    """

    def _decorator(func: _F) -> _F:
        if mode in MODE_RUNNERS:
            raise FdtError(
                code="E-MODE-DUPLICATE",
                message=f"모드 {mode.value} 는 이미 {MODE_RUNNERS[mode]!r} 로 등록되어 있다",
                details={"mode": mode.value, "existing": repr(MODE_RUNNERS[mode])},
            )
        MODE_RUNNERS[mode] = func
        return func

    return _decorator


def load_all() -> None:
    """`fdt.engine.modes.*` 서브모듈을 전부 import 해 레지스트리를 채운다.

    각 모듈은 import 시점에 최상위에서 `@register(...)` 를 실행하므로,
    import 만으로 등록이 끝난다. 이미 로드했으면 다시 훑지 않는다(멱등,
    반복 호출 비용 없음). `Engine.run()` 이 매 호출마다 불러도 안전하다.
    """

    global _loaded
    if _loaded:
        return

    package = importlib.import_module(__name__)
    for module_info in pkgutil.iter_modules(package.__path__, prefix=f"{__name__}."):
        if module_info.name == __name__:
            continue
        importlib.import_module(module_info.name)

    _loaded = True
