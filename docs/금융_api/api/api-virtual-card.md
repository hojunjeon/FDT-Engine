# 가상카드

- 제목: 가상카드
- 출처: https://project.ssafy.com/docs/ssafy-finance/api-virtual-card
- 크롤링 날짜: 2026-08-24
- 범위: 화면에 표시된 정적 문서 본문만 추출했으며, 실제 금융 API 호출·인증·데이터 변경은 수행하지 않았습니다.
- 요약: 가상카드 발급·목록·상세 조회·폐기, 결제 검증 및 결제 내역 조회 API의 설명·요청·응답 명세·JSON 예시·에러코드를 정리합니다. 예시 API KEY와 USER KEY 값은 redacted 처리했습니다.

### 2.19 가상카드

#### 2.19.1 가상카드 발급

##### 설명

실물 카드에 연결된 일회용 가상카드를 발급합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createVirtualCardNumber | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | 공통 요청 헤더 객체 |
| cardNo | 실물 카드번호 | String | 16 | Y | 가상카드를 연결할 16자리 실물 카드번호 |
| usageType | 사용 유형 | String |  | Y | ONCE 또는 TERM |
| validityMinutes | 일회성 유효시간(분) | String |  | N | ONCE 사용 시 1~1440, 미입력 시 30분 |
| validityDate | 기간성 유효일자 | String | 8 | N | TERM 사용 시 필수, YYYYMMDD |
| limitAmount | 결제 한도 | String |  | N | 문자열 금액, 미입력 시 실물 카드 한도 적용 |
| merchantId | 가맹점 ID | String |  | N | 문자열 ID, 미입력 시 가맹점 제한 없음 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "createVirtualCardNumber",

    "transmissionDate": "20260810",

    "transmissionTime": "113100",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "createVirtualCardNumber",

    "institutionTransactionUniqueNo": "20260810113100000001",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "cardNo": "1234567890123456",

  "usageType": "ONCE",

  "validityMinutes": "30",

  "validityDate": "",

  "limitAmount": "50000",

  "merchantId": "1"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 공통 응답 헤더 객체 |
