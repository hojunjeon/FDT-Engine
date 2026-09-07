# -*- coding: utf-8 -*-
"""
페르소나 소비 더미데이터 v3 생성기

  1) persona_consumption_90d_v2.csv (P-DEMO-002 이서준) 의 모순을 수정해 v3 로 재작성
  2) P-DEMO-003 / 004 / 005 페르소나 3개월(2026-06-06 ~ 2026-09-03) 데이터를 신규 생성
  3) 4개 파일 전부 정합성 검사

실행:  python docs/persona_dummy_v3_generator.py
출력:  docs/persona_consumption_90d_v3_P002.csv ... _P005.csv

스키마 의미 (v3 확정)
  is_fixed      : 매 주기 금액이 동일한가 (월세 TRUE, 전기요금 FALSE)
  is_recurring  : 주기적으로 반복되는가
  spend_pattern : ROUTINE / PLANNED / FIXED / IMPULSE  (INCOME 행은 N/A)
  classify_source: MERCHANT_MAP(전국 체인) / MODEL(첫 거래 추론) / RULE(사용자 확정 후 규칙, 자동이체) / USER(개인 송금)
  confirm_status : AUTO / CONFIRMED / PENDING
  merchant_area  : 결제가 일어난 지역. 교통은 승차 지역, 온라인은 "온라인", 해외결제는 "해외"
  merchant_id    : 페르소나 접두어 (M2-xx, M3-xx ...) 로 페르소나 내 고유
"""
import csv
import datetime as dt
import io
import os
import random
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(HERE, "persona_consumption_90d_v2.csv")

COLS = ["persona_id", "persona_name", "age", "occupation", "residence", "workplace", "income_band",
        "user_id", "transaction_id", "source", "direction", "transaction_type", "payment_method",
        "transaction_date", "day_of_week", "transaction_time", "category", "subcategory", "merchant",
        "merchant_id", "merchant_area", "amount_krw", "account_id", "card_id", "is_fixed", "is_recurring",
        "spend_pattern", "classify_source", "confirm_status", "exclude_tag", "status", "memo"]
W = "월화수목금토일"
D0, D1 = dt.date(2026, 6, 6), dt.date(2026, 9, 3)
HOLIDAYS = {dt.date(2026, 6, 6), dt.date(2026, 8, 15), dt.date(2026, 8, 17)}  # 현충일, 광복절, 대체공휴일


def d(m, day):
    return dt.date(2026, m, day)


def biz(date):
    """자동이체(계좌) 는 휴일이면 다음 영업일로 이월"""
    while date.weekday() >= 5 or date in HOLIDAYS:
        date += dt.timedelta(days=1)
    return date


def prevbiz(date):
    """연금·급여 등 지급일이 휴일이면 직전 영업일"""
    while date.weekday() >= 5 or date in HOLIDAYS:
        date -= dt.timedelta(days=1)
    return date


def hhmm(h, m):
    return "%02d:%02d" % (h, m)


def write_csv(path, rows):
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


# ---------------------------------------------------------------------------
# 공통 빌더
# ---------------------------------------------------------------------------
class Builder:
    def __init__(self, num, name, age, occ, res, work, band, seed):
        self.p = dict(persona_id="P-DEMO-%03d" % num, persona_name=name, age=str(age), occupation=occ,
                      residence=res, workplace=work, income_band=band, user_id="USR-DEMO-%03d" % num)
        self.num = num
        self.acc = "ACC-DEMO-%03d" % num
        self.card = "CARD-DEMO-%03d" % num
        self.rng = random.Random(seed)
        self.merchants = {}   # name -> dict(id, area, cat, sub, kind)
        self.seen = set()
        self.rows = []

    # 가맹점 등록. kind: chain(전국 체인) / local(동네) / rule(자동이체·공과금·급여) / person(개인) / online
    def m(self, name, area, cat, sub, kind):
        if name not in self.merchants:
            self.merchants[name] = dict(id="M%d-%02d" % (self.num, len(self.merchants) + 1),
                                        area=area, cat=cat, sub=sub, kind=kind)
        return name

    def t(self, h, mi, jit=0):
        if jit:
            mi += self.rng.randint(-jit, jit)
            while mi < 0:
                mi += 60; h -= 1
            while mi >= 60:
                mi -= 60; h += 1
        return hhmm(h, mi)

    def amt(self, base, pct=0.0, step=100):
        if not pct:
            return base
        v = base * (1 + self.rng.uniform(-pct, pct))
        return int(round(v / step) * step)

    def add(self, date, time, merchant, amount, memo="", *, direction="EXPENSE", ttype="CARD", pay="CARD",
            fixed=False, recurring=False, pattern="ROUTINE", src=None, status=None, excl="NONE",
            area=None, cat=None, sub=None):
        md = self.merchants[merchant]
        kind = md["kind"]
        if src is None:
            if kind == "chain" or kind == "online":
                src, st = "MERCHANT_MAP", "AUTO"
            elif kind == "rule":
                src, st = "RULE", "AUTO"
            elif kind == "person":
                src, st = "USER", "CONFIRMED"
            else:  # local
                if merchant in self.seen:
                    src, st = "RULE", "AUTO"
                else:
                    src, st = "MODEL", "CONFIRMED"
                    if recurring:  # 첫 거래에서는 반복성을 알 수 없음 → 두 번째부터 recurring
                        recurring, fixed = False, False
                        pattern = "PLANNED" if pattern == "FIXED" else pattern
                        memo = memo + " (첫 결제, 사용자 확정)"
        else:
            st = status or "AUTO"
        if status:
            st = status
        self.seen.add(merchant)
        if direction == "INCOME":
            pattern = "N/A"
        r = dict(self.p)
        r.update(source="SEED", direction=direction, transaction_type=ttype, payment_method=pay,
                 transaction_date=date.isoformat(), day_of_week=W[date.weekday()], transaction_time=time,
                 category=cat or md["cat"], subcategory=sub or md["sub"], merchant=merchant, merchant_id=md["id"],
                 merchant_area=area or md["area"], amount_krw=str(int(amount)),
                 account_id=self.acc if pay == "ACCOUNT" else "", card_id=self.card if pay == "CARD" else "",
                 is_fixed="TRUE" if fixed else "FALSE", is_recurring="TRUE" if recurring else "FALSE",
                 spend_pattern=pattern, classify_source=src, confirm_status=st, exclude_tag=excl,
                 status="NORMAL", memo=memo)
        self.rows.append(r)
        return r

    # 편의 래퍼 ---------------------------------------------------------
    def bill(self, date, time, merchant, amount, memo, fixed=True):
        """계좌 자동이체 고정비 (휴일 → 영업일 이월)"""
        return self.add(biz(date), time, merchant, amount, memo, ttype="WITHDRAW", pay="ACCOUNT",
                        fixed=fixed, recurring=True, pattern="FIXED")

    def cardbill(self, date, time, merchant, amount, memo, fixed=True):
        """카드 자동결제 (구독 등, 휴일 무관)"""
        return self.add(date, time, merchant, amount, memo, fixed=fixed, recurring=True, pattern="FIXED")

    def income(self, date, time, merchant, amount, memo, recurring=True, fixed=True, ttype="DEPOSIT", bizday=True):
        return self.add(biz(date) if bizday else date, time, merchant, amount, memo, direction="INCOME",
                        ttype=ttype, pay="ACCOUNT", fixed=fixed, recurring=recurring)

    def send(self, date, time, merchant, amount, memo, pattern="PLANNED", cat=None, sub=None):
        """개인 송금 (계좌 → 개인)"""
        return self.add(date, time, merchant, amount, memo, ttype="TRANSFER_OUT", pay="ACCOUNT",
                        pattern=pattern, cat=cat, sub=sub)

    def recv(self, date, time, merchant, amount, memo):
        return self.add(date, time, merchant, amount, memo, direction="INCOME", ttype="TRANSFER_IN",
                        pay="ACCOUNT")

    def save(self, date, time, merchant, amount, memo):
        return self.add(biz(date), time, merchant, amount, memo, direction="TRANSFER", ttype="TRANSFER_OUT",
                        pay="ACCOUNT", fixed=True, recurring=True, pattern="FIXED", excl="INTERNAL_TRANSFER")

    def finish(self, path):
        self.rows.sort(key=lambda r: (r["transaction_date"], r["transaction_time"]))
        for i, r in enumerate(self.rows, 1):
            r["transaction_id"] = "TX-DEMO%d-%04d" % (self.num, i)
        write_csv(path, self.rows)
        return self.rows


def each_day(f):
    date = D0
    while date <= D1:
        f(date)
        date += dt.timedelta(days=1)


def is_workday(date):
    return date.weekday() < 5 and date not in HOLIDAYS


