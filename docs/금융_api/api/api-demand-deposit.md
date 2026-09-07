# 수시입출금 API

- 제목: 수시입출금
- 원문: https://project.ssafy.com/docs/ssafy-finance/api-demand-deposit
- 크롤링 날짜: 2026-08-24
- 범위: 정적 문서 복사만 수행했으며 라이브 API 호출은 하지 않음.
- 요약: 수시입출금 상품 등록·조회와 계좌 생성·조회·거래·한도 변경·해지 API의 요청, 응답, 에러코드를 정리한 문서입니다.

## 2.4 수시입출금

---

### 2.4.1 상품 등록

#### 설명

은행별 수시입출금 상품을 등록합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/createDemandDeposit | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | userKey 제외 |
| bankCode | 은행코드 | String | 3 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |

#### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "createDemandDeposit",

        "transmissionDate": "20240401",

        "transmissionTime": "095500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createDemandDeposit",

        "institutionTransactionUniqueNo": "20240215121212123560",

        "apiKey": "<REDACTED>" 

    },

    "bankCode": "001",

    "accountName": "한국은행 수시입출금 상품명",

    "accountDescription": "한국은행 수시입출금 상품설명"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 등록된 상품 정보 | List |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1: 수시입출금, 2: 정기예금, 3: 정기적금, 4: 대출 |
| accountTypeName | 상품구분명 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| accountType | 통화 | String | 255 | Y | DOMESTIC: 원화, OVERSEAS: 외화 |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "createDemandDeposit",

        "transmissionDate": "20240401",

        "transmissionTime": "095500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "createDemandDeposit",

        "institutionTransactionUniqueNo": "20240215121212123560"

    },

    "REC": {

        "accountTypeUniqueNo": "001-1-ffa4253081d540",

        "bankCode": "001",

        "bankName": "한국은행",

        "accountTypeCode": "1",

        "accountTypeName": "수시입출금",

        "accountName": "한국은행 수시입출금 상품명",

        "accountDescription": "한국은행 수시입출금 상품설명",

        "accountType": "DOMESTIC"

    }

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API KEY가 유효하지 않습니다. |  |
| A1001 | 은행코드가 유효하지 않습니다. |  |
| A1021 | 상품명이 유효하지 않습니다. |  |
| A1031 | 상품설명 길이가 초과되었습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |
| --- |  |  |

### 2.4.2 상품 조회

#### 설명

은행별 계좌 상품을 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositList | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | userKey 제외 |

#### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "inquireDemandDepositList",

        "transmissionDate": "20240401",

        "transmissionTime": "100100",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireDemandDepositList",

        "institutionTransactionUniqueNo": "20240215121212123561",

        "apiKey": "<REDACTED>"

    }

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 은행별 상품 리스트 | List |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1: 수시입출금, 2: 정기예금, 3: 정기적금, 4: 대출 |
| accountTypeName | 상품구분명 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| accountType | 통화 | String | 255 | Y | DOMESTIC: 원화, OVERSEAS: 외화 |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireDemandDepositList",

        "transmissionDate": "20240401",

        "transmissionTime": "100100",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireDemandDepositList",

        "institutionTransactionUniqueNo": "20240215121212123561"

    },

    "REC": [

        {

            "accountTypeUniqueNo": "001-1-ffa4253081d540",

            "bankCode": "001",

            "bankName": "한국은행",

            "accountTypeCode": "1",

            "accountTypeName": "수시입출금",

            "accountName": "한국은행 수시입출금 상품명",

            "accountDescription": "한국은행 수시입출금 상품설명",

            "accountType": "DOMESTIC"

        },

        {

            "accountTypeUniqueNo": "020-1-5f3eb083664848",

            "bankCode": "020",

            "bankName": "우리은행",

            "accountTypeCode": "1",

            "accountTypeName": "수시입출금",

            "accountName": "우리은행 수시입출금 상품명",

            "accountDescription": "우리은행 수시입출금 상품설명",

            "accountType": "DOMESTIC"

        },

        {

            "accountTypeUniqueNo": "032-1-72012237b27b4c",

            "bankCode": "032",

            "bankName": "대구은행",

            "accountTypeCode": "1",

            "accountTypeName": "수시입출금",

            "accountName": "대구은행 수시입출금 상품명",

            "accountDescription": "대구은행 수시입출금 상품설명",

            "accountType": "DOMESTIC"

        }

    ]

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API KEY가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.3 계좌 생성

