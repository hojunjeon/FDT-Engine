"""`Engine`/`build_engine` 단위 테스트 (SPEC 4장, PLAN 5.1 test_engine, W5 완료
조건).

`tests/conftest.py` 의 세션 픽스처(`profiles_3m`, `engines_3m`,
`seed_engine_A/B/C/D`)를 재사용한다. 이 파일은 그 픽스처를 만든 W5 소유라
필요하면 고칠 수 있지만, 이후 작업(W6~)은 읽기만 한다(PLAN 4장).
"""

from __future__ import annotations

import json
import time
from datetime import date, timedelta
from pathlib import Path

import pytest

from fdt.engine import Engine, TwinInput, build_engine
from fdt.engine.behavior import estimate_behavior
from fdt.engine.engine import EngineBuildMeta
from fdt.engine.errors import (
    E_ENGINE_ID_MISMATCH,
    E_MODE_NOT_IMPLEMENTED,
    E_RECON,
    W_INPUT_FUTURE_TX,
    W_INPUT_SHORT_HISTORY,
    W_RECON,
    FdtError,
)
from fdt.engine.schemas.request import ModeRequest
from fdt.gen import PROFILE_NAMES

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SEED_DATA_ROOT = _REPO_ROOT / "data" / "seed"
_SEED = 7

# ---------------------------------------------------------------------------
# engine_id 안정성
# ---------------------------------------------------------------------------


def test_engine_id_stable_for_same_input(profiles_3m):
    twin, _gt = profiles_3m["B_card_crunch"]

    id_1 = build_engine(twin).meta.engine_id
    id_2 = build_engine(twin).meta.engine_id
    assert id_1 == id_2


def test_engine_id_changes_when_transaction_amount_changes(profiles_3m):
    twin, _gt = profiles_3m["B_card_crunch"]
    base_id = build_engine(twin).meta.engine_id

    raw = json.loads(twin.model_dump_json())
    assert raw["transactions"], "테스트 픽스처에 거래가 없다"
    raw["transactions"][0]["amount"] = raw["transactions"][0]["amount"] + 1000
    mutated = TwinInput.model_validate(raw)

    mutated_id = build_engine(mutated).meta.engine_id
    assert mutated_id != base_id


def test_engine_id_changes_when_as_of_changes(profiles_3m):
    twin, _gt = profiles_3m["B_card_crunch"]
    base_id = build_engine(twin).meta.engine_id
    earlier_id = build_engine(twin, as_of=twin.as_of - timedelta(days=1)).meta.engine_id
    assert earlier_id != base_id


# ---------------------------------------------------------------------------
# to_dict / from_dict 왕복
# ---------------------------------------------------------------------------


def test_to_dict_from_dict_roundtrip_preserves_state_behavior_ledger(engines_3m):
    engine = engines_3m["B_card_crunch"]
    restored = Engine.from_dict(engine.to_dict())

    assert restored.state.model_dump(mode="json") == engine.state.model_dump(mode="json")
    assert restored.behavior.model_dump(mode="json") == engine.behavior.model_dump(mode="json")
    assert restored.ledger == engine.ledger
    assert restored.meta.engine_id == engine.meta.engine_id


def test_from_dict_rejects_engine_id_mismatch(engines_3m):
    engine = engines_3m["B_card_crunch"]
    payload = engine.to_dict()
    payload["meta"]["engine_id"] = "0" * 12

    with pytest.raises(FdtError) as exc_info:
        Engine.from_dict(payload)
    assert exc_info.value.code == E_ENGINE_ID_MISMATCH


def test_from_dict_rejects_mismatch_when_twin_content_changed(engines_3m):
    engine = engines_3m["B_card_crunch"]
    payload = engine.to_dict()
    # engine_id 는 그대로 두고 twin 내용만 바꾸면(위조), 재계산한 해시가
    # 저장된 engine_id 와 달라져 거부돼야 한다.
    payload["twin"]["transactions"][0]["amount"] += 1

    with pytest.raises(FdtError) as exc_info:
        Engine.from_dict(payload)
    assert exc_info.value.code == E_ENGINE_ID_MISMATCH


# ---------------------------------------------------------------------------
# 경고 수집
# ---------------------------------------------------------------------------


def test_future_tx_warning_when_building_with_earlier_as_of(profiles_3m):
    twin, _gt = profiles_3m["B_card_crunch"]
    engine = build_engine(twin, as_of=twin.as_of - timedelta(days=30))
    codes = [w.code for w in engine.meta.warnings]
    assert W_INPUT_FUTURE_TX in codes


def test_short_history_warning_for_short_transaction_history(profiles_3m):
    # `generate(..., months=1)` 도 as_of 가 속한 달의 1일부터 만들어 실제로는
    # 28일보다 긴 이력을 낸다(월초 as_of 가 아닌 한). 이력 < 28일 케이스를
    # 결정론적으로 만들기 위해 3개월 생성 결과에서 최근 20일치 거래만 남긴다.
    twin, _gt = profiles_3m["A_steady"]
    raw = json.loads(twin.model_dump_json())
    cutoff = twin.as_of - timedelta(days=20)
    raw["transactions"] = [
        tx for tx in raw["transactions"] if date.fromisoformat(tx["tx_date"]) >= cutoff
    ]
    short_history_twin = TwinInput.model_validate(raw)

    engine = build_engine(short_history_twin)
    codes = [w.code for w in engine.meta.warnings]
    assert W_INPUT_SHORT_HISTORY in codes


