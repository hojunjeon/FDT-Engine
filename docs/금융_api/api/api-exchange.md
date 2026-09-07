# 환전

- Source URL: https://project.ssafy.com/docs/ssafy-finance/api-exchange
- Crawl date: 2026-08-24
- Scope: Static rendered documentation only; no live API calls, authentication, or data mutation.
- Verification: VERIFIED — final article DOM loaded in the in-app browser.
- Summary: Three POST endpoints cover exchange estimation, exchange application, and exchange-application history. The examples and field tables describe source/target currencies, amount, account data, and transaction history.

## Rendered article
# 환전

### 2.11 환전

---

#### 2.11.1 환전 예상 금액 조회

##### 설명

통화코드조회 API로 통화코드를 조회한 후에 사용합니다.
 ✅ **예상 환전 금액 조회 시 최소 환전 금액과 환전 금액 단위를 제한하지 않습니다.**

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/exchange/estimate | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |
| currency | 소유 통화코드 | String |  | Y | 소유한 통화코드 (ex. USD) |
| exchangeCurrency | 환전 통화코드 | String | 8 | Y | 환전할 통화의 코드 입력 (ex. JPY) |
| amount | 환전금액 | Double |  | Y | 환전하고 싶은 금액 (환전 금액 단위는 10) |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "estimate",
        "transmissionDate": "20240724",
        "transmissionTime": "102710",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "estimate",
        "institutionTransactionUniqueNo": "20240724102710632310",
        "apiKey": "[REDACTED]"
    },
    "currency": "USD",
    "exchangeCurrency": "JPY",
    "amount":"30000"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 환전 정보 |  |  | Y |  |
| currency | 소유 통화 정보 | List |  | Y |  |
| amount | 환전금액 | Double | 10 | Y |  |
| currency | 통화코드 | String | 16 | Y |  |
| currencyName | 통화명 | String | 10 | Y |  |
| exchangeCurrency | 환전 예상 통화 정보 | List |  | Y |  |
| amount | 환전 예상 금액 | Double |  | Y | **외화 간 환전 시 원화 기준으로 환전 (소유 통화 -> 원화 -> 환전할 통화)** |
| currency | 통화코드 | String | 16 | Y |  |
| currencyName | 통화명 | String | 10 | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "estimate",
        "transmissionDate": "20240724",
        "transmissionTime": "102710",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "estimate",
        "institutionTransactionUniqueNo": "20240724102710632310"
    },
    "REC": {
        "currency": {
            "amount": "1,000,000",
            "currency": "USD",
            "currencyName": "달러"
        },
        "exchangeCurrency": {
            "amount": "155,725,448.31",
            "currency": "JPY",
            "currencyName": "엔화"
        }
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
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A5001 | 통화코드가 유효하지 않습니다. |  |
| A5002 | 환전 금액을 입력해주세요. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.11.2 환전 신청

##### 설명

환전을 진행합니다.
 📌 **환전 신청 시 즉시 승인되며, 환율 변동으로 인해 환전 예상 금액 조회 API 결과와 다를 수 있습니다.**
 📌 **환전 금액은 10단위로 입력 가능합니다.**

✅ **최소 환전 금액:**
 - **KRW** (원화): 1000
 - **USD** (달러): 100
 - **EUR** (유로): 100
 - **JPY** (엔화): 100
 - **CNY** (위안): 800
 - **GBP** (파운드): 80
 - **CHF** (스위스 프랑): 100
 - **CAD** (캐나다 달러): 140

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/exchange | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 출금 계좌번호 | String | 16 | Y | 출금 계좌 (원화 계좌, 외화 계좌) 로 통화 파악 |
| exchangeCurrency | 환전 통화코드 | String | 8 | Y | 환전할 통화 코드 (ex. JPY) |
| exchangeAmount | 환전 금액 | Double |  | Y | 환전하고 싶은 금액 (환전 금액 단위는 10) |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "exchange",
        "transmissionDate": "20240724",
        "transmissionTime": "104536",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "exchange",
        "institutionTransactionUniqueNo": "20240724104536128480",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    },
    "accountNo": "0011214764051239",
    "exchangeCurrency": "JPY",
    "exchangeAmount": "30000"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 환전 정보 |  |  | Y |  |