# ---------------------------------------------------------------------------
# 1) P-DEMO-002 이서준 : v2 → v3 수정
# ---------------------------------------------------------------------------
STATION_AREA = {"봉천": "관악구 봉천동", "역삼": "강남구 역삼동", "안국": "종로구 안국동", "홍대입구": "마포구 동교동",
                "홍대": "마포구 동교동", "성수": "성동구 성수동", "종합운동장": "송파구 잠실동", "잠실": "송파구 잠실동",
                "강남": "강남구 역삼동", "선릉": "강남구 대치동", "고속터미널": "서초구 반포동"}
# 봉천 기준 거리비례 요금 (10km 이하 1,550 / 15km 이하 1,650 / 20km 이하 1,750)
FARE = {("봉천", "역삼"): 1550, ("역삼", "봉천"): 1550, ("봉천", "홍대입구"): 1650, ("봉천", "안국"): 1650,
        ("안국", "봉천"): 1650, ("봉천", "종합운동장"): 1650, ("봉천", "강남"): 1550, ("강남", "봉천"): 1550,
        ("봉천", "선릉"): 1650, ("선릉", "봉천"): 1650, ("봉천", "고속터미널"): 1550, ("고속터미널", "봉천"): 1550,
        ("역삼", "성수"): 1650, ("역삼", "홍대입구"): 1750}
LOCAL_002 = {"봉천 피트니스", "봉천 로스터리", "역삼 순대국집", "봉천 칼국수", "역삼 한식뷔페", "역삼 돈까스집",
             "봉천 헤어살롱", "역삼 연세내과", "봉천 온누리약국", "샤로수길 파스타", "회사 구내식당", "봉천 쌀국수"}


def fix_p002():
    rows = list(csv.DictReader(io.open(V2, encoding="utf-8-sig")))
    by = {r["transaction_id"][-4:]: r for r in rows}
    drop = set()

    # --- 동선 모순 9건 ---------------------------------------------------
    drop.add("0024")                                           # 6/12 퇴근 탭 삭제: 모임이 회사 근처(역삼), 도보 이동
    by["0025"]["memo"] = "모임 4인, 내가 대표 결제 (회사 근처, 퇴근 후 도보 이동 / N빵 정산 예정)"
    by["0154"].update(memo="모임 이동 (역삼→성수)", amount_krw="1650")      # 7/17
    by["0315"].update(memo="모임 이동 (역삼→성수)", amount_krw="1650")      # 8/28
    drop.add("0233")                                           # 8/7 퇴근 탭 삭제 (회사에서 바로 홍대로)
    by["0234"]["amount_krw"] = "1750"
    by["0281"].update(merchant="역삼 돈까스집", merchant_id="M-17", merchant_area="강남구 역삼동",
                      amount_krw="11000", memo="야근 전 저녁")           # 8/20 봉천 저녁 → 역삼 저녁
    by["0141"].update(transaction_time="22:35", memo="야근 후 퇴근 (역삼역→봉천역)")  # 7/14
    by["0172"]["transaction_time"] = "19:28"                    # 7/21 약국: 지하철 이동 시간 반영
    by["0173"]["transaction_time"] = "19:50"
    by["0310"]["transaction_time"] = "19:10"                    # 8/27 퇴근 먼저
    by["0309"].update(transaction_time="19:42")                 # 약국 나중
    drop.add("0330")                                           # 9/1 저녁 2회 → 신규 가맹점(PENDING) 건만 유지

    # --- 현실성 ---------------------------------------------------------
    for k in ("0210", "0262", "0264"):                          # 점심 시간대 외식 소분류
        by[k]["subcategory"] = "점심"
    by["0266"]["memo"] = "이동 (봉천→강남, 교보문고 강남점 도보)"
    by["0245"]["memo"] = "경기 후 택시 귀가 (종합운동장→봉천)"    # 야구장은 종합운동장역
    by["0318"]["memo"] = "이동 (봉천→고속터미널)"                # 신세계 강남점은 고속터미널역
    by["0320"]["memo"] = "귀가 (고속터미널→봉천)"

    # --- 스키마 의미 ------------------------------------------------------
    for r in rows:
        if r["merchant"] == "(주)케이마케팅 급여":
            r["is_fixed"] = "TRUE"
        if r["direction"] == "INCOME":
            r["spend_pattern"] = "N/A"
        r["memo"] = r["memo"].replace("→ ACC-DEMO-003", "→ ACC-DEMO-002-S")
        h, mi = r["transaction_time"].split(":")
        r["transaction_time"] = hhmm(int(h), int(mi))
        r["merchant_id"] = r["merchant_id"].replace("M-", "M2-")
    # 헬스장 첫 거래: 반복성은 두 번째 결제부터 알 수 있음
    by["0001"].update(is_fixed="FALSE", is_recurring="FALSE", spend_pattern="PLANNED",
                      memo="월 회원권 (첫 결제, 사용자 확정)")

    # 교통 승차지역 + 거리비례 요금
    for r in rows:
        mm = re.search(r"\((\S+?)→(\S+?)\)", r["memo"])
        if r["merchant"] in ("서울교통공사", "카카오T") and mm:
            o, dst = mm.group(1), mm.group(2)
            o = o[:-1] if o.endswith("역") else o
            dst = dst[:-1] if dst.endswith("역") else dst
            r["merchant_area"] = STATION_AREA[o]
            if r["merchant"] == "서울교통공사":
                r["amount_krw"] = str(FARE[(o, dst)])

    # 동네 가맹점: 첫 거래 MODEL/CONFIRMED, 이후 RULE/AUTO
    seen = set()
    for r in sorted(rows, key=lambda r: (r["transaction_date"], r["transaction_time"])):
        if r["transaction_id"][-4:] in drop:
            continue
        if r["merchant"] in LOCAL_002:
            if r["merchant"] in seen and r["confirm_status"] != "PENDING":
                r["classify_source"], r["confirm_status"] = "RULE", "AUTO"
            seen.add(r["merchant"])

    out = [r for r in rows if r["transaction_id"][-4:] not in drop]
    out.sort(key=lambda r: (r["transaction_date"], r["transaction_time"]))
    for i, r in enumerate(out, 1):
        r["transaction_id"] = "TX-DEMO2-%04d" % i
    write_csv(os.path.join(HERE, "persona_consumption_90d_v3_P002.csv"), out)
    return out


