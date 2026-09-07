# 예금 API

- 제목: 예금
- 원문: https://project.ssafy.com/docs/ssafy-finance/api-deposit
- 크롤링 날짜: 2026-08-24
- 범위: 정적 문서 복사만 수행했으며 라이브 API 호출은 하지 않음.
- 요약: 예금 상품 등록·조회와 예금 계좌 생성·조회·거래·해지 API의 요청, 응답, 에러코드를 정리한 문서입니다.

## 2.5 예금

---

### 2.5.1 예금 상품 등록

#### 설명

은행별 예금 상품을 등록합니다. 은행코드를 조회하여 해당 은행의 예금 상품을 생성할 수 있습니다.
예금 상품 조회 API를 통해 샘플 데이터를 참고하여 상품을 등록할 수 있습니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/createDepositProduct | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | userKey 제외 |
| bankCode | 은행코드 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y | 예금 상품명 입력 (ex. 7일 예금) |
| accountDescription | 상품설명 | String | 20 | N | 예금 상품 설명 입력 (ex. 최대 10% 이자 지급) |
| subscriptionPeriod | 가입기간 | String | 20 | Y | 2 이상 ~ 365 이하 / 단위(일) |
| minSubscriptionBalance | 최소가입가능금액 | Long |  | Y | 1 이상 / 단위(원) |
| maxSubscriptionBalance | 최대가입가능금액 | Long |  | Y | 100000000(1억) 이하 / 단위(원) |
| interestRate | 이자율 | Double |  | Y | 0.1 이상 ~ 20 이하 / 단위(%) |
| rateDescription | 이자율 설명 | String | 255 | N |  |

#### 요청 메세지 형태

