# 가상계좌

- Source URL: https://project.ssafy.com/docs/ssafy-finance/api-virtual-account
- Crawl date: 2026-08-24
- Scope: Visible documentation only; no live API calls, authentication, or data-changing requests were made.
- Summary: 가상계좌 발급과 목록·상세·입금 내역 조회에 필요한 요청·응답 필드, 예시 JSON, 오류 코드를 정리합니다.

# 가상계좌

### 2.14 가상계좌

---

#### 2.14.1 가상계좌 발급

##### 설명

가상계좌 발급 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/createVirtualAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| mainAccountNo | 연결 계좌번호 | String | 16 | Y | 본인 소유의 정상 원화 계좌번호 |
| depositorName | 입금자명 | String | 20 | Y | 예: 테스트사용자 |
| expectedAmount | 예상 입금 금액 | String |  | N | 숫자 형식의 문자열, 예: 1000 |
| expiryDate | 만료일 | String | 8 | Y | YYYYMMDD, 발급일로부터 30일 이내 |
| memo | 메모 | String | 255 | N | 예: API 명세 재작성 검증 |
| autoTransfer | 입금 후 자동 이체 여부 | Boolean |  | N | 미입력 시 true |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "createVirtualAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "102349",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "createVirtualAccount",
    "institutionTransactionUniqueNo": "20260731102349338463",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "mainAccountNo": "0019763592900582",
  "depositorName": "테스트사용자",
  "expectedAmount": "1000",
  "expiryDate": "20260820",
  "memo": "주문번호 ORD-20260716-001",
  "autoTransfer": true
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| virtualAccountId | 가상계좌 ID | String | 20 | Y | 예: VA446552536458449003 |
| virtualAccountNo | 가상계좌번호 | String | 16 | Y | 예: 8869006480404579 |
| bankCode | 은행 코드 | String | 3 | Y | 예: 088 |
| mainAccountNo | 연결 계좌번호 | String | 16 | Y | 예: 0019763592900582 |
| depositorName | 입금자명 | String | 20 | Y | 예: 테스트사용자 |
| expectedAmount | 예상 입금 금액 | String |  | N | 예: 1000 |
| expiryDate | 만료일 | String | 8 | Y | YYYYMMDD, 예: 20260825 |
| status | 가상계좌 상태 | String |  | Y | ACTIVE, DEPOSITED, EXPIRED, CLOSED |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "createVirtualAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "102349",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "createVirtualAccount",
    "institutionTransactionUniqueNo": "20260731102349338463"
  },
  "REC": {
    "virtualAccountId": "VA446552536458449003",
    "virtualAccountNo": "8869006480404579",
    "bankCode": "088",
    "mainAccountNo": "0019763592900582",
    "depositorName": "테스트사용자",
    "expectedAmount": "1000",
    "expiryDate": "20260820",
    "status": "ACTIVE",
    "createdAt": "20260731102358"
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4060 | 연결 계좌를 찾을 수 없음 | 가상계좌 발급 |
| E4061 | 계좌 소유자가 아님 | 가상계좌 발급 |
| E4062 | 계좌가 정상 상태가 아님 | 가상계좌 발급 |
| E4063 | 유효 기간이 30일 초과 | 가상계좌 발급 |
| E4064 | 유효기간 종료일이 과거 또는 형식 오류 | 가상계좌 발급 |
| E4065 | 활성 가상계좌 수 초과 | 가상계좌 발급 |
| E4066 | 예상 입금 금액이 유효하지 않음 | 가상계좌 발급 |
| E4071 | 요청 필드 타입이 유효하지 않음 | 가상계좌 발급 |

---

#### 2.14.2 가상계좌 목록 조회

##### 설명

가상계좌 목록 조회 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/inquireVirtualAccountList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| mainAccountNo | 연결 계좌번호 필터 | String | 16 | N | 미입력 시 전체 조회 |
| status | 가상계좌 상태 필터 | String |  | N | ACTIVE, DEPOSITED, EXPIRED, CLOSED |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "inquireVirtualAccountList",
    "transmissionDate": "20260731",
    "transmissionTime": "102429",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "inquireVirtualAccountList",
    "institutionTransactionUniqueNo": "20260731102429690107",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "status": "ACTIVE"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| virtualAccounts | 가상계좌 목록 | Array |  | Y | 조건에 맞는 가상계좌 배열 |
| virtualAccountId | 가상계좌 ID | String | 20 | Y | 예: VA446552536458449003 |
| virtualAccountNo | 가상계좌번호 | String | 16 | Y | 예: 8869006480404579 |
| depositorName | 입금자명 | String | 20 | Y | 예: 테스트사용자 |
| expectedAmount | 예상 입금 금액 | String |  | N | 예: 1000 |
| expiryDate | 만료일 | String | 8 | Y | YYYYMMDD |
| status | 가상계좌 상태 | String |  | Y | ACTIVE, DEPOSITED, EXPIRED, CLOSED |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "inquireVirtualAccountList",
    "transmissionDate": "20260731",
    "transmissionTime": "102429",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "inquireVirtualAccountList",
    "institutionTransactionUniqueNo": "20260731102429690107"
  },
  "REC": {
    "virtualAccounts": [
      {
        "virtualAccountId": "VA446552536458449003",
        "virtualAccountNo": "8869006480404579",
        "depositorName": "테스트사용자",
        "expectedAmount": "1000",
        "expiryDate": "20260820",
        "status": "ACTIVE"
      }
    ]
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4071 | 요청 필드 타입이 유효하지 않음 | 가상계좌 목록 조회 |

---

#### 2.14.3 가상계좌 상세 조회

##### 설명

가상계좌 상세 조회 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/inquireVirtualAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| virtualAccountId | 가상계좌 ID | String | 20 | Y | 예: VA446552536458449003 |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "inquireVirtualAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "102600",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "inquireVirtualAccount",
    "institutionTransactionUniqueNo": "20260731102600850199",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "virtualAccountId": "VA446552536458449003"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| virtualAccountId | 가상계좌 ID | String | 20 | Y | 예: VA446552536458449003 |
| virtualAccountNo | 가상계좌번호 | String | 16 | Y | 예: 8869006480404579 |
| bankCode | 은행 코드 | String | 3 | Y | 예: 088 |
| mainAccountNo | 연결 계좌번호 | String | 16 | Y | 예: 0019763592900582 |
| depositorName | 입금자명 | String | 20 | Y | 예: 테스트사용자 |
| expectedAmount | 예상 입금 금액 | String |  | N | 예: 1000 |
| expiryDate | 만료일 | String | 8 | Y | YYYYMMDD, 예: 20260825 |
| status | 가상계좌 상태 | String |  | Y | ACTIVE, DEPOSITED, EXPIRED, CLOSED |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| depositedAmount | 누적 입금 금액 | String |  | Y | 예: 1000 |
| pendingAmount | 미정산 보류 금액 | String |  | Y | 예: 0 |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "inquireVirtualAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "102600",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "inquireVirtualAccount",
    "institutionTransactionUniqueNo": "20260731102600850199"
  },
  "REC": {
    "virtualAccountId": "VA446552536458449003",
    "virtualAccountNo": "8869006480404579",
    "bankCode": "088",
    "mainAccountNo": "0019763592900582",
    "depositorName": "테스트사용자",
    "expectedAmount": "1000",
    "expiryDate": "20260820",
    "status": "ACTIVE",
    "createdAt": "20260731102358",
    "depositedAmount": "1000",
    "pendingAmount": "0"
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4067 | 가상계좌를 찾을 수 없음 | 가상계좌 상세 조회 |
| E4068 | 가상계좌 소유자가 아님 | 가상계좌 상세 조회 |
| E4071 | 요청 필드 타입이 유효하지 않음 | 가상계좌 상세 조회 |

---

#### 2.14.4 가상계좌 입금 내역 조회

##### 설명

가상계좌 입금 내역 조회 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/inquireVirtualAccountDeposits | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| virtualAccountId | 가상계좌 ID | String | 20 | Y | 예: VA446552536458449003 |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "inquireVirtualAccountDeposits",
    "transmissionDate": "20260731",
    "transmissionTime": "102935",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "inquireVirtualAccountDeposits",
    "institutionTransactionUniqueNo": "20260731102935380080",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "virtualAccountId": "VA446552536458449003"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| deposits | 입금 내역 | Array |  | Y | 입금 내역 배열 |
| depositAmount | 입금 금액 | String |  | Y | 예: 1000 |
| nameMatched | 입금자명 일치 여부 | Boolean |  | Y | 예: true |
| transferred | 연결 계좌 이체 여부 | Boolean |  | Y | 예: false |
| depositedAt | 입금 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| settledAt | 정산 일시 | String | 14 | N | 미정산 시 null |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "inquireVirtualAccountDeposits",
    "transmissionDate": "20260731",
    "transmissionTime": "102935",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "inquireVirtualAccountDeposits",
    "institutionTransactionUniqueNo": "20260731102935380080"
  },
  "REC": {
    "deposits": [
      {
        "depositAmount": "1000",
        "nameMatched": true,
        "transferred": false,
        "depositedAt": "20260731102905",
        "settledAt": null
      }
    ]
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4067 | 가상계좌를 찾을 수 없음 | 가상계좌 입금 내역 조회 |
| E4068 | 가상계좌 소유자가 아님 | 가상계좌 입금 내역 조회 |
| E4071 | 요청 필드 타입이 유효하지 않음 | 가상계좌 입금 내역 조회 |

---

#### 2.14.5 가상계좌 해지

##### 설명

가상계좌 해지 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/closeVirtualAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| virtualAccountId | 가상계좌 ID | String | 20 | Y | 예: VA446552536458449003 |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "closeVirtualAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "103010",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "closeVirtualAccount",
    "institutionTransactionUniqueNo": "20260731103010765130",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "virtualAccountId": "VA446552536458449003"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| virtualAccountId | 가상계좌 ID | String | 20 | Y | 예: VA446552536458449003 |
| virtualAccountNo | 가상계좌번호 | String | 16 | Y | 예: 8869006480404579 |
| bankCode | 은행 코드 | String | 3 | Y | 예: 088 |
| mainAccountNo | 연결 계좌번호 | String | 16 | Y | 예: 0019763592900582 |
| depositorName | 입금자명 | String | 20 | Y | 예: 테스트사용자 |
| expectedAmount | 예상 입금 금액 | String |  | N | 예: 1000 |
| expiryDate | 만료일 | String | 8 | Y | YYYYMMDD, 예: 20260825 |
| status | 가상계좌 상태 | String |  | Y | ACTIVE, DEPOSITED, EXPIRED, CLOSED |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| depositedAmount | 누적 입금 금액 | String |  | Y | 예: 1000 |
| pendingAmount | 미정산 보류 금액 | String |  | Y | 예: 0 |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "closeVirtualAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "103010",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "closeVirtualAccount",
    "institutionTransactionUniqueNo": "20260731103010765130"
  },
  "REC": {
    "virtualAccountId": "VA446552536458449003",
    "virtualAccountNo": "8869006480404579",
    "bankCode": "088",
    "mainAccountNo": "0019763592900582",
    "depositorName": "테스트사용자",
    "expectedAmount": "1000",
    "expiryDate": "20260820",
    "status": "CLOSED",
    "createdAt": "20260731102358",
    "depositedAmount": "1000",
    "pendingAmount": "0"
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4067 | 가상계좌를 찾을 수 없음 | 가상계좌 해지 |
| E4068 | 가상계좌 소유자가 아님 | 가상계좌 해지 |
| E4071 | 요청 필드 타입이 유효하지 않음 | 가상계좌 해지 |

---

#### 2.14.6 가상계좌 유효기간 연장

##### 설명

가상계좌 유효기간 연장 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/extendVirtualAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| virtualAccountId | 가상계좌 ID | String | 20 | Y | ACTIVE 또는 EXPIRED 상태만 연장 가능 |
| expiryDate | 변경할 만료일 | String | 8 | Y | YYYYMMDD, 발급일로부터 30일 이내 |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "extendVirtualAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "102758",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "extendVirtualAccount",
    "institutionTransactionUniqueNo": "20260731102758837362",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "virtualAccountId": "VA446552536458449003",
  "expiryDate": "20260825"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| virtualAccountId | 가상계좌 ID | String | 20 | Y | 예: VA446552536458449003 |
| virtualAccountNo | 가상계좌번호 | String | 16 | Y | 예: 8869006480404579 |
| bankCode | 은행 코드 | String | 3 | Y | 예: 088 |
| mainAccountNo | 연결 계좌번호 | String | 16 | Y | 예: 0019763592900582 |
| depositorName | 입금자명 | String | 20 | Y | 예: 테스트사용자 |
| expectedAmount | 예상 입금 금액 | String |  | N | 예: 1000 |
| expiryDate | 만료일 | String | 8 | Y | YYYYMMDD, 예: 20260825 |
| status | 가상계좌 상태 | String |  | Y | ACTIVE, DEPOSITED, EXPIRED, CLOSED |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| depositedAmount | 누적 입금 금액 | String |  | Y | 예: 1000 |
| pendingAmount | 미정산 보류 금액 | String |  | Y | 예: 0 |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "extendVirtualAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "102758",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "extendVirtualAccount",
    "institutionTransactionUniqueNo": "20260731102758837362"
  },
  "REC": {
    "virtualAccountId": "VA446552536458449003",
    "virtualAccountNo": "8869006480404579",
    "bankCode": "088",
    "mainAccountNo": "0019763592900582",
    "depositorName": "테스트사용자",
    "expectedAmount": "1000",
    "expiryDate": "20260825",
    "status": "ACTIVE",
    "createdAt": "20260731102358",
    "depositedAmount": "1000",
    "pendingAmount": "0"
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4063 | 유효 기간이 30일 초과 | 가상계좌 유효기간 연장 |
| E4064 | 유효기간 종료일이 과거 또는 형식 오류 | 가상계좌 유효기간 연장 |
| E4067 | 가상계좌를 찾을 수 없음 | 가상계좌 유효기간 연장 |
| E4068 | 가상계좌 소유자가 아님 | 가상계좌 유효기간 연장 |
| E4071 | 요청 필드 타입이 유효하지 않음 | 가상계좌 유효기간 연장 |

---

#### 2.14.7 가상계좌 보류금 정산

##### 설명

가상계좌 보류금 정산 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/settleVirtualAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| virtualAccountId | 가상계좌 ID | String | 20 | Y | 예: VA446552536458449003 |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "settleVirtualAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "102957",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "settleVirtualAccount",
    "institutionTransactionUniqueNo": "20260731102957585643",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "virtualAccountId": "VA446552536458449003"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| virtualAccountId | 가상계좌 ID | String | 20 | Y | 예: VA446552536458449003 |
| mainAccountNo | 정산 금액 입금 계좌번호 | String | 16 | Y | 예: 0019763592900582 |
| settledAmount | 정산 금액 | String |  | Y | 예: 1000 |
| pendingAmount | 정산 후 보류 금액 | String |  | Y | 예: 0 |
| settledAt | 정산 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "settleVirtualAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "102957",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "settleVirtualAccount",
    "institutionTransactionUniqueNo": "20260731102957585643"
  },
  "REC": {
    "virtualAccountId": "VA446552536458449003",
    "mainAccountNo": "0019763592900582",
    "settledAmount": "1000",
    "pendingAmount": "0",
    "settledAt": "20260731102959"
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4067 | 가상계좌를 찾을 수 없음 | 가상계좌 보류금 정산 |
| E4068 | 가상계좌 소유자가 아님 | 가상계좌 보류금 정산 |
| E4069 | 정산 가능한 보류금이 없음 | 가상계좌 보류금 정산 |
| E4070 | 이미 정산된 입금 | 가상계좌 보류금 정산 |
| E4071 | 요청 필드 타입이 유효하지 않음 | 가상계좌 보류금 정산 |

---