# ---------------------------------------------------------------------------
# 2) P-DEMO-003 김하늘 (24, 대학생·카페 알바, 마포구 신수동 자취)
# ---------------------------------------------------------------------------
def gen_p003():
    b = Builder(3, "김하늘", 24, "대학생 (4학년, 카페 알바)", "서울 마포구 신수동", "한빛대학교 (마포구 신수동)",
                "월 100~150만원 (알바+용돈)", seed=3003)
    m = b.m
    # 가맹점
    m("한빛대 학생식당", "마포구 신수동", "식비", "점심", "local")
    m("컴포즈커피 한빛대점", "마포구 신수동", "식비", "카페", "chain")
    m("GS25 신수점", "마포구 신수동", "식비", "편의점", "chain")
    m("GS25 서울역점", "용산구 동자동", "식비", "편의점", "chain")
    m("신수 김밥나라", "마포구 신수동", "식비", "점심", "local")
    m("한솥도시락 신수점", "마포구 신수동", "식비", "점심", "chain")
    m("요기요", "마포구 신수동", "식비", "배달", "online")
    m("스타벅스 신촌점", "서대문구 창천동", "식비", "카페", "chain")
    m("신수 스터디카페", "마포구 신수동", "교육", "스터디카페", "local")
    m("해커스 인강", "온라인", "교육", "온라인 강의", "online")
    m("한국TOEIC위원회", "온라인", "교육", "시험 응시료", "online")
    m("한빛대학교 등록금", "온라인", "교육", "등록금", "rule")
    m("서울교통공사", "마포구 신수동", "교통", "대중교통", "chain")
    m("서울시내버스", "마포구 신수동", "교통", "대중교통", "chain")
    m("부산교통공사", "부산 해운대구 우동", "교통", "대중교통", "chain")
    m("코레일", "온라인", "교통", "기차", "online")
    m("야놀자", "온라인", "여가·문화", "숙박", "online")
    m("해운대 밀면집", "부산 해운대구 우동", "식비", "점심", "local")
    m("광안리 카페 블루", "부산 수영구 광안동", "식비", "카페", "local")
    m("서면 돼지국밥", "부산 부산진구 부전동", "식비", "점심", "local")
    m("CU 해운대해변점", "부산 해운대구 우동", "식비", "편의점", "chain")
    m("집주인 박OO (월세)", "마포구 신수동", "주거·통신", "월세", "rule")
    m("한국전력", "온라인", "주거·통신", "전기요금", "rule")
    m("서울도시가스", "온라인", "주거·통신", "가스요금", "rule")
    m("KT M모바일", "온라인", "주거·통신", "통신", "chain")
    m("유튜브 프리미엄", "온라인", "주거·통신", "구독", "chain")
    m("쿠팡와우", "온라인", "주거·통신", "구독", "chain")
    m("카페 모먼트 신수점 (알바 급여)", "온라인", "수입", "알바 급여", "rule")
    m("어머니 (용돈)", "온라인", "수입", "가족 지원", "person")
    m("어머니 (월세 지원)", "온라인", "수입", "가족 지원", "person")
    m("어머니 (등록금)", "온라인", "수입", "가족 지원", "person")
    m("카카오뱅크 세이프박스", "온라인", "저축·투자", "예금", "rule")
    m("이준호", "온라인", "사회·경조", "모임 정산", "person")
    m("정다은", "온라인", "사회·경조", "모임 정산", "person")
    m("김서연 (동아리 총무)", "온라인", "사회·경조", "회비", "person")
    m("홍대 포차거리 술집", "마포구 서교동", "사회·경조", "모임", "local")
    m("카카오 선물하기", "온라인", "사회·경조", "선물", "online")
    m("코인노래방 신촌", "서대문구 창천동", "여가·문화", "노래방", "local")
    m("메가박스 홍대", "마포구 서교동", "여가·문화", "영화/공연", "chain")
    m("신촌 맑은피부과", "서대문구 창천동", "건강", "병원", "local")
    m("온누리약국 신촌점", "서대문구 창천동", "건강", "약국", "local")
    m("다비치안경 신촌점", "서대문구 창천동", "건강", "안경", "chain")
    m("에이블리", "온라인", "쇼핑", "의류", "online")
    m("무신사", "온라인", "쇼핑", "의류", "online")
    m("올리브영 신촌점", "서대문구 창천동", "쇼핑", "뷰티·건강", "chain")
    m("다이소 신촌점", "서대문구 창천동", "쇼핑", "생활용품", "chain")
    m("쿠팡", "온라인", "쇼핑", "생활용품", "online")
    m("신수 헤어", "마포구 신수동", "생활서비스", "미용", "local")
    m("신수동 마라탕", "마포구 신수동", "식비", "저녁/외식", "local")

    R = b.rng
    exam = {d(6, 15), d(6, 16), d(6, 17), d(6, 18), d(6, 19)}
    busan = {d(8, 3), d(8, 4)}
    term_end = d(6, 19)

    def day(date):
        wd = date.weekday()
        if date in busan:
            return
        if date <= term_end and is_workday(date):                       # 학기 중 평일
            b.add(date, b.t(12, 20, 25), "한빛대 학생식당", 4500, "학식")
            if R.random() < 0.6:
                b.add(date, b.t(13, 10, 10), "컴포즈커피 한빛대점", 1800, "식후 커피")
            if date in exam:
                b.add(date, b.t(19, 30, 20), "GS25 신수점", b.amt(6800, 0.3), "기말 기간 저녁 (편의점)")
                b.add(date, b.t(23, 20, 25), "GS25 신수점", b.amt(4200, 0.3), "기말 야식")
            elif R.random() < 0.4:
                b.add(date, b.t(20, 40, 40), "GS25 신수점", b.amt(4500, 0.4), "저녁 간식")
        elif date <= term_end:                                             # 학기 중 주말 = 알바 (10~16시)
            if date != d(6, 13) and R.random() < 0.5:                      # 6/13 은 홍대 약속
                b.add(date, b.t(19, 40, 30), "요기요", b.amt(17000, 0.15), "알바 후 배달 저녁")
        elif date > d(6, 21):                                              # 방학
            if wd in (0, 1, 3, 4) and date not in HOLIDAYS:                # 알바 월화목금 13~19시
                pick = R.random()
                if pick < 0.4:
                    b.add(date, b.t(12, 10, 10), "한솥도시락 신수점", 5900, "알바 전 점심")
                elif pick < 0.7:
                    b.add(date, b.t(12, 5, 10), "신수 김밥나라", 4000, "알바 전 점심")
                else:
                    b.add(date, b.t(12, 15, 10), "GS25 신수점", b.amt(4800, 0.25), "알바 전 점심 (편의점)")
                pick = R.random()
                if pick < 0.3:
                    b.add(date, b.t(19, 35, 15), "요기요", b.amt(16500, 0.15), "알바 후 배달 저녁")
                elif pick < 0.6:
                    b.add(date, b.t(19, 20, 15), "GS25 신수점", b.amt(6200, 0.3), "알바 후 저녁 (편의점)")
            elif wd == 2:                                                  # 수요일 휴무: 토익 공부
                if R.random() < 0.7:
                    b.add(date, b.t(14, 0, 40), "스타벅스 신촌점", 4500, "토익 인강 공부 (카페)")
                if R.random() < 0.4:
                    b.add(date, b.t(20, 10, 40), "GS25 신수점", b.amt(5000, 0.3), "저녁 간식")
            elif wd in (5, 6):
                if date != d(7, 26) and R.random() < 0.35:                 # 7/26 은 토익 시험
                    b.add(date, b.t(13, 20, 40), "요기요", b.amt(15500, 0.15), "주말 배달 점심")
                if date != d(7, 4) and R.random() < 0.3:                   # 7/4 는 홍대 술자리
                    b.add(date, b.t(21, 30, 30), "GS25 신수점", b.amt(4300, 0.3), "주말 야식")

    each_day(day)

    # 고정비 / 수입 -------------------------------------------------------
    for mo in (6, 7, 8):
        b.bill(d(mo, 28), "08:00", "집주인 박OO (월세)", 500000, "월세 자동이체")
        b.bill(d(mo, 28), "08:00", "집주인 박OO (월세)", 50000, "원룸 관리비 (월세와 별도 이체)")
        b.cardbill(d(mo, 20), "03:05", "KT M모바일", 22000, "알뜰폰 요금 자동결제")
        b.cardbill(d(mo, 15), "03:10", "쿠팡와우", 7890, "구독 자동결제")
        b.income(d(mo, 10), "10:00", "카페 모먼트 신수점 (알바 급여)", {6: 536600, 7: 784300, 8: 1032000}[mo],
                 {6: "5월 알바 급여 (학기 중 주말 52h)", 7: "6월 알바 급여 (학기말+방학 76h)",
                  8: "7월 알바 급여 (방학 100h)"}[mo], fixed=False)
        b.recv(d(mo, 25), "09:12", "어머니 (월세 지원)", 500000, "월세 지원 (매월 25일)")
        b.save(d(mo, 11), "08:00", "카카오뱅크 세이프박스", 100000, "알바 급여 다음날 저축 → ACC-DEMO-003-S")
    b.bill(d(6, 18), "09:30", "한국전력", 23400, "전기요금(전월 사용분, 변동)", fixed=False)
    b.bill(d(7, 18), "09:30", "한국전력", 31900, "전기요금(전월 사용분, 변동)", fixed=False)
    b.bill(d(8, 18), "09:30", "한국전력", 48700, "전기요금(7월 냉방, 변동)", fixed=False)
    b.bill(d(6, 25), "09:30", "서울도시가스", 9800, "도시가스 요금(변동)", fixed=False)
    b.bill(d(7, 25), "09:30", "서울도시가스", 6400, "도시가스 요금(변동)", fixed=False)
    b.bill(d(8, 25), "09:30", "서울도시가스", 5900, "도시가스 요금(변동)", fixed=False)
    for mo in (7, 8, 9):
        b.cardbill(d(mo, 3), "03:10", "유튜브 프리미엄", 14900, "구독 자동결제")
        b.recv(d(mo, 1), "08:30", "어머니 (용돈)", 500000, "월 용돈")
    b.recv(d(8, 24), "19:40", "어머니 (등록금)", 2150000, "2학기 등록금 지원")
    b.add(d(8, 25), "10:20", "한빛대학교 등록금", 2150000, "2학기 등록금 납부 (고지서, 계좌이체)", ttype="WITHDRAW",
          pay="ACCOUNT", pattern="PLANNED", src="USER", status="CONFIRMED")

    # 학업 --------------------------------------------------------------
    b.add(d(6, 8), "09:05", "신수 스터디카페", 45000, "기말 대비 2주권", pattern="PLANNED")
    b.add(d(6, 23), "21:30", "해커스 인강", 99000, "토익 인강 (방학 목표)", pattern="PLANNED")
    b.add(d(7, 6), "22:15", "한국TOEIC위원회", 48000, "7/26 토익 정기시험 접수", pattern="PLANNED")
    b.add(d(7, 26), "07:40", "GS25 신수점", 3200, "토익 시험 날 아침")
    b.add(d(7, 26), "08:05", "서울교통공사", 1550, "시험장 이동 (신촌→목동)", area="서대문구 창천동")
    b.add(d(7, 26), "12:25", "서울교통공사", 1550, "귀가 (목동→신촌)", area="양천구 목동")
    b.add(d(7, 26), "13:10", "신수 김밥나라", 4000, "시험 후 점심")

    # 사회 --------------------------------------------------------------
    b.send(d(6, 12), "21:10", "김서연 (동아리 총무)", 15000, "동아리 회비 (6월)")
    b.add(d(6, 13), "18:20", "서울시내버스", 1500, "이동 (신수동→홍대입구)")
    b.send(d(6, 13), "23:30", "이준호", 21000, "홍대 술자리 N빵 (이준호 결제)")
    b.add(d(6, 13), "23:45", "서울시내버스", 1500, "귀가 (홍대입구→신수동)", area="마포구 서교동")
    b.add(d(7, 4), "18:10", "서울시내버스", 1500, "이동 (신수동→홍대입구)")
    b.add(d(7, 4), "21:40", "홍대 포차거리 술집", 56000, "친구 2인, 내가 대표 결제 (N빵 예정)", pattern="PLANNED")
    b.add(d(7, 4), "23:50", "서울시내버스", 1500, "귀가 (홍대입구→신수동)", area="마포구 서교동")
    b.recv(d(7, 5), "11:20", "정다은", 28000, "7/4 홍대 N빵 입금")
    b.add(d(7, 9), "20:30", "카카오 선물하기", 25000, "친구 생일 선물", pattern="PLANNED")
    b.add(d(8, 22), "16:40", "코인노래방 신촌", 8000, "충동: 지나가다 코노", pattern="IMPULSE")
    b.add(d(8, 29), "14:00", "서울시내버스", 1500, "이동 (신수동→홍대입구)")
    b.add(d(8, 29), "14:30", "메가박스 홍대", 15000, "영화", pattern="PLANNED")
    b.add(d(8, 29), "17:20", "서울시내버스", 1500, "귀가 (홍대입구→신수동)", area="마포구 서교동")

    # 부산 여행 8/3~8/4 -------------------------------------------------
    b.add(d(7, 20), "22:40", "코레일", 119600, "KTX 서울↔부산 왕복 예매 (8/3~8/4)", pattern="PLANNED")
    b.add(d(7, 20), "22:55", "야놀자", 45000, "해운대 게스트하우스 1박 (8/3)", pattern="PLANNED")
    b.add(d(8, 3), "07:05", "서울교통공사", 1550, "이동 (신촌→서울역)", area="서대문구 창천동")
    b.add(d(8, 3), "07:30", "GS25 서울역점", 4500, "KTX 탑승 전 아침")
    b.add(d(8, 3), "11:40", "부산교통공사", 1600, "이동 (부산역→해운대)", area="부산 동구 초량동")
    b.add(d(8, 3), "12:20", "해운대 밀면집", 9000, "부산 점심", pattern="PLANNED")
    b.add(d(8, 3), "15:10", "부산교통공사", 1600, "이동 (해운대→광안)")
    b.add(d(8, 3), "15:40", "광안리 카페 블루", 6500, "광안리 카페", pattern="PLANNED")
    b.add(d(8, 3), "22:10", "CU 해운대해변점", 5800, "숙소 야식")
    b.add(d(8, 4), "09:20", "부산교통공사", 1600, "이동 (해운대→서면)")
    b.add(d(8, 4), "09:50", "서면 돼지국밥", 10000, "부산 아침 겸 점심", pattern="PLANNED")
    b.send(d(8, 4), "10:30", "정다은", 32000, "8/3 광안리 조개구이 N빵 (정다은 결제)")
    b.add(d(8, 4), "15:40", "부산교통공사", 1600, "이동 (서면→부산역)", area="부산 부산진구 부전동")
    b.add(d(8, 4), "20:10", "서울교통공사", 1550, "귀가 (서울역→신촌)", area="용산구 동자동")

    # 건강 / 쇼핑 / 미용 ----------------------------------------------------
    b.add(d(6, 30), "16:30", "신촌 맑은피부과", 15000, "여드름 진료")
    b.add(d(6, 30), "16:55", "온누리약국 신촌점", 8400, "처방약")
    b.add(d(8, 21), "15:20", "다비치안경 신촌점", 89000, "안경 렌즈 교체", pattern="PLANNED")
    b.add(d(6, 27), "14:10", "신수 헤어", 20000, "커트")
    b.add(d(7, 25), "14:30", "신수 헤어", 20000, "커트")
    b.add(d(8, 29), "11:30", "신수 헤어", 20000, "커트")
    b.add(d(6, 27), "15:00", "올리브영 신촌점", 22300, "기초화장품", pattern="PLANNED")
    b.add(d(7, 11), "23:50", "에이블리", 39900, "충동 구매: 급여 다음날 심야 의류", pattern="IMPULSE")
    b.add(d(8, 11), "23:10", "무신사", 58000, "충동 구매: 급여 다음날 심야 의류", pattern="IMPULSE")
    b.add(d(7, 18), "16:00", "다이소 신촌점", 8000, "생활용품", pattern="PLANNED")
    for mo, day_ in ((6, 16), (7, 14), (8, 12)):
        b.add(d(mo, day_), "21:20", "쿠팡", b.amt(24000, 0.15), "생필품 온라인", pattern="PLANNED")
    b.add(d(9, 2), "12:40", "신수동 마라탕", 12500, "수요일 점심 (신규 가맹점)", src="MODEL", status="PENDING",
          sub="점심")

    return b.finish(os.path.join(HERE, "persona_consumption_90d_v3_P003.csv"))