```json
{

     "Header": {

        "apiName": "createDepositProduct",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createDepositProduct",

        "institutionTransactionUniqueNo": "20240215121212123498",

        "apiKey": "<REDACTED>"

     },

    "bankCode": "002",

    "accountName": "특판 예금",

    "accountDescription": "선착순 특판 계좌",

    "subscriptionPeriod": "10",

    "minSubscriptionBalance": "200000",

    "maxSubscriptionBalance": "3000000",

    "interestRate": "15",

    "rateDescription": "이자 15프로 단기 가입"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 예금계좌정보 |  |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y | 1: 수시입출금, 2: 정기예금, 3: 정기적금, 4: 대출 |
| accountTypeName | 상품구분명 | String | 20 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| subscriptionPeriod | 가입기간 | String | 20 | Y |  |
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

        "apiName": "createDepositProduct",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "createDepositProduct",

        "institutionTransactionUniqueNo": "20240215121212123498"

    },

    "REC": {

        "accountTypeUniqueNo": "002-2-774f8e48",

        "bankCode": "002",

        "bankName": "산업은행",

        "accountTypeCode": "2",

        "accountTypeName": "정기예금",

        "accountName": "특판 예금",

        "accountDescription": "선착순 특판 계좌",

        "subscriptionPeriod": "10",

        "minSubscriptionBalance": "200000",

        "maxSubscriptionBalance": "3000000",

        "interestRate": "15",

        "rateDescription": "이자 15프로 단기 가입"

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
| A1035 | 가입금액은 1원 ~ 1억으로만 입력 가능합니다. |  |
| A1036 | 이자율은 0.1 ~ 20으로만 입력이 가능합니다. |  |
| A1040 | 최대가입가능금액은 최소가입가능금액보다 크거나 같아야 합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.5.2 예금 상품 조회

#### 설명

예금 상품 목록을 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositProducts | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | userKey 제외 |

#### 요청 메시지 형태

```json
{

     "Header": {

        "apiName": "inquireDepositProducts",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireDepositProducts",

        "institutionTransactionUniqueNo": "20240215121212123494",

        "apiKey": "<REDACTED>"

     }

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 예금상품목록 | List |  | N |  |
| accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountTypeCode | 상품구분코드 | String | 3 | Y |  |
| accountTypeName | 상품구분명 | String | 20 | Y | 1 : 수시입출금, 2: 정기예금, 3: 정기적금, 4: 대출 |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| subscriptionPeriod | 가입기간 | String | 20 | Y |  |
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

        "apiName": "inquireDepositProducts",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireDepositProducts",

        "institutionTransactionUniqueNo": "20240215121212123494"

    },

    "REC": [

        {

            "accountTypeUniqueNo": "002-2-d6cda5e000bb40",

            "bankCode": "002",

            "bankName": "산업은행",

            "accountTypeCode": "2",

            "accountTypeName": "정기예금",

            "accountName": "산업 단기 예금",

            "accountDescription": "단기 예금",

            "subscriptionPeriod": "20",

            "minSubscriptionBalance": "100000",

            "maxSubscriptionBalance": "3000000",

            "interestRate": "7.0",

            "rateDescription": "7% 이자"

        },

        {

            "accountTypeUniqueNo": "004-2-bafb564d",

            "bankCode": "004",

            "bankName": "국민은행",

            "accountTypeCode": "2",

            "accountTypeName": "정기예금",

            "accountName": "국민 한달 예금",

            "accountDescription": "한달 예금",

            "subscriptionPeriod": "30",

            "minSubscriptionBalance": "300000",

            "maxSubscriptionBalance": "5000000",

            "interestRate": "10.0",

            "rateDescription": "한달인데 이제 이자가 10%인"

        },

        {

            "accountTypeUniqueNo": "003-2-928e01fc",

            "bankCode": "003",

            "bankName": "기업은행",

            "accountTypeCode": "2",

            "accountTypeName": "정기예금",

            "accountName": "300일 예금",

            "accountDescription": "300일 동안 예금 들자",

            "subscriptionPeriod": "300",

            "minSubscriptionBalance": "500000",

            "maxSubscriptionBalance": "8000000",

            "interestRate": "7.0",

            "rateDescription": "300일 동안 7% 이자가?!"

        },

        {

            "accountTypeUniqueNo": "002-2-908de38e",

            "bankCode": "002",

            "bankName": "산업은행",

            "accountTypeCode": "2",

            "accountTypeName": "정기예금",

            "accountName": "90일 예금",

            "accountDescription": "90일 동안 예금 들자",

            "subscriptionPeriod": "100",

            "minSubscriptionBalance": "199999",

            "maxSubscriptionBalance": "9999999",

            "interestRate": "9.0",

            "rateDescription": "90일 동안 9% 이자가?!"

        },

        {

            "accountTypeUniqueNo": "002-2-774f8e48",

            "bankCode": "002",

            "bankName": "산업은행",

            "accountTypeCode": "2",

            "accountTypeName": "정기예금",

            "accountName": "특판 예금",

            "accountDescription": "선착순 특판 계좌",

            "subscriptionPeriod": "10",

            "minSubscriptionBalance": "100000",

            "maxSubscriptionBalance": "900000",

            "interestRate": "15.0",

            "rateDescription": "이자 15프로 단기 가입"

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

### 2.5.3 예금 계좌 생성

#### 설명

예금 계좌를 생성합니다. 사용자는 상품 고유번호를 통해 예금 계좌를 생성할 수 있습니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/createDepositAccount | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| withdrawalAccountNo | 출금계좌번호 | String | 20 | Y | 출금할 수시입출금 계좌번호 기입 |
| accountTypeUniqueNo | 상품고유번호 | String | 20 | Y | 가입할 예금 상품고유번호 기입 |
| depositBalance | 가입금액 | Long |  | Y | 가입할 예금의 가입 가능금액 범위 내 기입 |

#### 요청 메시지 형태

```json
{

     "Header": {

        "apiName": "createDepositAccount",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createDepositAccount",

        "institutionTransactionUniqueNo": "20240215121212123492",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

     },

     "withdrawalAccountNo": "0011541149756547",

     "accountTypeUniqueNo": "003-2-67718ffc",

     "depositBalance": "80000000"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 예금계좌정보 |  |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| withdrawalBankCode | 출금은행코드 | String | 3 | Y |  |
| withdrawalAccountNo | 출금은행계좌 | String | 16 | Y |  |
| subscriptionPeriod | 가입기간 | String | 20 | Y |  |
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

        "apiName": "createDepositAccount",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "createDepositAccount",

        "institutionTransactionUniqueNo": "20240215121212123492"

    },

    "REC": {

        "bankCode": "003",

        "bankName": "기업은행",

        "accountNo": "0038268358",

        "accountName": "청룡의 해 예금",

        "withdrawalBankCode": "001",

        "withdrawalAccountNo": "0011541149756547",

        "subscriptionPeriod": "3",

        "depositBalance": "80000000",

        "interestRate": "7.1",

        "accountCreateDate": "20240320",

        "accountExpiryDate": "20240323"

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
| H1007 | 기관거래고유번호가 유효하지 않습니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1014 | 계좌 잔액이 부족하여 거래가 실패했습니다. | 수시입출금 계좌의 잔액이 부족하여 발생 |
| A1023 | 상품고유번호가 유효하지 않습니다. |  |
| A1030 | 가입금액이 유효하지 않습니다. |  |
| A1037 | 해당 상품에 가입 가능한 금액이 아닙니다. | 가입금액이 가입 가능금액 범위에서 벗어나서 발생 |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.5.4 예금 계좌 목록 조회

#### 설명

사용자의 예금 계좌 목록 전체를 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositInfoList | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |

#### 요청 메시지 형태

```json
{

     "Header": {

        "apiName": "inquireDepositInfoList",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireDepositInfoList",

        "institutionTransactionUniqueNo": "20240215171212123492",

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
| REC | 예금계좌목록 | List |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| userName | 예금주명 | String | 50 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| withdrawalBankCode | 출금은행코드 | String | 3 | Y |  |
| withdrawalBankName | 출금은행명 | String | 20 | Y |  |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y |  |
| subscriptionPeriod | 가입 기간 | String | 20 | Y |  |
| depositBalance | 가입금액 | Long |  | Y |  |
| interestRate | 이자율 | Double |  | Y |  |
| accountCreateDate | 계좌 개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌 만기일 | String | 8 | Y |  |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireDepositInfoList",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireDepositInfoList",

        "institutionTransactionUniqueNo": "20240215171212123493"

    },

    "REC": {

        "totalCount": "4",

        "list": [

            {

                "bankCode": "003",

                "bankName": "기업은행",

                "userName": "customer",

                "accountNo": "0019169157",

                "accountName": "기업 단기 예금",

                "accountDescription": "단기 예금",

                "withdrawalBankCode": "001",

                "withdrawalBankName": "한국은행",

                "withdrawalAccountNo": "0011143384483418",

                "subscriptionPeriod": "20",

                "depositBalance": "3000000",

                "interestRate": "7.0",

                "accountCreateDate": "20240314",

                "accountExpiryDate": "20240403"

            },

            {

                "bankCode": "004",

                "bankName": "국민은행",

                "userName": "customer",

                "accountNo": "0019016181",

                "accountName": "국민 한달 예금",

                "accountDescription": "한달 예금",

                "withdrawalBankCode": "001",

                "withdrawalBankName": "한국은행",

                "withdrawalAccountNo": "0011541149756547",

                "subscriptionPeriod": "30",

                "depositBalance": "2500000",

                "interestRate": "10.0",

                "accountCreateDate": "20240315",

                "accountExpiryDate": "20240414"

            },

            {

                "bankCode": "002",

                "bankName": "산업은행",

                "userName": "customer",

                "accountNo": "0027341298",

                "accountName": "60일 예금",

                "accountDescription": "60일 동안 예금 들자",

                "withdrawalBankCode": "002",

                "withdrawalBankName": "산업은행",

                "withdrawalAccountNo": "0028889135848149",

                "subscriptionPeriod": "60",

                "depositBalance": "1000000",

                "interestRate": "9.0",

                "accountCreateDate": "20240318",

                "accountExpiryDate": "20240526"

            },

            {

                "bankCode": "001",

                "bankName": "한국은행",

                "userName": "customer",

                "accountNo": "0029812177",

                "accountName": "특판 예금",

                "accountDescription": "선착순 특판 계좌",

                "withdrawalBankCode": "002",

                "withdrawalBankName": "산업은행",

                "withdrawalAccountNo": "0028889135848149",

                "subscriptionPeriod": "10",

                "depositBalance": "500000",

                "interestRate": "15.0",

                "accountCreateDate": "20240319",

                "accountExpiryDate": "20240329"

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
| H1007 | 기관거래고유번호가 중복된 값입니다. |  |
| H1008 | API_KEY가 유효하지 않습니다. |  |
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

### 2.5.5 예금 계좌 조회(단건)

#### 설명

사용자의 특정 예금 계좌에 대한 정보를 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositInfoDetail | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 요청 메시지 형태

```json
{

     "Header": {

        "apiName": "inquireDepositInfoDetail",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireDepositInfoDetail",

        "institutionTransactionUniqueNo": "20240215121212123491",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

     },

     "accountNo": "0019016181"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 예금계좌정보 |  |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| userName | 예금주명 | String | 50 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| accountDescription | 상품설명 | String | 255 | N |  |
| withdrawalBankCode | 출금은행코드 | String | 3 | Y |  |
| withdrawalBankName | 출금은행명 | String | 20 | Y |  |
| withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y |  |
| subscriptionPeriod | 가입 기간 | String | 20 | Y |  |
| depositBalance | 가입금액 | Long |  | Y |  |
| interestRate | 이자율 | Double |  | Y |  |
| accountCreateDate | 계좌 개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌 만기일 | String | 8 | Y |  |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireDepositInfoDetail",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireDepositInfoDetail",

        "institutionTransactionUniqueNo": "20240215121212123491"

    },

    "REC": {

        "bankCode": "004",

        "bankName": "국민은행",

        "userName": "customer",

        "accountNo": "0019016181",

        "accountName": "국민 한달 예금",

        "accountDescription": "한달 예금",

        "withdrawalBankCode": "001",

        "withdrawalBankName": "한국은행",

        "withdrawalAccountNo": "0011541149756547",

        "subscriptionPeriod": "30",

        "depositBalance": "2500000",

        "interestRate": "10.0",

        "accountCreateDate": "20240315",

        "accountExpiryDate": "20240414"

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

### 2.5.6 예금 납입 상세 조회

#### 설명

가입한 예금 계좌의 납입 내역을 상세 조회합니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositPayment | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 요청 메시지 형태

```json
{

     "Header": {

        "apiName": "inquireDepositPayment",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireDepositPayment",

        "institutionTransactionUniqueNo": "20240215121212123489",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

     },

     "accountNo": "0019169157"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 예금납입내역 |  |  | Y |  |
| paymentUniqueNo | 납입 고유번호 | String |  | Y |  |
| paymentDate | 납입일자 | String | 8 | Y |  |
| paymentTime | 납입시각 | String | 6 | Y |  |
| paymentBalance | 납입금액 | Long |  | Y |  |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireDepositPayment",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireDepositPayment",

        "institutionTransactionUniqueNo": "20240215121212123489"

    },

    "REC": {

        "paymentUniqueNo": "1",

        "paymentDate": "20240314",

        "paymentTime": "173950",

        "paymentBalance": "3000000"

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

### 2.5.7 예금 만기 이자 조회

#### 설명

가입한 예금 계좌의 만기 이자를 조회합니다.
만기 시 해당 날짜 기준 오전 07:00 출금 연결 계좌(수시입출금)로 자동 지급되며,
예금 계좌는 자동 해지됩니다.

이자 산출식:

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositExpiryInterest | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 요청 메시지 형태

```json
{

     "Header": {

        "apiName": "inquireDepositExpiryInterest",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireDepositExpiryInterest",

        "institutionTransactionUniqueNo": "20240215121212123498",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

     },

     "accountNo": "0024379394"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC |  |  |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| interestRate | 이자율 | Double |  | Y |  |
| accountCreateDate | 계좌 개설일 | String | 8 | Y |  |
| accountExpiryDate | 계좌 만기일 | String | 8 | Y |  |
| expiryBalance | 만기예정금액 | Long |  | Y | 납입원금 |
| expiryInterest | 만기이자 | Long |  | Y | 만기 예정금액에 대한 이자 |
| expiryTotalBalance | 만기시 총금액 | Long |  | Y | 만기예정금액과 만기이자 합산 |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireDepositExpiryInterest",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireDepositExpiryInterest",

        "institutionTransactionUniqueNo": "20240215121212123498"

    },

    "REC": {

        "bankCode": "002",

        "bankName": "산업은행",

        "accountNo": "0024379394",

        "accountName": "90일 예금",

        "interestRate": "9.0",

        "accountCreateDate": "20240318",

        "accountExpiryDate": "20240626",

        "expiryBalance": "1000000",

        "expiryInterest": "20860",

        "expiryTotalBalance": "1020860"

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

### 2.5.8 예금 중도 해지 이자 조회

#### 설명

가입한 예금 계좌의 중도 해지 이자를 조회합니다.
해지 예상일은 요청 날짜 기준으로 조회되며, 중도 해지 이자율은 만기 이자율과 동일합니다.

만기이자 산출식:

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositEarlyTerminationInterest | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 요청 메시지 형태

```json
{

     "Header": {

        "apiName": "inquireDepositEarlyTerminationInterest",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireDepositEarlyTerminationInterest",

        "institutionTransactionUniqueNo": "20240215121212123498",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

     },

     "accountNo": "0024379394"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC |  |  |  | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| accountName | 상품명 | String | 20 | Y |  |
| interestRate | 이자율 | Double |  | Y |  |
| accountCreateDate | 계좌 개설일 | String |  | Y |  |
| earlyTerminationDate | 해지 예상일 | String | 8 | Y | 오늘 기준 |
| depositBalance | 해지 원금 | Long |  | Y | 납입 원금 |
| earlyTerminationInterest | 중도해지이자 | Long |  | Y | 해지 원금에 대한 이자 |
| earlyTerminationBalance | 중도해지금액 | Long |  | Y | 해지 원금과 중도 해지 이자 합산 |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireDepositEarlyTerminationInterest",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "inquireDepositEarlyTerminationInterest",

        "institutionTransactionUniqueNo": "20240215121212123498"

    },

    "REC": {

        "bankCode": "002",

        "bankName": "산업은행",

        "accountNo": "0024379394",

        "accountName": "90일 예금",

        "interestRate": "9.0",

        "accountCreateDate": "20240318",

        "earlyTerminationDate": "20240319",

        "depositBalance": "1000000",

        "earlyTerminationInterest": "209",

        "earlyTerminationBalance": "1000209"

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

### 2.5.9 예금 계좌 해지

#### 설명

가입한 예금 계좌를 중도 해지합니다.
예금 계좌는 계좌 목록에서 삭제되며, 납입한 원금과 이자를 합산한 금액이 자동으로 출금 계좌에 입금됩니다.

#### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/deleteDepositAccount | POST |

#### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |

#### 요청 메시지 형태

```json
{

     "Header": {

        "apiName": "deleteDepositAccount",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "deleteDepositAccount",

        "institutionTransactionUniqueNo": "20240215121212123498",

        "apiKey": "<REDACTED>",

        "userKey": "<REDACTED>"

     },

     "accountNo": "0011347488"

}
```

#### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC |  |  |  | Y |  |
| status | 상태 | String | 20 | Y |  |
| bankCode | 은행코드 | String | 3 | Y |  |
| bankName | 은행명 | String | 20 | Y |  |
| accountNo | 해지 계좌번호 | String | 16 | Y |  |
| accountName | 해지 상품명 | String | 20 | Y |  |
| depositBalance | 해지 원금 | Long |  | Y | 납입 원금 |
| earlyTerminationInterest | 중도해지이자 | Long |  | Y | 해지 원금에 대한 이자 |
| earlyTerminationBalance | 중도해지금액 | Long |  | Y | 해지 원금과 중도 해지 이자 합산 |
| earlyTerminationDate | 중도해지일 | String | 8 | Y | 오늘 날짜 |

#### 응답 메세지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "deleteDepositAccount",

        "transmissionDate": "20240101",

        "transmissionTime": "121212",

        "institutionCode": "00100",

        "apiKey": "<REDACTED>",

        "apiServiceCode": "deleteDepositAccount",

        "institutionTransactionUniqueNo": "20240215121212123498"

    },

    "REC": {

        "status": "CLOSED",

        "bankCode": "004",

        "bankName": "국민은행",

        "accountNo": "0011347488",

        "accountName": "국민 한달 예금",

        "depositBalance": "2700270",

        "earlyTerminationInterest": "2503",

        "earlyTerminationBalance": "2702773",

        "earlyTerminationDate": "20240319"

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

