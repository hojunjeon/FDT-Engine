# 적금 API

- 제목: 적금
- 원문: https://project.ssafy.com/docs/ssafy-finance/api-savings
- 크롤링 날짜: 2026-08-24
- 범위: 정적 문서 복사만 수행했으며 라이브 API 호출은 하지 않음.
- 요약: 적금 상품 등록·조회와 적금 계좌 생성·조회·거래·해지 API의 요청, 응답, 에러코드를 정리한 문서입니다.

## 2.6 적금

---

### 2.6.1 적금 상품 등록

#### 설명

은행별 적금 상품을 등록합니다.
은행코드를 조회하여 해당 은행의 적금 상품을 생성할 수 있습니다.
적금 상품 조회 API를 통해 샘플 데이터를 참고하여 상품을 등록할 수 있습니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/createProduct | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | userKey 제외 |
| bankCode | 은행코드 | String | 3 | Y |  |
| accountName | 상품명 | String | 20 | Y | 적금 상품명 입력 (ex. 7일 적금) |
| accountDescription | 상품설명 | String | 255 | N | 적금 상품 설명 입력 (ex. 최대 19.5% 이자 지급) |
| subscriptionPeriod | 가입 기간 | String | 20 | Y | 2일 이상 ~ 365일 이하 |
| minSubscriptionBalance | 최소 가입 가능금액 | Long |  | Y | 1 이상 단위(원) |
| maxSubscriptionBalance | 최대 가입 가능금액 | Long |  | Y | 1000000(1백만) 이하 단위(원) |
| interestRate | 이자율 | Double |  | Y | 0.1 이상 ~ 20 이하 단위(%) |
| rateDescription | 이자율 설명 | String | 255 | N |  |

#### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "createProduct",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createProduct",

        "institutionTransactionUniqueNo": "20240101121212123456",

        "apiKey": "<REDACTED>"

    },

    "bankCode": "001",

    "accountName": "7일 적금",

    "accountDescription": "7일 적금입니다",

    "subscriptionPeriod": "7",

    "minSubscriptionBalance": "10000",

    "maxSubscriptionBalance": "1000000",

    "interestRate": "10",

    "rateDescription": "10% 이자를 지급합니다"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 상품목록 | List |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1: 수시입출금, 2: 정기예금, 3: 정기적금, 4: 대출 |
