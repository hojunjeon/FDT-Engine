"""Behavior 스키마 (SPEC 6장).

이 모듈은 Behavior 의 형태와 클립 범위만 정의한다. 실제 추정 로직(원장에서
daily_rate, weekday_mult 등을 추정하는 계산)은 `engine/behavior.py`(다른
작업 ID 소유)가 담당한다. 여기서는 SPEC 6장 표의 클립·기본값 범위를
pydantic 제약으로만 강제한다.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat, NonNegativeInt, model_validator

from fdt.engine.schemas.state import IncomeSchedule

__all__ = [
    "Behavior",
    "EnvelopeBehavior",
    "IncomeSchedule",
    "ShockModel",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


class EnvelopeBehavior(_Base):
    envelope_id: int
    daily_rate: NonNegativeFloat
    weekday_mult: list[float] = Field(min_length=7, max_length=7)
    amount_mu: float
    amount_sigma: float = Field(ge=0.2, le=1.5)
    card_share: float = Field(ge=0, le=1)
    elasticity: float = Field(ge=0.5, le=2.0)
    n_obs: NonNegativeInt

    @model_validator(mode="after")
    def _check_weekday_mult_mean(self) -> EnvelopeBehavior:
        mean = sum(self.weekday_mult) / len(self.weekday_mult)
        if abs(mean - 1.0) > 1e-6:
            raise ValueError(
                "weekday_mult 의 평균은 1.0(+-1e-6) 이어야 한다 (SPEC 6장, "
                f"envelope_id={self.envelope_id}, mean={mean})"
            )
        return self


class ShockModel(_Base):
    daily_prob: float = Field(ge=0, le=1)
    mu: float
    sigma: NonNegativeFloat


class Behavior(_Base):
    as_of: date
    # SPEC 6장 윈도우는 기본 90일/최소 28일이지만, 이력이 28일 미만인
    # 신규 사용자도 엔진을 돌려야 한다(SPEC 3.3 "거래 이력 < 28일" 은
    # E-INPUT- 오류가 아니라 W-INPUT-SHORT_HISTORY 경고 후 진행). 그 경우
    # window_days 에는 실제 보유 이력 일수를 담고(0일은 있을 수 없으므로
    # ge=1), Behavior 추정치는 기본값 비중을 높여 보정한다. 하한을 28로
    # 강제하면 이력이 짧은 입력 자체를 담을 수 없어 리뷰(N10a)에 따라
    # 완화한다.
    window_days: int = Field(ge=1)
    envelopes: list[EnvelopeBehavior] = Field(min_length=7, max_length=7)
    payday_boost: float = Field(ge=0.7, le=2.0)
    # SPEC v0.3 §6 표 추가 항목(W4/S 리뷰 반영): 다음 수입 5일 전 일평균 /
    # 그 외(급여 후 7일과 급여 전 5일을 모두 제외한 날) 일평균. 표본
    # 부족(10일 미만)이면 1.0.
    pre_payday_damp: float = Field(ge=0.5, le=1.3)
    shock: ShockModel
    income: IncomeSchedule
