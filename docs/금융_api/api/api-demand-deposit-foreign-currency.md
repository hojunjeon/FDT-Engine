# 외화 수시입출금

- Source URL: https://project.ssafy.com/docs/ssafy-finance/api-demand-deposit-foreign-currency
- Crawl date: 2026-08-24
- Scope: Static rendered documentation only; no live API calls, authentication, or data mutation.
- Verification: VERIFIED — final article DOM loaded in the in-app browser.
- Summary: Fourteen POST endpoints cover foreign-currency product registration and lookup, account creation/list/detail/holder/balance operations, withdrawals, deposits, transfers, transfer-limit changes, transaction-history list/detail lookup, and account closure.

## Rendered article
# 외화 수시입출금

### 2.12 외화 수시입출금

---

#### 2.12.1 외화 상품 등록

##### 설명

은행별 **외화 수시입출금 상품을 등록**합니다.
 📌 **외화 수시입출금 상품 조회 API를 통해 샘플 데이터를 참고하여 상품을 등록할 수 있습니다.**

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/createForeignCurrencyDemandDeposit | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |
| bankCode | 은행코드 | String | 3 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "createForeignCurrencyDemandDeposit",
        "transmissionDate": "20240401",
        "transmissionTime": "095500",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "createForeignCurrencyDemandDeposit",
        "institutionTransactionUniqueNo": "20240215121212123560",
        "apiKey": "[REDACTED]"
    },
    "bankCode": "001",
    "accountName": "한국은행 외화 수시입출금 상품명",
    "accountDescription": "한국은행 외화 수시입출금 상품설명"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 등록된 상품 정보 | List |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1 : 수시입출금, 2: 정기예금, 3 : 정기적금, 4: 대출 |
