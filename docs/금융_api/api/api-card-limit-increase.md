# 카드 한도 증액

- 제목: 카드 한도 증액
- 출처: https://project.ssafy.com/docs/ssafy-finance/api-card-limit-increase
- 크롤링 날짜: 2026-08-24
- 범위: 화면에 표시된 정적 문서 본문만 추출했으며, 실제 금융 API 호출·인증·데이터 변경은 수행하지 않았습니다.
- 요약: 카드 한도 일시 증액, 증액 이력 조회, 증액 취소, 현재 한도 조회 API의 설명·요청·응답 명세·JSON 예시·에러코드를 정리합니다. 예시 API KEY와 USER KEY 값은 redacted 처리했습니다.

### 2.20 카드 한도 증액

#### 2.20.1 카드 한도 일시 증액

##### 설명

카드 이용 한도를 지정 기간 동안 일시 증액하도록 신청합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/temporaryLimitIncrease | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| increaseAmount | 증액 금액 | String |  | Y |  |
| purpose | 증액 목적 | String | 7 | Y | TRAVEL / WEDDING / MOVING / MEDICAL / OTHER |
| startDate | 시작일(YYYYMMDD) | String | 8 | Y |  |
| endDate | 종료일(YYYYMMDD) | String | 8 | Y |  |
| reason | 증액 사유 | String | 100 | N |  |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "temporaryLimitIncrease",

    "transmissionDate": "20260810",

    "transmissionTime": "120000",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "temporaryLimitIncrease",

    "institutionTransactionUniqueNo": "20260810120000000001",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "cardNo": "1234567890123456",

  "increaseAmount": "300000",

  "purpose": "TRAVEL",

  "startDate": "20260810",

  "endDate": "20260910",

  "reason": "해외여행 결제 예정"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 응답 데이터 | Object |  | Y |  |
