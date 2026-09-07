# 비대면 계좌개설

- Source URL: https://project.ssafy.com/docs/ssafy-finance/api-account-opening-untact
- Crawl date: 2026-08-24
- Scope: Visible documentation only; no live API calls, authentication, or data-changing requests were made.
- Summary: 비대면 계좌개설의 1원 인증 요청, 계좌 개설, 인증 상태·상품 목록 조회에 필요한 명세와 예시 JSON, 오류 코드를 정리합니다.

# 비대면 계좌개설

### 2.15 비대면 계좌개설

---

#### 2.15.1 비대면 계좌개설 1원 인증 요청

##### 설명

비대면 계좌개설 1원 인증 요청 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/openAccountAuth | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| authAccountNo | 본인 확인용 기존 보유 계좌번호 | String | 16 | Y | 예: 0010000000000001 |
| authText | 거래내역 입금자명에 표기될 기업명 | String | 20 | Y | 예: SSAFY |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "openAccountAuth",
    "transmissionDate": "20260731",
    "transmissionTime": "104536",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "openAccountAuth",
    "institutionTransactionUniqueNo": "20260731104536015409",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "authAccountNo": "0010000000000001",
  "authText": "SSAFY"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| authId | 1원 인증 ID | String | 20 | Y | 예: OWA20260731104540453 |
