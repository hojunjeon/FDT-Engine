# SSAFY 금융망 — 1원 인증 API

- Source: https://project.ssafy.com/docs/ssafy-finance/api-account-auth
- Crawled: 2026-08-24
- Scope: Read-only document crawl; no live API calls, authentication, or financial data changes were performed.
- Summary: Visible article content covers the two POST endpoints for sending a 1원 verification transfer and validating the depositor-name verification code, with request/response schemas and error-code tables.

# 1원 인증

### 2.9 1원 인증

---

#### 2.9.1 1원 송금

##### 설명

회원의 실명 계좌를 확인하기 위해 **기업명과 인증코드를 포함하여 1원을 송금**합니다.

**인증코드는 4자리 숫자로 랜덤 생성되며**, 기업명은 앱 식별을 위해 앱 관리자가(교육생) 입력합니다.

**인증코드는 거래 내역에서 '기업명 인증코드' 형식으로 조회됩니다.**

예시:

- **기업명:** SSAFY

- **인증코드:** 1234

- **거래 내역:** `SSAFY 1234`

📌 **원화 수시입출금 상품에만 사용 가능합니다.**

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/accountAuth/openAccountAuth | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| authText | 기업명 | String | 20 | Y | 회사 이니셜, 메시지 등을 통해 앱 관리자가(교육생) 본인을 식별할 수 있도록 입력 |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "openAccountAuth",

        "transmissionDate": "20240723",

        "transmissionTime": "152345",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "openAccountAuth",

        "institutionTransactionUniqueNo": "20240723152345666098",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "accountNo" : "0011214764051239",

    "authText": "SSAFY"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 인증 송금 정보 |  |  | Y |  |
| transactionUniqueNo | 거래 고유번호 | Long |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "openAccountAuth",

        "transmissionDate": "20240723",

        "transmissionTime": "152345",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "openAccountAuth",

        "institutionTransactionUniqueNo": "20240723152345666098"

    },

    "REC": {

        "transactionUniqueNo": "7",

        "accountNo": "0011214764051239"

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
| A1001 | 은행코드가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1089 | 기업명이 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.9.2 1원 송금 검증

##### 설명

송금 내역에서 조회되는 **기업명, 인증코드와 입력한 기업명, 인증코드가 일치하는지 검증**합니다.

**계좌거래내역조회에서 인증코드를 확인할 수 있습니다.**

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/accountAuth/checkAuthCode | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| authText | 기업명 | String | 20 | Y | 앱 관리자가 본인을 식별할 수 있도록 입력한 문자 |
| authCode | 인증코드 | String | 16 | Y | 0000 (숫자 4자리) |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "checkAuthCode",

        "transmissionDate": "20240723",

        "transmissionTime": "152415",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "checkAuthCode",

        "institutionTransactionUniqueNo": "20240723152415461262",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "accountNo" : "0011214764051239",

    "authText": "SSAFY",

    "authCode": "8212"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 인증 검증 정보 |  |  | Y |  |
| status | 성공 여부 | String | 10 | Y | SUCCESS, FAIL |
| transactionUniqueNo | 거래 고유번호 | Long |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "checkAuthCode",

        "transmissionDate": "20240723",

        "transmissionTime": "152415",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "checkAuthCode",

        "institutionTransactionUniqueNo": "20240723152415461262"

    },

    "REC": {

        "status": "SUCCESS",

        "transactionUniqueNo": "7",

        "accountNo": "0011214764051239"

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
| A1001 | 은행코드가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1086 | 인증코드 발급 기록이 없습니다. |  |
| A1087 | 인증 시간이 만료되었습니다. |  |
| A1088 | 인증코드가 일치하지 않습니다. |  |
| A1089 | 기업명이 유효하지 않습니다. |  |
| A1090 | 인증코드가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---