| requestId | 한도 증액 요청 ID | String |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| originalLimit | 기본 이용 한도 | String |  | Y |  |
| increasedLimit | 증액 후 한도 | String |  | Y |  |
| increaseAmount | 증액 금액 | String |  | Y |  |
| startDate | 증액 시작일 | String | 8 | Y |  |
| endDate | 증액 종료일 | String | 8 | Y |  |
| purpose | 증액 목적 | String | 7 | Y | TRAVEL / WEDDING / MOVING / MEDICAL / OTHER |
| status | 증액 상태 | String |  | Y | WAITING / APPROVED / CANCELED / EXPIRED |
| createdAt | 생성 일시 | String | 14 | Y |  |
| updatedAt | 수정 일시 | String | 14 | Y |  |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "temporaryLimitIncrease",

    "transmissionDate": "20260810",

    "transmissionTime": "120000",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "temporaryLimitIncrease",

    "institutionTransactionUniqueNo": "20260810120000000001"

  },

  "REC": {

    "requestId": "TLI20260810120000123",

    "cardNo": "123456******3456",

    "originalLimit": "200000",

    "increasedLimit": "500000",

    "increaseAmount": "300000",

    "startDate": "20260810",

    "endDate": "20260910",

    "purpose": "TRAVEL",

    "status": "APPROVED",

    "createdAt": "20260810120000",

    "updatedAt": "20260810120000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4050 | 카드를 찾을 수 없음 | 카드 한도 일시 증액 |
| E4051 | 카드 소유자가 아님 | 카드 한도 일시 증액 |
| E4052 | 카드가 정상 상태가 아님 | 카드 한도 일시 증액 |
| E4053 | 증액 기간이 90일 초과 | 카드 한도 일시 증액 |
| E4054 | 증액 금액이 허용 한도 초과 | 카드 한도 일시 증액 |
| E4055 | 이미 활성 또는 대기 중인 증액 요청 존재 | 카드 한도 일시 증액 |
| E4056 | 시작일이 종료일보다 이전이 아님 | 카드 한도 일시 증액 |
| E4059 | 요청 필드 타입 또는 요청값이 유효하지 않음 | 카드 한도 일시 증액 |

#### 2.20.2 카드 한도 증액 이력 조회

##### 설명

카드의 한도 증액 신청 이력을 상태 조건으로 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireLimitIncreaseHistory | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| status | 증액 상태 | String |  | N | WAITING / APPROVED / CANCELED / EXPIRED |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireLimitIncreaseHistory",

    "transmissionDate": "20260810",

    "transmissionTime": "120100",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireLimitIncreaseHistory",

    "institutionTransactionUniqueNo": "20260810120100000002",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "cardNo": "1234567890123456",

  "status": "APPROVED"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 응답 데이터 | Object |  | Y |  |
| history[] | 한도 증액 이력 | Array |  | Y |  |
| ↳ requestId | 한도 증액 요청 ID | String |  | Y |  |
| ↳ increaseAmount | 증액 금액 | String |  | Y |  |
| ↳ purpose | 증액 목적 | String |  | Y |  |
| ↳ startDate | 증액 시작일 | String | 8 | Y |  |
| ↳ endDate | 증액 종료일 | String | 8 | Y |  |
| ↳ status | 증액 상태 | String |  | Y |  |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireLimitIncreaseHistory",

    "transmissionDate": "20260810",

    "transmissionTime": "120100",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireLimitIncreaseHistory",

    "institutionTransactionUniqueNo": "20260810120100000002"

  },

  "REC": {

    "history": [

      {

        "requestId": "TLI20260810120000123",

        "increaseAmount": "300000",

        "purpose": "TRAVEL",

        "startDate": "20260810",

        "endDate": "20260910",

        "status": "APPROVED"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4050 | 카드를 찾을 수 없거나 카드번호가 유효하지 않음 | 한도 증액 이력 조회 |
| E4051 | 카드 소유자가 아님 | 한도 증액 이력 조회 |
| E4052 | 카드가 정상 상태가 아님 | 한도 증액 이력 조회 |
| E4059 | 요청 필드 타입 또는 상태 필터가 유효하지 않음 | 한도 증액 이력 조회 |

#### 2.20.3 카드 한도 증액 취소

##### 설명

증액 시작 전 대기 상태인 한도 증액 신청을 취소합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/cancelLimitIncrease | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| requestId | 한도 증액 요청 ID | String |  | Y |  |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "cancelLimitIncrease",

    "transmissionDate": "20260810",

    "transmissionTime": "121000",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "cancelLimitIncrease",

    "institutionTransactionUniqueNo": "20260810121000000003",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "requestId": "TLI20260810120500456"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 응답 데이터 | Object |  | Y |  |
| requestId | 한도 증액 요청 ID | String |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| originalLimit | 기본 이용 한도 | String |  | Y |  |
| increasedLimit | 증액 후 한도 | String |  | Y |  |
| increaseAmount | 증액 금액 | String |  | Y |  |
| startDate | 증액 시작일 | String | 8 | Y |  |
| endDate | 증액 종료일 | String | 8 | Y |  |
| purpose | 증액 목적 | String | 7 | Y | TRAVEL / WEDDING / MOVING / MEDICAL / OTHER |
| status | 증액 상태 | String |  | Y | WAITING / APPROVED / CANCELED / EXPIRED |
| createdAt | 생성 일시 | String | 14 | Y |  |
| updatedAt | 수정 일시 | String | 14 | Y |  |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "cancelLimitIncrease",

    "transmissionDate": "20260810",

    "transmissionTime": "121000",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "cancelLimitIncrease",

    "institutionTransactionUniqueNo": "20260810121000000003"

  },

  "REC": {

    "requestId": "TLI20260810120500456",

    "cardNo": "123456******3456",

    "originalLimit": "200000",

    "increasedLimit": "400000",

    "increaseAmount": "200000",

    "startDate": "20260815",

    "endDate": "20260915",

    "purpose": "MEDICAL",

    "status": "CANCELED",

    "createdAt": "20260810120500",

    "updatedAt": "20260810121000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4050 | 연결된 카드를 찾을 수 없음 | 한도 증액 취소 |
| E4051 | 카드 또는 증액 요청 소유자가 아님 | 한도 증액 취소 |
| E4052 | 카드가 정상 상태가 아님 | 한도 증액 취소 |
| E4057 | 증액 요청을 찾을 수 없거나 요청 ID가 유효하지 않음 | 한도 증액 취소 |
| E4058 | 시작 전 대기 요청이 아니어서 취소할 수 없음 | 한도 증액 취소 |
| E4059 | 요청 필드 타입이 유효하지 않음 | 한도 증액 취소 |

#### 2.20.4 카드 한도 조회

##### 설명

카드의 기본 한도, 현재 한도, 사용금액과 가용금액을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireCardLimit | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireCardLimit",

    "transmissionDate": "20260810",

    "transmissionTime": "121500",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireCardLimit",

    "institutionTransactionUniqueNo": "20260810121500000004",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "cardNo": "1234567890123456"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 응답 데이터 | Object |  | Y |  |
| originalLimit | 기본 이용 한도 | String |  | Y |  |
| currentLimit | 현재 이용 한도 | String |  | Y |  |
| usedAmount | 사용 금액 | String |  | Y |  |
| availableAmount | 이용 가능 금액 | String |  | Y |  |
| activeIncreaseRequestId | 활성 증액 요청 ID | String |  | N |  |
| increaseEndDate | 증액 종료일 | String | 8 | N |  |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireCardLimit",

    "transmissionDate": "20260810",

    "transmissionTime": "121500",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireCardLimit",

    "institutionTransactionUniqueNo": "20260810121500000004"

  },

  "REC": {

    "originalLimit": "200000",

    "currentLimit": "500000",

    "usedAmount": "100000",

    "availableAmount": "400000",

    "activeIncreaseRequestId": "TLI20260810120000123",

    "increaseEndDate": "20260910"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4050 | 카드를 찾을 수 없거나 카드번호가 유효하지 않음 | 카드 한도 조회 |
| E4051 | 카드 소유자가 아님 | 카드 한도 조회 |
| E4052 | 카드가 정상 상태가 아님 | 카드 한도 조회 |
| E4059 | 요청 필드 타입이 유효하지 않음 | 카드 한도 조회 |
