# 공통

- 출처: https://project.ssafy.com/docs/ssafy-finance/api-common
- 크롤링 날짜: 2026-08-24
- 범위: 화면에 표시된 정적 문서 본문만 추출했으며, 실제 API 호출·인증·데이터 변경은 수행하지 않았습니다.
- 요약: 공통 HEADER API, 은행코드 조회, 통화코드 조회의 요청·응답 구조와 오류코드를 정리합니다. 예시 API KEY와 USER KEY 값은 redacted 처리했습니다.

### 2.3 공통

#### 2.3.1 공통 HEADER API

##### 설명

API 요청 / 응답 시, BODY에 공통으로 사용하는 데이터입니다. BODY 안에 Header 라는 키로 들어가며, 공통부를 포함하여 API들의 요청, 응답값을 전송합니다.

##### 요청 메시지 명세

- 기관거래고유번호: 새로운 번호로 임의 채번 (YYYYMMDD + HHMMSS + 일련번호 6자리) 또는 20자리의 난수. API 요청 시 사용자가 항상 새로운 번호로 임의 채번해야 함. 예: 2024021609000000000, 2024021609000000001

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| apiName | API 이름 | String | 30 | Y | 호출 API URI의 마지막 path 명 |
| transmissionDate | 전송일자 | String | 8 | Y | API 전송일자 (YYYYMMDD) 요청일 |
| transmissionTime | 전송시각 | String | 6 | Y | API 전송시각 (HHMMSS), 요청시간 기준 ±5분 |
| institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| apiServiceCode | API 서비스코드 | String | 30 | Y | API 이름 필드와 동일 |
| institutionTransactionUniqueNo | 기관거래고유번호 | String | 20 | Y | 기관별 API 서비스 호출 단위의 고유 코드 |
| apiKey | API KEY | String | 40 | Y | 앱 관리자 (개발자)가 발급받은 API KEY |
| userKey | USER KEY | String | 40 | Y | 앱 사용자가 회원가입할 때 발급받은 USER KEY |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "drawingTransfer",
    "transmissionDate": "20240101",
    "transmissionTime": "121212",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "drawingTransfer",
    "institutionTransactionUniqueNo": "20240215121212123453",
    "apiKey": "<REDACTED_API_KEY>",
    "userKey": "<REDACTED_USER_KEY>"
  }
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| responseCode | 응답코드 | String |  | Y | H0000 |
| responseMessage | 응답메세지 | String |  | Y | 정상처리 되었습니다. |
| apiName | API 이름 | String | 30 | Y | 호출 API URI 뒷부분 |
| transmissionDate | 전송일자 | String | 8 | Y | API 전송일자 (YYYYMMDD) 요청일 |
| transmissionTime | 전송시각 | String | 6 | Y | API 전송시각 (HHMMSS), 요청시간 기준 ±5분 |
| institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| apiServiceCode | API 서비스코드 | String | 30 | Y | API 이름 필드와 동일 |
| institutionTransactionUniqueNo | 기관거래고유번호 | String | 20 | Y | 기관별 API 서비스 호출 단위의 고유 코드 |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "inqureBankCodes",
    "transmissionDate": "20240207",
    "transmissionTime": "133415",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "inqureBankCodes",
    "institutionTransactionUniqueNo": "20191129000000000001"
  }
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. | |
| H1001 | API 이름이 유효하지 않습니다. | |
| H1002 | 전송일자 형식이 유효하지 않습니다. | |
| H1003 | 전송시각 형식이 유효하지 않습니다. | |
| H1004 | 기관코드가 유효하지 않습니다. | |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. | |
| H1006 | API 서비스코드가 유효하지 않습니다. | |
| H1010 | 기관거래고유번호가 유효하지 않습니다. | |
| H1007 | 기관거래고유번호가 중복된 값입니다. | |
| H1008 | API_KEY가 유효하지 않습니다. | |
| H1009 | USER_KEY가 유효하지 않습니다. | |
| --- |  |  |

#### 2.3.2 은행코드 조회

##### 설명

