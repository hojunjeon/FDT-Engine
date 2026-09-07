# SSAFY 금융망 — 대출 API

- Source: https://project.ssafy.com/docs/ssafy-finance/api-loan
- Crawled: 2026-08-24
- Scope: Read-only document crawl; no live API calls, authentication, or financial data changes were performed.
- Summary: Visible article content covers 10 POST endpoints for credit-rating criteria, loan products, credit ratings, loan assessments, loan accounts, repayment records, and full repayment, with request/response schemas and error-code tables.

# 대출

### 2.7 대출

---

#### 2.7.1 신용등급 기준 조회

##### 설명

신용등급 기준을 조회합니다.

자산 기준은 사용자의 수시입출금, 예·적금을 모두 합친 금액입니다.

최대 자산 가치 중 가장 큰 금액을 넘는 자산 보유 시 최고 등급으로 산정됩니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireAssetBasedCreditRatingList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |

##### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "inquireAssetBasedCreditRatingList",

        "transmissionDate": "20240412",

        "transmissionTime": "131500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireAssetBasedCreditRatingList",

        "institutionTransactionUniqueNo": "20240215121212123553",

        "apiKey": "<REDACTED_API_KEY>"

    }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 신용등급 정보 |  |  | Y |  |
| ratingUniqueNo | 신용등급 기준 고유번호 | String | 20 | Y |  |
| ratingName | 신용등급 | String | 20 | Y | A~E |
| minAssetValue | 최소 자산 가치 | Long |  | Y |  |
| maxAssetValue | 최대 자산 가치 | Long |  | Y |  |

##### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireAssetBasedCreditRatingList",

        "transmissionDate": "20240412",

        "transmissionTime": "131500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireAssetBasedCreditRatingList",

        "institutionTransactionUniqueNo": "20240215121212123553"

    },

    "REC": [

        {

            "ratingUniqueNo": "RT-0fa85f6425e811ea4",

            "ratingName": "A",

            "minAssetValue": "100000000",

            "maxAssetValue": "2000000000"

        },

        {

            "ratingUniqueNo": "RT-2gwxr5125e640552a",

            "ratingName": "B",

            "minAssetValue": "80000000",

            "maxAssetValue": "99999999"

        },

        {

            "ratingUniqueNo": "RT-690a65f6425e6ea7a",

            "ratingName": "C",

            "minAssetValue": "50000000",

            "maxAssetValue": "79999999"

        },

        {

            "ratingUniqueNo": "RT-9xr3811ea45aa56hg",

            "ratingName": "D",

            "minAssetValue": "30000000",

            "maxAssetValue": "49999999"

        },

        {

            "ratingUniqueNo": "RT-a335h7aa7f3x74ag5",

            "ratingName": "E",

            "minAssetValue": "0",

            "maxAssetValue": "29999999"

        }

    ]

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| H1000 | HEADER 정보가 유효하지 않습니다. |  |
| H1001 | API이름이 유효하지 않습니다. |  |
| H1002 | 전송일자 형식이 유효하지 않습니다. |  |
| H1003 | 전송시각 형식이 유효하지 않습니다. |  |
| H1004 | 기관코드가 유효하지 않습니다. |  |
| H1005 | 핀테크 앱 일련번호가 유효하지 않습니다. |  |
| H1006 | API서비스코드가 유효하지 않습니다. |  |
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.7.2 대출 상품 등록

##### 설명

은행별 대출 상품을 등록합니다.

신용등급과 은행코드를 조회하여 해당 은행의 대출 상품을 생성할 수 있습니다.

대출 상품 조회 API를 통해 샘플 데이터를 참고하여 상품을 등록할 수 있습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/createLoanProduct | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |
| bankCode | 은행코드 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y | 대출 상품명 입력 (ex. 한국은행 저금리 대출) |
| accountDescription | 상품설명 | String | 255 | N | 대출 상품 설명 입력 |
| ratingUniqueNo | 신용등급 기준 고유번호 | String | 20 | Y |  |
| loanPeriod | 대출기간 | Int |  | Y | 2 ~ 365 / 단위(일) |
| minLoanBalance | 최소 대출 금액 | Long |  | Y | 1,000 이상 / 단위(원) |
| maxLoanBalance | 최대 대출 금액 | Long |  | Y | 300,000,000 (3억) 이하 / 단위(원) |
| interestRate | 기본 금리 | Double |  | Y | 0.1 이상 ~ 20 이하 단위(%) |

##### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "createLoanProduct",

        "transmissionDate": "20240415",

        "transmissionTime": "145000",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createLoanProduct",

        "institutionTransactionUniqueNo": "20240215121212123555",

        "apiKey": "<REDACTED_API_KEY>"

    },

    "bankCode": "001",

    "accountName": "한국은행 저금리 대출",

    "accountDescription": null,

    "ratingUniqueNo": "RT-0fa85f6425e811ea4",

    "loanPeriod": "3",

    "minLoanBalance": "10000",

    "maxLoanBalance": "100000000",

    "interestRate": "5"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 대출 상품 정보 |  |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| ratingUniqueNo | 신용등급 기준 고유번호 | String | 20 | Y |  |
| ratingName | 신용등급명 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| loanPeriod | 대출기간 | Int |  | Y |  |
| minLoanBalance | 최소 대출 금액 | Long |  | Y |  |
| maxLoanBalance | 최대 대출 금액 | Long |  | Y |  |
| interestRate | 기본 금리 | Double |  | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1: 수시입출금, 2: 정기예금, 3: 정기적금, 4: 대출 |

| accountTypeName | 상품구분명 | String | 20 | Y |  |
| loanTypeCode | 대출 구분 코드 | String | 3 | Y | 001 : 신용대출 |
| loanTypeName | 대출 구분 코드명 | String | 20 | Y |  |
| repaymentMethodTypeCode | 대출상환방법 코드 | String | 4 | Y | 0001 : 원리금균등상환 |
| repaymentMethodTypeName | 대출상환방법 코드명 | String | 20 | Y |  |

##### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "createLoanProduct",

        "transmissionDate": "20240415",

        "transmissionTime": "145000",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "createLoanProduct",

        "institutionTransactionUniqueNo": "20240215121212123555"

    },

    "REC": {

        "accountTypeUniqueNo": "001-4-82838a9c9fcb4f",

        "bankCode": "001",

        "bankName": "한국은행",

        "ratingUniqueNo": "RT-0fa85f6425e811ea4",

        "ratingName": "A",

        "accountName": "한국은행 저금리 대출",

        "loanPeriod": "3",

        "minLoanBalance": "10000",

        "maxLoanBalance": "100000000",

        "interestRate": "5",

        "accountDescription": "",

        "accountTypeCode": "4",

        "accountTypeName": "대출",

        "loanTypeCode": "001",

        "loanTypeName": "신용대출",

        "repaymentMethodTypeCode": "0001",

        "repaymentMethodTypeName": "원리금균등상환"

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
| A1061 | 신용등급 고유번호가 유효하지 않습니다. |  |
| A1026 | 가입기간이 유효하지 않습니다. |  |
| A1034 | 가입기간은 2일 ~ 365일 기간으로만 입력 가능합니다. |  |
| A1027 | 최소가입가능금액이 유효하지 않습니다. |  |
| A1062 | 가입금액은 1천원 ~ 3억으로만 입력 가능합니다. |  |
| A1028 | 최대가입가능금액이 유효하지 않습니다. |  |
| A1029 | 이자율이 유효하지 않습니다. |  |
| A1036 | 이자율은 0.1 ~ 20으로만 입력이 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.7.3 대출 상품 조회

##### 설명

대출 상품 목록을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireLoanProductList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |

##### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "inquireLoanProductList",

        "transmissionDate": "20240415",

        "transmissionTime": "151000",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireLoanProductList",

        "institutionTransactionUniqueNo": "20240215121212123554",

        "apiKey": "<REDACTED_API_KEY>"

    }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 대출 상품 리스트 | List |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| ratingUniqueNo | 신용등급 기준 고유번호 | String | 20 | Y |  |
| ratingName | 최소 가입가능 신용등급명 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| loanPeriod | 대출기간 | Int |  | Y |  |
| minLoanBalance | 최소 대출 금액 | Long |  | Y |  |
| maxLoanBalance | 최대 대출 금액 | Long |  | Y |  |
| interestRate | 기본 금리 | Double |  | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1: 수시입출금, 2: 정기예금, 3: 정기적금, 4: 대출 |
| accountTypeName | 상품구분명 | String | 20 | Y |  |
| loanTypeCode | 대출 구분 코드 | String | 3 | Y | 001 : 신용대출 |
| loanTypeName | 대출 구분 코드명 | String | 20 | Y |  |
| repaymentMethodTypeCode | 대출상환방법 코드 | String | 4 | Y | 0001 : 원리금균등상환 |
| repaymentMethodTypeName | 대출상환방법 코드명 | String | 20 | Y |  |

##### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireLoanProductList",

        "transmissionDate": "20240415",

        "transmissionTime": "151000",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireLoanProductList",

        "institutionTransactionUniqueNo": "20240215121212123554"

    },

    "REC": [

        {

            "accountTypeUniqueNo": "001-4-82838a9c9fcb4f",

            "bankCode": "001",

            "bankName": "한국은행",

            "ratingUniqueNo": "RT-0fa85f6425e811ea4",

            "ratingName": "A",

            "accountName": "한국은행 저금리 대출",

            "loanPeriod": "3",

            "minLoanBalance": "10000",

            "maxLoanBalance": "100000000",

            "interestRate": "5",

            "accountDescription": null,

            "accountTypeCode": "4",

            "accountTypeName": "대출",

            "loanTypeCode": "001",

            "loanTypeName": "신용대출",

            "repaymentMethodTypeCode": "0001",

            "repaymentMethodTypeName": "원리금균등상환"

        },

        {

            "accountTypeUniqueNo": "001-4-c07cbf67ae3440",

            "bankCode": "001",

            "bankName": "한국은행",

            "ratingUniqueNo": "RT-0fa85f6425e811ea4",

            "ratingName": "A",

            "accountName": "한국은행 저금리 대출",

            "loanPeriod": "7",

            "minLoanBalance": "50000000",

            "maxLoanBalance": "100000000",

            "interestRate": "5",

            "accountDescription": null,

            "accountTypeCode": "4",

            "accountTypeName": "대출",

            "loanTypeCode": "001",

            "loanTypeName": "신용대출",

            "repaymentMethodTypeCode": "0001",

            "repaymentMethodTypeName": "원리금균등상환"

        },

        {


            "accountTypeUniqueNo": "004-4-67140989453846",

            "bankCode": "004",

            "bankName": "국민은행",

            "ratingUniqueNo": "RT-2gwxr5125e640552a",

            "ratingName": "B",

            "accountName": "국민은행 믿고 가입하는 대출",

            "loanPeriod": "5",

            "minLoanBalance": "30000000",

            "maxLoanBalance": "100000000",

            "interestRate": "20",

            "accountDescription": "상품 대한 설명",

            "accountTypeCode": "4",

            "accountTypeName": "대출",

            "loanTypeCode": "001",

            "loanTypeName": "신용대출",

            "repaymentMethodTypeCode": "0001",

            "repaymentMethodTypeName": "원리금균등상환"

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

#### 2.7.4 내 신용등급 조회

##### 설명

사용자의 신용등급을 조회합니다.

현재 가입되어 있는 수시입출금 및 예·적금 자산을 합산하여 신용등급 기준에 해당하는 등급이 조회됩니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMyCreditRating | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |

##### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "inquireMyCreditRating",

        "transmissionDate": "20240415",

        "transmissionTime": "151500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireMyCreditRating",

        "institutionTransactionUniqueNo": "20240215121212123552",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 내 신용등급 정보 |  |  | Y |  |
| ratingName | 신용등급명 | String | 20 | Y |  |
| demandDepositAssetValue | 수시입출금 자산 | Long |  | Y | 사용자의 모든 수시입출금 합산한 자산 |
| depositSavingsAssetValue | 예·적금 자산 | Long |  | Y | 사용자의 모든 예·적금 합산한 자산 |
| totalAssetValue | 전체 자산 | Long |  | Y | 전체 합산한 자산 |

##### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireMyCreditRating",

        "transmissionDate": "20240415",

        "transmissionTime": "151500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireMyCreditRating",

        "institutionTransactionUniqueNo": "20240215121212123552"

    },

    "REC": {

        "ratingName": "A",

        "demandDepositAssetValue": "1089427976",

        "depositSavingsAssetValue": "0",

        "totalAssetValue": "1089427976"

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
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.7.5 대출심사 신청

##### 설명

대출심사를 신청합니다.

해당 대출 상품의 가입 가능한 신용등급 정보를 확인하고

사용자의 신용등급 조회 결과를 고려하여 특정 대출 상품에 대한 심사 결과를 확인할 수 있습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/createLoanApplication | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |

##### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "createLoanApplication",

        "transmissionDate": "20240411",

        "transmissionTime": "090500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createLoanApplication",

        "institutionTransactionUniqueNo": "20240215121212123559",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "accountTypeUniqueNo": "004-4-67140989453846"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 대출심사 정보 |  |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| status | 심사 상태 | String | 20 | Y | 승인, 거절(대출 상품 신용등급 기준 미달 시) |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| ratingUniqueNo | 신용등급 기준 고유번호 | String | 20 | Y |  |
| ratingName | 신용등급명 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| loanPeriod | 대출기간 | Int |  | Y |  |
| minLoanBalance | 최소 대출 금액 | Long |  | Y |  |
| maxLoanBalance | 최대 대출 금액 | Long |  | Y |  |
| interestRate | 기본 금리 | Double |  | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| applicationDate | 심사 신청 날짜 | String | 8 | Y |  |
| applicationTime | 심사 신청 시간 | String | 6 | Y |  |
| decisionDate | 심사 날짜 | String | 8 | Y |  |
| decisionTime | 심사 시간 | String | 6 | Y |  |

##### 응답 메세지 형태

```json
{    

    "Header": {

        "apiName": "createLoanApplication",

        "transmissionDate": "20240411",

        "transmissionTime": "090500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createLoanApplication",

        "institutionTransactionUniqueNo": "20240215121212123559",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },


    "accountTypeUniqueNo": "004-4-67140989453846"

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
| A1019 | 없는 상품입니다. 상품 조회를 다시 확인해주세요. |  |
| A1023 | 상품고유번호가 유효하지 않습니다. |  |
| A1084 | 이미 승인된 대출입니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.7.6 대출심사 목록 조회

##### 설명

대출 심사 목록을 조회합니다.

사용자가 신청한 대출 상품들의 심사 정보를 조회할 수 있으며,

승인된 목록에 한하여 대출 가입이 가능합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireLoanApplicationList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |

##### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "inquireLoanApplicationList",

        "transmissionDate": "20240415",

        "transmissionTime": "152500",

        "institutionCode": "00100",

        "fintechAppNo": "001", 

        "apiServiceCode": "inquireLoanApplicationList",

        "institutionTransactionUniqueNo": "20240215121212123554",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 대출심사 리스트 |  |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| status | 심사 상태 | String | 20 | Y | 승인, 거절(대출 상품 신용등급 기준 미달 시) |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| ratingUniqueNo | 신용등급 기준 고유번호 | String | 20 | Y |  |
| ratingName | 신용등급명 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| loanPeriod | 대출기간 | Int |  | Y |  |
| minLoanBalance | 최소 대출 금액 | Long |  | Y |  |
| maxLoanBalance | 최대 대출 금액 | Long |  | Y |  |
| interestRate | 기본 금리 | Double |  | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| applicationDate | 심사 신청 날짜 | String | 8 | Y |  |
| applicationTime | 심사 신청 시간 | String | 6 | Y |  |
| decisionDate | 심사 날짜 | String | 8 | Y |  |
| decisionTime | 심사 시간 | String | 6 | Y |  |

##### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireLoanApplicationList",

        "transmissionDate": "20240415",

        "transmissionTime": "152500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireLoanApplicationList",

        "institutionTransactionUniqueNo": "20240215121212123554"

    },

    "REC": [

        {

            "accountTypeUniqueNo": "004-4-67140989453846",

            "status": "승인",

            "bankCode": "004",

            "bankName": "국민은행",

            "ratingUniqueNo": "RT-2gwxr5125e640552a",

            "ratingName": "B",

            "accountName": "국민은행 믿고 가입하는 대출",

            "loanPeriod": "5",

            "minLoanBalance": "30000000",

            "maxLoanBalance": "100000000",

            "interestRate": "20",

            "accountDescription": "상품 대한 설명",

            "applicationDate": "20240415",

            "applicationTime": "151856",

            "decisionDate": "20240415",

            "decisionTime": "151856"

        },

        {

            "accountTypeUniqueNo": "045-4-b3262da30da445",

            "status": "승인",

            "bankCode": "045",

            "bankName": "새마을금고",

            "ratingUniqueNo": "RT-0fa85f6425e811ea4",

            "ratingName": "A",

            "accountName": "새마을금고 대출 상품",

            "loanPeriod": "3",

            "minLoanBalance": "100000000",

            "maxLoanBalance": "300000000",

            "interestRate": "5",

            "accountDescription": "상품 대한 설명",

            "applicationDate": "20240327",

            "applicationTime": "090644",

            "decisionDate": "20240327",

            "decisionTime": "090644"

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
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.7.7 대출 상품 가입

##### 설명

대출 상품에 가입합니다.

대출 심사 목록을 조회 후 **심사 승인 상품**에 대해서만 가입을 진행할 수 있습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/createLoanAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| loanBalance | 대출금 | Long |  | Y |  |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y | 수시입출금 계좌 (대출금 지급 계좌) |

##### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "createLoanAccount",

        "transmissionDate": "20240415",

        "transmissionTime": "153000",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createLoanAccount",

        "institutionTransactionUniqueNo": "20240215121212123558",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "accountTypeUniqueNo":"004-4-67140989453846",

    "loanBalance": "100000000",

    "withdrawalAccountNo": "0324003842129948"

}
```

##### 응답 메시지 명세


| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 대출상품 가입 정보 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| status | 계좌 상태 | String | 20 | Y | 개설, 상환중, 연체 |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| loanPeriod | 대출기간 | Int |  | Y |  |
| loanDate | 대출 날짜 | String | 8 | Y |  |
| maturityDate | 대출 만료 날짜 | String | 8 | Y |  |
| loanBalance | 대출금 | Long |  | Y |  |
| interestRate | 기본 금리 | Double |  | Y |  |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y |  |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "createLoanAccount",

        "transmissionDate": "20240415",

        "transmissionTime": "153000",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "createLoanAccount",

        "institutionTransactionUniqueNo": "20240215121212123558"

    },

    "REC": {

        "accountNo": "0044815881614041",

        "accountName": "국민은행 믿고 가입하는 대출",

        "status": "개설",

        "accountTypeUniqueNo": "004-4-67140989453846",

        "loanPeriod": "5",

        "loanDate": "20240415",

        "maturityDate": "20240420",

        "loanBalance": "100000000",

        "interestRate": "20",

        "withdrawalAccountNo": "0324003842129948"

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
| A1019 | 없는 상품입니다. 상품 조회를 다시 확인해주세요. |  |
| A1023 | 상품고유번호가 유효하지 않습니다. |  |
| A1030 | 가입금액이 유효하지 않습니다. |  |
| A1037 | 해당 상품에 가입 가능한 금액이 아닙니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.7.8 대출 상품 가입 목록 조회

##### 설명

사용자의 대출 상품 가입 목록을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireLoanAccountList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |

##### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "inquireLoanAccountList",

        "transmissionDate": "20240415",

        "transmissionTime": "153500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireLoanAccountList",

        "institutionTransactionUniqueNo": "20240215121212123561",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 대출상품 가입 정보 리스트 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| status | 계좌 상태 | String | 20 | Y | 개설, 상환중, 연체 |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| loanPeriod | 대출기간 | Int |  | Y |  |
| loanDate | 대출 날짜 | String | 8 | Y |  |
| maturityDate | 대출 만료 날짜 | String | 8 | Y |  |
| loanBalance | 대출금 | Long |  | Y |  |
| interestRate | 기본 금리 | Double |  | Y |  |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y |  |

##### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireLoanAccountList",

        "transmissionDate": "20240415",

        "transmissionTime": "153500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireLoanAccountList",

        "institutionTransactionUniqueNo": "20240215121212123561"

    },

    "REC": [

        {

            "accountNo": "0044815881614041",

            "accountName": "국민은행 믿고 가입하는 대출",

            "status": "개설",

            "accountTypeUniqueNo": "004-4-67140989453846",

            "loanPeriod": "5",

            "loanDate": "20240415",

            "maturityDate": "20240420",

            "loanBalance": "100000000",

            "interestRate": "20",

            "withdrawalAccountNo": "0324003842129948"

        },

        {

            "accountNo": "0451863702889610",

            "accountName": "새마을금고 대출 상품",

            "status": "개설",

            "accountTypeUniqueNo": "045-4-b3262da30da445",

            "loanPeriod": "3",

            "loanDate": "20240405",

            "maturityDate": "20240408",

            "loanBalance": "200000000",

            "interestRate": "5",

            "withdrawalAccountNo": "0324003842129948"

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
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.7.9 대출 상환 내역 조회

##### 설명

사용자의 특정 대출 계좌의 상환 내역을 조회합니다.

대출금 상환은 개설일 **다음날부터 매일 오전 08:30**에 대출 상품에서 기입한

**수시입출금 계좌에서 자동 상환**됩니다.

상환이 완료되면 대출 계좌는 자동 해지되고,

한 번이라도 연체 상태가 있다면 **연체금을 납입할 때까지 계좌가 유지**됩니다.

**대출이자 산출식:**

> (원금 * (이자율 / 100) * (일수 / 365)) 반올림하여 이자 계산

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireRepaymentRecords | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |

| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "inquireRepaymentRecords",

        "transmissionDate": "20240415",

        "transmissionTime": "154500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireRepaymentRecords",

        "institutionTransactionUniqueNo": "20240215121212123571",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "accountNo": "0044815881614041"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 대출 상환 내역 정보 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| status | 계좌 상태 | String | 20 | Y | 개설, 상환중, 연체 |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| loanBalance | 대출금 | Long |  | Y | (원금 + 이자) 대출금 |
| remainingLoanBalance | 남은 대출금 | Double |  | Y | 남은 (원금 + 이자) 대출금 |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y |  |
| repaymentRecords | 상환 내역 | List |  | N |  |
| installmentNumber | 회차 | String | 255 | Y |  |
| status | 상환 상태 | String | 20 | Y | SUCCESS, FAIL |
| paymentBalance | 상환 금액 | Long |  | Y |  |
| repaymentAttemptDate | 상환 시도 일자 | String | 8 | Y |  |
| repaymentAttemptTime | 상환 시도 시각 | String | 6 | Y |  |
| repaymentActualDate | 실제 상환 일자 | String | 8 | N |  |
| repaymentActualTime | 실제 상환 시각 | String | 6 | N |  |
| failureReason | 실패이유 | String | 255 | N | FAIL 시 (대출) 자동이체 실패 잔액 부족 |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireRepaymentRecords",

        "transmissionDate": "20240416",

        "transmissionTime": "103500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireRepaymentRecords",

        "institutionTransactionUniqueNo": "20240215121212123571"

    },

    "REC": {

        "accountNo": "0044815881614041",

        "accountName": "국민은행 믿고 가입하는 대출",

        "status": "상환중",

        "accountTypeUniqueNo": "004-4-67140989453846",

        "loanBalance": "120000000",

        "remainingLoanBalance": "96000000",

        "withdrawalAccountNo": "0324003842129948",

        "repaymentRecords": [

            {

                "installmentNumber": "1",

                "status": "SUCCESS",

                "paymentBalance": "24000000",

                "repaymentAttemptDate": "20240416",

                "repaymentAttemptTime": "080030",

                "repaymentActualDate": "20240416",

                "repaymentActualTime": "080030",

                "failureReason": ""

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
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.7.10 대출 일시납 상환

##### 설명

사용자의 특정 계좌에 대한 대출금을 모두 상환합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/updateRepaymentLoanBalanceInFull | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "updateRepaymentLoanBalanceInFull",

        "transmissionDate": "20240416",

        "transmissionTime": "104000",

        "institutionCode": "00100",

        "fintechAppNo": "001", 

        "apiServiceCode": "updateRepaymentLoanBalanceInFull",

        "institutionTransactionUniqueNo": "20240215121212123562",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "accountNo": "0044815881614041"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 대출 일시납 결과 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| status | 계좌 상태 | String | 20 | Y | CLOSED (대출금 일시납 상환) |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "updateRepaymentLoanBalanceInFull",

        "transmissionDate": "20240416",

        "transmissionTime": "104000",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "updateRepaymentLoanBalanceInFull",

        "institutionTransactionUniqueNo": "20240215121212123562"

    },

    "REC": {

        "accountNo": "0044815881614041",

        "status": "CLOSED"

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
| A1014 | 계좌 잔액이 부족하여 거래가 실패했습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---
