# 예약이체

- 제목: 예약이체
- 출처: https://project.ssafy.com/docs/ssafy-finance/api-scheduled-transfer
- 크롤링 날짜: 2026-08-24
- 범위: 화면에 표시된 정적 문서 본문만 추출했으며, 실제 금융 API 호출·인증·데이터 변경은 수행하지 않았습니다.
- 검증 상태: UNVERIFIED — 라이브 API 동작은 확인하지 않았습니다.
- 요약: 예약이체 등록, 실행 내역 조회, 목록·상세 조회, 수정, 취소, 일시정지·재개 API의 설명·요청·응답 명세·JSON 예시·에러코드를 정리합니다. 예시 API KEY와 USER KEY 값은 redacted 처리했습니다.

### 2.16 예약이체

---

#### 2.16.1 예약이체 등록

##### 설명

예약이체 등록 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/transferReservation | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y | 예: 0019763592900582 |
| depositBankCode | 입금 계좌의 은행 코드 | String | 3 | Y | 예: 001 |
| depositAccountNo | 입금 계좌번호 | String | 16 | Y | 예: 0019763592900583 |
| transactionBalance | 0보다 큰 정수 형태의 이체 금액 | String |  | Y | 예: 500000 |
| reservationName | 예약이체 이름 | String |  | Y | 예: 매월 월세 |
| reservationType | 예약 유형 | String |  | Y | ONCE, REPEAT |
| startDate | 예약 시작일 | String | 8 | Y | YYYYMMDD, 예: 20260715 |
| endDate | 반복 예약 종료일 | String | 8 | N | YYYYMMDD, 예: 20261231 |
| transferCycle | 반복 이체 주기 | String |  | N | DAILY, WEEKLY, MONTHLY |
| transferDay | 월간 반복 이체일 | String | 2 | N | 01~31, 예: 25 |
| depositTransactionSummary | 입금계좌의 거래요약 메모 | String |  | N | 1회 예약의 가상계좌 입금 시 예상 입금자명 입력 |
| withdrawalTransactionSummary | 출금 통장 거래 요약 | String |  | N | 예: 월세이체 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "transferReservation",

    "transmissionDate": "20260731",

    "transmissionTime": "110953",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "transferReservation",

    "institutionTransactionUniqueNo": "20260731110953428107",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "withdrawalAccountNo": "0019763592900582",

  "depositBankCode": "001",

  "depositAccountNo": "0019763592900583",

  "transactionBalance": "500000",

  "reservationName": "매월 월세",

  "reservationType": "REPEAT",

  "startDate": "20260715",

  "endDate": "20261231",

  "transferCycle": "MONTHLY",

  "transferDay": "25",

  "depositTransactionSummary": "입금 메모",

  "withdrawalTransactionSummary": "월세이체"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| reservationId | 예약이체 ID | String | 20 | Y | 예약이체 식별자 |