| accountTypeName | 상품구분명 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| subscriptionPeriod | 가입 가능기간 | String | 20 | Y |  |
| minSubscriptionBalance | 최소 가입 가능금액 | Long |  | Y |  |
| maxSubscriptionBalance | 최대 가입 가능금액 | Long |  | Y |  |
| interestRate | 이자율 | Double |  | Y |  |
| rateDescription | 이자율 설명 | String | 255 | N |  |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "createProduct",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "createProduct",

        "institutionTransactionUniqueNo": "20240101121212123456"

    },

    "REC": {

        "accountTypeUniqueNo": "001-3-a73d33e608af42",

        "bankCode": "001",

        "bankName": "한국은행",

        "accountTypeCode": "3",

        "accountTypeName": "적금",

        "accountName": "7일 적금",

        "accountDescription": "7일 적금입니다",

        "subscriptionPeriod": "7",

        "minSubscriptionBalance": "10000",

        "maxSubscriptionBalance": "1000000",

        "interestRate": "10",

        "rateDescription": "10% 이자를 지급합니다"

    }

}
```

#### 에러코드 목록

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
| A1001 | 은행코드가 유효하지 않습니다. |  |
| A1021 | 상품명이 유효하지 않습니다. |  |
| A1026 | 가입기간이 유효하지 않습니다. |  |
| A1027 | 최소가입가능금액이 유효하지 않습니다. |  |
| A1028 | 최대가입가능금액이 유효하지 않습니다. |  |
| A1029 | 이자율이 유효하지 않습니다. |  |
| A1031 | 상품설명 길이가 초과되었습니다. |  |
| A1032 | 이자율 설명 길이가 초과되었습니다. |  |
| A1033 | 상품명 길이가 초과되었습니다. |  |
| A1034 | 가입기간은 2일 ~ 365일 기간으로만 입력 가능합니다. |  |
| A1036 | 이자율은 0.1 ~ 20으로만 입력이 가능합니다. |  |
| A1038 | 가입금액은 1원 ~ 100만원으로만 입력 가능합니다. |  |
| A1040 | 최대가입가능금액은 최소가입가능금액보다 크거나 같아야 합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.6.2 적금 상품 조회

#### 설명

적금 상품 목록을 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquireSavingsProducts | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | userKey 제외 |

#### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "inquireSavingsProducts",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireSavingsProducts",

        "institutionTransactionUniqueNo": "20240101121212123456",

        "apiKey": "<REDACTED>"



    }

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 적금상품목록 | List |  | N |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1: 수시입출금, 2: 정기예금, 3: 정기적금, 4: 대출 |
| accountTypeName | 상품구분명 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| subscriptionPeriod | 가입 가능기간 | String | 20 | Y |  |
| minSubscriptionBalance | 최소 가입 가능금액 | Long |  | Y |  |
| maxSubscriptionBalance | 최대 가입 가능금액 | Long |  | Y |  |
| interestRate | 이자율 | Double |  | Y |  |
| rateDescription | 이자율 설명 | String | 255 | N |  |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireSavingsProducts",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireSavingsProducts",

        "institutionTransactionUniqueNo": "20240101121212123456"

    },

    "REC": [

        {

            "accountTypeUniqueNo": "001-3-364730d9a69244",

            "bankCode": "001",

            "bankName": "한국은행",

            "accountTypeCode": "3",

            "accountTypeName": "적금",

            "accountName": "7일 적금",

            "accountDescription": "7일 적금입니다",

            "subscriptionPeriod": "7",

            "minSubscriptionBalance": "10000",

            "maxSubscriptionBalance": "1000000",

            "interestRate": "10",

            "rateDescription": "10% 이자를 지급합니다"

        },

        {

            "accountTypeUniqueNo": "001-3-4373985ee26f4d",

            "bankCode": "001",

            "bankName": "한국은행",

            "accountTypeCode": "3",

            "accountTypeName": "적금",

            "accountName": "10일 적금",

            "accountDescription": "10일 적금입니다",

            "subscriptionPeriod": "10",

            "minSubscriptionBalance": "200000",

            "maxSubscriptionBalance": "1000000",

            "interestRate": "8",

            "rateDescription": "8% 이자를 지급합니다"

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
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.6.3 적금 계좌 생성

#### 설명

적금 계좌를 생성합니다. 사용자는 상품 고유번호를 통해 적금 계좌를 생성할 수 있습니다.
설정한 가입금액은 매일 출금 계좌번호에서 자동이체됩니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/createAccount | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| withdrawalAccountNo | 출금계좌번호 | String | 16 | Y | 가입 금액에 대해 자동이체할 수시입출금 계좌번호 기입 |
| accountTypeUniqueNo | 상품고유번호 | String | 20 | Y | 가입할 적금 상품고유번호 기입 |
| depositBalance | 가입금액 | Long |  | Y | 가입할 적금의 가입 가능금액 범위 내 기입 |

#### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "createAccount",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createAccount",

        "institutionTransactionUniqueNo": "20240101121212123456",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    },

    "accountTypeUniqueNo": "001-3-5e4f5b87fa2047", 

    "depositBalance": "100000",

    "withdrawalAccountNo": "0328073978527981"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 적금계좌정보 |  |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| withdrawalBankCode | 출금은행코드 | String | 3 | Y |  |
| withdrawalAccountNo | 출금은행계좌 | String | 16 | Y | 자동이체 수시입출금 계좌번호 |
| subscriptionPeriod | 가입 기간 | String | 20 | Y |  |
| depositBalance | 가입금액 | Long |  | Y |  |
| interestRate | 가입적용금리 | Double |  | Y |  |
| accountCreateDate | 계좌 개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌 만기일 | String | 8 | Y |  |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "createAccount",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "createAccount",

        "institutionTransactionUniqueNo": "20240101121212123456"

    },

    "REC": {

        "bankCode": "001",

        "bankName": "한국은행",

        "accountNo": "0016056377",

        "withdrawalBankCode": "032",

        "withdrawalAccountNo": "0328073978527981",

        "accountName": "7일 적금",

        "interestRate": "10.0",

        "subscriptionPeriod": "7",

        "depositBalance": "100000",

        "accountCreateDate": "20240326",

        "accountExpiryDate": "20240402"

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
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1014 | 계좌 잔액이 부족하여 거래가 실패했습니다. | 수시입출금 계좌의 잔액이 부족하여 발생 |
| A1023 | 상품고유번호가 유효하지 않습니다. |  |
| A1030 | 가입금액이 유효하지 않습니다. |  |
| A1037 | 해당 상품에 가입 가능한 금액이 아닙니다. | 가입금액이 가입 가능금액 범위에서 벗어나서 발생 |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.6.4 적금 계좌 목록 조회

#### 설명

사용자의 적금 계좌 목록 전체를 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquireAccountList | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |

#### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "inquireAccountList",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireAccountList",

        "institutionTransactionUniqueNo": "20240101121212123456",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    }

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| totalCount | 조회총건수 | String |  | N |  |
| REC | 적금계좌목록 | List |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| userName | 예금주명 | String | 50 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| withdrawalBankCode | 출금은행코드 | String | 3 | Y | 만기 시에도 사용할 정보 (출금) |
| withdrawalBankName | 출금은행명 | String | 10 | Y |  |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y | 적금 - (자동이체 경우에만 입력) 수시입출금 계좌번호 |
| subscriptionPeriod | 가입 기간 | String | 20 | Y |  |
| depositBalance | 가입금액 | Long |  | Y |  |
| interestRate | 가입적용금리 | Double |  | Y |  |
| installmentNumber | 회차 | String | 20 | Y | 최종회차 |
| totalBalance | 누적납입금액 | Long |  | Y | 현재까지 누적된 납입된 금액 |
| accountCreateDate | 계좌 개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌 만기일 | String | 8 | Y |  |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireAccountList",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireAccountList",

        "institutionTransactionUniqueNo": "20240101121212123456"

    },

    "REC": [

        {

            "bankCode": "001",

            "bankName": "한국은행",

            "userName": "USER",

            "accountNo": "0017675199", 

            "accountName": "7일 적금",

            "accountDescription": "7일 적금입니다",

            "withdrawalBankCode": "032",

            "withdrawalBankName": "대구은행",

            "withdrawalAccountNo": "0328073978527981",

            "subscriptionPeriod": "7",

            "depositBalance": "100000",

            "interestRate": "10",

            "installmentNumber": "3",

            "totalBalance": "100000",

            "accountCreateDate": "20240326",

            "accountExpiryDate": "20240402"

        },

        {

            "bankCode": "001",

            "bankName": "한국은행",

            "userName": "USER",

            "accountNo": "0017675199", 

            "accountName": "7일 적금",

            "accountDescription": "7일 적금입니다",

            "withdrawalBankCode": "032",

            "withdrawalBankName": "대구은행",

            "withdrawalAccountNo": "0328073978527981",

            "subscriptionPeriod": "7",

            "depositBalance": "100000",

            "interestRate": "10",

            "installmentNumber": "3",

            "totalBalance": "100000",

            "accountCreateDate": "20240326",

            "accountExpiryDate": "20240402"

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
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.6.5 적금 계좌 조회(단건)

#### 설명

사용자의 특정 적금 계좌에 대한 정보를 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquireAccount | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "inquireAccount",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireAccount",

        "institutionTransactionUniqueNo": "20240215121212123467",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

     },

    "accountNo": "1234567890123"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 적금계좌정보 |  |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| userName | 예금주명 | String | 50 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| withdrawalBankCode | 출금은행코드 | String | 3 | Y | 만기 시에도 사용할 정보 (출금) |
| withdrawalBankName | 출금은행명 | String | 10 | Y |  |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y | 적금 - (자동이체 경우에만 입력) 수시입출금 계좌번호 |
| subscriptionPeriod | 가입 기간 | String | 20 | Y |  |
| depositBalance | 가입금액 | Long |  | Y |  |
| interestRate | 가입적용금리 | Double |  | Y |  |
| installmentNumber | 회차 | String | 20 | Y | 최종회차 |
| totalBalance | 누적납입금액 | Long |  | Y | 현재까지 누적된 납입된 금액 |
| accountCreateDate | 계좌 개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌 만기일 | String | 8 | Y |  |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireAccount",

        "transmissionDate": "20240404",

        "transmissionTime": "110500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireAccount",

        "institutionTransactionUniqueNo": "20240302121213322343"

    },

    "REC": {

        "bankCode": "001",

        "bankName": "한국은행",

        "userName": "USER",

        "accountNo": "0011510578",

        "accountName": "10일 적금",

        "accountDescription": "10일 적금입니다",

        "withdrawalBankCode": "001",

        "withdrawalBankName": "한국은행",

        "withdrawalAccountNo": "032355504232351",

        "subscriptionPeriod": "10",

        "depositBalance": "100000",

        "interestRate": "5",

        "installmentNumber": "1",

        "totalBalance": "100000",

        "accountCreateDate": "20240328",

        "accountExpiryDate": "20240407"

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
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.6.6 적금 납입 회차 조회

#### 설명

가입한 적금 계좌의 납입 내역과 납입 회차를 상세 조회합니다.
적금 납입액 자동이체 출금은 가입기간에 따른 날짜 기준 오전 06:30에
출금 연결 계좌(수시입출금)에서 자동 출금됩니다.

자동이체로 납입된 내역을 확인할 수 있으며,
출금계좌의 잔액이 부족하여 납입되지 못한 경우
납입 상태와 실패사유로 확인할 수 있습니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquirePayment | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "inquirePayment",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquirePayment",

        "institutionTransactionUniqueNo": "20240101121212123456",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    },

    "accountNo":"0017675199"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 납입은행정보 |  |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| interestRate | 이자율 | Double |  | Y |  |
| depositBalance | 가입금액 | Long |  | Y |  |
| totalBalance | 누적납입금액 | Long |  | Y | 현재까지 누적된 납입된 금액 |
| accountCreateDate | 계좌 개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌 만기일 | String | 8 | Y |  |
| paymentInfo | 납입 회차 정보 | List |  | Y |  |
| depositInstallment | 입금회차 | String | 10 | Y |  |
| paymentBalance | 납입금액 | Long |  | Y |  |
| paymentDate | 납입일자 | String | 8 | Y |  |
| paymentTime | 납입시각 | String | 6 | Y |  |
| status | 상태 | String | 20 | Y | SUCCESS, FAIL |
| failureReason | 실패사유 | String | 255 | N |  |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquirePayment",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquirePayment",

        "institutionTransactionUniqueNo": "20240101121212123456"

    },

    "REC": [

        {

            "bankCode": "001",

            "bankName": "한국은행",

            "accountNo": "0017675199",

            "accountName": "7일 적금",

            "interestRate": "10",

            "depositBalance": "100000",

            "totalBalance": "100000",

            "accountCreateDate": "20240326",

            "accountExpiryDate": "20240402",

            "paymentInfo": [

                {

                    "depositInstallment": "1",

                    "paymentBalance": "100000",

                    "paymentDate": "20240324",

                    "paymentTime": "141506",

                    "status": "SUCCESS",

                    "failureReason": ""

                },

                {

                    "depositInstallment": "2",

                    "paymentBalance": "100000",

                    "paymentDate": "20240325",

                    "paymentTime": "095012",

                    "status": "SUCCESS",

                    "failureReason": ""

                },

                {

                    "depositInstallment": "3",

                    "paymentBalance": "100000",

                    "paymentDate": "20240326",

                    "paymentTime": "095012",

                    "status": "SUCCESS",

                    "failureReason": ""

                }

            ]

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
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.6.7 적금 만기 이자 조회

#### 설명

가입한 적금 계좌의 만기 이자를 조회합니다.
만기 시 해당 날짜 기준 오전 07:00에 출금 연결 계좌(수시입출금)로 자동 지급되며,
적금 계좌는 자동 해지됩니다.

만기이자 산출식:

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquireExpiryInterest | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "inquireExpiryInterest",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireExpiryInterest",

        "institutionTransactionUniqueNo": "20240101121212123456",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    },

    "accountNo":"0017675199"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 만기이자목록 |  |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| interestRate | 이자율 | Double |  | Y |  |
| accountCreateDate | 계좌 개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌 만기일 | String | 8 | Y |  |
| expiryBalance | 만기예정금액 | Long |  | Y | 최초 납입금액 * 가입 기간에 대한 만기 예정금액 |
| expiryInterest | 만기이자 | Long |  | Y | 만기 예정금액에 대한 이자 |
| expiryTotalBalance | 만기시 총금액 | Long |  | Y | 만기 예정금액과 만기 이자 합산 |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireExpiryInterest",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireExpiryInterest",

        "institutionTransactionUniqueNo": "20240101121212123456"

    },

    "REC": {

        "bankCode": "001",

        "bankName": "한국은행",

        "accountNo": "0017675199",

        "accountName": "7일 적금",

        "interestRate": "10",

        "accountCreateDate": "20240326",

        "accountExpiryDate": "20240402",

        "expiryBalance": "700000",

        "expiryInterest": "649",

        "expiryTotalBalance": "700649"

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
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.6.8 적금 중도 해지 이자 조회

#### 설명

가입한 적금 계좌의 중도 해지 이자를 조회합니다.
해지 예상일은 요청 날짜 기준으로 조회되며, 중도 해지 이자율은 만기 이자율과 동일합니다.

만기이자 산출식:

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquireEarlyTerminationInterest | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "inquireEarlyTerminationInterest",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireEarlyTerminationInterest",

        "institutionTransactionUniqueNo": "20240101121212123456",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    },

    "accountNo":"0017675199"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 중도해지조회 |  |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| interestRate | 이자율 | Double |  | Y |  |
| accountCreateDate | 계좌 개설일 | String | 8 | Y |  |
| earlyTerminationDate | 해지 예상일 | String | 8 | Y | 오늘 기준 |
| totalBalance | 해지 원금 | Long |  | Y | 납입 누적 금액 |
| earlyTerminationInterest | 중도해지이자 | Long |  | Y | 해지 원금에 대한 이자 |
| earlyTerminationBalance | 중도해지금액 | Long |  | Y | 해지 원금과 중도 해지 이자 합산 |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireEarlyTerminationInterest",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireEarlyTerminationInterest",

        "institutionTransactionUniqueNo": "20240101121212123456"

    },

    "REC": {

        "bankCode": "001",

        "bankName": "한국은행",

        "accountNo": "0017675199",

        "accountName": "7일 적금",

        "interestRate": "10",

        "accountCreateDate": "20240324",

        "earlyTerminationDate": "20240326",

        "totalBalance": "300000",

        "earlyTerminationInterest": "70",

        "earlyTerminationBalance": "300070"

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
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.6.9 적금 계좌 해지

#### 설명

가입한 적금 계좌를 중도 해지합니다.
적금 계좌는 계좌 목록에서 삭제되며, 납입한 원금과 이자를 합산한 금액이 자동으로 출금 계좌에 입금됩니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/deleteAccount | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 요청 메시지 형태

```json
{    

    "Header": {

        "apiName": "deleteAccount",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "deleteAccount",

        "institutionTransactionUniqueNo": "20240101121212123456",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

    },

    "accountNo":"0017675199"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 적금계좌해지 |  |  | Y |  |
| status | 상태 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountNo | 해지 계좌번호 | String | 16 | Y |  |
| accountName | 해지 상품명 | String | 20 | Y |  |
| totalBalance | 해지 원금 | Long |  | Y | 납입 누적 금액 |
| earlyTerminationInterest | 중도해지이자 | Long |  | Y | 해지 원금에 대한 이자 (세전) |
| earlyTerminationBalance | 중도해지금액 | Long |  | Y | 해지 원금과 중도해지이자 합산 (세전) |
| earlyTerminationDate | 중도해지일 | String | 8 | Y | 오늘 날짜 |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "deleteAccount",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "deleteAccount",

        "institutionTransactionUniqueNo": "20240101121212123456"

    },

    "REC": {

        "status": "CLOSED",

        "bankCode": "001",

        "bankName": "한국은행",

        "accountNo": "0017675199",

        "accountName": "7일 적금",

        "totalBalance": "100000",

        "earlyTerminationInterest": "70",

        "earlyTerminationBalance": "300000",

        "earlyTerminationDate": "300070"

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
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

