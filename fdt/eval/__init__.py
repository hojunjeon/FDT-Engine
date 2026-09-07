"""평가 도구 (SPEC 12장, PLAN §3 Phase 7 / §4 W14).

`fdt/eval/**` 는 엔진과 달리 `ground_truth` 를 읽어도 되는 평가 계층이다
(SPEC 11장 "엔진 코드는 ground_truth 를 읽지 않는다" - eval 은 엔진 코드가
아니다). `fdt.engine.**` 는 여기서 `build_engine`/`Engine.run` 을 통해서만
쓰고, 전이 규칙을 재구현하지 않는다.

이 모듈에는 다섯 파일이 공유하는 작은 헬퍼만 둔다: sMAPE(SPEC §12 정의),
PRIMARY 계좌 판별(엔진 `State.accounts[].role` 을 신뢰, 재계산하지 않음),
ground_truth 의 날짜별 PRIMARY 잔액 합산, 프로필 이름 -> SPEC §11/§12 표의
문자(A/B/C/D) 변환.
"""

from __future__ import annotations

from datetime import date, timedelta

from fdt.engine import Engine

__all__ = [
    "SMAPE_EPS",
    "date_range",
    "gt_date_range",
    "gt_primary_balance",
    "primary_account_ids",
    "profile_letter",
    "smape",
]

# SPEC §12 sMAPE 정의: mean(|m-t| / ((|m|+|t|)/2 + 100,000))
SMAPE_EPS = 100_000


def profile_letter(profile_name: str) -> str:
    """`"B_card_crunch"` -> `"B"` (SPEC §11/§12 표 열 이름)."""

    return profile_name.split("_", 1)[0]


def primary_account_ids(engine: Engine) -> set[int]:
    """엔진 `State.accounts` 에서 PRIMARY 역할 계좌 id 집합을 뽑는다.

    역할 판정 자체는 `fdt.engine.state` 가 이미 끝낸 것을 그대로 읽기만
    한다 - eval 이 PRIMARY 여부를 다시 판정하지 않는다(작업 지시 "계좌
    역할은 State 로 판별").
    """

    return {acc.id for acc in engine.state.accounts if acc.role == "PRIMARY"}


def gt_primary_balance(
    ground_truth: dict, primary_ids: set[int], d: date
) -> int:
    """`ground_truth["daily_balance"][d.isoformat()]` 중 PRIMARY 계좌 합.

    생성기가 그 날짜를 기록하지 않았으면(범위 밖) `KeyError` 를 그대로
    전파한다 - 조용히 0을 반환해 오차를 숨기지 않는다.
    """

    day = ground_truth["daily_balance"][d.isoformat()]
    return sum(int(v) for acc_id, v in day.items() if int(acc_id) in primary_ids)


def gt_date_range(ground_truth: dict) -> tuple[date, date]:
    """`ground_truth["daily_balance"]` 가 덮는 날짜 범위(최소, 최대)."""

    keys = sorted(ground_truth["daily_balance"].keys())
    return date.fromisoformat(keys[0]), date.fromisoformat(keys[-1])


def date_range(start: date, end: date, step_days: int = 1) -> list[date]:
    """`start` 부터 `end` 까지(포함) `step_days` 간격 날짜 목록."""

    out = []
    d = start
    while d <= end:
        out.append(d)
        d += timedelta(days=step_days)
    return out


def smape(m: float, t: float) -> float:
    """SPEC §12 sMAPE 항 하나: `|m-t| / ((|m|+|t|)/2 + 100,000)`."""

    return abs(m - t) / ((abs(m) + abs(t)) / 2 + SMAPE_EPS)