| reservationName | 예약이체명 | String |  | Y | 사용자가 지정한 예약 이름 |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| depositAccountNo | 입금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| transactionBalance | 이체 금액 | String |  | Y | 숫자 형식의 문자열 |
| reservationType | 예약 유형 | String |  | Y | ONCE, REPEAT |
| transferCycle | 이체 주기 | String |  | N | DAILY, WEEKLY, MONTHLY |
| nextTransferDate | 다음 이체일 | String | 8 | Y | YYYYMMDD |
| status | 예약 상태 | String |  | Y | ACTIVE, PAUSED, CANCELED, COMPLETED, FAILED |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| updatedAt | 수정 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "transferReservation",

    "transmissionDate": "20260731",

    "transmissionTime": "110953",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "transferReservation",

    "institutionTransactionUniqueNo": "20260731110953428107"

  },

  "REC": {

    "reservationId": "RSV4F8A1C2D3E5B67890",

    "reservationName": "매월 월세",

    "withdrawalAccountNo": "0019763592900582",

    "depositAccountNo": "0019763592900583",

    "transactionBalance": "500000",

    "reservationType": "REPEAT",

    "transferCycle": "MONTHLY",

    "nextTransferDate": "20260725",

    "status": "ACTIVE",

    "createdAt": "20260715162232",

    "updatedAt": "20260715162232"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4010 | 출금 계좌를 찾을 수 없음 | 예약이체 등록 |
| E4011 | 출금 계좌 소유자가 아님 | 예약이체 등록 |
| E4012 | 출금 계좌가 정상 상태가 아님 | 예약이체 등록 |
| E4013 | 입금 계좌를 찾을 수 없음 | 예약이체 등록 |
| E4014 | 종료일이 시작일보다 이전 | 예약이체 등록 |
| E4015 | 이체 주기가 올바르지 않음 | 예약이체 등록 |
| E4016 | 이체일이 올바르지 않음 | 예약이체 등록 |
| E4017 | 예약이체 이름 누락 또는 유효하지 않음 | 예약이체 등록 |
| E4018 | 예약이체 유형이 올바르지 않음 | 예약이체 등록 |
| E4021 | 최초 이체일이 종료일보다 이후 | 예약이체 등록 |
| E4022 | 요청 필드 타입이 유효하지 않음 | 예약이체 등록 |
| E4023 | 출금 계좌 잔액 부족 | 예약이체 등록 |

---

#### 2.16.2 예약이체 실행 내역 조회

##### 설명

예약이체 실행 내역 조회 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/inquireTransferReservationHistory | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| reservationId | 예약이체 ID | String | 20 | Y | 예약이체 등록 결과의 식별자 |
| startDate | 조회 시작일 | String | 8 | N | YYYYMMDD |
| endDate | 조회 종료일 | String | 8 | N | YYYYMMDD |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireTransferReservationHistory",

    "transmissionDate": "20260731",

    "transmissionTime": "111012",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireTransferReservationHistory",

    "institutionTransactionUniqueNo": "20260731111012087471",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "reservationId": "RSV4F8A1C2D3E5B67890",

  "startDate": "20260701",

  "endDate": "20260731"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| history | 이체 예약 실행 이력 목록 | Array |  | Y | 조회 조건에 맞는 실행 이력 배열 |
| transferDate | 이체일 | String | 8 | Y | YYYYMMDD |
| transferTime | 이체 시각 | String | 6 | Y | HHmmss |
| transactionBalance | 이체 금액 | String |  | Y | 숫자 형식의 문자열 |
| resultCode | 처리 결과 코드 | String |  | Y | 실행 결과 코드 |
| resultMessage | 처리 결과 메시지 | String |  | N | 실행 결과 설명 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireTransferReservationHistory",

    "transmissionDate": "20260731",

    "transmissionTime": "111012",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireTransferReservationHistory",

    "institutionTransactionUniqueNo": "20260731111012087471"

  },

  "REC": {

    "history": [

      {

        "transferDate": "20260725",

        "transferTime": "090000",

        "transactionBalance": "500000",

        "resultCode": "H0000",

        "resultMessage": "정상처리 되었습니다."

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4014 | 조회 종료일이 시작일보다 이전 | 예약이체 실행 이력 조회 |
| E4019 | 예약이체를 찾을 수 없음 | 예약이체 실행 이력 조회 |
| E4020 | 예약이체 소유자가 아님 | 예약이체 실행 이력 조회 |
| E4022 | 요청 필드 타입이 유효하지 않음 | 예약이체 실행 이력 조회 |

---

#### 2.16.3 예약이체 목록 조회

##### 설명

예약이체 목록 조회 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/inquireTransferReservation | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | N | 조회할 출금 계좌번호 |
| status | 예약 상태 | String |  | N | ACTIVE, PAUSED, CANCELED, COMPLETED, FAILED |
| keyword | 검색어 | String |  | N | 예약이체명 검색어 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireTransferReservation",

    "transmissionDate": "20260731",

    "transmissionTime": "111028",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireTransferReservation",

    "institutionTransactionUniqueNo": "20260731111028653283",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "withdrawalAccountNo": "0010000000000001",

  "status": "ACTIVE",

  "keyword": "월세"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| reservations | 이체 예약 목록 | Array |  | Y | 조회 조건에 맞는 예약 배열 |
| reservationId | 예약이체 ID | String | 20 | Y | 예약이체 식별자 |
| reservationName | 예약이체명 | String |  | Y | 사용자가 지정한 예약 이름 |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| depositAccountNo | 입금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| depositBankCode | 입금 은행 코드 | String | 3 | Y | 예: 001 |
| transactionBalance | 이체 금액 | String |  | Y | 숫자 형식의 문자열 |
| nextTransferDate | 다음 이체일 | String | 8 | Y | YYYYMMDD |
| reservationType | 예약 유형 | String |  | Y | 예: REPEAT |
| transferCycle | 이체 주기 | String |  | N | 예: MONTHLY |
| transferDay | 월간 반복 이체일 | String | 2 | N | 01~31, 예: 25 |
| status | 예약 상태 | String |  | Y | ACTIVE, PAUSED, CANCELED, COMPLETED, FAILED |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireTransferReservation",

    "transmissionDate": "20260731",

    "transmissionTime": "111028",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireTransferReservation",

    "institutionTransactionUniqueNo": "20260731111028653283"

  },

  "REC": {

    "reservations": [

      {

        "reservationId": "RSV4F8A1C2D3E5B67890",

        "reservationName": "매월 월세",

        "withdrawalAccountNo": "0019763592900582",

        "depositAccountNo": "0019763592900583",

        "depositBankCode": "001",

        "transactionBalance": "500000",

        "nextTransferDate": "20260725",

        "reservationType": "REPEAT",

        "transferCycle": "MONTHLY",

        "transferDay": "25",

        "status": "ACTIVE"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4010 | 출금 계좌번호가 유효하지 않음 | 예약이체 목록 조회 |
| E4018 | 예약이체 상태 필터가 올바르지 않음 | 예약이체 목록 조회 |
| E4022 | 요청 필드 타입이 유효하지 않음 | 예약이체 목록 조회 |

---

#### 2.16.4 예약이체 상세 조회

##### 설명

예약이체 상세 조회 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/inquireTransferReservationDetail | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| reservationId | 예약이체 ID | String | 20 | Y | 예약이체 등록 결과의 식별자 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireTransferReservationDetail",

    "transmissionDate": "20260731",

    "transmissionTime": "111046",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireTransferReservationDetail",

    "institutionTransactionUniqueNo": "20260731111046571391",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "reservationId": "RSV4F8A1C2D3E5B67890"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| reservationId | 예약이체 ID | String | 20 | Y | 예약이체 식별자 |
| reservationName | 예약이체명 | String |  | Y | 사용자가 지정한 예약 이름 |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| depositAccountNo | 입금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| depositBankCode | 입금 은행 코드 | String | 3 | Y | 예: 001 |
| transactionBalance | 이체 금액 | String |  | Y | 숫자 형식의 문자열 |
| withdrawalTransactionSummary | 출금 계좌 거래 요약 | String |  | N | 예: 예약이체 출금 |
| depositTransactionSummary | 입금 계좌 거래 요약 | String |  | N | 예: 예약이체 입금 |
| reservationType | 예약 유형 | String |  | Y | 예: REPEAT |
| startDate | 이체 시작일 | String | 8 | Y | YYYYMMDD |
| endDate | 이체 종료일 | String | 8 | N | YYYYMMDD |
| transferCycle | 이체 주기 | String |  | N | 예: MONTHLY |
| transferDay | 월간 반복 이체일 | String | 2 | N | 01~31, 예: 25 |
| nextTransferDate | 다음 이체일 | String | 8 | Y | YYYYMMDD |
| status | 예약 상태 | String |  | Y | 예: ACTIVE |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| updatedAt | 수정 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireTransferReservationDetail",

    "transmissionDate": "20260731",

    "transmissionTime": "111046",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireTransferReservationDetail",

    "institutionTransactionUniqueNo": "20260731111046571391"

  },

  "REC": {

    "reservationId": "RSV4F8A1C2D3E5B67890",

    "reservationName": "매월 월세",

    "withdrawalAccountNo": "0019763592900582",

    "depositAccountNo": "0019763592900583",

    "depositBankCode": "001",

    "transactionBalance": "500000",

    "withdrawalTransactionSummary": "월세이체",

    "depositTransactionSummary": "입금 메모",

    "reservationType": "REPEAT",

    "startDate": "20260715",

    "endDate": "20261231",

    "transferCycle": "MONTHLY",

    "transferDay": "25",

    "nextTransferDate": "20260725",

    "status": "ACTIVE",

    "createdAt": "20260715162232",

    "updatedAt": "20260715162232"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4019 | 예약이체를 찾을 수 없음 | 예약이체 상세 조회 |
| E4020 | 예약이체 소유자가 아님 | 예약이체 상세 조회 |
| E4022 | 요청 필드 타입이 유효하지 않음 | 예약이체 상세 조회 |

---

#### 2.16.5 예약이체 수정

##### 설명

예약이체 수정 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/updateTransferReservation | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| reservationId | 예약이체 ID | String | 20 | Y | 수정할 예약이체 식별자 |
| reservationName | 예약이체명 | String |  | N | 변경할 예약 이름 |
| transactionBalance | 이체 금액 | String |  | N | 숫자 형식의 문자열 |
| transferCycle | 이체 주기 | String |  | N | DAILY, WEEKLY, MONTHLY |
| transferDay | 이체일 | String |  | N | 주기 내 이체일 |
| endDate | 이체 종료일 | String | 8 | N | YYYYMMDD |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "updateTransferReservation",

    "transmissionDate": "20260731",

    "transmissionTime": "111059",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "updateTransferReservation",

    "institutionTransactionUniqueNo": "20260731111059018986",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "reservationId": "RSV4F8A1C2D3E5B67890",

  "reservationName": "매월 월세",

  "transactionBalance": "550000",

  "transferCycle": "MONTHLY",

  "transferDay": "25",

  "endDate": "20261231"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| reservationId | 예약이체 ID | String | 20 | Y | 예약이체 식별자 |
| reservationName | 예약이체명 | String |  | Y | 사용자가 지정한 예약 이름 |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| depositAccountNo | 입금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| transactionBalance | 이체 금액 | String |  | Y | 숫자 형식의 문자열 |
| reservationType | 예약 유형 | String |  | Y | 예: REPEAT |
| transferCycle | 이체 주기 | String |  | N | DAILY, WEEKLY, MONTHLY |
| nextTransferDate | 다음 이체일 | String | 8 | Y | YYYYMMDD |
| status | 예약 상태 | String |  | Y | ACTIVE, PAUSED, CANCELED, COMPLETED, FAILED |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| updatedAt | 수정 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "updateTransferReservation",

    "transmissionDate": "20260731",

    "transmissionTime": "111059",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "updateTransferReservation",

    "institutionTransactionUniqueNo": "20260731111059018986"

  },

  "REC": {

    "reservationId": "RSV4F8A1C2D3E5B67890",

    "reservationName": "매월 월세",

    "withdrawalAccountNo": "0019763592900582",

    "depositAccountNo": "0019763592900583",

    "transactionBalance": "550000",

    "reservationType": "REPEAT",

    "transferCycle": "MONTHLY",

    "nextTransferDate": "20260725",

    "status": "ACTIVE",

    "createdAt": "20260715162232",

    "updatedAt": "20260731111103"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4014 | 종료일이 시작일보다 이전 | 예약이체 수정 |
| E4015 | 이체 주기가 올바르지 않음 | 예약이체 수정 |
| E4016 | 이체일이 올바르지 않음 | 예약이체 수정 |
| E4017 | 예약이체 이름이 유효하지 않음 | 예약이체 수정 |
| E4019 | 예약이체를 찾을 수 없거나 수정 가능한 상태가 아님 | 예약이체 수정 |
| E4020 | 예약이체 소유자가 아님 | 예약이체 수정 |
| E4022 | 요청 필드 타입이 유효하지 않음 | 예약이체 수정 |

---

#### 2.16.6 예약이체 취소

##### 설명

예약이체 취소 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/cancelTransferReservation | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| reservationId | 예약이체 ID | String | 20 | Y | 취소할 예약이체 식별자 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "cancelTransferReservation",

    "transmissionDate": "20260731",

    "transmissionTime": "111124",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "cancelTransferReservation",

    "institutionTransactionUniqueNo": "20260731111124153639",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "reservationId": "RSV4F8A1C2D3E5B67890"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| reservationId | 예약이체 ID | String | 20 | Y | 예약이체 식별자 |
| reservationName | 예약이체명 | String |  | Y | 사용자가 지정한 예약 이름 |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| depositAccountNo | 입금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| transactionBalance | 이체 금액 | String |  | Y | 숫자 형식의 문자열 |
| reservationType | 예약 유형 | String |  | Y | 예: REPEAT |
| transferCycle | 이체 주기 | String |  | N | 예: MONTHLY |
| nextTransferDate | 다음 이체일 | String | 8 | Y | YYYYMMDD |
| status | 예약 상태 | String |  | Y | ACTIVE, PAUSED, CANCELED, COMPLETED, FAILED |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| updatedAt | 수정 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "cancelTransferReservation",

    "transmissionDate": "20260731",

    "transmissionTime": "111124",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "cancelTransferReservation",

    "institutionTransactionUniqueNo": "20260731111124153639"

  },

  "REC": {

    "reservationId": "RSV4F8A1C2D3E5B67890",

    "reservationName": "매월 월세",

    "withdrawalAccountNo": "0019763592900582",

    "depositAccountNo": "0019763592900583",

    "transactionBalance": "500000",

    "reservationType": "REPEAT",

    "transferCycle": "MONTHLY",

    "nextTransferDate": "20260725",

    "status": "CANCELED",

    "createdAt": "20260715162232",

    "updatedAt": "20260731111128"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4019 | 예약이체를 찾을 수 없거나 이미 완료됨 | 예약이체 취소 |
| E4020 | 예약이체 소유자가 아님 | 예약이체 취소 |
| E4022 | 요청 필드 타입이 유효하지 않음 | 예약이체 취소 |
| E4024 | 이미 취소된 예약이체 | 예약이체 취소 |

---

#### 2.16.7 예약이체 일시정지·재개

##### 설명

예약이체 일시정지·재개 기능

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/pauseTransferReservation | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | API 호출 공통 정보 |
| reservationId | 일시정지 또는 재개할 예약이체 ID | String | 20 | Y | 예: RSV4F8A1C2D3E5B67890 |
| action | 예약이체 상태 변경 동작 | String |  | Y | PAUSED, ACTIVE |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "pauseTransferReservation",

    "transmissionDate": "20260731",

    "transmissionTime": "111200",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "pauseTransferReservation",

    "institutionTransactionUniqueNo": "20260731111200674820",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "reservationId": "RSV4F8A1C2D3E5B67890",

  "action": "PAUSED"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | 처리 결과 및 요청 식별 정보 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| reservationId | 예약이체 ID | String | 20 | Y | 예약이체 식별자 |
| reservationName | 예약이체명 | String |  | Y | 사용자가 지정한 예약 이름 |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| depositAccountNo | 입금 계좌번호 | String | 16 | Y | 숫자 형식의 문자열 |
| transactionBalance | 이체 금액 | String |  | Y | 숫자 형식의 문자열 |
| reservationType | 예약 유형 | String |  | Y | 예: REPEAT |
| transferCycle | 이체 주기 | String |  | N | 예: MONTHLY |
| nextTransferDate | 다음 이체일 | String | 8 | Y | YYYYMMDD |
| status | 예약 상태 | String |  | Y | ACTIVE, PAUSED, CANCELED, COMPLETED, FAILED |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |
| updatedAt | 수정 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "pauseTransferReservation",

    "transmissionDate": "20260731",

    "transmissionTime": "111200",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "pauseTransferReservation",

    "institutionTransactionUniqueNo": "20260731111200674820"

  },

  "REC": {

    "reservationId": "RSV4F8A1C2D3E5B67890",

    "reservationName": "매월 월세",

    "withdrawalAccountNo": "0019763592900582",

    "depositAccountNo": "0019763592900583",

    "transactionBalance": "500000",

    "reservationType": "REPEAT",

    "transferCycle": "MONTHLY",

    "nextTransferDate": "20260725",

    "status": "PAUSED",

    "createdAt": "20260715162232",

    "updatedAt": "20260731111204"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4018 | 상태 변경 동작이 올바르지 않음 | 예약이체 일시정지·재개 |
| E4019 | 예약이체를 찾을 수 없거나 상태 변경 불가 | 예약이체 일시정지·재개 |
| E4020 | 예약이체 소유자가 아님 | 예약이체 일시정지·재개 |
| E4022 | 요청 필드 타입이 유효하지 않음 | 예약이체 일시정지·재개 |

---