| exchangeCurrency | 환전 통화 정보 | List |  | Y |  |
| amount | 환전 금액 | Double |  | Y | 환전할 통화의 금액 |
| exchangeRate | 적용 환율 | Double |  | Y |  |
| currency | 통화코드 | String | 8 | Y | 환전할 통화코드 |
| currencyName | 통화명 | String | 10 | Y | 환전할 통화명 |
| accountInfo | 계좌 정보 | List |  | Y |  |
| accountNo | 출금 계좌 | String | 16 | Y |  |
| amount | 출금 금액 | Double |  | Y | 원화, 엔화의 경우 정수로 절삭 |
| balance | 출금 후 계좌 잔액 | Double |  | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "exchange",
        "transmissionDate": "20240724",
        "transmissionTime": "104536",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "exchange",
        "institutionTransactionUniqueNo": "20240724104536128480"
    },
    "REC": {
        "exchangeCurrency": {
            "amount": "30000",
            "exchangeRate": "901.32",
            "currency": "JPY",
            "currencyName": "엔화"
        },
        "accountInfo": {
            "accountNo": "0044757578641471",
            "amount": "195.22",
            "balance": "2499668388.84"
        }
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
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A5001 | 통화코드가 유효하지 않습니다. |  |
| A5002 | 환전 금액을 입력해주세요. |  |
| A5007 | 환전 금액 단위는 10 입니다. |  |
| A5008 | 환전할 통화의 최소 금액은 {{amount}} 입니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.11.3 환전 신청내역 조회

##### 설명

작성한 계좌번호에 대한 **환전 신청 내역을 조회**합니다.
 ✅ **계좌번호 미입력 시 소유한 전체 계좌에 대한 환전 신청 내역을 조회합니다.**

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/exchange/exchangeHistory | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | N | 미입력 시 소유한 전체 계좌에 대한 내역 조회 |
| startDate | 조회 시작일 | String | 8 | Y | YYYYMMDD |
| endDate | 조회 종료일 | String | 8 | Y | YYYYMMDD |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "exchangeHistory",
        "transmissionDate": "20240724",
        "transmissionTime": "104536",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "exchangeHistory",
        "institutionTransactionUniqueNo": "20240724104536128480",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    },
    "accountNo": "0041869351281557",
    "startDate": "20240101",
    "endDate": "20240726"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 환전 내역 정보 | List |  | Y |  |
| account | 계좌 정보 | List |  | Y |  |
| bankName | 은행명 | String |  | Y |  |
| userName | 예금주명 | String |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 16 | Y |  |
| currency | 소유 통화 정보 | List |  | Y |  |
| currency | 통화코드 | String | 8 | Y |  |
| currencyName | 통화명 | String | 10 | Y |  |
| amount | 환전 금액 | Double |  | Y |  |
| exchangeCurrency | 환전 통화 정보 | List |  | Y |  |
| currency | 통화코드 | String | 8 | Y | 환전할 통화코드 |
| currencyName | 통화명 | String | 10 | Y | 환전할 통화명 |
| amount | 환전 금액 | Double |  | Y |  |
| exchangeRate | 적용 환율 | Double |  | Y |  |
| created | 생성일 | String | 10 | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "exchangeHistory",
        "transmissionDate": "20240724",
        "transmissionTime": "104536",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "exchangeHistory",
        "institutionTransactionUniqueNo": "20240724104536128480"
    },
    "REC": [
        {
            "account": {
                "bankName": "국민은행",
                "userName": "user1",
                "accountNo": "0041869351281557",
                "accountName": "국민은행 수시입출금"
            },
            "currency": {
                "currency": "KRW",
                "currencyName": "원화",
                "amount": "100000"
            },
            "exchangeCurrency": {
                "currency": "JPY",
                "currencyName": "엔화",
                "amount": "11094.84",
                "exchangeRate": "901.32"
            },
            "created": "2024-07-26 10:05:17"
        },
        {
            "account": {
                "bankName": "국민은행",
                "userName": "user1",
                "accountNo": "0041869351281557",
                "accountName": "국민은행 수시입출금"
            },
            "currency": {
                "currency": "KRW",
                "currencyName": "원화",
                "amount": "100000"
            },
            "exchangeCurrency": {
                "currency": "JPY",
                "currencyName": "엔화",
                "amount": "11094.84",
                "exchangeRate": "901.32"
            },
            "created": "2024-07-26 10:01:42"
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
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1004 | 조회 시작일자가 유효하지 않습니다. |  |
| A1005 | 조회 종료일자가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

