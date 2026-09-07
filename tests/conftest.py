# 공용 pytest fixture (PLAN 4장, W5 담당). 생성 비용이 큰 픽스처는 전부
# session 스코프로 묶어 스위트 전체에서 한 번만 만든다. 이후 작업(W6~)은
# 이 파일을 읽기만 하고 고치지 않는다(PLAN 4장 병렬 규칙).

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from fdt.engine import Engine, TwinInput, build_engine
from fdt.gen import PROFILE_NAMES, generate

_SEED = 7
_MONTHS_SHORT = 3
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SEED_DATA_ROOT = _REPO_ROOT / "data" / "seed"


@pytest.fixture(scope="session")
def profiles_3m() -> dict[str, tuple[TwinInput, dict[str, Any]]]:
    """4 프로필(A/B/C/D) x seed=7, months=3 의 (TwinInput, ground_truth).

    6개월 생성보다 훨씬 빨라 매 테스트가 반복 호출해도 부담이 적지만,
    그래도 스위트 전체에서 한 번만 생성하도록 session 스코프로 묶는다.
    """

    out: dict[str, tuple[TwinInput, dict[str, Any]]] = {}
    for name in PROFILE_NAMES:
        twin, _twin_raw, ground_truth = generate(name, seed=_SEED, months=_MONTHS_SHORT)
        out[name] = (twin, ground_truth)
    return out


@pytest.fixture(scope="session")
def engines_3m(
    profiles_3m: dict[str, tuple[TwinInput, dict[str, Any]]],
) -> dict[str, Engine]:
    """`profiles_3m` 각각을 `build_engine` 한 결과."""

    return {name: build_engine(twin) for name, (twin, _gt) in profiles_3m.items()}


def _load_seed_engine(profile_name: str) -> Engine:
    twin_input_path = _SEED_DATA_ROOT / f"{profile_name}_{_SEED}" / "twin_input.json"
    raw = twin_input_path.read_text(encoding="utf-8")
    twin = TwinInput.model_validate_json(raw)
    return build_engine(twin)


@pytest.fixture(scope="session")
def seed_engine_A() -> Engine:
    """`data/seed/A_steady_7/twin_input.json`(6개월) 로 만든 엔진."""

    return _load_seed_engine("A_steady")


@pytest.fixture(scope="session")
def seed_engine_B() -> Engine:
    """`data/seed/B_card_crunch_7/twin_input.json`(6개월) 로 만든 엔진."""

    return _load_seed_engine("B_card_crunch")


@pytest.fixture(scope="session")
def seed_engine_C() -> Engine:
    """`data/seed/C_impulsive_7/twin_input.json`(6개월) 로 만든 엔진."""

    return _load_seed_engine("C_impulsive")


@pytest.fixture(scope="session")
def seed_engine_D() -> Engine:
    """`data/seed/D_goal_saver_7/twin_input.json`(6개월) 로 만든 엔진."""

    return _load_seed_engine("D_goal_saver")