# ---------------------------------------------------------------------------
# 3) P-DEMO-004 박정민 (42, 프리랜서 백엔드 개발자, 기혼·자녀1, 분당 정자동, 차량 보유)
# ---------------------------------------------------------------------------
def gen_p004():
    b = Builder(4, "박정민", 42, "프리랜서 백엔드 개발자 (기혼, 자녀 1)", "경기 성남시 분당구 정자동",
                "판교 코워킹 스페이스 (월~목) / 재택 (금)", "월 350~450만원 (프로젝트+유지보수, 변동)", seed=4004)
    m = b.m
    m("샐러디 판교점", "성남 분당구 삼평동", "식비", "점심", "chain")
    m("백소정 판교점", "성남 분당구 삼평동", "식비", "점심", "chain")
    m("판교 순두부집", "성남 분당구 삼평동", "식비", "점심", "local")
    m("본죽&비빔밥 판교점", "성남 분당구 삼평동", "식비", "점심", "chain")
    m("폴바셋 판교점", "성남 분당구 삼평동", "식비", "카페", "chain")
    m("CU 판교테크노밸리점", "성남 분당구 삼평동", "식비", "편의점", "chain")
    m("GS25 정자점", "성남 분당구 정자동", "식비", "편의점", "chain")
    m("배달의민족", "성남 분당구 정자동", "식비", "배달", "online")
    m("이마트 분당점", "성남 분당구 서현동", "식비", "장보기", "chain")
    m("아웃백 정자점", "성남 분당구 정자동", "식비", "저녁/외식", "chain")
    m("정자동 브런치 카페 마고", "성남 분당구 정자동", "식비", "저녁/외식", "local")
    m("분당 한우갈비", "성남 분당구 정자동", "식비", "저녁/외식", "local")
    m("빕스 서현점", "성남 분당구 서현동", "식비", "저녁/외식", "chain")
    m("정자 쌀국수", "성남 분당구 정자동", "식비", "저녁/외식", "local")
    m("스타벅스 정자점", "성남 분당구 정자동", "식비", "카페", "chain")
    m("SK에너지 정자셀프", "성남 분당구 정자동", "교통", "주유", "chain")
    m("정자 자동세차", "성남 분당구 정자동", "교통", "세차", "local")
    m("삼성역 공영주차장", "강남구 삼성동", "교통", "주차", "local")
    m("카카오T 대리", "강남구 역삼동", "교통", "대리운전", "chain")
    m("KB국민은행 주택담보대출", "온라인", "주거·통신", "대출 상환", "rule")
    m("정자 ○○아파트 관리사무소", "온라인", "주거·통신", "관리비", "rule")
    m("SKT", "온라인", "주거·통신", "통신", "rule")
    m("LG U+ 키즈폰", "온라인", "주거·통신", "통신", "chain")
    m("KT 인터넷", "온라인", "주거·통신", "인터넷", "rule")
    m("넷플릭스", "온라인", "주거·통신", "구독", "chain")
    m("OPENAI CHATGPT SUBSCR", "해외", "주거·통신", "구독", "chain")
    m("GITHUB COPILOT", "해외", "주거·통신", "구독", "chain")
    m("쿠팡와우", "온라인", "주거·통신", "구독", "chain")
    m("패스트파이브 판교", "성남 분당구 삼평동", "업무", "코워킹", "chain")
    m("국민건강보험공단", "온라인", "세금·공과", "사회보험", "rule")
    m("국민연금공단", "온라인", "세금·공과", "사회보험", "rule")
    m("위택스 (자동차세)", "온라인", "세금·공과", "자동차세", "online")
    m("정자 태권도장", "성남 분당구 정자동", "교육", "자녀 학원", "local")
    m("정자 피아노교습소 김OO", "온라인", "교육", "자녀 학원", "person")
    m("정자 영어학원 (여름캠프)", "온라인", "교육", "자녀 캠프", "person")
    m("알파문구 정자점", "성남 분당구 정자동", "교육", "학용품", "chain")
    m("알라딘", "온라인", "교육", "도서", "online")
    m("정자 키즈카페", "성남 분당구 정자동", "여가·문화", "키즈카페", "local")
    m("CGV 오리", "성남 분당구 구미동", "여가·문화", "영화/공연", "chain")
    m("토이저러스 판교점", "성남 분당구 삼평동", "쇼핑", "장난감", "chain")
    m("쿠팡", "온라인", "쇼핑", "생활용품", "online")
    m("무신사", "온라인", "쇼핑", "의류", "online")
    m("스팀", "온라인", "여가·문화", "게임", "online")
    m("스포애니 정자점", "성남 분당구 정자동", "여가·문화", "헬스장", "chain")
    m("정자 소아청소년과", "성남 분당구 정자동", "건강", "병원", "local")
    m("정자 온누리약국", "성남 분당구 정자동", "건강", "약국", "local")
    m("정자 미소치과", "성남 분당구 정자동", "건강", "병원", "local")
    m("㈜넥스트커머스", "온라인", "수입", "프로젝트 대금", "rule")
    m("㈜데이터브릿지", "온라인", "수입", "프로젝트 대금", "rule")
    m("배우자 (생활비)", "온라인", "수입", "가족 생활비", "person")
    m("미래에셋 IRP", "온라인", "저축·투자", "연금", "rule")
    m("삼성증권 CMA", "온라인", "저축·투자", "증권", "rule")
    m("강남 한정식 미담", "강남구 역삼동", "업무", "고객 미팅", "local")
    m("스타벅스 삼성역점", "강남구 삼성동", "업무", "고객 미팅", "chain")
    m("이재현 (후배 결혼 축의금)", "온라인", "사회·경조", "경조사", "person")
    m("어머니 (생신 용돈)", "온라인", "사회·경조", "가족 용돈", "person")
    m("수원 한정식 고향", "수원 팔달구 인계동", "사회·경조", "가족 외식", "local")
    m("야놀자", "온라인", "여가·문화", "숙박", "online")
    m("강릉 초당 순두부집", "강릉 초당동", "식비", "점심", "local")
    m("테라로사 강릉", "강릉 구정면", "식비", "카페", "chain")
    m("강릉 중앙시장 닭강정", "강릉 성남동", "식비", "간식", "local")
    m("GS25 강릉경포점", "강릉 안현동", "식비", "편의점", "chain")
    m("경포 카페 라운지", "강릉 안현동", "식비", "카페", "local")
    m("강릉 사천 회센터", "강릉 사천면", "식비", "저녁/외식", "local")
    m("경포 아쿠아리움", "강릉 안현동", "여가·문화", "관람", "local")
    m("강릉 교동짬뽕", "강릉 교동", "식비", "점심", "local")
    m("SK에너지 강릉IC셀프", "강릉 홍제동", "교통", "주유", "chain")
    m("판교 라멘집", "성남 분당구 삼평동", "식비", "점심", "local")

    R = b.rng
    trip = {d(7, 31), d(8, 1), d(8, 2)}
    lunches = [("샐러디 판교점", 10900), ("백소정 판교점", 12500), ("판교 순두부집", 9500),
               ("본죽&비빔밥 판교점", 9800)]
    sunday_out = [("아웃백 정자점", 89000), ("정자동 브런치 카페 마고", 42000), ("분당 한우갈비", 138000),
                  ("빕스 서현점", 96000), ("정자 쌀국수", 34000), ("정자동 브런치 카페 마고", 46000)]
    sun_i = [0]

    def day(date):
        wd = date.weekday()
        if date in trip:
            return
        if is_workday(date) and wd <= 3:                                # 코워킹 출근 (자가용, 결제 없음)
            if date in (d(6, 24), d(7, 22), d(8, 19), d(9, 1)):
                return                                                   # 고객 미팅 / 신규 가맹점 날 별도 처리
            name, price = R.choice(lunches)
            b.add(date, b.t(12, 20, 20), name, price, "판교 점심")
            if R.random() < 0.7:
                b.add(date, b.t(13, 15, 10), "폴바셋 판교점", 5300, "식후 커피")
            if R.random() < 0.25:
                b.add(date, b.t(16, 30, 30), "CU 판교테크노밸리점", b.amt(3200, 0.3), "오후 간식")
        elif is_workday(date) and wd == 4:                              # 금요일 재택 + 하원 픽업
            if R.random() < 0.4:
                b.add(date, b.t(12, 30, 15), "배달의민족", b.amt(15500, 0.15), "재택 점심 배달")
            if R.random() < 0.45:
                b.add(date, b.t(16, 10, 20), "GS25 정자점", b.amt(6500, 0.3), "하원 후 아이 간식")
            if R.random() < 0.55:
                b.add(date, b.t(19, 10, 20), "배달의민족", b.amt(29000, 0.12), "금요일 가족 배달 (치킨/피자)")
        elif wd == 5 and date not in trip:                              # 토요일 장보기
            b.add(date, b.t(11, 0, 30), "이마트 분당점", b.amt(182000, 0.18, 100), "주간 장보기 (3인)", pattern="PLANNED")
            if R.random() < 0.5:
                b.add(date, b.t(15, 20, 40), "정자 키즈카페", 18000, "아이 키즈카페", pattern="PLANNED")
        elif wd == 6 and date not in trip:                              # 일요일 가족 외식
            if date != d(8, 16) and R.random() < 0.75:                  # 8/16 은 어머니 생신 (수원)
                name, price = sunday_out[sun_i[0] % len(sunday_out)]
                sun_i[0] += 1
                b.add(date, b.t(12, 30, 20), name, price, "가족 외식 (3인)", pattern="PLANNED")
                if R.random() < 0.6:
                    b.add(date, b.t(14, 20, 30), "스타벅스 정자점", 13400, "가족 카페")

    each_day(day)

    # 고객 미팅 (강남, 자가용) ------------------------------------------------
    b.add(d(6, 24), "12:10", "판교 순두부집", 9500, "판교 점심")
    b.add(d(6, 24), "18:40", "삼성역 공영주차장", 14000, "고객 회식 주차", cat="업무", sub="고객 미팅")
    b.add(d(6, 24), "23:10", "카카오T 대리", 38000, "회식 후 대리운전 (삼성→정자)", pattern="PLANNED")
    b.add(d(7, 22), "12:05", "강남 한정식 미담", 66000, "고객 미팅 점심 (2인, 내가 결제)", pattern="PLANNED")
    b.add(d(7, 22), "13:40", "삼성역 공영주차장", 8000, "미팅 주차")
    b.add(d(8, 19), "10:20", "스타벅스 삼성역점", 11200, "고객 미팅 커피", pattern="PLANNED")
    b.add(d(8, 19), "11:50", "삼성역 공영주차장", 6000, "미팅 주차")
    b.add(d(8, 19), "13:10", "백소정 판교점", 12500, "판교 복귀 후 점심")

    # 차량 -----------------------------------------------------------------
    for date, amt in ((d(6, 13), 68000), (d(6, 27), 72000), (d(7, 11), 69500), (d(7, 25), 71000),
                      (d(8, 8), 66000), (d(8, 22), 70500)):
        b.add(date, "09:40", "SK에너지 정자셀프", amt, "주유")
    for date in (d(6, 13), d(7, 25), d(8, 22)):
        b.add(date, "10:05", "정자 자동세차", 12000, "세차")
    b.add(d(6, 26), "21:30", "위택스 (자동차세)", 224600, "자동차세 1기분 납부", pattern="PLANNED")

    # 고정비 -----------------------------------------------------------------
    for mo in (6, 7, 8):
        b.bill(d(mo, 15), "08:00", "KB국민은행 주택담보대출", 1382000, "주담대 원리금 자동이체")
        b.bill(d(mo, 25), "09:30", "정자 ○○아파트 관리사무소", {6: 212300, 7: 241800, 8: 318600}[mo],
               "아파트 관리비 (전기 포함, 변동)", fixed=False)
        b.bill(d(mo, 10), "09:30", "SKT", 69000, "휴대폰 요금 자동이체")
        b.cardbill(d(mo, 10), "03:10", "LG U+ 키즈폰", 19800, "자녀 키즈폰 자동결제")
        b.bill(d(mo, 20), "09:30", "KT 인터넷", 44000, "인터넷+IPTV 자동이체")
        b.bill(d(mo, 10), "09:30", "국민건강보험공단", 218400, "건강보험료 (지역가입자)")
        b.bill(d(mo, 10), "09:30", "국민연금공단", 283500, "국민연금 (지역가입자)")
        b.cardbill(d(mo, 8), "03:10", "OPENAI CHATGPT SUBSCR", {6: 29480, 7: 29120, 8: 29760}[mo],
                   "ChatGPT Plus $20 해외결제 (환율 변동)", fixed=False)
        b.cardbill(d(mo, 12), "03:10", "GITHUB COPILOT", {6: 14740, 7: 14560, 8: 14880}[mo],
                   "GitHub Copilot $10 해외결제 (환율 변동)", fixed=False)
        b.cardbill(d(mo, 18), "03:10", "쿠팡와우", 7890, "구독 자동결제")
        b.recv(d(mo, 25), "18:30", "배우자 (생활비)", 1500000, "배우자 생활비 분담 (매월 25일)")
        b.income(d(mo, 15), "11:00", "㈜넥스트커머스", 531850, "유지보수 계약 월 대금 (총 55만, 3.3% 원천징수 후)",
                 fixed=True)
        b.save(d(mo, 27), "08:00", "미래에셋 IRP", 300000, "IRP 자동이체 → ACC-DEMO-004-IRP")
    for mo in (7, 8, 9):
        b.cardbill(d(mo, 3), "03:10", "넷플릭스", 13500, "구독 자동결제")
        b.cardbill(d(mo, 1), "03:10", "패스트파이브 판교", 259000, "코워킹 월 이용권 자동결제")
        b.cardbill(d(mo, 2), "03:10", "스포애니 정자점", 39000, "헬스장 월 회원권 자동결제")
    for mo in (7, 8):
        b.add(biz(d(mo, 5)), "18:30", "정자 태권도장", 160000, "자녀 태권도 월 수강료", pattern="FIXED",
              fixed=True, recurring=True)
        b.send(biz(d(mo, 5)), "18:35", "정자 피아노교습소 김OO", 180000, "자녀 피아노 월 수강료", pattern="FIXED")

    # 수입 ----------------------------------------------------------------
    b.income(d(6, 10), "14:20", "㈜넥스트커머스", 2901000, "프로젝트 잔금 (총 300만, 3.3% 원천징수 후)",
             recurring=False, fixed=False)
    b.income(d(6, 30), "15:05", "㈜데이터브릿지", 4351500, "신규 프로젝트 착수금 (총 450만, 3.3% 원천징수 후)",
             recurring=False, fixed=False)
    b.income(d(8, 14), "11:40", "㈜데이터브릿지", 3868000, "프로젝트 중도금 (총 400만, 3.3% 원천징수 후)",
             recurring=False, fixed=False)
    b.add(d(8, 14), "12:30", "삼성증권 CMA", 1500000, "중도금 일부 CMA 이동 → ACC-DEMO-004-CMA", direction="TRANSFER",
          ttype="TRANSFER_OUT", pay="ACCOUNT", pattern="PLANNED", excl="INTERNAL_TRANSFER", src="USER",
          status="CONFIRMED")

    # 자녀 / 건강 -----------------------------------------------------------
    b.add(d(6, 9), "17:10", "알파문구 정자점", 12000, "학용품", pattern="PLANNED")
    b.add(d(6, 16), "17:30", "정자 소아청소년과", 8500, "자녀 감기 진료")
    b.add(d(6, 16), "17:50", "정자 온누리약국", 6200, "자녀 처방약")
    b.send(d(7, 20), "20:10", "정자 영어학원 (여름캠프)", 250000, "자녀 여름 영어캠프 (8/3~8/7)")
    b.add(d(8, 12), "17:20", "정자 소아청소년과", 9000, "자녀 장염 진료")
    b.add(d(8, 12), "17:45", "정자 온누리약국", 7100, "자녀 처방약")
    b.add(d(7, 29), "18:20", "정자 미소치과", 18000, "스케일링 (건보)", pattern="PLANNED")
    b.add(d(8, 9), "15:30", "토이저러스 판교점", 69000, "충동 구매: 아이가 고른 장난감", pattern="IMPULSE")
    b.add(d(7, 12), "16:40", "CGV 오리", 45000, "가족 영화 3인", pattern="PLANNED")
    b.add(d(7, 16), "22:00", "알라딘", 32400, "기술서 2권", pattern="PLANNED")

    # 경조사 / 가족 -----------------------------------------------------------
    b.send(d(7, 4), "11:30", "이재현 (후배 결혼 축의금)", 100000, "후배 결혼식 축의금 (참석 못함, 송금)")
    b.send(d(8, 16), "09:00", "어머니 (생신 용돈)", 300000, "어머니 생신 용돈")
    b.add(d(8, 16), "12:40", "수원 한정식 고향", 168000, "어머니 생신 가족 식사 (5인)", pattern="PLANNED")

    # 충동 -----------------------------------------------------------------
    b.add(d(6, 11), "23:15", "무신사", 78000, "충동 구매: 잔금 입금 다음날 심야", pattern="IMPULSE")
    b.add(d(7, 1), "23:40", "쿠팡", 189000, "충동 구매: 착수금 다음날 기계식 키보드", pattern="IMPULSE")
    b.add(d(8, 15), "22:30", "스팀", 42000, "충동 구매: 연휴 게임 세일", pattern="IMPULSE")
    for date in (d(6, 19), d(7, 3), d(7, 17), d(8, 7), d(8, 21)):
        b.add(date, "21:40", "쿠팡", b.amt(58000, 0.2), "생활용품·기저귀 외 온라인", pattern="PLANNED")

    # 강릉 가족여행 7/31(금)~8/2(일) ------------------------------------------
    b.add(d(7, 10), "22:20", "야놀자", 380000, "강릉 펜션 2박 (7/31~8/2)", pattern="PLANNED")
    b.add(d(7, 31), "07:10", "SK에너지 정자셀프", 74000, "여행 출발 전 주유")
    b.add(d(7, 31), "12:20", "강릉 초당 순두부집", 38000, "강릉 점심 (3인)", pattern="PLANNED")
    b.add(d(7, 31), "15:00", "테라로사 강릉", 18500, "카페", pattern="PLANNED")
    b.add(d(7, 31), "18:30", "강릉 중앙시장 닭강정", 15000, "시장 간식")
    b.add(d(7, 31), "20:00", "GS25 강릉경포점", 12300, "펜션 간식·음료")
    b.add(d(8, 1), "09:10", "경포 카페 라운지", 34000, "브런치 (3인)", pattern="PLANNED")
    b.add(d(8, 1), "11:30", "경포 아쿠아리움", 66000, "아쿠아리움 3인", pattern="PLANNED")
    b.add(d(8, 1), "18:20", "강릉 사천 회센터", 95000, "저녁 회 (3인)", pattern="PLANNED")
    b.add(d(8, 1), "20:40", "GS25 강릉경포점", 8900, "펜션 간식")
    b.add(d(8, 2), "10:20", "경포 카페 라운지", 12000, "체크아웃 후 커피")
    b.add(d(8, 2), "12:10", "강릉 교동짬뽕", 36000, "귀가 전 점심 (3인)", pattern="PLANNED")
    b.add(d(8, 2), "13:30", "SK에너지 강릉IC셀프", 45000, "귀가 주유")

    b.add(d(9, 1), "12:15", "판교 라멘집", 11000, "판교 점심 (신규 가맹점)", src="MODEL", status="PENDING")
    b.add(d(9, 1), "13:12", "폴바셋 판교점", 5300, "식후 커피")
    return b.finish(os.path.join(HERE, "persona_consumption_90d_v3_P004.csv"))