| REC | 응답 데이터 | Object |  | Y | API별 응답 데이터 객체 |
| virtualCardId | 가상카드 ID | String |  | Y | 예: VCN20260731173716375 |
| virtualCardNo | 가상카드 번호 | String | 16 | Y | 예: 9999305260714250 |
| virtualCvc | 가상카드 CVC | String | 3 | Y | 예: 914 |
| virtualExpiry | 가상카드 유효기간 | String | 8 | Y | YYYYMMDD, 예: 20260802 |
| usageType | 사용 유형 | String |  | Y | ONCE 또는 TERM |
| expiresAt | 만료 일시 | String | 14 | Y | YYYYMMDDHHmmss, 예: 20260802235959 |
| limitAmount | 결제 한도 | String |  | Y | 문자열 금액, 예: "50000" |
| status | 가상카드 상태 | String |  | Y | ACTIVE, USED 또는 EXPIRED |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss, 예: 20260731173719 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "createVirtualCardNumber",

    "transmissionDate": "20260810",

    "transmissionTime": "113100",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "createVirtualCardNumber",

    "institutionTransactionUniqueNo": "20260810113100000001"

  },

  "REC": {

    "virtualCardId": "VCN20260810113000123",

    "virtualCardNo": "9999123456789012",

    "virtualCvc": "321",

    "virtualExpiry": "20260811",

    "usageType": "ONCE",

    "expiresAt": "20260810120000",

    "limitAmount": "50000",

    "status": "ACTIVE",

    "createdAt": "20260810113000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4030 | 실물 카드를 찾을 수 없음 | 가상카드 발급 |
| E4031 | 카드 소유자가 아님 | 가상카드 발급 |
| E4032 | 실물 카드가 정상 상태가 아님 | 가상카드 발급 |
| E4036 | 실물 카드 유효기간 만료 | 가상카드 발급 |
| E4040 | 가상카드 유효 시간이 허용 범위 초과 | 가상카드 발급 |
| E4041 | 유효기간 종료일이 과거 | 가상카드 발급 |
| E4042 | 활성 가상카드 수 초과 | 가상카드 발급 |
| E4043 | 제한 가맹점을 찾을 수 없음 | 가상카드 발급 |
| E4048 | 요청 필드 타입이 유효하지 않음 | 가상카드 발급 |

#### 2.19.2 가상카드 목록 조회

##### 설명

사용자의 가상카드 목록을 카드번호와 상태 조건으로 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireVirtualCardList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | 공통 요청 헤더 객체 |
| cardNo | 실물 카드번호 | String | 16 | N | 조회 조건, 미입력 시 전체 카드 조회 |
| status | 가상카드 상태 | String |  | N | ACTIVE, USED, EXPIRED; 미입력 시 전체 상태 조회 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireVirtualCardList",

    "transmissionDate": "20260810",

    "transmissionTime": "113200",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireVirtualCardList",

    "institutionTransactionUniqueNo": "20260810113200000002",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "cardNo": "1234567890123456",

  "status": "ACTIVE"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 공통 응답 헤더 객체 |
| REC | 응답 데이터 | Object |  | Y | API별 응답 데이터 객체 |
| virtualCards[] | 가상카드 목록 | Array |  | Y | 조회된 가상카드 배열 |
| └ virtualCardId | 가상카드 ID | String |  | Y | 예: VCN20260731173716375 |
| └ virtualCardNo | 마스킹된 가상카드 번호 | String | 16 | Y | 예: 999930******4250 |
| └ usageType | 사용 유형 | String |  | Y | ONCE 또는 TERM |
| └ limitAmount | 결제 한도 | String |  | Y | 문자열 금액, 예: "50000" |
| └ expiresAt | 만료 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| └ status | 가상카드 상태 | String |  | Y | ACTIVE, USED 또는 EXPIRED |
| └ createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| └ updatedAt | 수정 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireVirtualCardList",

    "transmissionDate": "20260810",

    "transmissionTime": "113200",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireVirtualCardList",

    "institutionTransactionUniqueNo": "20260810113200000002"

  },

  "REC": {

    "virtualCards": [

      {

        "virtualCardId": "VCN20260810113000123",

        "virtualCardNo": "999912******9012",

        "usageType": "ONCE",

        "limitAmount": "50000",

        "expiresAt": "20260810120000",

        "status": "ACTIVE",

        "createdAt": "20260810113000",

        "updatedAt": "20260810113000"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4048 | 요청 필드 타입이 유효하지 않음 | 가상카드 목록 조회 |
| E4049 | 카드번호 필터가 16자리 숫자가 아님 | 가상카드 목록 조회 |

#### 2.19.3 가상카드 상세 조회

##### 설명

가상카드 ID로 카드번호, CVC, 한도와 상태를 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireVirtualCardDetails | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | 공통 요청 헤더 객체 |
| virtualCardId | 가상카드 ID | String |  | Y | 조회할 가상카드 ID, 예: VCN20260731173716375 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireVirtualCardDetails",

    "transmissionDate": "20260810",

    "transmissionTime": "113300",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireVirtualCardDetails",

    "institutionTransactionUniqueNo": "20260810113300000003",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "virtualCardId": "VCN20260810113000123"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 공통 응답 헤더 객체 |
| REC | 응답 데이터 | Object |  | Y | API별 응답 데이터 객체 |
| virtualCardId | 가상카드 ID | String |  | Y | 예: VCN20260731173716375 |
| virtualCardNo | 가상카드 번호 | String | 16 | Y | 예: 9999305260714250 |
| virtualCvc | 가상카드 CVC | String | 3 | Y | 예: 914 |
| virtualExpiry | 가상카드 유효기간 | String | 8 | Y | YYYYMMDD |
| usageType | 사용 유형 | String |  | Y | ONCE 또는 TERM |
| expiresAt | 만료 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| limitAmount | 결제 한도 | String |  | Y | 문자열 금액, 예: "50000" |
| merchantId | 가맹점 ID | String |  | N | 제한 가맹점이 없으면 null, 예: "1" |
| status | 가상카드 상태 | String |  | Y | ACTIVE, USED 또는 EXPIRED |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireVirtualCardDetails",

    "transmissionDate": "20260810",

    "transmissionTime": "113300",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireVirtualCardDetails",

    "institutionTransactionUniqueNo": "20260810113300000003"

  },

  "REC": {

    "virtualCardId": "VCN20260810113000123",

    "virtualCardNo": "9999123456789012",

    "virtualCvc": "321",

    "virtualExpiry": "20260811",

    "usageType": "ONCE",

    "expiresAt": "20260810120000",

    "limitAmount": "50000",

    "merchantId": "1",

    "status": "ACTIVE",

    "createdAt": "20260810113000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4031 | 가상카드 소유자가 아님 | 가상카드 상세 조회 |
| E4044 | 가상카드를 찾을 수 없음 | 가상카드 상세 조회 |
| E4048 | 요청 필드 타입이 유효하지 않음 | 가상카드 상세 조회 |

#### 2.19.4 가상카드 폐기

##### 설명

가상카드를 즉시 폐기하고 상태를 만료로 변경합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/revokeVirtualCard | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | 공통 요청 헤더 객체 |
| virtualCardNo | 가상카드 번호 | String | 16 | Y | 폐기할 16자리 가상카드 번호, 예: 9999305260714250 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "revokeVirtualCard",

    "transmissionDate": "20260810",

    "transmissionTime": "113400",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "revokeVirtualCard",

    "institutionTransactionUniqueNo": "20260810113400000004",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "virtualCardNo": "9999123456789012"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 공통 응답 헤더 객체 |
| REC | 응답 데이터 | Object |  | Y | API별 응답 데이터 객체 |
| virtualCardId | 가상카드 ID | String |  | Y | 예: VCN20260731173716375 |
| virtualCardNo | 가상카드 번호 | String | 16 | Y | 예: 9999305260714250 |
| virtualCvc | 가상카드 CVC | String | 3 | Y | 예: 914 |
| virtualExpiry | 가상카드 유효기간 | String | 8 | Y | YYYYMMDD, 예: 20260802 |
| usageType | 사용 유형 | String |  | Y | ONCE 또는 TERM |
| expiresAt | 만료 일시 | String | 14 | Y | YYYYMMDDHHmmss, 예: 20260802235959 |
| limitAmount | 결제 한도 | String |  | Y | 문자열 금액, 예: "50000" |
| status | 가상카드 상태 | String |  | Y | ACTIVE, USED 또는 EXPIRED |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss, 예: 20260731173719 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "revokeVirtualCard",

    "transmissionDate": "20260810",

    "transmissionTime": "113400",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "revokeVirtualCard",

    "institutionTransactionUniqueNo": "20260810113400000004"

  },

  "REC": {

    "virtualCardId": "VCN20260810113000123",

    "virtualCardNo": "9999123456789012",

    "virtualCvc": "321",

    "virtualExpiry": "20260811",

    "usageType": "ONCE",

    "expiresAt": "20260810120000",

    "limitAmount": "50000",

    "status": "EXPIRED",

    "createdAt": "20260810113000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4031 | 가상카드 소유자가 아님 | 가상카드 폐기 |
| E4044 | 가상카드를 찾을 수 없음 | 가상카드 폐기 |
| E4048 | 요청 필드 타입이 유효하지 않음 | 가상카드 폐기 |

#### 2.19.5 가상카드 결제 검증

##### 설명

가상카드 정보와 결제 조건을 검증하고 사용 가능 여부를 반환합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/validateVirtualCardPayment | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | 공통 요청 헤더 객체 |
| virtualCardNo | 가상카드 번호 | String | 16 | Y | 결제할 16자리 가상카드 번호, 예: 9999305260714250 |
| virtualCvc | 가상카드 CVC | String | 3 | Y | 3자리 CVC, 예: 914 |
| paymentAmount | 결제 금액 | String |  | Y | 문자열 금액, 예: "10000" |
| merchantId | 결제 가맹점 ID | String |  | Y | 문자열 가맹점 ID, 예: "1" |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "validateVirtualCardPayment",

    "transmissionDate": "20260810",

    "transmissionTime": "113500",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "validateVirtualCardPayment",

    "institutionTransactionUniqueNo": "20260810113500000005",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "virtualCardNo": "9999123456789012",

  "virtualCvc": "321",

  "paymentAmount": "10000",

  "merchantId": "1"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 공통 응답 헤더 객체 |
| REC | 응답 데이터 | Object |  | Y | API별 응답 데이터 객체 |
| valid | 결제 가능 여부 | Boolean |  | Y | 결제 검증 성공 시 true |
| resultCode | 검증 결과 코드 | String |  | Y | 정상 처리 시 H0000 |
| resultMessage | 검증 결과 메시지 | String |  | Y | 검증 결과 설명 |
| remainingLimit | 결제 후 잔여 한도 | String |  | Y | 문자열 금액, 예: "40000" |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "validateVirtualCardPayment",

    "transmissionDate": "20260810",

    "transmissionTime": "113500",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "validateVirtualCardPayment",

    "institutionTransactionUniqueNo": "20260810113500000005"

  },

  "REC": {

    "valid": true,

    "resultCode": "H0000",

    "resultMessage": "정상처리 되었습니다.",

    "remainingLimit": "40000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4030 | 연결 실물 카드를 찾을 수 없음 | 가상카드 결제 검증 |
| E4031 | 가상카드 소유자가 아님 | 가상카드 결제 검증 |
| E4043 | 가맹점을 찾을 수 없음 | 가상카드 결제 검증 |
| E4044 | 가상카드를 찾을 수 없거나 카드번호·CVC 불일치 | 가상카드 결제 검증 |
| E4045 | 가상카드가 만료·폐기·사용 완료되었거나 가맹점 조건 불일치 | 가상카드 결제 검증 |
| E4046 | 결제 한도 초과 | 가상카드 결제 검증 |
| E4048 | 요청 필드 타입이 유효하지 않음 | 가상카드 결제 검증 |

#### 2.19.6 가상카드 결제 내역 조회

##### 설명

가상카드 결제 내역 정보를 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireVirtualCardTransactionList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | 공통 요청 헤더 객체 |
| virtualCardNo | 가상카드 번호 | String | 16 | Y | 조회할 16자리 가상카드 번호, 예: 9999305260714250 |
| startDate | 조회 시작일자 | String | 8 | N | YYYYMMDD, 미입력 시 전체 기간 조회 |
| endDate | 조회 종료일자 | String | 8 | N | YYYYMMDD, 미입력 시 전체 기간 조회 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireVirtualCardTransactionList",

    "transmissionDate": "20260810",

    "transmissionTime": "113600",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireVirtualCardTransactionList",

    "institutionTransactionUniqueNo": "20260810113600000006",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "virtualCardNo": "9999123456789012",

  "startDate": "20260801",

  "endDate": "20260810"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 공통 응답 헤더 객체 |
| REC | 응답 데이터 | Object |  | Y | API별 응답 데이터 객체 |
| virtualCardNo | 가상카드 번호 | String | 16 | Y | 예: 9999305260714250 |
| transactionList[] | 결제 내역 목록 | Array |  | Y | 가상카드 결제 내역 배열 |
| └ transactionUniqueNo | 거래 고유번호 | String |  | Y | 문자열 거래 고유번호, 예: "34" |
| └ merchantId | 가맹점 ID | String |  | Y | 문자열 가맹점 ID, 예: "1" |
| └ transactionDate | 거래 일자 | String | 8 | Y | YYYYMMDD, 예: 20260731 |
| └ transactionTime | 거래 시간 | String | 6 | Y | HHmmss, 예: 173904 |
| └ transactionBalance | 거래 금액 | String |  | Y | 문자열 금액, 예: "10000" |
| └ cardStatus | 결제 상태 | String |  | Y | 예: SUCCESS |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireVirtualCardTransactionList",

    "transmissionDate": "20260810",

    "transmissionTime": "113600",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireVirtualCardTransactionList",

    "institutionTransactionUniqueNo": "20260810113600000006"

  },

  "REC": {

    "virtualCardNo": "9999123456789012",

    "transactionList": [

      {

        "transactionUniqueNo": "202608101140000001",

        "merchantId": "1",

        "transactionDate": "20260810",

        "transactionTime": "114000",

        "transactionBalance": "10000",

        "cardStatus": "SUCCESS"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4031 | 가상카드 소유자가 아님 | 가상카드 결제 내역 조회 |
| E4044 | 가상카드를 찾을 수 없음 | 가상카드 결제 내역 조회 |
| E4048 | 요청 필드 타입이 유효하지 않음 | 가상카드 결제 내역 조회 |