#### 설명

계좌를 생성합니다. 상품을 조회한 사용자는 상품 고유번호를 통해 계좌를 생성할 수 있습니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/createDemandDepositAccount | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |

#### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "createDemandDepositAccount",

        "transmissionDate": "20240401",

        "transmissionTime": "100500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createDemandDepositAccount",

        "institutionTransactionUniqueNo": "20240215121212123457",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    },

    "accountTypeUniqueNo": "001-1-ffa4253081d540"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 계좌정보 | List |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| currency | 통화정보 | List |  | Y |  |
| currency | 통화코드 | String | 8 | Y |  |
| currencyName | 통화명 | String | 16 | Y |  |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "createDemandDepositAccount",

        "transmissionDate": "20240401",

        "transmissionTime": "100500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "createDemandDepositAccount",

        "institutionTransactionUniqueNo": "20240215121212123457"

    },

    "REC": {

        "bankCode": "001",

        "accountNo": "0016174648358792",

        "currency": {

            "currency": "KRW",

            "currencyName": "원화"

        }

    }

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API KEY가 유효하지 않습니다. |  |
| H1009 | USER KEY가 유효하지 않습니다. |  |
| A1019 | 없는 상품입니다. 은행별 상품 조회를 다시 확인해주세요. |  |
| A1023 | 상품 고유번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.4 계좌 목록 조회

#### 설명

사용자의 계좌 목록 전체를 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccountList | POST |

#### 요청 메시지 형태