# ---------------------------------------------------------------------------
# 4) P-DEMO-005 정미숙 (61, 은퇴 초등교사·공무원연금, 대구 수성구 범어동, 부부 2인)
# ---------------------------------------------------------------------------
def gen_p005():
    b = Builder(5, "정미숙", 61, "은퇴 (전 초등교사, 공무원연금 수령)", "대구 수성구 범어동", "해당 없음 (은퇴)",
                "월 250~300만원 (연금)", seed=5005)
    m = b.m
    m("범어 카페 그린", "대구 수성구 범어동", "식비", "카페", "local")
    m("파리바게뜨 범어점", "대구 수성구 범어동", "식비", "빵·간식", "chain")
    m("하나로마트 범어점", "대구 수성구 범어동", "식비", "장보기", "chain")
    m("대구은행 ATM 범어동", "대구 수성구 범어동", "현금", "ATM 출금", "rule")
    m("대구교통공사", "대구 수성구 범어동", "교통", "대중교통", "chain")
    m("대구시내버스", "대구 수성구 범어동", "교통", "대중교통", "chain")
    m("신세계 아카데미 대구", "대구 동구 신천동", "여가·문화", "문화센터", "chain")
    m("대구신세계 푸드코트", "대구 동구 신천동", "식비", "점심", "chain")
    m("대구신세계 (의류)", "대구 동구 신천동", "쇼핑", "의류", "chain")
    m("수성구민 스포츠센터", "대구 수성구 범어동", "여가·문화", "수영", "local")
    m("범어 손칼국수", "대구 수성구 범어동", "식비", "저녁/외식", "local")
    m("수성못 오리고기", "대구 수성구 두산동", "식비", "저녁/외식", "local")
    m("범어 초밥", "대구 수성구 범어동", "식비", "저녁/외식", "local")
    m("들안길 한정식", "대구 수성구 두산동", "식비", "저녁/외식", "local")
    m("범어 갈비", "대구 수성구 범어동", "식비", "저녁/외식", "local")
    m("범어 연합내과", "대구 수성구 범어동", "건강", "병원", "local")
    m("온누리약국 범어점", "대구 수성구 범어동", "건강", "약국", "local")
    m("범어 한의원", "대구 수성구 범어동", "건강", "한의원", "local")
    m("범어 미소치과", "대구 수성구 범어동", "건강", "병원", "local")
    m("CU 팔공산입구점", "대구 동구 용수동", "식비", "편의점", "chain")
    m("범어 ○○아파트 관리사무소", "온라인", "주거·통신", "관리비", "rule")
    m("대성에너지", "온라인", "주거·통신", "가스요금", "rule")
    m("SKT", "온라인", "주거·통신", "통신", "rule")
    m("KT 인터넷", "온라인", "주거·통신", "인터넷", "rule")
    m("현대해상 실손보험", "온라인", "보험", "실손보험", "rule")
    m("유니세프 정기후원", "온라인", "사회·경조", "기부", "chain")
    m("범어성당 교무금", "온라인", "사회·경조", "종교", "rule")
    m("공무원연금공단", "온라인", "수입", "연금", "rule")
    m("딸 김수진 (용돈)", "온라인", "수입", "가족 지원", "person")
    m("대구은행 정기적금", "온라인", "저축·투자", "적금", "rule")
    m("팔공산 산악회 총무 이OO", "온라인", "사회·경조", "회비", "person")
    m("박영희 (부의금)", "온라인", "사회·경조", "경조사", "person")
    m("조카 김지원 (축의금)", "온라인", "사회·경조", "경조사", "person")
    m("동창회 총무 최OO", "온라인", "사회·경조", "회비", "person")
    m("딸 김수진 (손주 용돈)", "온라인", "사회·경조", "가족 용돈", "person")
    m("코레일", "온라인", "교통", "기차", "online")
    m("카카오T", "서울 용산구 동자동", "교통", "택시", "chain")
    m("서울교통공사", "서울 강남구 논현동", "교통", "대중교통", "chain")
    m("스타벅스 서울역점", "서울 용산구 동자동", "식비", "카페", "chain")
    m("이월드", "대구 달서구 두류동", "여가·문화", "놀이공원", "chain")
    m("이월드 매점", "대구 달서구 두류동", "식비", "간식", "chain")
    m("범어 키즈카페", "대구 수성구 범어동", "여가·문화", "키즈카페", "local")
    m("GS SHOP", "온라인", "쇼핑", "건강식품", "online")
    m("다이소 범어점", "대구 수성구 범어동", "쇼핑", "생활용품", "chain")
    m("범어 미용실", "대구 수성구 범어동", "생활서비스", "미용", "local")
    m("반월당 카페 온", "대구 중구 덕산동", "식비", "카페", "local")
    m("범어 반찬가게", "대구 수성구 범어동", "식비", "반찬", "local")

    R = b.rng
    grand = {d(8, 7), d(8, 8), d(8, 9), d(8, 10)}
    seoul = d(7, 11)
    hikes = [d(6, 13), d(6, 27), d(7, 18), d(7, 25), d(8, 22)]
    sunday_out = [("범어 손칼국수", 18000), ("수성못 오리고기", 62000), ("범어 초밥", 48000), ("범어 손칼국수", 19000),
                  ("들안길 한정식", 54000), ("수성못 오리고기", 64000), ("범어 초밥", 52000)]
    sun_i = [0]

    def day(date):
        wd = date.weekday()
        if date == seoul or date in grand:
            return
        if wd == 0:                                                        # 월: ATM 현금 (시장 장보기)
            b.add(date, b.t(9, 30, 10), "대구은행 ATM 범어동", 100000, "주간 현금 (수성시장 장보기용)", ttype="WITHDRAW",
                  pay="ACCOUNT", pattern="ROUTINE", recurring=True, fixed=True)
        if wd in (0, 2, 4) and R.random() < 0.5:                           # 수영 후 카페 (월수금 07시 수영)
            b.add(date, b.t(9, 0, 15), "범어 카페 그린", 4500, "수영 후 지인과 커피")
        if wd == 1 and d(6, 9) <= date <= d(8, 25):                        # 화: 문화센터 요가 (동대구 신세계)
            b.add(date, b.t(9, 50, 10), "대구교통공사", 1500, "문화센터 이동 (범어→동대구)")
            if R.random() < 0.5:
                b.add(date, b.t(12, 30, 15), "대구신세계 푸드코트", b.amt(10500, 0.2), "요가 후 점심 (지인)")
            b.add(date, b.t(14, 0, 30), "대구교통공사", 1500, "귀가 (동대구→범어)", area="대구 동구 신천동")
        if wd == 5:
            if date in hikes:                                               # 팔공산 산행
                b.add(date, "07:30", "대구시내버스", 1500, "산행 이동 (범어→팔공산)")
                b.add(date, "08:35", "CU 팔공산입구점", b.amt(2500, 0.3), "물·간식")
                b.add(date, "16:10", "대구시내버스", 1500, "귀가 (팔공산→범어)", area="대구 동구 용수동")
            else:
                b.add(date, b.t(10, 30, 20), "하나로마트 범어점", b.amt(74000, 0.22), "주간 장보기", pattern="PLANNED")
            b.add(date, b.t(17, 30, 30), "파리바게뜨 범어점", b.amt(12800, 0.12), "주말 빵")
        if wd == 6 and R.random() < 0.7:                                    # 일: 성당(도보) 후 부부 외식
            name, price = sunday_out[sun_i[0] % len(sunday_out)]
            sun_i[0] += 1
            b.add(date, b.t(12, 30, 20), name, price, "성당 후 부부 외식", pattern="PLANNED")

    each_day(day)

    # 고정비 / 수입 ---------------------------------------------------------
    for mo in (6, 7, 8):
        b.bill(d(mo, 20), "09:30", "범어 ○○아파트 관리사무소", {6: 168400, 7: 197200, 8: 264900}[mo],
               "아파트 관리비 (전기 포함, 변동)", fixed=False)
        b.bill(d(mo, 12), "09:30", "대성에너지", {6: 14300, 7: 9800, 8: 8600}[mo], "도시가스 요금(변동)", fixed=False)
        b.bill(d(mo, 18), "09:30", "SKT", 45000, "휴대폰 요금 자동이체")
        b.bill(d(mo, 15), "09:30", "KT 인터넷", 38500, "인터넷+TV 자동이체")
        b.cardbill(d(mo, 15), "03:10", "유니세프 정기후원", 30000, "정기후원 자동결제")
        b.bill(d(mo, 10), "09:30", "범어성당 교무금", 100000, "교무금 자동이체")
        b.income(prevbiz(d(mo, 25)), "09:00", "공무원연금공단", 2680000, "공무원연금 (매월 25일, 휴일이면 전 영업일)",
                 bizday=False)
        b.save(d(mo, 26), "08:00", "대구은행 정기적금", 300000, "정기적금 자동이체 → ACC-DEMO-005-S")
    for mo in (7, 8):
        b.send(biz(d(mo, 3)), "10:00", "팔공산 산악회 총무 이OO", 20000, "산악회 월 회비", pattern="FIXED")
        b.bill(d(mo, 5), "09:30", "현대해상 실손보험", 87300, "실손보험료 자동이체")
    for mo in (7, 8, 9):
        b.recv(d(mo, 1), "20:15", "딸 김수진 (용돈)", 200000, "딸 용돈 (매월 1일)")
        if mo < 9:
            b.add(d(mo, 1), "08:10", "수성구민 스포츠센터", 62000, "수영 월 회원권", pattern="FIXED", fixed=True,
                  recurring=True)
    b.add(d(6, 8), "10:30", "대구교통공사", 1500, "문화센터 등록 이동 (범어→동대구)")
    b.add(d(6, 8), "11:10", "신세계 아카데미 대구", 165000, "여름학기 요가 12주 (6/9~8/25)", pattern="PLANNED")
    b.add(d(6, 8), "12:20", "대구신세계 푸드코트", 11000, "등록 후 점심")
    b.add(d(6, 8), "13:40", "대구교통공사", 1500, "귀가 (동대구→범어)", area="대구 동구 신천동")

    # 건강 ------------------------------------------------------------------
    for date in (d(6, 10), d(7, 8), d(8, 5), d(9, 2)):
        b.add(date, "09:40", "범어 연합내과", 12600, "고혈압·고지혈 정기진료 (4주)", pattern="ROUTINE", recurring=True)
        b.add(date, "10:05", "온누리약국 범어점", 21400, "처방약 28일분", pattern="ROUTINE", recurring=True)
    for date in (d(7, 14), d(7, 16), d(7, 21)):
        b.add(date, "15:30", "범어 한의원", 7500, "무릎 침 치료")
    b.add(d(7, 3), "11:20", "온누리약국 범어점", 9800, "파스·상비약")
    b.add(d(8, 19), "10:30", "범어 미소치과", 15000, "스케일링 (연 1회 건보)", pattern="PLANNED")

    # 서울 조카 결혼식 7/11 ------------------------------------------------------
    b.add(d(6, 29), "20:30", "코레일", 87000, "KTX 동대구↔서울 왕복 예매 (7/11)", pattern="PLANNED")
    b.send(d(7, 10), "10:20", "조카 김지원 (축의금)", 300000, "조카 결혼 축의금")
    b.add(d(7, 11), "07:20", "대구교통공사", 1500, "이동 (범어→동대구)")
    b.add(d(7, 11), "10:50", "카카오T", 21500, "택시 (서울역→논현 웨딩홀)")
    b.add(d(7, 11), "15:10", "스타벅스 서울역점", 11000, "귀가 전 언니와 커피", area="서울 강남구 논현동")
    b.add(d(7, 11), "16:20", "서울교통공사", 1550, "이동 (논현→서울역)")
    b.add(d(7, 11), "19:35", "대구교통공사", 1500, "귀가 (동대구→범어)", area="대구 동구 신천동")

    # 손주 방문 8/7(금)~8/10(월) ---------------------------------------------------
    b.add(d(8, 6), "10:40", "하나로마트 범어점", 143000, "딸 가족 방문 대비 장보기", pattern="PLANNED")
    b.add(d(8, 7), "18:40", "범어 갈비", 128000, "딸 가족 도착, 저녁 외식 (5인)", pattern="PLANNED")
    b.add(d(8, 8), "10:30", "이월드", 84000, "손주와 이월드 (3인, 딸 차량 이동)", pattern="PLANNED")
    b.add(d(8, 8), "13:10", "이월드 매점", 18000, "간식")
    b.add(d(8, 8), "18:00", "파리바게뜨 범어점", 14200, "주말 빵")
    b.add(d(8, 9), "12:40", "들안길 한정식", 156000, "가족 외식 (5인)", pattern="PLANNED")
    b.add(d(8, 9), "15:30", "범어 키즈카페", 22000, "손주 키즈카페")
    b.send(d(8, 10), "09:40", "딸 김수진 (손주 용돈)", 100000, "손주 용돈 (딸 계좌로)")
    b.add(d(8, 10), "09:50", "대구은행 ATM 범어동", 100000, "주간 현금 (수성시장 장보기용)", ttype="WITHDRAW",
          pay="ACCOUNT", pattern="ROUTINE", recurring=True, fixed=True)

    # 경조사 / 모임 -------------------------------------------------------------
    b.send(d(6, 20), "09:10", "박영희 (부의금)", 100000, "지인 부친상 부의금")
    b.send(d(8, 28), "09:30", "동창회 총무 최OO", 50000, "동창회 회비 (8/29 모임)")
    b.add(d(8, 29), "11:20", "대구교통공사", 1500, "동창 모임 이동 (범어→반월당)")
    b.add(d(8, 29), "14:40", "반월당 카페 온", 6000, "모임 후 커피")
    b.add(d(8, 29), "16:00", "대구교통공사", 1500, "귀가 (반월당→범어)", area="대구 중구 덕산동")

    # 쇼핑 / 미용 -------------------------------------------------------------
    b.add(d(6, 14), "14:00", "범어 미용실", 65000, "커트+염색", pattern="PLANNED")
    b.add(d(8, 23), "14:20", "범어 미용실", 20000, "커트")
    b.add(d(6, 26), "15:10", "다이소 범어점", 27000, "주방·생활용품", pattern="PLANNED")
    b.add(d(7, 22), "21:40", "GS SHOP", 169000, "충동 구매: TV 홈쇼핑 홍삼 세트", pattern="IMPULSE")
    b.add(d(8, 11), "13:20", "대구신세계 (의류)", 128000, "충동 구매: 요가 후 여름 세일 블라우스", pattern="IMPULSE")
    b.add(d(9, 1), "11:10", "범어 반찬가게", 18000, "반찬 (신규 가맹점)", src="MODEL", status="PENDING")

    return b.finish(os.path.join(HERE, "persona_consumption_90d_v3_P005.csv"))


