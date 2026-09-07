"""더미 데이터 생성기 (SPEC 11장). 프로필 YAML + 시드 -> TwinInput + ground_truth.

`fdt/engine/**` 는 이 패키지를 참조하지 않는다(SPEC 11장 "엔진 코드는
ground_truth 를 읽지 않는다"). 이 패키지는 `fdt.engine.taxonomy` 와
`fdt.engine.schemas.input` 만 신뢰한다.
"""

from __future__ import annotations

from fdt.gen.generator import (
    DEFAULT_END,
    DEFAULT_MONTHS,
    PROFILE_NAMES,
    generate,
    list_profiles,
    load_profile,
    write_profile,
)

__all__ = [
    "DEFAULT_END",
    "DEFAULT_MONTHS",
    "PROFILE_NAMES",
    "generate",
    "list_profiles",
    "load_profile",
    "write_profile",
]