| authAccountNo | 인증 대상 계좌번호 | String | 16 | Y | 예: 0881816422703833 |
| expiresAt | 인증 만료 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "openAccountAuth",
    "transmissionDate": "20260731",
    "transmissionTime": "104536",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "openAccountAuth",
    "institutionTransactionUniqueNo": "20260731104536015409"
  },
  "REC": {
    "authId": "OWA20260731104540453",
    "authAccountNo": "0010000000000001",
    "expiresAt": "20260731105540"
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4092 | 인증 대상 계좌를 찾을 수 없거나 인증 가능한 계좌가 아님 | 1원 인증 요청 |
| E4097 | 요청 필드 타입이 유효하지 않음 | 1원 인증 요청 |

---

#### 2.15.2 비대면 계좌 개설

##### 설명

비대면 계좌 개설 기능입니다. 개설 가능한 계좌 수 제한은 없습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/createNonFaceAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| authId | 1원 인증 요청 ID | String | 20 | Y | 예: OWA20260731104540453 |
| authCode | 입금자명에 포함된 숫자 4자리 인증코드 | String | 4 | Y | 예: 1234 |
| accountTypeCode | 개설할 계좌 종류 코드 | String | 3 | Y | 001, 002, 003 |
| accountTypeUniqueNo | 개설할 상품 고유번호 | String | 20 | Y | 상품 조회 결과 사용 |
| initialDeposit | 초기 입금액 | String |  | N | 수시입출금 미입력 시 0, 예금·적금은 최소 가입금액 이상 필수 |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "createNonFaceAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "104909",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "createNonFaceAccount",
    "institutionTransactionUniqueNo": "20260731104909139088",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "authId": "OWA20260731104540453",
  "authCode": "1234",
  "accountTypeCode": "001",
  "accountTypeUniqueNo": "001-1-abcdef12345678",
  "initialDeposit": "10000"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| accountNo | 신규 개설 계좌번호 | String | 16 | Y | 예: 0019999999999999 |
| accountTypeCode | 계좌 종류 코드 | String | 3 | Y | 001, 002, 003 |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y | 예: 001-1-abcdef12345678 |
| productName | 상품명 | String |  | Y | 예: 자유입출금통장 |
| initialDeposit | 초기 입금액 | String |  | Y | 예: 10000 |
| openDate | 계좌 개설일 | String | 8 | Y | YYYYMMDD |
| status | 계좌 상태 | String |  | Y | ACTIVE |
| createdAt | 계좌 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "createNonFaceAccount",
    "transmissionDate": "20260731",
    "transmissionTime": "104909",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "createNonFaceAccount",
    "institutionTransactionUniqueNo": "20260731104909139088"
  },
  "REC": {
    "accountNo": "0019999999999999",
    "accountTypeCode": "001",
    "accountTypeUniqueNo": "001-1-abcdef12345678",
    "productName": "자유입출금통장",
    "initialDeposit": "10000",
    "openDate": "20260731",
    "status": "ACTIVE",
    "createdAt": "20260731104910"
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4090 | 1원 인증이 현재 요청 처리 중 만료됨 | 비대면 계좌 개설 |
| E4091 | 1원 인증 코드 불일치 | 비대면 계좌 개설 |
| E4092 | 인증 대상 계좌를 찾을 수 없거나 소유자가 아님 | 비대면 계좌 개설 |
| E4093 | 상품 또는 계좌 유형을 찾을 수 없음 | 비대면 계좌 개설 |
| E4095 | 인증 정보가 없거나 이전 단계가 완료되지 않음 | 비대면 계좌 개설 |
| E4096 | 이미 만료된 개설 프로세스 | 비대면 계좌 개설 |
| E4097 | 요청 필드 타입이 유효하지 않음 | 비대면 계좌 개설 |

---

#### 2.15.3 1원 인증 상태 조회

##### 설명

1원 인증 상태 조회 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/inquireOpenAccountAuth | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| authId | 1원 인증 ID | String | 20 | Y | 예: OWA20260731104540453 |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "inquireOpenAccountAuth",
    "transmissionDate": "20260731",
    "transmissionTime": "104750",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "inquireOpenAccountAuth",
    "institutionTransactionUniqueNo": "20260731104750072639",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "authId": "OWA20260731104540453"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| authId | 1원 인증 ID | String | 20 | Y | 예: OWA20260731104540453 |
| authAccountNo | 인증 대상 계좌번호 | String | 16 | Y | 예: 0881816422703833 |
| authStatus | 인증 상태 | String |  | Y | REQUESTED, SUCCEEDED, EXPIRED |
| expiresAt | 인증 만료 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| remainSeconds | 남은 인증 유효시간 | String |  | Y | 초 단위, 예: 465 |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "inquireOpenAccountAuth",
    "transmissionDate": "20260731",
    "transmissionTime": "104750",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "inquireOpenAccountAuth",
    "institutionTransactionUniqueNo": "20260731104750072639"
  },
  "REC": {
    "authId": "OWA20260731104540453",
    "authAccountNo": "0010000000000001",
    "authStatus": "REQUESTED",
    "expiresAt": "20260731105540",
    "remainSeconds": "465"
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4095 | 인증 ID가 없거나 인증 정보를 찾을 수 없음 | 1원 인증 상태 조회 |
| E4097 | 요청 필드 타입이 유효하지 않음 | 1원 인증 상태 조회 |

---

#### 2.15.4 계좌 상품 목록 조회

##### 설명

계좌 상품 목록 조회 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/inquireAccountProducts | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| accountTypeCode | 조회할 계좌 종류 코드 | String | 3 | Y | 001, 002, 003 |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "inquireAccountProducts",
    "transmissionDate": "20260731",
    "transmissionTime": "104526",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "inquireAccountProducts",
    "institutionTransactionUniqueNo": "20260731104526587692",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "accountTypeCode": "001"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| products | 개설 가능한 상품 목록 | Array |  | Y | 조건에 맞는 상품 배열 |
| accountTypeUniqueNo | 계좌 상품 고유 번호 | String | 20 | Y | 예: 001-1-0cf00defe39249 |
| productName | 상품명 | String |  | Y | 예: 한국은행 외화 수시입출금 상품 |
| accountTypeCode | 계좌 종류 코드 | String | 3 | Y | 001, 002, 003 |
| minInitialDeposit | 최소 초기 입금 금액 | String |  | Y | 예: 0 |
| interestRate | 기본 금리(%) | String |  | Y | 예: 2.5 |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "inquireAccountProducts",
    "transmissionDate": "20260731",
    "transmissionTime": "104526",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "inquireAccountProducts",
    "institutionTransactionUniqueNo": "20260731104526587692"
  },
  "REC": {
    "products": [
      {
        "accountTypeUniqueNo": "001-1-abcdef12345678",
        "productName": "자유입출금통장",
        "accountTypeCode": "001",
        "minInitialDeposit": "0",
        "interestRate": "2.5"
      }
    ]
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4093 | 계좌 유형 또는 상품을 찾을 수 없음 | 개설 가능 상품 조회 |
| E4097 | 요청 필드 타입이 유효하지 않음 | 개설 가능 상품 조회 |

---

#### 2.15.5 1원 인증 재요청

##### 설명

기존 1원 인증 건의 인증 코드를 다시 발송합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/reopenAccountAuth | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| authId | 재발송할 1원 인증 요청 ID | String | 20 | Y | 예: OWA20260731104540453 |
| authText | 거래내역 입금자명에 표기될 기업명 | String | 20 | Y | 예: SSAFY |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "reopenAccountAuth",
    "transmissionDate": "20260731",
    "transmissionTime": "105110",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "reopenAccountAuth",
    "institutionTransactionUniqueNo": "20260731105110358794",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  },
  "authId": "OWA20260731104540453",
  "authText": "SSAFY"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| authId | 1원 인증 요청 ID | String | 20 | Y | 요청값과 동일(새로 발급하지 않음) |
| authAccountNo | 1원이 입금된 계좌번호 | String | 16 | Y | 예: 0010000000000001 |
| expiresAt | 인증 만료 일시 | String | 14 | Y | YYYYMMDDHHmmss, 재요청 시점 기준 10분 뒤로 갱신 |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "reopenAccountAuth",
    "transmissionDate": "20260731",
    "transmissionTime": "105110",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "reopenAccountAuth",
    "institutionTransactionUniqueNo": "20260731105110358794"
  },
  "REC": {
    "authId": "OWA20260731104540453",
    "authAccountNo": "0010000000000001",
    "expiresAt": "20260731110110"
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4092 | 인증 대상 계좌를 찾을 수 없거나 인증 가능한 계좌가 아님 | 1원 인증 재요청 |
| E4097 | 요청 필드 타입이 유효하지 않음 | 1원 인증 재요청 |

---