수시입출금, 예금, 적금, 대출 상품 등록 시 필요한 은행코드를 조회하는 API 입니다. 은행코드를 조회하여 각 은행의 상품을 만들 수 있습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/inquireBankCodes | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | userKey 제외 |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "inquireBankCodes",
    "transmissionDate": "20240401",
    "transmissionTime": "135500",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "inquireBankCodes",
    "institutionTransactionUniqueNo": "20240215121212123557",
    "apiKey": "<REDACTED_API_KEY>"
  }
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 은행코드 리스트 | List |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행코드명 | String | 3 | Y |  |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "inquireBankCodes",
    "transmissionDate": "20240401",
    "transmissionTime": "135500",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "inquireBankCodes",
    "institutionTransactionUniqueNo": "20240215121212123557"
  },
  "REC": [
    { "bankCode": "001", "bankName": "한국은행" },
    { "bankCode": "002", "bankName": "산업은행" },
    { "bankCode": "003", "bankName": "기업은행" },
    { "bankCode": "004", "bankName": "국민은행" },
    { "bankCode": "011", "bankName": "농협은행" },
    { "bankCode": "020", "bankName": "우리은행" },
    { "bankCode": "023", "bankName": "SC제일은행" },
    { "bankCode": "027", "bankName": "시티은행" },
    { "bankCode": "032", "bankName": "대구은행" },
    { "bankCode": "034", "bankName": "광주은행" },
    { "bankCode": "035", "bankName": "제주은행" },
    { "bankCode": "037", "bankName": "전북은행" },
    { "bankCode": "039", "bankName": "경남은행" },
    { "bankCode": "045", "bankName": "새마을금고" },
    { "bankCode": "081", "bankName": "KEB하나은행" },
    { "bankCode": "088", "bankName": "신한은행" },
    { "bankCode": "090", "bankName": "카카오뱅크" },
    { "bankCode": "999", "bankName": "싸피은행" }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. | |
| H1001 | API 이름이 유효하지 않습니다. | |
| H1002 | 전송일자 형식이 유효하지 않습니다. | |
| H1003 | 전송시각 형식이 유효하지 않습니다. | |
| H1004 | 기관코드가 유효하지 않습니다. | |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. | |
| H1006 | API 서비스코드가 유효하지 않습니다. | |
| H1010 | 기관거래고유번호가 유효하지 않습니다. | |
| H1007 | 기관거래고유번호가 중복된 값입니다. | |
| H1008 | API KEY가 유효하지 않습니다. | |
| Q1000 | 그 이외에 에러 메시지 | |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. | |

#### 2.3.3 통화코드 조회

##### 설명

환율, 환전, 외화 수시입출금 상품 등록 시 필요한 통화 코드를 조회하는 API 입니다. 통화 코드를 조회하여 다양한 통화의 외화 상품을 만들 수 있습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/inquireBankCurrency | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | userKey 제외 |

##### 요청 메시지 형태

```json
{
  "Header": {
    "apiName": "inquireBankCurrency",
    "transmissionDate": "20240724",
    "transmissionTime": "154635",
    "institutionCode": "00100",
    "fintechAppNo": "001",
    "apiServiceCode": "inquireBankCurrency",
    "institutionTransactionUniqueNo": "20240724154635412480",
    "apiKey": "<REDACTED_API_KEY>"
  }
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 통화코드 리스트 | List |  | Y |  |
| currency | 통화코드 | String | 3 | Y |  |
| currencyName | 통화명 | String | 20 | Y |  |

##### 응답 메시지 형태

```json
{
  "Header": {
    "responseCode": "H0000",
    "responseMessage": "정상처리 되었습니다.",
    "apiName": "inquireBankCurrency",
    "transmissionDate": "20240724",
    "transmissionTime": "154635",
    "institutionCode": "00100",
    "apiKey": "<REDACTED_API_KEY>",
    "apiServiceCode": "inquireBankCurrency",
    "institutionTransactionUniqueNo": "20240724154635412480"
  },
  "REC": [
    { "currency": "KRW", "currencyName": "원화" },
    { "currency": "USD", "currencyName": "달러" },
    { "currency": "EUR", "currencyName": "유로" },
    { "currency": "JPY", "currencyName": "엔화" },
    { "currency": "CNY", "currencyName": "위안화" },
    { "currency": "GBP", "currencyName": "영국 파운드" },
    { "currency": "CHF", "currencyName": "스위스 프랑" },
    { "currency": "CAD", "currencyName": "캐나다 달러" }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. | |
| H1001 | API 이름이 유효하지 않습니다. | |
| H1002 | 전송일자 형식이 유효하지 않습니다. | |
| H1003 | 전송시각 형식이 유효하지 않습니다. | |
| H1004 | 기관코드가 유효하지 않습니다. | |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. | |
| H1006 | API 서비스코드가 유효하지 않습니다. | |
| H1010 | 기관거래고유번호가 유효하지 않습니다. | |
| H1007 | 기관거래고유번호가 중복된 값입니다. | |
| H1008 | API KEY가 유효하지 않습니다. | |
| Q1000 | 그 이외에 에러 메시지 | |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. | |
