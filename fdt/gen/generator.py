"""더미 데이터 생성기 (SPEC 11장, PLAN Phase 1 / W1).

프로필 YAML(A_steady, B_card_crunch, C_impulsive, D_goal_saver) + 시드 ->
`TwinInput` + `ground_truth.json`.

생성기는 시뮬레이터(향후 `engine/simulate.py`)의 정답 분포다. 하루 처리
순서는 SPEC 7.2 와 반드시 같아야 한다:

    1 수입      규칙적(SALARY)이면 day_of_month, 불규칙(IRREGULAR)이면
                median_gap_days 기반 다음 지급일에 입금. 급여일에 한해
                emergency_transfer_monthly 만큼 EMERGENCY 계좌로 TRANSFER.
    2 고정비    due==d 인 고정비를 계좌형은 WITHDRAW, 카드형은 CARD 로 기록.
                계좌형은 잔액 부족 시 당일 그대로 거절(재시도 없음).
    3 청구 발행 월요일에 직전 월~일 카드 사용분(취소 제외)을 합산해
                `card_billings` 를 UNPAID 로 발행.
    4 카드 출금 청구서별 예정 출금일(`_first_due`: billing_date 이후 당일 포함
                첫 withdrawal_weekday) 이 지난 청구서만, 오래된 것부터 시도.
                부족하면 `card_shortfalls` 기록 후 그 카드의 그날 남은
                청구서는 시도하지 않는다(SPEC S16, 리뷰 B1).
    5 소비      봉투별 daily_rate x weekday_mult x payday_boost/
                pre_payday_damp x elasticity(잔여 예산 <20%, 봉투별) 로
                포아송 강도를 구하고, 발생 건수만큼 로그정규 금액을 뽑는다.
                card_share 비율만큼 카드 결제, 나머지는 체크성 출금(잔액
                부족 시 거절 + `declined_debits`(kind=SPEND) 기록).
    6 돌발      hidden.shock 파라미터로 하루 1건 이하의 대형 지출을 봉투
                "기타" 에 발생시킨다. 카드/체크 비율은 전 봉투 card_share
                평균을 쓴다.
    7 취소·더치 오늘 만든 카드 결제 일부를 취소(같은 레코드의 status 만
                CANCELED 로 바꾼다, 새 레코드를 만들지 않는다)하고, 외식
                고액 결제 일부에 더치페이 입금을 더한다(수령분은 그 봉투의
                순지출에서 차감, 리뷰 B2).
    8 기록      계좌별 그날의 잔액을 ground_truth.daily_balance 에, 누적
                unpaid_obligation/suppressed_demand 를 남긴다(리뷰 N8).

엔진(`fdt/engine/**`)이 절대 읽지 않는 값: `spending`/`hidden` 전체
(payday_boost, pre_payday_damp, elasticity, shock 분포, cancel_prob,
dutch_pay_prob, pending_ratio, 잔액 부족 시 체크 거절 여부)와
`ground_truth.json` 전체(SPEC 11장).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from fdt.engine.schemas.input import TwinInput
from fdt.engine.taxonomy import ENVELOPE_IDS, ENVELOPES, OTHER_ENVELOPE_ID, SUBCATEGORIES
from fdt.gen.profile_schema import validate_profile

PROFILE_DIR = Path(__file__).parent / "profiles"
DEFAULT_END = date(2026, 9, 7)
DEFAULT_MONTHS = 6

PROFILE_NAMES: tuple[str, ...] = (
    "A_steady",
    "B_card_crunch",
    "C_impulsive",
    "D_goal_saver",
)

# ---------------------------------------------------------------------------
# 세분류별 가맹점 이름(3~5개, 고정). subcategory_id -> [merchant, ...]
# ---------------------------------------------------------------------------

_MERCHANTS: dict[int, list[str]] = {
    1: ["김밥천국", "한솥도시락", "백반집", "국밥집"],
    2: ["스타벅스", "메가커피", "이디야커피", "컴포즈커피"],
    3: ["배달의민족", "요기요", "쿠팡이츠"],
    4: ["호프집", "포차", "이자카야"],
    5: ["지하철", "시내버스", "티머니"],
    6: ["카카오T", "우티", "티맵택시"],
    7: ["SK에너지", "GS칼텍스", "현대오일뱅크"],
    8: ["온누리약국", "연세내과", "서울정형외과"],
    9: ["헬스장", "필라테스", "요가원"],
    10: ["CGV", "메가박스", "인터파크"],
    11: ["잠실야구장", "월드컵경기장", "KBO샵"],
    12: ["스팀", "플레이스테이션스토어", "넥슨캐시"],
    13: ["야놀자", "여기어때", "에어비앤비"],
    14: ["무신사", "유니클로", "자라"],
    15: ["올리브영", "이니스프리", "시코르"],
    16: ["쿠팡", "네이버쇼핑", "11번가"],
    17: ["GS25", "CU", "세븐일레븐"],
    18: ["이마트", "홈플러스", "롯데마트"],
    19: ["다이소", "무인양품", "이케아"],
    20: ["교보문고", "패스트캠퍼스", "인프런"],
    21: ["아마존", "알리익스프레스", "이베이"],
    22: ["경조사비", "기부", "기타결제"],
}

_SUBCATS_BY_ENVELOPE: dict[int, list[int]] = {}
for _sub_id, _env_id, _name in SUBCATEGORIES:
    _SUBCATS_BY_ENVELOPE.setdefault(_env_id, []).append(_sub_id)

_DINING_ENVELOPE_ID = ENVELOPE_IDS["외식"]
_OTHER_SUBCATS = _SUBCATS_BY_ENVELOPE[OTHER_ENVELOPE_ID]

_ENVELOPE_FULL_DEFS: list[dict[str, Any]] = [
    {"id": ENVELOPE_IDS[name], "name": name} for name in ENVELOPES
]
_SUBCATEGORY_FULL_DEFS: list[dict[str, Any]] = [
    {"id": sub_id, "envelope_id": env_id, "name": name} for sub_id, env_id, name in SUBCATEGORIES
]


def _add_months(y: int, m: int, delta: int) -> tuple[int, int]:
    total = (m - 1) + delta
    return y + total // 12, total % 12 + 1


def _round100(v: float) -> int:
    return max(0, round(v / 100.0) * 100)


def _day_or_last(d: date, day: int) -> bool:
    last = (d.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    return d.day == min(day, last.day)


def _first_due(billing_date: date, withdrawal_weekday: int) -> date:
    """청구서의 예정 출금일 (SPEC S16 / 리뷰 B1 수정 지시).

    `billing_date` 이후(당일 포함) 첫 `d.weekday() == withdrawal_weekday` 인
    날을 반환하는 순수 함수. `withdrawal_weekday` 가 월요일(0)이고 청구서가
    월요일에 발행되면 발행 당일이 곧 예정 출금일이다(경계는
    `test_generator.py` 의 단위 테스트로 고정).
    """

    d = billing_date
    for _ in range(7):
        if d.weekday() == withdrawal_weekday:
            return d
        d += timedelta(days=1)
    return d  # pragma: no cover - withdrawal_weekday 는 0..6 이라 도달 불가


@dataclass
class _AccountState:
    id: int
    alias: str
    is_income: bool
    opening_balance: int
    managed: bool
    balance: int = 0

    def __post_init__(self) -> None:
        self.balance = self.opening_balance


@dataclass
class _CardBilling:
    id: int
    card_id: int
    billing_date: date
    total_amount: int
    status: str = "UNPAID"
    paid_at: date | None = None


@dataclass
class _CardState:
    id: int
    alias: str
    kind: str
    withdrawal_weekday: int
    withdrawal_account_id: int
    billings: list[_CardBilling] = field(default_factory=list)


class _IdSeq:
    def __init__(self, start: int) -> None:
        self._next = start

    def take(self) -> int:
        v = self._next
        self._next += 1
        return v


class Generator:
    """프로필 dict + 시드 -> (twin_input dict, ground_truth dict).

    SPEC 7.2 의 하루 처리 순서를 그대로 따른다(모듈 docstring 참조).
    """

    def __init__(self, profile: dict[str, Any], *, seed: int, months: int, end: date) -> None:
        self.profile = profile
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.end = end
        y, m = _add_months(end.year, end.month, -months)
        self.start = date(y, m, 1)

        self.accounts: dict[int, _AccountState] = {
            a["id"]: _AccountState(
                id=a["id"],
                alias=a["alias"],
                is_income=a["is_income"],
                opening_balance=a["opening_balance"],
                managed=a["managed"],
            )
            for a in profile["accounts"]
        }
        self.primary_id: int = next(
            a["id"] for a in profile["accounts"] if a["is_income"]
        )
        self._emergency_id: int | None = next(
            (a["id"] for a in profile["accounts"] if not a["is_income"]), None
        )

        self.cards: dict[int, _CardState] = {
            c["id"]: _CardState(
                id=c["id"],
                alias=c["alias"] or f"카드{c['id']}",
                kind=c["kind"],
                withdrawal_weekday=c["withdrawal_weekday"],
                withdrawal_account_id=c["withdrawal_account_id"],
            )
            for c in profile["cards"]
        }
        self._card_ids: list[int] = list(self.cards)

        self.tx_id = _IdSeq(1001)
        self.billing_id = _IdSeq(9001)

        self.transactions: list[dict[str, Any]] = []
        self.card_billings_out: list[_CardBilling] = []

        self._month_spent: dict[int, int] = {ENVELOPE_IDS[n]: 0 for n in ENVELOPES}
        self._budget_ref: dict[int, int] = {
            ENVELOPE_IDS[name]: amount for name, amount in profile["budgets"]["envelopes"].items()
        }
        self._avg_card_share = float(
            np.mean([cfg["card_share"] for cfg in profile["spending"].values()])
        )
        self._elasticity: dict[int, float] = self._build_elasticity_table(
            profile["hidden"]["elasticity"]
        )

        self._next_income: date | None = None
        self._last_income: date | None = None
        self._init_income_schedule()

        self._unpaid_obligation_total = 0
        self._suppressed_demand_total = 0

        self.gt: dict[str, Any] = {
            "daily_balance": {},
            "card_shortfalls": [],
            "declined_debits": [],
            "shocks": [],
            "cancels": [],
            "dutch_pays": [],
            "envelope_true_spend": {},
            "income_events": [],
            "unpaid_obligation": {},
            "suppressed_demand": {},
            "hidden_params": {
                "spending": profile["spending"],
                "hidden": profile["hidden"],
                "income": profile["income"],
            },
        }

    @staticmethod
    def _build_elasticity_table(raw: float | dict[str, float]) -> dict[int, float]:
        """`hidden.elasticity` 를 봉투별 dict 로 확장한다 (SPEC S24 / 리뷰 N4).

        스칼라면 전 봉투에 같은 값을 준다. dict 면 봉투 이름 키를 id 로 바꾸고,
        빠진 봉투는 1.0(탄력도 중립)으로 채운다.
        """

        if isinstance(raw, dict):
            table = {ENVELOPE_IDS[name]: float(v) for name, v in raw.items()}
            for eid in ENVELOPE_IDS.values():
                table.setdefault(eid, 1.0)
            return table
        return {eid: float(raw) for eid in ENVELOPE_IDS.values()}

    # -- 수입 일정 ------------------------------------------------------

    def _init_income_schedule(self) -> None:
        inc = self.profile["income"]
        if inc["type"] == "SALARY":
            self._next_income = self._next_salary_on_or_after(self.start, inc["day_of_month"])
        else:
            self._next_income = self.start + timedelta(days=int(inc["median_gap_days"]) // 2)

    @staticmethod
    def _next_salary_on_or_after(d: date, day_of_month: int) -> date:
        cur = d
        for _ in range(40):
            if _day_or_last(cur, day_of_month):
                return cur
            cur += timedelta(days=1)
        return d

    # -- 거래 기록 헬퍼 ---------------------------------------------------

    def _confirm_status(self, flow_hint: str | None, exclude_tag: str) -> str:
        """거래 흐름별 확정 상태 (SPEC S20 / 리뷰 N5).

        수입·고정비·카드대금·자기이체는 사용자가 다시 세분류를 확인할
        필요가 없는 자동 인식 거래이므로 `CONFIRMED`. 더치페이 입금은
        `AUTO`. 소비(그 외, `flow_hint is None`)만 프로필별
        `hidden.pending_ratio` 확률로 `PENDING`, 나머지는 `AUTO` 다.
        """

        if flow_hint in ("INCOME", "FIXED", "CARD_BILL") or exclude_tag == "SELF_TRANSFER":
            return "CONFIRMED"
        if exclude_tag == "DUTCH":
            return "AUTO"
        pending_ratio = float(self.profile["hidden"]["pending_ratio"])
        return "PENDING" if self.rng.random() < pending_ratio else "AUTO"

    def _time(self, lo: int = 8, hi: int = 22) -> time:
        h = int(self.rng.integers(lo, hi))
        return time(h, int(self.rng.integers(0, 60)), int(self.rng.integers(0, 60)))

    def _add_tx(
        self,
        *,
        tx_type: str,
        tx_date: date,
        amount: int,
        account_id: int | None = None,
        card_id: int | None = None,
        merchant_name_raw: str | None = None,
        subcategory_id: int | None = None,
        exclude_tag: str = "NONE",
        flow_hint: str | None = None,
        counterparty_account_id: int | None = None,
        status: str = "NORMAL",
    ) -> dict[str, Any]:
        tx = {
            "id": self.tx_id.take(),
            "source": "SEED",
            "tx_type": tx_type,
            "account_id": account_id,
            "card_id": card_id,
            "merchant_id": None,
            "merchant_name_raw": merchant_name_raw,
            "amount": amount,
            "tx_date": tx_date,
            "tx_time": self._time(),
            "subcategory_id": subcategory_id,
            "confirm_status": self._confirm_status(flow_hint, exclude_tag),
            "exclude_tag": exclude_tag,
            "status": status,
            "flow_hint": flow_hint,
            "counterparty_account_id": counterparty_account_id,
        }
        self.transactions.append(tx)
        return tx

    def _record_envelope_spend(self, d: date, envelope_id: int, amount: int) -> None:
        ym = f"{d.year:04d}{d.month:02d}"
        month_bucket = self.gt["envelope_true_spend"].setdefault(ym, {})
        month_bucket[str(envelope_id)] = month_bucket.get(str(envelope_id), 0) + amount

    def _record_declined(
        self, d: date, *, kind: str, amount: int, envelope_id: int | None = None
    ) -> None:
        """잔액 부족으로 거절된 이체/결제 (SPEC S26 / 리뷰 N8).

        `kind` 는 `FIXED`(계좌형 고정비 거절, 재시도 없음, `unpaid_obligation`
        누적) | `LOAN`(대출이자 거절, 같은 방식으로 누적) |
        `SPEND`(체크성 소비 거절, `suppressed_demand` 누적) 중 하나다.
        """

        self.gt["declined_debits"].append(
            {"date": d.isoformat(), "kind": kind, "envelope_id": envelope_id, "amount": amount}
        )
        if kind == "SPEND":
            self._suppressed_demand_total += amount
        else:
            self._unpaid_obligation_total += amount

    # -- 하루 처리 순서 (SPEC 7.2) ----------------------------------------

    def run(self) -> None:
        d = self.start
        while d <= self.end:
            if d.day == 1:
                self._month_spent = {k: 0 for k in self._month_spent}
            self._step_income(d)
            self._step_fixed(d)
            self._step_billing_issue(d)
            self._step_card_withdraw(d)
            self._step_spending(d)
            self._step_shock(d)
            self._step_cancel_and_dutch(d)
            self._step_record(d)
            d += timedelta(days=1)

    def _step_income(self, d: date) -> None:
        inc = self.profile["income"]
        if self._next_income is None or d < self._next_income:
            return
        if inc["type"] == "SALARY":
            amount = int(inc["amount"])
            self._next_income = self._next_salary_on_or_after(
                d + timedelta(days=1), inc["day_of_month"]
            )
        else:
            base = float(inc["amount"])
            jitter = float(self.rng.lognormal(mean=0.0, sigma=float(inc["jitter_sigma"])))
            amount = _round100(base * jitter)
            gap = int(inc["median_gap_days"])
            actual_gap = max(3, round(gap + self.rng.normal(0, gap * 0.3)))
            self._next_income = d + timedelta(days=actual_gap)

        acc = self.accounts[self.primary_id]
        acc.balance += amount
        self._add_tx(
            tx_type="DEPOSIT",
            tx_date=d,
            amount=amount,
            account_id=self.primary_id,
            merchant_name_raw="급여" if inc["type"] == "SALARY" else "입금",
            flow_hint="INCOME",
        )
        self.gt["income_events"].append({"date": d.isoformat(), "amount": amount})
        self._last_income = d

        emergency_amt = int(self.profile["hidden"]["emergency_transfer_monthly"])
        if emergency_amt > 0 and self._emergency_id is not None:
            emer = self.accounts[self._emergency_id]
            if acc.balance >= emergency_amt:
                acc.balance -= emergency_amt
                emer.balance += emergency_amt
                self._add_tx(
                    tx_type="TRANSFER",
                    tx_date=d,
                    amount=emergency_amt,
                    account_id=self.primary_id,
                    counterparty_account_id=self._emergency_id,
                    merchant_name_raw="비상금이체",
                    exclude_tag="SELF_TRANSFER",
                )
            # 부족하면 당일 건너뛴다(재시도 없음, SPEC §7.2 2단계 / S62)

    def _step_fixed(self, d: date) -> None:
        for fx in self.profile["fixed_expenses"]:
            if not _day_or_last(d, fx["payment_day"]):
                continue
            amount = int(fx["amount"])
            if fx["card_id"] is not None:
                self._add_tx(
                    tx_type="CARD",
                    tx_date=d,
                    amount=amount,
                    account_id=self.cards[fx["card_id"]].withdrawal_account_id,
                    card_id=fx["card_id"],
                    merchant_name_raw=fx["name"],
                    flow_hint="FIXED",
                )
            else:
                acc = self.accounts[fx["withdrawal_account_id"]]
                if acc.balance >= amount:
                    acc.balance -= amount
                    self._add_tx(
                        tx_type="WITHDRAW",
                        tx_date=d,
                        amount=amount,
                        account_id=acc.id,
                        merchant_name_raw=fx["name"],
                        flow_hint="FIXED",
                    )
                else:
                    self._record_declined(d, kind="FIXED", amount=amount)

        for loan in self.profile["loans"]:
            if not _day_or_last(d, loan["interest_day"]):
                continue
            interest = int(
                round(loan["balance"] * loan["annual_rate_pct"] / 100 / 12 / 10) * 10
            )
            acc = self.accounts[loan["withdrawal_account_id"]]
            if acc.balance >= interest:
                acc.balance -= interest
                self._add_tx(
                    tx_type="WITHDRAW",
                    tx_date=d,
                    amount=interest,
                    account_id=acc.id,
                    merchant_name_raw="대출이자",
                    flow_hint="FIXED",
                )
            else:
                self._record_declined(d, kind="LOAN", amount=interest)

    def _week_card_total(self, card_id: int, start: date, end: date) -> int:
        s, e = start.isoformat(), end.isoformat()
        total = 0
        for tx in self.transactions:
            if (
                tx["tx_type"] == "CARD"
                and tx["card_id"] == card_id
                and tx["status"] == "NORMAL"
                and s <= tx["tx_date"].isoformat() <= e
            ):
                total += tx["amount"]
        return total

    def _step_billing_issue(self, d: date) -> None:
        if d.weekday() != 0 or d == self.start:
            return
        week_start, week_end = d - timedelta(days=7), d - timedelta(days=1)
        for card in self.cards.values():
            total = self._week_card_total(card.id, week_start, week_end)
            if total <= 0:
                continue
            billing = _CardBilling(
                id=self.billing_id.take(),
                card_id=card.id,
                billing_date=d,
                total_amount=total,
            )
            card.billings.append(billing)
            self.card_billings_out.append(billing)

    def _step_card_withdraw(self, d: date) -> None:
        for card in self.cards.values():
            unpaid = sorted(
                (b for b in card.billings if b.status == "UNPAID" and b.billing_date <= d),
                key=lambda b: b.billing_date,
            )
            # 예정 출금일(첫 withdrawal_weekday) 이 지난 청구서만 시도한다.
            # SPEC S16 / 리뷰 B1: "발행일이 지났는가" 가 아니라 "예정 출금일이
            # 지났는가" 로 판정해야 withdrawal_weekday 가 지켜진다.
            attemptable = [
                b for b in unpaid if _first_due(b.billing_date, card.withdrawal_weekday) <= d
            ]
            if not attemptable:
                continue
            acc = self.accounts[card.withdrawal_account_id]
            for billing in attemptable:
                if acc.balance >= billing.total_amount:
                    acc.balance -= billing.total_amount
                    billing.status = "PAID"
                    billing.paid_at = d
                    self._add_tx(
                        tx_type="WITHDRAW",
                        tx_date=d,
                        amount=billing.total_amount,
                        account_id=acc.id,
                        merchant_name_raw=f"카드대금 {card.alias}",
                        flow_hint="CARD_BILL",
                    )
                else:
                    self.gt["card_shortfalls"].append(
                        {"date": d.isoformat(), "card_id": card.id, "amount": billing.total_amount}
                    )
                    break

    def _elasticity_gate(self, envelope_id: int) -> float:
        budget = self._budget_ref.get(envelope_id, 0)
        if budget <= 0:
            return 1.0
        remaining_ratio = 1 - self._month_spent[envelope_id] / budget
        return self._elasticity[envelope_id] if remaining_ratio < 0.2 else 1.0

    def _cycle_mult(self, d: date) -> float:
        """SPEC §7.2 5단계 `boost` 복합 계수 (리뷰 N3, SPEC S23 제안).

        `boost(d) = payday_boost^[수입 후 7일] * pre_payday_damp^[다음 수입
        5일 전]`. 두 조건은 겹치지 않는다(수입 후 7일 구간과 다음 수입 5일
        전 구간은 최소 급여 주기 10일 이상에서 서로 배타적). `pre_payday_damp`
        는 생성기가 여전히 `hidden` 에 숨기는 값이고(SPEC §11), 엔진은
        `payday_boost` 만 원장에서 추정한다(§6).
        """

        hidden = self.profile["hidden"]
        m = 1.0
        if self._last_income is not None and 0 <= (d - self._last_income).days < 7:
            m *= float(hidden["payday_boost"])
        if self._next_income is not None and 0 < (self._next_income - d).days <= 5:
            m *= float(hidden["pre_payday_damp"])
        return m

    def _pick_card(self) -> int:
        if len(self._card_ids) == 1:
            return self._card_ids[0]
        return self._card_ids[int(self.rng.integers(0, len(self._card_ids)))]

    def _step_spending(self, d: date) -> None:
        cm = self._cycle_mult(d)
        for env_name in ENVELOPES:
            envelope_id = ENVELOPE_IDS[env_name]
            cfg = self.profile["spending"][env_name]
            rate = (
                cfg["daily_rate"]
                * cfg["weekday_mult"][d.weekday()]
                * cm
                * self._elasticity_gate(envelope_id)
            )
            n = int(self.rng.poisson(max(0.0, rate)))
            for _ in range(n):
                subcat_id = int(
                    self.rng.choice(_SUBCATS_BY_ENVELOPE[envelope_id])
                )
                merchant = self._MERCHANT_choice(subcat_id)
                amount = _round100(
                    float(self.rng.lognormal(mean=cfg["amount_mu"], sigma=cfg["amount_sigma"]))
                )
                self._spend_one(d, envelope_id, subcat_id, merchant, amount, cfg["card_share"])

    def _MERCHANT_choice(self, subcategory_id: int) -> str:
        names = _MERCHANTS[subcategory_id]
        return names[int(self.rng.integers(0, len(names)))]

    def _spend_one(
        self,
        d: date,
        envelope_id: int,
        subcategory_id: int,
        merchant: str,
        amount: int,
        card_share: float,
    ) -> None:
        if amount <= 0:
            return
        via_card = bool(self.cards) and self.rng.random() < card_share
        if via_card:
            card_id = self._pick_card()
            self._add_tx(
                tx_type="CARD",
                tx_date=d,
                amount=amount,
                account_id=self.cards[card_id].withdrawal_account_id,
                card_id=card_id,
                merchant_name_raw=merchant,
                subcategory_id=subcategory_id,
            )
            self._month_spent[envelope_id] += amount
            self._record_envelope_spend(d, envelope_id, amount)
            return

        acc = self.accounts[self.primary_id]
        if acc.balance >= amount:
            acc.balance -= amount
            self._add_tx(
                tx_type="WITHDRAW",
                tx_date=d,
                amount=amount,
                account_id=self.primary_id,
                merchant_name_raw=merchant,
                subcategory_id=subcategory_id,
            )
            self._month_spent[envelope_id] += amount
            self._record_envelope_spend(d, envelope_id, amount)
        else:
            self._record_declined(d, kind="SPEND", amount=amount, envelope_id=envelope_id)

    def _step_shock(self, d: date) -> None:
        sh = self.profile["hidden"]["shock"]
        if self.rng.random() >= float(sh["daily_prob"]):
            return
        subcat_id = int(self.rng.choice(_OTHER_SUBCATS))
        merchant = self._MERCHANT_choice(subcat_id)
        amount = _round100(
            float(self.rng.lognormal(mean=float(sh["mu"]), sigma=float(sh["sigma"])))
        )
        self.gt["shocks"].append({"date": d.isoformat(), "amount": amount})
        self._spend_one(d, OTHER_ENVELOPE_ID, subcat_id, merchant, amount, self._avg_card_share)

    def _step_cancel_and_dutch(self, d: date) -> None:
        hidden = self.profile["hidden"]
        today = d.isoformat()
        todays_card_tx = [
            tx
            for tx in self.transactions
            if tx["tx_type"] == "CARD"
            and tx["tx_date"] == d
            and tx["status"] == "NORMAL"
            and tx["flow_hint"] is None
        ]
        for tx in todays_card_tx:
            if self.rng.random() < float(hidden["cancel_prob"]):
                tx["status"] = "CANCELED"
                envelope_id = self._envelope_of(tx["subcategory_id"])
                self._month_spent[envelope_id] -= tx["amount"]
                ym = f"{d.year:04d}{d.month:02d}"
                self.gt["envelope_true_spend"][ym][str(envelope_id)] -= tx["amount"]
                self.gt["cancels"].append(
                    {"date": today, "tx_id": tx["id"], "amount": tx["amount"]}
                )

        dining = [
            tx
            for tx in self.transactions
            if tx["tx_date"] == d
            and tx["status"] == "NORMAL"
            and tx["subcategory_id"] is not None
            and self._envelope_of(tx["subcategory_id"]) == _DINING_ENVELOPE_ID
            and tx["amount"] >= 30000
            and tx["tx_type"] in ("CARD", "WITHDRAW")
            and tx["flow_hint"] is None
        ]
        for tx in dining:
            if self.rng.random() < float(hidden["dutch_pay_prob"]):
                n = int(self.rng.integers(2, 5))
                share = _round100(tx["amount"] * (n - 1) / n)
                if share <= 0:
                    continue
                acc = self.accounts[self.primary_id]
                acc.balance += share
                self._add_tx(
                    tx_type="DEPOSIT",
                    tx_date=d,
                    amount=share,
                    account_id=self.primary_id,
                    merchant_name_raw="더치페이",
                    subcategory_id=tx["subcategory_id"],
                    exclude_tag="DUTCH",
                )
                self.gt["dutch_pays"].append({"date": today, "amount": share})
                # 리뷰 B2(생성기 측): 더치 수령분은 그 봉투의 순지출에서
                # 빠져야 한다(원장은 §5.2 규칙 4 에 따라 DUTCH 입금을 그
                # 봉투의 REFUND 로 반영하므로 정답도 같은 정의를 따른다).
                envelope_id = self._envelope_of(tx["subcategory_id"])
                self._month_spent[envelope_id] -= share
                self._record_envelope_spend(d, envelope_id, -share)

    @staticmethod
    def _envelope_of(subcategory_id: int | None) -> int:
        if subcategory_id is None:
            return OTHER_ENVELOPE_ID
        for sub_id, env_id, _name in SUBCATEGORIES:
            if sub_id == subcategory_id:
                return env_id
        return OTHER_ENVELOPE_ID

    def _step_record(self, d: date) -> None:
        key = d.isoformat()
        self.gt["daily_balance"][key] = {
            str(acc.id): acc.balance for acc in self.accounts.values()
        }
        # SPEC S26 / 리뷰 N8: 경제 잔액(§7.2 8단계) 검증용 일별 누적 스냅샷.
        self.gt["unpaid_obligation"][key] = self._unpaid_obligation_total
        self.gt["suppressed_demand"][key] = self._suppressed_demand_total

    # -- 출력 -------------------------------------------------------------

    def build_twin_input(self, *, omit_opening_balance: bool = False) -> dict[str, Any]:
        accounts_out = []
        for a in self.profile["accounts"]:
            acc = self.accounts[a["id"]]
            accounts_out.append(
                {
                    "id": a["id"],
                    "fin_account_no": f"{a['id']:016d}",
                    "bank_code": "001",
                    "alias": a["alias"],
                    "is_managed": a["managed"],
                    "is_income": a["is_income"],
                    "balance": acc.balance,
                    "opening_balance": None if omit_opening_balance else a["opening_balance"],
                }
            )

        cards_out = [
            {
                "id": c["id"],
                "issuer_code": f"{1000 + c['id']}",
                "card_name": c["alias"] or f"카드{c['id']}",
                "kind": c["kind"],
                "withdrawal_account_id": c["withdrawal_account_id"],
                "withdrawal_weekday": c["withdrawal_weekday"],
                "is_managed": True,
            }
            for c in self.profile["cards"]
        ]

        card_billings_out = [
            {
                "id": b.id,
                "card_id": b.card_id,
                "billing_date": b.billing_date.isoformat(),
                "total_amount": b.total_amount,
                "status": b.status,
                "paid_at": b.paid_at.isoformat() if b.paid_at else None,
            }
            for b in self.card_billings_out
        ]

        fixed_expenses_out = [
            {
                "id": fx["id"],
                "name": fx["name"],
                "expense_type": fx["expense_type"],
                "amount": fx["amount"],
                "is_variable": fx["is_variable"],
                "payment_day": fx["payment_day"],
                "withdrawal_account_id": fx["withdrawal_account_id"],
                "card_id": fx["card_id"],
                "active": True,
            }
            for fx in self.profile["fixed_expenses"]
        ]

        loans_out = [
            {
                "id": loan["id"],
                "balance": loan["balance"],
                "annual_rate_pct": loan["annual_rate_pct"],
                "interest_day": loan["interest_day"],
                "withdrawal_account_id": loan["withdrawal_account_id"],
                "repayment": loan["repayment"],
            }
            for loan in self.profile["loans"]
        ]

        budget_month = f"{self.end.year:04d}{self.end.month:02d}"
        confirmed = bool(self.profile["budgets"]["confirmed"])
        budgets_out = [
            {
                "budget_month": budget_month,
                "status": "CONFIRMED" if confirmed else "PROPOSED",
                "envelopes": [
                    {
                        "envelope_id": ENVELOPE_IDS[name],
                        "proposed_amount": amount,
                        "confirmed_amount": amount if confirmed else None,
                    }
                    for name, amount in self.profile["budgets"]["envelopes"].items()
                ],
            }
        ]

        transactions_out = [
            {
                "id": tx["id"],
                "source": tx["source"],
                "tx_type": tx["tx_type"],
                "account_id": tx["account_id"],
                "card_id": tx["card_id"],
                "merchant_id": tx["merchant_id"],
                "merchant_name_raw": tx["merchant_name_raw"],
                "amount": tx["amount"],
                "tx_date": tx["tx_date"].isoformat(),
                "tx_time": tx["tx_time"].isoformat(),
                "subcategory_id": tx["subcategory_id"],
                "confirm_status": tx["confirm_status"],
                "exclude_tag": tx["exclude_tag"],
                "status": tx["status"],
                "flow_hint": tx["flow_hint"],
                "counterparty_account_id": tx["counterparty_account_id"],
            }
            for tx in self.transactions
        ]

        return {
            "schema_version": "twin-input/1",
            "as_of": self.end.isoformat(),
            "user": {"id": 1, "employment_status": None, "income_band": None, "birth_date": None},
            "envelopes": _ENVELOPE_FULL_DEFS,
            "subcategories": _SUBCATEGORY_FULL_DEFS,
            "accounts": accounts_out,
            "cards": cards_out,
            "card_billings": card_billings_out,
            "fixed_expenses": fixed_expenses_out,
            "loans": loans_out,
            "budgets": budgets_out,
            "transactions": transactions_out,
            "externals": {
                "price_index_mult": 1.0,
                "loan_rate_delta_bp": 0,
                "income_growth_pct": 0.0,
            },
        }


def load_profile(name_or_path: str) -> dict[str, Any]:
    """프로필 YAML 을 읽고 `Profile` pydantic 모델로 검증한다 (리뷰 N10).

    반환값은 `model_dump(mode="json")` 을 거친 dict 라서, 원본 YAML 이 생략한
    선택 필드도 `profile_schema.Profile` 이 정의한 기본값으로 채워져 있다.
    """

    p = Path(name_or_path)
    if not p.exists():
        p = PROFILE_DIR / f"{name_or_path}.yaml"
    with open(p, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return validate_profile(raw)


def list_profiles() -> list[str]:
    return sorted(p.stem for p in PROFILE_DIR.glob("*.yaml"))


def generate(
    profile_name: str,
    *,
    seed: int,
    months: int = DEFAULT_MONTHS,
    end: date = DEFAULT_END,
    omit_opening_balance: bool = False,
) -> tuple[TwinInput, dict[str, Any], dict[str, Any]]:
    """프로필 이름 + 시드 -> (TwinInput, twin_input dict, ground_truth dict).

    반환하는 `TwinInput` 은 `model_validate` 를 이미 통과한 것이다.
    `omit_opening_balance=True` 면 `accounts[].opening_balance` 를 전부
    `null` 로 내보내 SPEC §3.2 의 역산 경로(`balance` - Σ거래)를 실데이터로
    검증할 수 있게 한다 (리뷰 N12).
    """

    profile = load_profile(profile_name)
    gen = Generator(profile, seed=seed, months=months, end=end)
    gen.run()
    twin_input_dict = gen.build_twin_input(omit_opening_balance=omit_opening_balance)
    twin_input = TwinInput.model_validate(twin_input_dict)
    return twin_input, twin_input_dict, gen.gt


def write_profile(
    profile_name: str,
    out_root: Path,
    *,
    seed: int,
    months: int = DEFAULT_MONTHS,
    end: date = DEFAULT_END,
    omit_opening_balance: bool = False,
) -> Path:
    """`out_root/<profile>_<seed>/` 에 twin_input.json, ground_truth.json,
    profile.yaml 을 쓴다. 재현성: 같은 (profile, seed, months, end) 는
    `generated_at` 같은 시각 필드 없이 바이트 단위로 같은 twin_input.json 을
    낸다."""

    twin_input, _twin_input_raw, ground_truth = generate(
        profile_name,
        seed=seed,
        months=months,
        end=end,
        omit_opening_balance=omit_opening_balance,
    )
    # twin_input.json 은 model_dump(mode="json") 으로 직렬화해 스키마가
    # 실제로 왕복 검증됨을 보장한다(빌더가 만든 raw dict 를 그대로 쓰지 않음).
    dumped = twin_input.model_dump(mode="json")

    out_dir = out_root / f"{profile_name}_{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "twin_input.json").write_text(
        json.dumps(dumped, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "ground_truth.json").write_text(
        json.dumps(ground_truth, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    profile_raw = load_profile(profile_name)
    (out_dir / "profile.yaml").write_text(
        yaml.safe_dump(profile_raw, allow_unicode=True, sort_keys=False, default_flow_style=None),
        encoding="utf-8",
    )
    return out_dir