def test_recon_warning_for_hand_modified_balance(profiles_3m):
    twin, _gt = profiles_3m["A_steady"]
    raw = json.loads(twin.model_dump_json())
    account = raw["accounts"][0]
    assert account["opening_balance"] is not None, "대사 검사에는 opening_balance 가 필요하다"
    account["balance"] += 12345
    mutated = TwinInput.model_validate(raw)

    engine = build_engine(mutated, strict=False)
    codes = [w.code for w in engine.meta.warnings]
    assert W_RECON in codes


def test_strict_recon_raises_e_recon(profiles_3m):
    twin, _gt = profiles_3m["A_steady"]
    raw = json.loads(twin.model_dump_json())
    account = raw["accounts"][0]
    assert account["opening_balance"] is not None
    account["balance"] += 12345
    mutated = TwinInput.model_validate(raw)

    with pytest.raises(FdtError) as exc_info:
        build_engine(mutated, strict=True)
    assert exc_info.value.code == E_RECON


# ---------------------------------------------------------------------------
# fork
# ---------------------------------------------------------------------------


def test_fork_copies_state_and_shares_ledger(engines_3m):
    engine = engines_3m["B_card_crunch"]
    forked = engine.fork()

    assert forked.ledger is engine.ledger
    assert forked.state is not engine.state

    forked.state.liquidity = engine.state.liquidity + 999999
    assert forked.state.liquidity != engine.state.liquidity


# ---------------------------------------------------------------------------
# run() 골격
# ---------------------------------------------------------------------------


def test_run_returns_error_result_for_unimplemented_mode_without_raising(engines_3m):
    engine = engines_3m["A_steady"]
    req = ModeRequest(
        mode="FORECAST", params={"include_envelopes": True, "include_events": True}
    )

    result = engine.run(req)

    assert result.status == "ERROR"
    assert result.result is None
    assert result.error is not None
    assert result.error.code == E_MODE_NOT_IMPLEMENTED
    assert result.meta.engine_id == engine.meta.engine_id
    assert result.meta.mode.value == "FORECAST"


def test_run_does_not_raise_for_every_mode(engines_3m):
    engine = engines_3m["A_steady"]
    requests = [
        ModeRequest(mode="FORECAST", params={}),
        ModeRequest(mode="RISK", params={}),
        ModeRequest(
            mode="WHATIF",
            params={
                "injections": [
                    {
                        "type": "INCOME",
                        "days_from_now": 1,
                        "amount": 10000,
                    }
                ]
            },
        ),
        ModeRequest(mode="GOAL", params={"goal_type": "ENVELOPE_ADHERE"}),
        ModeRequest(mode="OPTIMIZE", params={"objective": "MIN_SHORTFALL_PROB"}),
    ]
    for req in requests:
        result = engine.run(req)
        assert result.status == "ERROR"
        assert result.error.code == E_MODE_NOT_IMPLEMENTED


# ---------------------------------------------------------------------------
# Behavior 가 State 의 예산으로 추정됐는지
# ---------------------------------------------------------------------------


def test_behavior_uses_state_budgets(seed_engine_D):
    engine = seed_engine_D
    budget_sources = {env.budget_source for env in engine.state.envelopes}
    assert "CONFIRMED" in budget_sources, "D 프로필은 CONFIRMED 예산을 써야 한다"

    budgets = {env.envelope_id: env.budget for env in engine.state.envelopes}
    expected_behavior = estimate_behavior(engine.ledger, engine.state.as_of, budgets=budgets)

    assert engine.behavior.model_dump(mode="json") == expected_behavior.model_dump(mode="json")


# ---------------------------------------------------------------------------
# 성능: 4 프로필 build_engine < 1.0s (6개월 seed 데이터)
# ---------------------------------------------------------------------------


def test_build_engine_performance_under_one_second_for_all_profiles():
    twins = {}
    for name in PROFILE_NAMES:
        path = _SEED_DATA_ROOT / f"{name}_{_SEED}" / "twin_input.json"
        twins[name] = TwinInput.model_validate_json(path.read_text(encoding="utf-8"))

    # 첫 실행(파일 로드 직후 콜드 경로)은 제외하고 2 회 측정한다.
    for twin in twins.values():
        build_engine(twin)

    elapsed_by_profile: dict[str, float] = {}
    for _run_index in range(2):
        for name, twin in twins.items():
            start = time.perf_counter()
            build_engine(twin)
            elapsed = time.perf_counter() - start
            elapsed_by_profile[name] = max(elapsed_by_profile.get(name, 0.0), elapsed)

    for name, elapsed in elapsed_by_profile.items():
        assert elapsed < 1.0, f"{name} build_engine 이 1.0s 를 넘었다: {elapsed:.3f}s"


# ---------------------------------------------------------------------------
# EngineBuildMeta 형태 확인 (built_at 없음, schema_version 고정)
# ---------------------------------------------------------------------------


def test_engine_build_meta_has_no_built_at_and_fixed_schema_version(engines_3m):
    engine = engines_3m["A_steady"]
    assert not hasattr(engine.meta, "built_at")
    assert engine.meta.schema_version == "engine/1"
    assert isinstance(engine.meta.as_of, date)
    assert isinstance(engine.meta, EngineBuildMeta)