```json
{

     "Header": {

        "apiName": "inquireDemandDepositAccountList",

        "transmissionDate": "20240401",

        "transmissionTime": "101000",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireDemandDepositAccountList",

        "institutionTransactionUniqueNo": "20240215121212123473",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    }

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 계좌목록 | List |  | N | 생성된 계좌가 없는 경우 응답 JSON에 존재하지 않음 |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| username | 예금주명 | String | 50 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1: 수시입출금, 2: 정기예금, 3: 정기적금, 4: 대출 |
| accountTypeName | 상품종류명 | String | 20 | Y |  |
| accountCreatedDate | 계좌개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌만기일 | String | 8 | Y |  |
| dailyTransferLimit | 1일이체한도 | Long |  | Y | default: 5억 |
| oneTimeTransferLimit | 1회이체한도 | Long |  | Y | default: 1억 |
| accountBalance | 계좌잔액 | Long |  | Y |  |
| lastTransactionDate | 최종거래일 | String | 8 | N |  |
| currency | 통화코드 | String | 8 | Y |  |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireDemandDepositAccountList",

        "transmissionDate": "20240401",

        "transmissionTime": "101000",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireDemandDepositAccountList",

        "institutionTransactionUniqueNo": "20240215121212123473"

    },

    "REC": [

        {

            "bankCode": "001",

            "bankName": "한국은행",

            "userName": "USER",

            "accountNo": "0016174648358792",

            "accountName": "한국은행 수시입출금 상품명",

            "accountTypeCode": "1",

            "accountTypeName": "수시입출금",

            "accountCreatedDate": "20240401",

            "accountExpiryDate": "20290401",

            "dailyTransferLimit": "100000000",

            "oneTimeTransferLimit": "20000000",

            "accountBalance": "0",

            "lastTransactionDate": "",

            "currency": "KRW"

        },

        {

            "bankCode": "020",

            "bankName": "우리은행",

            "userName": "USER",

            "accountNo": "0204667768182760",

            "accountName": "우리은행 수시입출금 상품명",

            "accountTypeCode": "1",

            "accountTypeName": "수시입출금",

            "accountCreatedDate": "20240320",

            "accountExpiryDate": "20290320",

            "dailyTransferLimit": "100000000",

            "oneTimeTransferLimit": "20000000",

            "accountBalance": "8003477",

            "lastTransactionDate": "20240323",

            "currency": "KRW"

        },

        {

            "bankCode": "020",

            "bankName": "우리은행",

            "userName": "USER",

            "accountNo": "0205782816344769",

            "accountName": "우리은행 수시입출금 상품명",

            "accountTypeCode": "1",

            "accountTypeName": "수시입출금",

            "accountCreatedDate": "20240320",

            "accountExpiryDate": "20290320",

            "dailyTransferLimit": "100000000",

            "oneTimeTransferLimit": "20000000",

            "accountBalance": "98516155",

            "lastTransactionDate": "20240325",

            "currency": "KRW"

        },

        {

            "bankCode": "032",

            "bankName": "대구은행",

            "userName": "USER",

            "accountNo": "0324003842129948",

            "accountName": "대구은행 수시입출금 상품명",

            "accountTypeCode": "1",

            "accountTypeName": "수시입출금",

            "accountCreatedDate": "20240320",

            "accountExpiryDate": "20290320",

            "dailyTransferLimit": "100000000",

            "oneTimeTransferLimit": "20000000",

            "accountBalance": "809008344",

            "lastTransactionDate": "20240329",

            "currency": "KRW"

        }

    ]

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.5 계좌 조회 (단건)

#### 설명

특정 계좌에 대한 정보를 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccount | POST |

#### 요청 메시지 형태

```json
{     

    "Header": {

        "apiName": "inquireDemandDepositAccount",

        "transmissionDate": "20240401",

        "transmissionTime": "101500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireDemandDepositAccount",

        "institutionTransactionUniqueNo": "20240215121212123455",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    }, 

    "accountNo": "0016174648358792"

}
```

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 계좌정보 | List |  | N |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| username | 예금주명 | String | 50 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1: 수시입출금, 2: 정기예금, 3: 정기적금, 4: 대출 |
| accountTypeName | 상품종류명 | String | 20 | Y |  |
| accountCreatedDate | 계좌개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌만기일 | String | 8 | Y |  |
| dailyTransferLimit | 1일이체한도 | Long |  | Y |  |
| oneTimeTransferLimit | 1회이체한도 | Long |  | Y |  |
| accountBalance | 계좌잔액 | Long |  | Y |  |
| lastTransactionDate | 최종거래일 | String | 8 | N |  |
| currency | 통화코드 | String | 8 | Y |  |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireDemandDepositAccount",

        "transmissionDate": "20240401",

        "transmissionTime": "101500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireDemandDepositAccount",

        "institutionTransactionUniqueNo": "20240215121212123455"

    },

    "REC": {

        "bankCode": "001",

        "bankName": "한국은행",

        "userName": "USER",

        "accountNo": "0016174648358792",

        "accountName": "한국은행 수시입출금 상품명",

        "accountTypeCode": "1",

        "accountTypeName": "수시입출금",

        "accountCreatedDate": "20240401",

        "accountExpiryDate": "20290401",

        "dailyTransferLimit": "100000000",

        "oneTimeTransferLimit": "20000000",

        "accountBalance": "0",

        "lastTransactionDate": "",

        "currency": "KRW"

    }

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A5004 | 원화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.6 예금주 조회

#### 설명

계좌에 대한 예금주명을 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccountHolderName | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y | 외화 계좌 가능 |

#### 요청 메시지 형태

```json
{

   "Header": {

        "apiName": "inquireDemandDepositAccountHolderName",

        "transmissionDate": "20240401",

        "transmissionTime": "102000",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireDemandDepositAccountHolderName",

        "institutionTransactionUniqueNo": "20240215121212123451",

         "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    },

    "accountNo": "0016174648358792"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 계좌정보 | List |  | N |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| userName | 예금주명 | String | 50 | Y |  |
| currency | 통화코드 | String | 8 | Y |  |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireDemandDepositAccountHolderName",

        "transmissionDate": "20240401",

        "transmissionTime": "102000",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireDemandDepositAccountHolderName",

        "institutionTransactionUniqueNo": "20240215121212123451"

    },

    "REC": {

        "bankCode": "001",

        "bankName": "한국은행",

        "accountNo": "0016174648358792",

        "userName": "USER",

        "currency": "KRW"

    }

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.7 계좌 잔액 조회

#### 설명

특정 계좌의 잔액을 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccountBalance | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 요청 메시지 형태

```json
{

   "Header": {

        "apiName": "inquireDemandDepositAccountBalance",

        "transmissionDate": "20240401",

        "transmissionTime": "102500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireDemandDepositAccountBalance",

        "institutionTransactionUniqueNo": "20240215121212123463",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    },

    "accountNo": "0016174648358792"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 계좌정보 | List |  | N |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountBalance | 계좌잔액 | Long |  | Y |  |
| accountCreatedDate | 계좌개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌만기일 | String | 8 | Y |  |
| lastTransactionDate | 최종거래일 | String | 8 | N |  |
| currency | 통화코드 | String | 8 | Y |  |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireDemandDepositAccountBalance",

        "transmissionDate": "20240401",

        "transmissionTime": "102500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireDemandDepositAccountBalance",

        "institutionTransactionUniqueNo": "20240215121212123463"

    },

    "REC": {

        "bankCode": "001",

        "accountNo": "0016174648358792",

        "accountBalance": "0",

        "accountCreatedDate": "20240401",

        "accountExpiryDate": "20290401",

        "lastTransactionDate": "",

        "currency": "KRW"

    }

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A5004 | 원화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.8 계좌 출금

#### 설명

이용기관이 사용자의 계좌로부터 대금을 출금합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/updateDemandDepositAccountWithdrawal | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| transactionBalance | 출금금액 | Long |  | Y |  |
| transactionSummary | 출금계좌요약 | String | 255 | N |  |

#### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "updateDemandDepositAccountWithdrawal",

        "transmissionDate": "20240401",

        "transmissionTime": "102500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "updateDemandDepositAccountWithdrawal",

        "institutionTransactionUniqueNo": "20240215121212123456",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    },

    "accountNo": "0016174648358792",

    "transactionBalance": "100000",

    "transactionSummary": "(수시입출금) : 출금"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 거래 정보 | List |  | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| transactionDate | 거래일자 | String | 8 | Y |  |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "updateDemandDepositAccountWithdrawal",

        "transmissionDate": "20240401",

        "transmissionTime": "102500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "updateDemandDepositAccountWithdrawal",

        "institutionTransactionUniqueNo": "20240215121212123456"

    },

    "REC": {

        "transactionUniqueNo": "60",

        "transactionDate": "20240401"

    }

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1011 | 거래금액이 유효하지 않습니다. |  |
| A1014 | 계좌 잔액이 부족하여 거래가 실패했습니다. | 출금 시 계좌의 잔액이 부족하여 발생 |
| A1016 | 이체 가능 한도 초과(1회) | 1회 이체 가능한 금액을 초과 |
| A1017 | 이체 가능 한도 초과(1일) | 1일 이체 가능한 금액을 초과 |
| A1018 | 거래요약내용 길이가 초과되었습니다. |  |
| A5004 | 원화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.9 계좌 입금

#### 설명

이용기관이 사용자의 계좌로부터 대금을 입금합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/updateDemandDepositAccountDeposit | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| transactionBalance | 입금금액 | Long |  | Y |  |
| transactionSummary | 입금계좌요약 | String | 255 | N |  |

#### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "updateDemandDepositAccountDeposit",

        "transmissionDate": "20240401",

        "transmissionTime": "102500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "updateDemandDepositAccountDeposit",

        "institutionTransactionUniqueNo": "20240215121212123463",

         "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    },

    "accountNo": "0016174648358792",

    "transactionBalance": "100000000",

    "transactionSummary": "(수시입출금) : 입금"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 거래 정보 | List |  | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| transactionDate | 거래일자 | String | 8 | Y |  |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "updateDemandDepositAccountDeposit",

        "transmissionDate": "20240401",

        "transmissionTime": "102500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "updateDemandDepositAccountDeposit",

        "institutionTransactionUniqueNo": "20240215121212123463"

    },

    "REC": {

        "transactionUniqueNo": "59",

        "transactionDate": "20240401"

    }

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1011 | 거래금액이 유효하지 않습니다. |  |
| A1018 | 거래요약내용 길이가 초과되었습니다. |  |
| A5004 | 원화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.10 계좌 이체

#### 설명

한 계좌로부터 다른 계좌로 대금을 이체합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/updateDemandDepositAccountTransfer | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| depositAccountNo | 입금계좌번호 | String | 16 | Y | 원화, 외화 계좌 가능 |
| transactionBalance | 거래금액 | Long |  | Y | 출금할 금액 입력 |
| withdrawalAccountNo | 출금계좌번호 | String | 16 | Y | 원화 계좌만 가능 |
| depositTransactionSummary | 거래 요약내용 (입금계좌) | String | 255 | N |  |
| withdrawalTransactionSummary | 거래 요약내용 (출금계좌) | String | 255 | N |  |

#### 요청 메시지 형태

```json
{

     "Header": {

        "apiName": "updateDemandDepositAccountTransfer",

        "transmissionDate": "20240401",

        "transmissionTime": "103500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "updateDemandDepositAccountTransfer",

        "institutionTransactionUniqueNo": "20240215121212123453",

         "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    }, 

    "depositAccountNo": "0204667768182760",

    "depositTransactionSummary": "(수시입출금) : 입금(이체)",

    "transactionBalance": "10000000", 

    "withdrawalAccountNo": "0016174648358792", 

    "withdrawalTransactionSummary": "(수시입출금) : 출금(이체)"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 거래목록 | List |  | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |
| transactionType | 거래유형 | String | 1 | Y | 1, 2 ... |
| transactionTypeName | 거래유형명 | String | 8 | Y | 입금이체, 출금이체 ... |
| transactionAccountNo | 거래 계좌번호 | String | 16 | Y | 이체 거래에 대한 계좌번호 |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "updateDemandDepositAccountTransfer",

        "transmissionDate": "20240401",

        "transmissionTime": "103500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "updateDemandDepositAccountTransfer",

        "institutionTransactionUniqueNo": "20240215121212123453"

    },

    "REC": [

        {

            "transactionUniqueNo": "61",

            "accountNo": "0016174648358792",

            "transactionDate": "20240401",

            "transactionType": "2",

            "transactionTypeName": "출금(이체)",

            "transactionAccountNo": "0204667768182760"

        },

        {

            "transactionUniqueNo": "62",

            "accountNo": "0204667768182760",

            "transactionDate": "20240401",

            "transactionType": "1",

            "transactionTypeName": "입금(이체)",

            "transactionAccountNo": "0016174648358792"

        }

    ]

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1011 | 거래금액이 유효하지 않습니다. |  |
| A1014 | 계좌 잔액이 부족하여 거래가 실패했습니다. | 출금 시 계좌의 잔액이 부족하여 발생 |
| A1016 | 이체 가능 한도 초과(1회) | 1회 이체 가능한 금액을 초과 |
| A1017 | 이체 가능 한도 초과(1일) | 1일 이체 가능한 금액을 초과 |
| A1018 | 거래요약내용 길이가 초과되었습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.11 계좌 이체 한도 변경

#### 설명

계좌에 대한 이체한도를 변경합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/updateTransferLimit | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| oneTimeTransferLimit | 1회 이체한도 | Long |  | Y | 1원 ~ 100억 |
| dailyTransferLimit | 1일 이체한도 | Long |  | Y | 1원 ~ 2000억 |

#### 요청 메시지 형태

```json
{

     "Header": {

        "apiName": "updateTransferLimit",

        "transmissionDate": "20240401",

        "transmissionTime": "104000",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "updateTransferLimit",

        "institutionTransactionUniqueNo": "20240215121212123452",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    }, 

    "accountNo": "0016174648358792", 

    "oneTimeTransferLimit": "20000000", 

    "dailyTransferLimit": "100000000"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 변경 계좌 정보 | List |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| userName | 예금주명 | String | 50 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1: 수시입출금, 2: 정기예금, 3: 정기적금, 4: 대출 |
| accountTypeName | 상품종류명 | String | 20 | Y |  |
| accountCreatedDate | 계좌개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌만기일 | String | 8 | Y |  |
| dailyTransferLimit | 1일 이체한도 | Long |  | Y |  |
| oneTimeTransferLimit | 1회 이체한도 | Long |  | Y |  |
| accountBalance | 계좌잔액 | Long |  | Y |  |
| lastTransactionDate | 최종거래일 | String | 8 | N |  |
| currency | 통화코드 | String |  | Y |  |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "updateTransferLimit",

        "transmissionDate": "20240401",

        "transmissionTime": "104000",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "updateTransferLimit",

        "institutionTransactionUniqueNo": "20240215121212123452"

    },

    "REC": {

        "bankCode": "001",

        "bankName": "한국은행",

        "userName": "USER",

        "accountNo": "0016174648358792",

        "accountName": "한국은행 수시입출금 상품명",

        "accountTypeCode": "1",

        "accountTypeName": "수시입출금",

        "accountCreatedDate": "20240401",

        "accountExpiryDate": "20290401",

        "dailyTransferLimit": "100000000",

        "oneTimeTransferLimit": "20000000",

        "accountBalance": "89900000",

        "lastTransactionDate": "20240401",

        "currency": "KRW"

    }

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1024 | 1회 이체한도가 유효하지 않습니다. |  |
| A1025 | 1일 이체한도가 유효하지 않습니다. |  |
| A1066 | 1회 이체한도는 1원 ~ 200억으로만 입력 가능합니다. |  |
| A1067 | 1일 이체한도는 1원 ~ 1000억으로만 입력 가능합니다. |  |
| A5004 | 원화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.12 계좌 거래 내역 조회

#### 설명

계좌 거래 내역 목록을 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireTransactionHistoryList | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| startDate | 조회시작일자 | String | 8 | Y | YYYYMMDD |
| endDate | 조회종료일자 | String | 8 | Y | YYYYMMDD |
| transactionType | 거래구분 | String | 1 | Y | M:입금 D:출금 A: 전체 |
| orderByType | 정렬순서 | String | 4 | N | 거래고유번호 기준 ASC:오름차순, DESC:내림차순 |

#### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "inquireTransactionHistoryList",

        "transmissionDate": "20240401",

        "transmissionTime": "105000",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireTransactionHistoryList",

        "institutionTransactionUniqueNo": "20240215121212123459",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    },

    "accountNo": "0016174648358792",

    "startDate": "20240101",

    "endDate": "20241231",

    "transactionType": "A",

    "orderByType": "ASC"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 거래내역 | List |  | N |  |
| totalCount | 조회총건수 | String |  | N |  |
| list | 거래목록 | List |  | N |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| transactionDate | 거래일자 | String | 8 | Y |  |
| transactionTime | 거래시각 | String | 6 | Y |  |
| transactionType | 입금출금구분 | String | 1 | Y | 1, 2 |
| transactionTypeName | 입금출금구분명 | String | 10 | Y | 입금, 출금, 입금(이체), 출금(이체) |
| transactionAccountNo | 거래계좌번호 | String | 16 | N |  |
| transactionBalance | 거래금액 | Long |  | Y |  |
| transactionAfterBalance | 거래후잔액 | Long |  | Y |  |
| transactionSummary | 거래 요약내용 | String | 255 | N |  |
| transactionMemo | 거래 메모 | String | 255 | N |  |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireTransactionHistoryList",

        "transmissionDate": "20240401",

        "transmissionTime": "105000",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireTransactionHistoryList",

        "institutionTransactionUniqueNo": "20240215121212123459"

    },

    "REC": {

        "totalCount": "3",

        "list": [

            {

                "transactionUniqueNo": "59",

                "transactionDate": "20240401",

                "transactionTime": "102447",

                "transactionType": "1",

                "transactionTypeName": "입금",

                "transactionAccountNo": "",

                "transactionBalance": "100000000",

                "transactionAfterBalance": "100000000",

                "transactionSummary": "(수시입출금) : 입금",

                "transactionMemo": ""

            },

            {

                "transactionUniqueNo": "60",

                "transactionDate": "20240401",

                "transactionTime": "102452",

                "transactionType": "2",

                "transactionTypeName": "출금",

                "transactionAccountNo": "",

                "transactionBalance": "100000",

                "transactionAfterBalance": "99900000",

                "transactionSummary": "(수시입출금) : 출금",

                "transactionMemo": ""

            },

            {

                "transactionUniqueNo": "61",

                "transactionDate": "20240401",

                "transactionTime": "103229",

                "transactionType": "2",

                "transactionTypeName": "출금(이체)",

                "transactionAccountNo": "0204667768182760",

                "transactionBalance": "10000000",

                "transactionAfterBalance": "89900000",

                "transactionSummary": "(수시입출금) : 출금(이체)",

                "transactionMemo": ""

            }

        ]

    }

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1004 | 조회 시작일자가 유효하지 않습니다. |  |
| A1005 | 조회 종료일자가 유효하지 않습니다. |  |
| A1006 | 거래 구분이 유효하지 않습니다. |  |
| A1007 | 정렬 순서가 유효하지 않습니다. |  |
| A5004 | 원화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.13 계좌 거래 내역 조회 (단건)

#### 설명

계좌 거래 내역 (단건)을 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireTransactionHistory | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |

#### 요청 메시지 형태

```json
{

   "Header": {

        "apiName": "inquireTransactionHistory",

        "transmissionDate": "20240401",

        "transmissionTime": "105500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireTransactionHistory",

        "institutionTransactionUniqueNo": "20240215121212123452",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"    

    },

    "accountNo": "0016174648358792",

    "transactionUniqueNo": "61"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 거래내역 | List |  | N |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| transactionDate | 거래일자 | String | 8 | Y |  |
| transactionTime | 거래시각 | String | 6 | Y |  |
| transactionType | 입금출금구분 | String | 1 | Y | 1, 2 |
| transactionTypeName | 입금출금구분명 | String | 10 | Y | 입금, 출금, 입금(이체), 출금(이체) |
| transactionAccountNo | 거래계좌번호 | String | 16 | N |  |
| transactionBalance | 거래금액 | Long |  | Y |  |
| transactionAfterBalance | 거래후잔액 | Long |  | Y |  |
| transactionSummary | 거래 요약내용 | String | 255 | N |  |
| transactionMemo | 거래 메모 | String | 255 | N |  |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireTransactionHistory",

        "transmissionDate": "20240401",

        "transmissionTime": "105500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireTransactionHistory",

        "institutionTransactionUniqueNo": "20240215121212123452"

    },

    "REC": {

        "transactionUniqueNo": "61",

        "transactionDate": "20240401",

        "transactionTime": "103229",

        "transactionType": "2",

        "transactionTypeName": "출금(이체)",

        "transactionAccountNo": "0204667768182760",

        "transactionBalance": "10000000",

        "transactionAfterBalance": "89900000",

        "transactionSummary": "(수시입출금) : 출금(이체)",

        "transactionMemo": ""

    }

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1010 | 거래고유번호가 유효하지 않습니다. |  |
| A5004 | 원화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.4.14 계좌 해지

#### 설명

계좌를 해지합니다. 예·적금, 대출, 카드의 연결계좌인 경우 해지가 불가능합니다.
잔액이 0원인 계좌는 금액 반환 계좌번호를 작성하지 않아도 정상 해지됩니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/deleteDemandDepositAccount | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| refundAccountNo | 금액 반환 계좌번호 | String | 16 | N | 해지 계좌번호의 잔액이 0일 시 생략 가능 |

#### 요청 메시지 형태

```json
{

   "Header": {

        "apiName": "deleteDemandDepositAccount",

        "transmissionDate": "20240401",

        "transmissionTime": "112000",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "deleteDemandDepositAccount",

        "institutionTransactionUniqueNo": "20240215121212123455",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"    

    },

    "accountNo": "0018770964252220",

    "refundAccountNo": "0324003842129948"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 해지 계좌정보 | List |  | Y |  |
| status | 상태 | String | 20 | Y |  |
| accountNo | 해지 계좌번호 | String | 16 | Y |  |
| refundAccountNo | 금액 반환 계좌번호 | String | 16 | Y |  |
| accountBalance | 계좌 해지 잔액 | Long |  | Y |  |

#### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "deleteDemandDepositAccount",

        "transmissionDate": "20240401",

        "transmissionTime": "112000",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "deleteDemandDepositAccount",

        "institutionTransactionUniqueNo": "20240215121212123455"

    },

    "REC": {

        "status": "CLOSED",

        "accountNo": "0018770964252220",

        "refundAccountNo": "0324003842129948",

        "accountBalance": "0"

    }

}
```

#### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API 이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API 서비스코드가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1068 | 예·적금 계좌에서 연결계좌로 사용 중인 계좌는 삭제가 불가합니다. |  |
| A1069 | 카드 계좌에서 연결계좌로 사용 중인 계좌는 삭제가 불가합니다. |  |
| A1070 | 대출 계좌에서 출금계좌로 사용 중인 계좌는 삭제가 불가합니다. |  |
| A1095 | 같은 통화 계좌만 이체가 가능합니다. |  |
| A5004 | 원화 계좌만 가능합니다. |  |
| A1010 | 거래고유번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