| accountTypeName | 상품구분명 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| accountType | 통화 | String | 255 | Y | **DOMESTIC**: 원화, **OVERSEAS**: 외화 |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "createForeignCurrencyDemandDeposit",
        "transmissionDate": "20240401",
        "transmissionTime": "095500",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "createForeignCurrencyDemandDeposit",
        "institutionTransactionUniqueNo": "20240215121212123560"
    },
    "REC": {
        "accountTypeUniqueNo": "001-1-ffa4253081d540",
        "bankCode": "001",
        "bankName": "한국은행",
        "accountTypeCode": "1",
        "accountTypeName": "수시입출금",
        "accountName": "한국은행 외화 수시입출금 상품명",
        "accountDescription": "한국은행 외화 수시입출금 상품설명",
        "accountType": "OVERSEAS"
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
| A1021 | 상품명이 유효하지 않습니다. |  |
| A1031 | 상품설명 길이가 초과되었습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.12.2 외화 상품 조회

##### 설명

은행별 **외화 계좌 상품을 조회**합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyDemandDepositList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "inquireForeignCurrencyDemandDepositList",
        "transmissionDate": "20240401",
        "transmissionTime": "100100",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "inquireForeignCurrencyDemandDepositList",
        "institutionTransactionUniqueNo": "20240215121212123561",
        "apiKey": "[REDACTED]"
    }
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 은행별 상품 리스트 | List |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1 : 수시입출금, 2: 정기예금, 3 : 정기적금, 4: 대출 |
| accountTypeName | 상품구분명 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| accountType | 통화 | String | 255 | Y | **DOMESTIC**: 원화, **OVERSEAS**: 외화 |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "inquireForeignCurrencyDemandDepositList",
        "transmissionDate": "20240401",
        "transmissionTime": "100100",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "inquireForeignCurrencyDemandDepositList",
        "institutionTransactionUniqueNo": "20240215121212123561"
    },
    "REC": [
        {
            "accountTypeUniqueNo": "001-1-ffa4253081d540",
            "bankCode": "001",
            "bankName": "한국은행",
            "accountTypeCode": "1",
            "accountTypeName": "수시입출금",
            "accountName": "한국은행 외화 수시입출금",
            "accountDescription": "외화 거래 가능한 수시입출금 상품",
            "accountType": "OVERSEAS"
        },
        {
            "accountTypeUniqueNo": "020-1-5f3eb083664848",
            "bankCode": "020",
            "bankName": "우리은행",
            "accountTypeCode": "1",
            "accountTypeName": "수시입출금",
            "accountName": "우리은행 외화 수시입출금 상품",
            "accountDescription": "우리은행 외화 수시입출금 상품",
            "accountType": "OVERSEAS"
        },
        {
            "accountTypeUniqueNo": "032-1-72012237b27b4c",
            "bankCode": "032",
            "bankName": "대구은행",
            "accountTypeCode": "1",
            "accountTypeName": "수시입출금",
            "accountName": "대구은행 외화거래 수시입출금 통장",
            "accountDescription": "외화 수시입출금 통장",
            "accountType": "OVERSEAS"
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

#### 2.12.3 외화 계좌 생성

##### 설명

**계좌를 생성합니다.**
 상품을 조회한 사용자는 **상품 고유번호를 통해 계좌를 생성**할 수 있습니다.

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
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/createForeignCurrencyDemandDepositAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| currency | 통화코드 | String | 20 | Y |  |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "createForeignCurrencyDemandDepositAccount",
        "transmissionDate": "20240401",
        "transmissionTime": "100500",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "createForeignCurrencyDemandDepositAccount",
        "institutionTransactionUniqueNo": "20240215121212123457",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    },
    "accountTypeUniqueNo": "001-1-ffa4253081d540",
    "currency": "USD"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 계좌정보 | List |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| currency | 통화 정보 | List |  | Y |  |
| currency | 통화코드 | String | 8 | Y |  |
| currencyName | 통화명 | String | 16 | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "createForeignCurrencyDemandDepositAccount",
        "transmissionDate": "20240401",
        "transmissionTime": "100500",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "createForeignCurrencyDemandDepositAccount",
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1019 | 없는 상품입니다. 은행별 상품 조회를 다시 확인해주세요. |  |
| A1023 | 상품고유번호가 유효하지 않습니다. |  |
| A5003 | 통화 코드가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.12.4 외화 계좌 목록 조회

##### 설명

사용자의 **외화 계좌 목록 전체를 조회**합니다.
 📌 **계좌번호 미입력 시, 소유한 전체 외화 계좌를 조회합니다.**

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyDemandDepositAccountList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| currency | 통화코드 | List |  | N | 미입력 시 소유한 전체 외화 계좌 조회 |

##### 요청 메시지 형태

```json
{
     "Header": {
        "apiName": "inquireForeignCurrencyDemandDepositAccountList",
        "transmissionDate": "20240401",
        "transmissionTime": "101000",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "inquireForeignCurrencyDemandDepositAccountList",
        "institutionTransactionUniqueNo": "20240215121212123473",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    },
    "currency": ["USD", "JPY"]
}
```

##### 응답 메시지 명세

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
| dailyTransferLimit | 1일이체한도 | Double |  | Y | USD:300000, EUR:300000, JPY:50000000, CNY:2000000, GBP:200000, CHF:300000, CAD:400000 |
| oneTimeTransferLimit | 1회이체한도 | Double |  | Y | USD:70000, EUR:60000, JPY:10000000, CNY:500000, GBP:50000, CHF:60000, CAD:90000 |
| accountBalance | 계좌잔액 | Double |  | Y | 소수점 둘째 자리까지 조회 (절삭) |
| lastTransactionDate | 최종거래일 | String | 8 | N |  |
| currency | 통화코드 | String | 8 | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "inquireForeignCurrencyDemandDepositAccountList",
        "transmissionDate": "20240401",
        "transmissionTime": "101000",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "inquireForeignCurrencyDemandDepositAccountList",
        "institutionTransactionUniqueNo": "20240215121212123473"
    },
    "REC": [
        {
            "bankCode": "001",
            "bankName": "한국은행",
            "userName": "USER",
            "accountNo": "0016174648358792",
            "accountName": "한국은행 달러 입출금 통장",
            "accountTypeCode": "1",
            "accountTypeName": "수시입출금",
            "accountCreatedDate": "20240401",
            "accountExpiryDate": "20290401",
            "dailyTransferLimit": "100000000",
            "oneTimeTransferLimit": "20000000",
            "accountBalance": "0",
            "lastTransactionDate": "",
            "currency": "USD"
        },
        {
            "bankCode": "020",
            "bankName": "우리은행",
            "userName": "USER",
            "accountNo": "0204667768182760",
            "accountName": "우리은행 외화 거래 상품",
            "accountTypeCode": "1",
            "accountTypeName": "수시입출금",
            "accountCreatedDate": "20240320",
            "accountExpiryDate": "20290320",
            "dailyTransferLimit": "100000000",
            "oneTimeTransferLimit": "20000000",
            "accountBalance": "8003477",
            "lastTransactionDate": "20240323",
            "currency": "USD"
        },
        {
            "bankCode": "020",
            "bankName": "우리은행",
            "userName": "USER",
            "accountNo": "0205782816344769",
            "accountName": "우리 일본여행가자 수시입출금 통장",
            "accountTypeCode": "1",
            "accountTypeName": "수시입출금",
            "accountCreatedDate": "20240320",
            "accountExpiryDate": "20290320",
            "dailyTransferLimit": "100000000",
            "oneTimeTransferLimit": "20000000",
            "accountBalance": "98516155",
            "lastTransactionDate": "20240325",
            "currency": "JPY"
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A5001 | 통화코드가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.12.5 외화 계좌 조회 (단건)

##### 설명

특정 **외화 계좌에 대한 정보를 조회**합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyDemandDepositAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

##### 요청 메시지 형태

```json
{
     "Header": {
        "apiName": "inquireForeignCurrencyDemandDepositAccount",
        "transmissionDate": "20240401",
        "transmissionTime": "101500",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "inquireForeignCurrencyDemandDepositAccount",
        "institutionTransactionUniqueNo": "20240215121212123455",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    }, 
    "accountNo": "0016174648358792"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 계좌정보 | List |  | N |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| username | 예금주명 | String | 50 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1 : 수시입출금, 2: 정기예금, 3 : 정기적금, 4: 대출 |
| accountTypeName | 상품종류명 | String | 20 | Y |  |
| accountCreatedDate | 계좌개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌만기일 | String | 8 | Y |  |
| dailyTransferLimit | 1일이체한도 | Double |  | Y |  |
| oneTimeTransferLimit | 1회이체한도 | Double |  | Y |  |
| accountBalance | 계좌잔액 | Double |  | Y | 소수점 둘째 자리까지 조회(절삭) |
| lastTransactionDate | 최종거래일 | String | 8 | N |  |
| currency | 통화코드 | String | 8 | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "inquireForeignCurrencyDemandDepositAccount",
        "transmissionDate": "20240401",
        "transmissionTime": "101500",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "inquireForeignCurrencyDemandDepositAccount",
        "institutionTransactionUniqueNo": "20240215121212123455"
    },
    "REC": {
        "bankCode": "001",
        "bankName": "한국은행",
        "userName": "USER",
        "accountNo": "0016174648358792",
        "accountName": "한국은행 달러 입출금 통장",
        "accountTypeCode": "1",
        "accountTypeName": "수시입출금",
        "accountCreatedDate": "20240401",
        "accountExpiryDate": "20290401",
        "dailyTransferLimit": "100000000",
        "oneTimeTransferLimit": "20000000",
        "accountBalance": "0",
        "lastTransactionDate": "",
        "currency": "USD"
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A5005 | 외화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.12.6 외화 예금주 조회

##### 설명

특정 **외화 계좌의 예금주명을 조회**합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyDemandDepositAccountHolderName | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y | 원화 계좌 가능 |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "inquireForeignCurrencyDemandDepositAccountHolderName",
        "transmissionDate": "20240401",
        "transmissionTime": "102000",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "inquireForeignCurrencyDemandDepositAccountHolderName",
        "institutionTransactionUniqueNo": "20240215121212123451",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    },
    "accountNo": "0016174648358792"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 계좌정보 | List |  | N |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| userName | 예금주명 | String | 50 | Y |  |
| currency | 통화코드 | String | 8 | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "inquireForeignCurrencyDemandDepositAccountHolderName",
        "transmissionDate": "20240401",
        "transmissionTime": "102000",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "inquireForeignCurrencyDemandDepositAccountHolderName",
        "institutionTransactionUniqueNo": "20240215121212123451"
    },
    "REC": {
        "bankCode": "001",
        "bankName": "한국은행",
        "accountNo": "0016174648358792",
        "userName": "USER",
        "currency": "USD"
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.12.7 외화 계좌 잔액 조회

##### 설명

특정 **외화 계좌의 잔액을 조회**합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyDemandDepositAccountBalance | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "inquireForeignCurrencyDemandDepositAccountBalance",
        "transmissionDate": "20240401",
        "transmissionTime": "102500",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "inquireForeignCurrencyDemandDepositAccountBalance",
        "institutionTransactionUniqueNo": "20240215121212123463",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    },
    "accountNo": "0016174648358792"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 계좌정보 | List |  | N |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountBalance | 계좌잔액 | Double |  | Y | 소수점 둘째자리까지 조회(절삭) |
| accountCreatedDate | 계좌개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌만기일 | String | 8 | Y |  |
| lastTransactionDate | 최종거래일 | String | 8 | N |  |
| currency | 통화코드 | String | 8 | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "inquireForeignCurrencyDemandDepositAccountBalance",
        "transmissionDate": "20240401",
        "transmissionTime": "102500",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "inquireForeignCurrencyDemandDepositAccountBalance",
        "institutionTransactionUniqueNo": "20240215121212123463"
    },
    "REC": {
        "bankCode": "001",
        "accountNo": "0016174648358792",
        "accountBalance": "125235.25",
        "accountCreatedDate": "20240401",
        "accountExpiryDate": "20290401",
        "lastTransactionDate": "20240424",
        "currency": "USD"
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A5005 | 외화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.12.8 외화 계좌 출금

##### 설명

이용기관이 **사용자의 외화 계좌로부터 대금을 출금**합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/updateForeignCurrencyDemandDepositAccountWithdrawal | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| transactionBalance | 출금금액 | Double |  | Y | 소수점 둘째자리까지 가능 (엔화의 경우 정수 입력) |
| transactionSummary | 출금계좌요약 | String | 255 | N |  |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "updateForeignCurrencyDemandDepositAccountWithdrawal",
        "transmissionDate": "20240401",
        "transmissionTime": "102500",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "updateForeignCurrencyDemandDepositAccountWithdrawal",
        "institutionTransactionUniqueNo": "20240215121212123456",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    },
    "accountNo": "0016174648358792",
    "transactionBalance": "100000",
    "transactionSummary": "(수시입출금) : 출금"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 거래 정보 | List |  | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "updateForeignCurrencyDemandDepositAccountWithdrawal",
        "transmissionDate": "20240401",
        "transmissionTime": "102500",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "updateForeignCurrencyDemandDepositAccountWithdrawal",
        "institutionTransactionUniqueNo": "20240215121212123456"
    },
    "REC": {
        "transactionUniqueNo": "60",
        "transactionDate": "20240401"
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1011 | 거래금액이 유효하지 않습니다. |  |
| A1014 | 계좌 잔액이 부족하여 거래가 실패했습니다. | 출금 시 계좌의 잔액이 부족하여 발생 |
| A1018 | 거래요약내용 길이가 초과되었습니다. |  |
| A5005 | 외화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.12.9 외화 계좌 입금

##### 설명

이용기관이 **사용자의 외화 계좌로 대금을 입금**합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/updateForeignCurrencyDemandDepositAccountDeposit | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| transactionBalance | 입금금액 | Double |  | Y | 소수점 둘째자리까지 가능 (엔화의 경우 정수 입력) |
| transactionSummary | 입금계좌요약 | String | 255 | N |  |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "updateForeignCurrencyDemandDepositAccountDeposit",
        "transmissionDate": "20240401",
        "transmissionTime": "102500",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "updateForeignCurrencyDemandDepositAccountDeposit",
        "institutionTransactionUniqueNo": "20240215121212123463",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    },
    "accountNo": "0016174648358792",
    "transactionBalance": "100000000",
    "transactionSummary": "(수시입출금) : 입금"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 거래 정보 | List |  | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "updateForeignCurrencyDemandDepositAccountDeposit",
        "transmissionDate": "20240401",
        "transmissionTime": "102500",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "updateForeignCurrencyDemandDepositAccountDeposit",
        "institutionTransactionUniqueNo": "20240215121212123463"
    },
    "REC": {
        "transactionUniqueNo": "59",
        "transactionDate": "20240401"
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1011 | 거래금액이 유효하지 않습니다. |  |
| A1018 | 거래요약내용 길이가 초과되었습니다. |  |
| A5005 | 외화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.12.10 외화 계좌 이체

##### 설명

한 계좌로부터 **다른 계좌로 대금을 이체**합니다.
 📌 **원화와 엔화의 경우, 이체된 금액이 소수점일 시 정수로 절삭되어 입금됩니다.**

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/updateForeignCurrencyDemandDepositAccountTransfer | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| depositAccountNo | 입금계좌번호 | String | 16 | Y | 원화, 외화 계좌 가능 |
| transactionBalance | 거래금액 | Double |  | Y | 출금할 통화의 금액 입력 (원화, 엔화는 정수 / 이외 통화 소수점 둘째 자리까지 허용) |
| withdrawalAccountNo | 출금계좌번호 | String | 16 | Y | 외화 계좌만 가능 |
| depositTransactionSummary | 거래 요약내용 (입금계좌) | String | 255 | N |  |
| withdrawalTransactionSummary | 거래 요약내용 (출금계좌) | String | 255 | N |  |

##### 요청 메시지 형태

```json
{
     "Header": {
        "apiName": "updateForeignCurrencyDemandDepositAccountTransfer",
        "transmissionDate": "20240401",
        "transmissionTime": "103500",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "updateForeignCurrencyDemandDepositAccountTransfer",
        "institutionTransactionUniqueNo": "20240215121212123453",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    }, 
    "depositAccountNo": "0204667768182760",
    "depositTransactionSummary": "(외화 수시입출금) : 입금(이체)",
    "transactionBalance": "100000", 
    "withdrawalAccountNo": "0016174648358792", 
    "withdrawalTransactionSummary": "(외화 수시입출금) : 출금(이체)"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 거래 목록 | List |  | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |
| transactionType | 거래유형 | String | 1 | Y | 1, 2 ... |
| transactionTypeName | 거래유형명 | String | 8 | Y | 입금이체, 출금이체 ... |
| transactionAccountNo | 거래 계좌번호 | String | 16 | Y | 이체 거래에 대한 계좌번호 |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "updateForeignCurrencyDemandDepositAccountTransfer",
        "transmissionDate": "20240401",
        "transmissionTime": "103500",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "updateForeignCurrencyDemandDepositAccountTransfer",
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1011 | 거래금액이 유효하지 않습니다. |  |
| A1014 | 계좌 잔액이 부족하여 거래가 실패했습니다. | 출금 시 계좌의 잔액이 부족하여 발생 |
| A1016 | 이체 가능 한도 초과 (1회) | 1회 이체 가능한 금액을 초과 |
| A1017 | 이체 가능 한도 초과 (1일) | 1일 이체 가능한 금액을 초과 |
| A1018 | 거래요약내용 길이가 초과되었습니다. |  |
| A5005 | 외화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.12.11 외화 계좌 이체 한도 변경

##### 설명

외화 계좌에 대한 **이체한도를 변경**합니다.
 📌 **1일 및 1회 이체 한도는 통화마다 다르며, 엔화는 정수만 입력 가능합니다.**

##### 금융망 API 적용 한도 및 이체한도 변경 API 설정 범위

| 통화 | 회당 한도 | 1일 한도 | 1회 이체 한도 설정 가능 범위 | 1일 이체한도 설정 가능 범위 |
| --- | --- | --- | --- | --- |
| 원화 (KRW) | 100,000,000 | 500,000,000 | 1 ~ 10,000,000,000 | 1 ~ 20,000,000,000 |
| 미국 달러 (USD) | 70,000 | 300,000 | 0.01 ~ 7,200,000 | 0.01 ~ 144,000,000 |
| 유럽연합 유로 (EUR) | 60,000 | 300,000 | 0.01 ~ 6,600,000 | 0.01 ~ 132,000,000 |
| 일본 엔 (JPY) | 10,000,000 | 50,000,000 | 0.01 ~ 1,100,000,000 | 0.01 ~ 22,800,000,000 |
| 중국 위안 (CNY) | 500,000 | 2,000,000 | 0.01 ~ 52,000,000 | 0.01 ~ 1,050,000,000 |
| 영국 파운드 (GBP) | 50,000 | 200,000 | 0.01 ~ 5,500,000 | 0.01 ~ 111,000,000 |
| 스위스 프랑 (CHF) | 60,000 | 300,000 | 0.01 ~ 6,400,000 | 0.01 ~ 129,000,000 |
| 캐나다 달러 (CAD) | 90,000 | 400,000 | 0.01 ~ 9,800,000 | 0.01 ~ 197,000,000 |

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/updateForeignCurrencyTransferLimit | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| oneTimeTransferLimit | 1회 이체한도 | Double |  | Y | 통화별 한도 상이 |
| dailyTransferLimit | 1일 이체한도 | Double |  | Y | 통화별 한도 상이 |

##### 요청 메시지 형태

```json
{
     "Header": {
        "apiName": "updateForeignCurrencyTransferLimit",
        "transmissionDate": "20240401",
        "transmissionTime": "104000",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "updateForeignCurrencyTransferLimit",
        "institutionTransactionUniqueNo": "20240215121212123452",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    }, 
    "accountNo": "0016174648358792", 
    "oneTimeTransferLimit": "20000000", 
    "dailyTransferLimit": "100000000"
}
```

##### 응답 메시지 명세

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
| dailyTransferLimit | 1일 이체한도 | Double |  | Y | 통화별 최대값 참조 |
| oneTimeTransferLimit | 1회 이체한도 | Double |  | Y | 통화별 최대값 참조 |
| accountBalance | 계좌잔액 | Double |  | Y |  |
| lastTransactionDate | 최종거래일 | String | 8 | N |  |
| currency | 통화코드 | String | 8 | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "updateForeignCurrencyTransferLimit",
        "transmissionDate": "20240401",
        "transmissionTime": "104000",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "updateForeignCurrencyTransferLimit",
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
        "currency": "USD"
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1024 | 1회 이체한도가 유효하지 않습니다. |  |
| A1025 | 1일 이체한도가 유효하지 않습니다. |  |
| A5005 | 외화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |

---

#### 2.12.12 외화 계좌 거래 내역 조회

##### 설명

**외화 계좌 거래 내역 목록을 조회**합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyTransactionHistoryList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| startDate | 조회시작일자 | String | 8 | Y | YYYYMMDD |
| endDate | 조회종료일자 | String | 8 | Y | YYYYMMDD |
| transactionType | 거래구분 | String | 1 | Y | M: 입금, D: 출금, A: 전체 |
| orderByType | 정렬순서 | String | 4 | N | ASC: 오름차순, DESC: 내림차순 |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "inquireForeignCurrencyTransactionHistoryList",
        "transmissionDate": "20240401",
        "transmissionTime": "105000",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "inquireForeignCurrencyTransactionHistoryList",
        "institutionTransactionUniqueNo": "20240215121212123459",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"
    },
    "accountNo": "0016174648358792",
    "startDate": "20240101",
    "endDate": "20241231",
    "transactionType": "A",
    "orderByType": "ASC"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 거래내역 | List |  | N |  |
| totalCount | 조회총건수 | String |  | N |  |
| list | 거래목록 | List |  | N |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |
| transactionTime | 거래시각 | String | 6 | Y | HHMMSS |
| transactionType | 입출금구분 | String | 1 | Y | 1, 2 |
| transactionTypeName | 입출금구분명 | String | 10 | Y | 입금, 출금, 입금(이체), 출금(이체) |
| transactionAccountNo | 거래계좌번호 | String | 16 | N |  |
| transactionBalance | 거래금액 | Double |  | Y |  |
| transactionAfterBalance | 거래후잔액 | Double |  | Y |  |
| transactionSummary | 거래 요약내용 | String | 255 | N |  |
| transactionMemo | 거래 메모 | String | 255 | N |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "inquireForeignCurrencyTransactionHistoryList",
        "transmissionDate": "20240401",
        "transmissionTime": "105000",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "inquireForeignCurrencyTransactionHistoryList",
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1004 | 조회 시작일자가 유효하지 않습니다. |  |
| A1005 | 조회 종료일자가 유효하지 않습니다. |  |
| A1006 | 거래 구분이 유효하지 않습니다. |  |
| A1007 | 정렬 순서가 유효하지 않습니다. |  |
| A5005 | 외화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.12.13 외화 계좌 거래 내역 조회 (단건)

##### 설명

특정 **외화 계좌의 거래 내역 (단건)을 조회**합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyTransactionHistory | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |

##### 요청 메시지 형태

```json
{
   "Header": {
        "apiName": "inquireForeignCurrencyTransactionHistory",
        "transmissionDate": "20240401",
        "transmissionTime": "105500",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "inquireForeignCurrencyTransactionHistory",
        "institutionTransactionUniqueNo": "20240215121212123452",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"    
    },
    "accountNo": "0016174648358792",
    "transactionUniqueNo": "61"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 거래내역 | List |  | N |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |
| transactionTime | 거래시각 | String | 6 | Y | HHMMSS |
| transactionType | 입출금구분 | String | 1 | Y | 1, 2 |
| transactionTypeName | 입출금구분명 | String | 10 | Y | 입금, 출금, 입금(이체), 출금(이체) |
| transactionAccountNo | 거래계좌번호 | String | 16 | N |  |
| transactionBalance | 거래금액 | Double |  | Y |  |
| transactionAfterBalance | 거래후잔액 | Double |  | Y |  |
| transactionSummary | 거래 요약내용 | String | 255 | N |  |
| transactionMemo | 거래 메모 | String | 255 | N |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "inquireForeignCurrencyTransactionHistory",
        "transmissionDate": "20240401",
        "transmissionTime": "105500",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "inquireForeignCurrencyTransactionHistory",
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1010 | 거래고유번호가 유효하지 않습니다. |  |
| A5005 | 외화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.12.14 외화 계좌 해지

##### 설명

외화 계좌를 해지합니다.
 📌 **계좌 해지 시 같은 통화의 계좌로만 금액 반환이 가능합니다.**
 📌 **잔액이 0원인 계좌는 금액 반환 계좌번호를 작성하지 않아도 정상 해지됩니다.**

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/deleteForeignCurrencyDemandDepositAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| refundAccountNo | 금액반환계좌번호 | String | 16 | N | 해지 계좌번호의 잔액이 0원일 경우 미입력 가능 |

##### 요청 메시지 형태

```json
{
   "Header": {
        "apiName": "deleteForeignCurrencyDemandDepositAccount",
        "transmissionDate": "20240401",
        "transmissionTime": "112000",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "deleteForeignCurrencyDemandDepositAccount",
        "institutionTransactionUniqueNo": "20240215121212123455",
        "apiKey": "[REDACTED]",
        "userKey": "[REDACTED]"    
    },
    "accountNo": "0018770964252220",
    "refundAccountNo": "0324003842129948"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 해지 계좌정보 | List |  | Y |  |
| status | 상태 | String | 20 | Y | CLOSED (계좌 해지 완료) |
| accountNo | 해지 계좌번호 | String | 16 | Y |  |
| refundAccountNo | 금액 반환 계좌번호 | String | 16 | Y |  |
| accountBalance | 계좌 해지 잔액 | Double |  | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "responseCode": "H0000",
        "responseMessage": "정상처리 되었습니다.",
        "apiName": "deleteForeignCurrencyDemandDepositAccount",
        "transmissionDate": "20240401",
        "transmissionTime": "112000",
        "institutionCode": "00100",
        "apiKey": "[REDACTED]",
        "apiServiceCode": "deleteForeignCurrencyDemandDepositAccount",
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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1095 | 같은 통화 계좌로만 이체가 가능합니다. |  |
| A5005 | 외화 계좌만 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