# ---------------------------------------------------------------------------
# 5) 정합성 검사
# ---------------------------------------------------------------------------
def validate(path):
    rows = list(csv.DictReader(io.open(path, encoding="utf-8-sig")))
    issues = []
    assert len(set(r["transaction_id"] for r in rows)) == len(rows), "duplicate id"
    for r in rows:
        date = dt.date.fromisoformat(r["transaction_date"])
        if not (D0 <= date <= D1):
            issues.append("기간 밖 %s %s" % (r["transaction_id"], date))
        if W[date.weekday()] != r["day_of_week"]:
            issues.append("요일 불일치 %s" % r["transaction_id"])
        if not re.fullmatch(r"\d{2}:\d{2}", r["transaction_time"]):
            issues.append("시각 포맷 %s" % r["transaction_id"])
        if r["direction"] == "INCOME" and r["spend_pattern"] != "N/A":
            issues.append("INCOME spend_pattern %s" % r["transaction_id"])
        if r["payment_method"] == "CARD" and (not r["card_id"] or r["account_id"]):
            issues.append("card/account 불일치 %s" % r["transaction_id"])
        if r["payment_method"] == "ACCOUNT" and (r["card_id"] or not r["account_id"]):
            issues.append("card/account 불일치 %s" % r["transaction_id"])
        if r["transaction_type"] in ("WITHDRAW", "TRANSFER_OUT", "DEPOSIT", "TRANSFER_IN") and r["payment_method"] != "ACCOUNT":
            issues.append("type/pay 불일치 %s" % r["transaction_id"])
        if r["transaction_type"] in ("WITHDRAW", "TRANSFER_OUT") and r["payment_method"] == "ACCOUNT" \
                and date.weekday() >= 5 and r["classify_source"] == "RULE" and r["transaction_type"] == "WITHDRAW":
            issues.append("휴일 자동이체 %s %s" % (r["transaction_id"], r["transaction_date"]))
    # 시간 순 정렬 & ID 순서
    prev = None
    for r in rows:
        k = (r["transaction_date"], r["transaction_time"])
        if prev and k < prev:
            issues.append("시간 역순 %s" % r["transaction_id"])
        prev = k
    # 동네 가맹점 첫 거래 = MODEL, 이후 = RULE
    first = {}
    for r in rows:
        first.setdefault(r["merchant"], r)
    for r in rows:
        if r["classify_source"] == "MODEL" and first[r["merchant"]] is not r and r["confirm_status"] != "PENDING":
            issues.append("MODEL 재등장 %s" % r["transaction_id"])
    # 같은 날 식사(점심/저녁/배달) 2건이 90분 이내 → 중복 식사
    meal_subs = {"점심", "저녁/외식", "배달"}
    for date, rs in group_by_day(rows).items():
        meals = [r for r in rs if r["direction"] == "EXPENSE" and r["subcategory"] in meal_subs]
        for a, c in zip(meals, meals[1:]):
            ta = int(a["transaction_time"][:2]) * 60 + int(a["transaction_time"][3:])
            tc = int(c["transaction_time"][:2]) * 60 + int(c["transaction_time"][3:])
            if tc - ta < 90:
                issues.append("중복 식사 %s %s (%s / %s)" % (date, c["transaction_id"], a["merchant"], c["merchant"]))
    # 이동 체인: (A→B) 메모의 출발지가 직전 이동의 도착지와 맞는지 (같은 날)
    for date, rs in group_by_day(rows).items():
        loc = None
        for r in rs:
            mm = re.search(r"\((\S+?)→(\S+?)\)", r["memo"])
            if mm and r["category"] == "교통":
                o, dst = mm.group(1), mm.group(2)
                # KTX 구간(동대구/서울역/부산역)은 승차권을 사전 결제해 당일 행이 없으므로 건너뜀
                if loc and norm(o) != norm(loc) and norm(loc) not in ("동대구", "서울", "부산"):
                    issues.append("동선 단절 %s %s: %s 에서 %s 출발" % (r["transaction_id"], date, loc, o))
                loc = dst
    # 월별 합계
    ms = defaultdict(Counter)
    for r in rows:
        ms[r["transaction_date"][:7]][r["direction"]] += int(r["amount_krw"])
    return rows, issues, ms


def norm(s):
    return re.sub(r"(역|동|입구)$", "", s)


def group_by_day(rows):
    g = defaultdict(list)
    for r in rows:
        g[r["transaction_date"]].append(r)
    return g


if __name__ == "__main__":
    outs = {"P002": fix_p002(), "P003": gen_p003(), "P004": gen_p004(), "P005": gen_p005()}
    report = []
    for k in ("P002", "P003", "P004", "P005"):
        path = os.path.join(HERE, "persona_consumption_90d_v3_%s.csv" % k)
        rows, issues, ms = validate(path)
        report.append("== %s  rows=%d  issues=%d" % (k, len(rows), len(issues)))
        for i in issues:
            report.append("   ! " + i)
        for mo in sorted(ms):
            c = ms[mo]
            report.append("   %s  income=%9d  expense=%9d  transfer=%8d" % (mo, c["INCOME"], c["EXPENSE"], c["TRANSFER"]))
    with io.open(os.path.join(HERE, "_v3_validation_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print("\n".join(report).encode("utf-8", "replace").decode("utf-8", "replace"))
