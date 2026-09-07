# 환율

- Source URL: https://project.ssafy.com/docs/ssafy-finance/api-exchange-rate
- Crawl date: 2026-08-24
- Scope: Static rendered documentation only; no live API calls, authentication, or data mutation.
- Verification: VERIFIED — final article DOM loaded in the in-app browser.
- Summary: Two POST endpoints provide all supported-currency rates and a single-currency rate lookup. The page lists USD, EUR, JPY, CNY, GBP, CHF, and CAD, and notes that rates refresh every 10 minutes.

## Rendered article
# 환율

### 2.10 환율

---

#### 2.10.1 환율 전체 조회

##### 설명

7개 통화에 대해 실시간 환율을 조회할 수 있습니다.
 📌 **환율은 10분마다 갱신되므로 실제 환율과 다를 수 있습니다.**

✅ **지원 통화코드:**
 - **USD** (달러)
 - **EUR** (유로)
 - **JPY** (엔화)
 - **CNY** (위안)
 - **GBP** (파운드)
 - **CHF** (스위스 프랑)
 - **CAD** (캐나다 달러)

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/exchangeRate | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "exchangeRate",
        "transmissionDate": "20240724",
        "transmissionTime": "101641",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "exchangeRate",
        "institutionTransactionUniqueNo": "20240724101641312362",
        "apiKey": "[REDACTED]"
    }
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 환율 목록 | List |  | Y |  |
| id | 환율 고유번호 | Long |  | Y |  |
| currency | 통화코드 | String | 8 | Y |  |
| exchangeRate | 환율 | Double |  | Y |  |
| exchangeMin | 최소 환전금액 | Double |  | Y |  |
| created | 생성일 | String | 10 | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "exchangeRate",
        "transmissionDate": "20240724",
        "transmissionTime": "101641",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "exchangeRate",
        "institutionTransactionUniqueNo": "20240724101641312362"
    },
    "REC": [
        {
            "id": 2127,
            "currency": "CAD",
            "exchangeRate": "1,003.08",
            "exchangeMin": "140",
            "created": "2024-07-25 23:55:04"
        },
        {
            "id": 2128,
            "currency": "CHF",
            "exchangeRate": "1,565.35",
            "exchangeMin": "100",
            "created": "2024-07-25 23:55:04"
        },
        {
            "id": 2129,
            "currency": "CNY",
            "exchangeRate": "190.06",
            "exchangeMin": "800",
            "created": "2024-07-25 23:55:04"
        },
        {
            "id": 2130,
            "currency": "EUR",
            "exchangeRate": "1,501.45",
            "exchangeMin": "100",
            "created": "2024-07-25 23:55:04"
        },
        {
            "id": 2131,
            "currency": "GBP",
            "exchangeRate": "1,786.99",
            "exchangeMin": "80",
            "created": "2024-07-25 23:55:04"
        },
        {
            "id": 2132,
            "currency": "JPY",
            "exchangeRate": "901.32",
            "exchangeMin": "100",
            "created": "2024-07-25 23:55:04"
        },
        {
            "id": 2134,
            "currency": "USD",
            "exchangeRate": "1,385.1",
            "exchangeMin": "100",
            "created": "2024-07-25 23:55:04"
        }
    ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.10.2 환율 단건 조회

##### 설명

입력한 통화에 대해 실시간 환율을 조회할 수 있습니다.
 📌 **환율은 10분마다 갱신되므로 실제 환율과 다를 수 있습니다.**

✅ **지원 통화코드:**
 - **USD** (달러)
 - **EUR** (유로)
 - **JPY** (엔화)
 - **CNY** (위안)
 - **GBP** (파운드)
 - **CHF** (스위스 프랑)
 - **CAD** (캐나다 달러)

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/exchangeRate/exchangeRateSearch | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |
| currency | 통화코드 | String | 8 | Y | currency |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "exchangeRateSearch",
        "transmissionDate": "20240724",
        "transmissionTime": "101020",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "exchangeRateSearch",
        "institutionTransactionUniqueNo": "20240724101020562463",
        "apiKey": "[REDACTED]"
    },
    "currency":"USD"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 환율 정보 |  |  | Y |  |
| id | 환율 고유번호 | Long |  | Y |  |
| currency | 통화코드 | String | 8 | Y |  |
| exchangeRate | 환율 | Double | 16 | Y |  |
| exchangeMin | 최소 환전금액 | Double |  | Y |  |
| created | 생성일 | String | 10 | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "exchangeRateSearch",
        "transmissionDate": "20240724",
        "transmissionTime": "101020",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "exchangeRateSearch",
        "institutionTransactionUniqueNo": "20240724101020562463"
    },
    "REC": {
        "id": 153,
        "currency": "USD",
        "exchangeRate": "1,388.6",
        "exchangeMin": "100",
        "created": "2024-07-23T15:20:55.972351+09:00"
    }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A5001 | 통화코드가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

