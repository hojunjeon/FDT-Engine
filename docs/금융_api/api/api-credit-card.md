# SSAFY 금융망 — 카드 API

- Source: https://project.ssafy.com/docs/ssafy-finance/api-credit-card
- Crawled: 2026-08-24
- Scope: Read-only document crawl; no live API calls, authentication, or financial data changes were performed.
- Summary: Visible article content covers card-category, merchant, card-company, card-product, issuance, inquiry, payment, and related card operations, with request/response schemas and error-code tables.

# 카드

### 2.8 카드

---

#### 2.8.1 카테고리 조회

##### 설명

가맹점 등록을 위한 카테고리를 조회하는 API 입니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireCategoryList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "inquireCategoryList",

        "transmissionDate": "20240409",

        "transmissionTime": "094600",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireCategoryList",

        "institutionTransactionUniqueNo": "20240215121212123555",

        "apiKey": "<REDACTED_API_KEY>"

    }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 신용등급 정보 |  |  | Y |  |
| categoryId | 카테고리ID | String | 20 | Y |  |
| categoryName | 카테고리명 | String | 255 | Y |  |
| categoryDescription | 카테고리 설명 | String | 255 | N |  |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireCategoryList",

        "transmissionDate": "20240409",

        "transmissionTime": "094600",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireCategoryList",

        "institutionTransactionUniqueNo": "20240215121212123555"

    },

    "REC": [

        {

            "categoryId": "CG-3fa85f6425e811e",

            "categoryName": "주유",

            "categoryDescription": ""

        },

        {

            "categoryId": "CG-4fa85f6425ad1d3",

            "categoryName": "대형마트",

            "categoryDescription": ""

        },

        {

            "categoryId": "CG-4fa85f6455cad4a",

            "categoryName": "교통",

            "categoryDescription": "(버스, 지하철, 택시)"

        },

        {

            "categoryId": "CG-6dd85f6425ez11o",

            "categoryName": "교육/육아",

            "categoryDescription": ""

        },

        {

            "categoryId": "CG-7fa85f6425bc311",

            "categoryName": "통신",

            "categoryDescription": "(전화요금, 인터넷 이용료, 케이블TV 업종)"

        },

        {

            "categoryId": "CG-8fa85f6425e1123",

            "categoryName": "해외",

            "categoryDescription": "(해외직구)"

        },

        {

            "categoryId": "CG-9ca85f66311a23d",

            "categoryName": "생활",

            "categoryDescription": "(음식점, 커피전문점, 편의점, 약국 ..)"

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

#### 2.8.2 가맹점 등록

##### 설명

카테고리 조회 후 가맹점을 등록합니다.

카테고리 하위로 다양한 가맹점을 생성할 수 있으며,

추후 등록된 가맹점 목록 내에서 카드 결제를 할 수 있습니다.

가맹점 목록 조회 API를 통해 샘플 데이터를 참고하여 가맹점을 등록할 수 있습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createMerchant | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |
| categoryId | 카테고리ID | String | 20 | Y |  |
| merchantName | 가맹점명 | String | 100 | Y | 카테고리에 맞는 가맹점명 입력 (ex. 이마트, 에쓰오일, 지하철 등) |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "createMerchant",

        "transmissionDate": "20240409",

        "transmissionTime": "094800",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createMerchant",

        "institutionTransactionUniqueNo": "20240215121212123553",

        "apiKey": "<REDACTED_API_KEY>"

    },

    "categoryId": "CG-4fa85f6425ad1d3",

    "merchantName": "코스트코"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC |  | List |  | Y |  |
| categoryId | 카테고리ID | String | 20 | Y |  |
| categoryName | 카테고리명 | String | 255 | Y |  |
| merchantId | 가맹점ID | Long |  | Y |  |
| merchantName | 가맹점명 | String | 100 | Y |  |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "createMerchant",

        "transmissionDate": "20240409",

        "transmissionTime": "094800",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "createMerchant",

        "institutionTransactionUniqueNo": "20240215121212123553"

    },

    "REC": [

        {

            "categoryId": "CG-9ca85f66311a23d",

            "categoryName": "생활",

            "merchantId": "1",

            "merchantName": "스타벅스"

        },

        {

            "categoryId": "CG-4fa85f6455cad4a",

            "categoryName": "교통",

            "merchantId": "2",

            "merchantName": "지하철"

        },

        {

            "categoryId": "CG-4fa85f6425ad1d3",

            "categoryName": "대형마트",

            "merchantId": "3",

            "merchantName": "코스트코"

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
| A1042 | 카테고리 ID가 유효하지 않습니다. |  |
| A1043 | 가맹점명이 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.8.3 카드사 조회

##### 설명

카드 상품 등록 시 필요한 카드사를 조회하는 API 입니다.

카드사를 조회하여 각 카드 상품을 만들 수 있습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireCardIssuerCodesList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "inquireCardIssuerCodesList",

        "transmissionDate": "20240409",

        "transmissionTime": "095900",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireCardIssuerCodesList",

        "institutionTransactionUniqueNo": "20240215121212123553",

        "apiKey": "<REDACTED_API_KEY>"

    }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC |  | List |  | Y |  |
| cardIssuerCode | 카드사코드 | String | 4 | Y |  |
| cardIssuerName | 카드사명 | String | 20 | Y |  |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireCardIssuerCodesList",

        "transmissionDate": "20240409",

        "transmissionTime": "095900",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireCardIssuerCodesList",

        "institutionTransactionUniqueNo": "20240215121212123553"

    },

    "REC": [

        {

            "cardIssuerCode": "1001",

            "cardIssuerName": "KB국민카드"

        },

        {

            "cardIssuerCode": "1002",

            "cardIssuerName": "삼성카드"

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

#### 2.8.4 카드 상품 등록

##### 설명

카드사별 카드 상품을 등록합니다.

카테고리별 카드 혜택을 설정하여 추후 실적에 따라 금액을 할인받을 수 있습니다.

카드 혜택은 반드시 하나 이상 지정되어야 하며, 기준실적이 0일 경우 조건 없이 혜택이 적용됩니다.

카드 상품 조회 API를 통해 샘플 데이터를 참고하여 상품을 등록할 수 있습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createCreditCardProduct | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |
| cardIssuerCode | 카드사코드 | String | 4 | Y |  |
| cardName | 카드명 | String | 20 | Y | 카드 상품명 입력 (ex. 트래블플러스 카드, 교통할인카드 등) |
| baselinePerformance | 기준실적 | Long |  | Y | 카드 혜택을 받기 위한 전월 기준실적 (0 이상 200만원 이하) |
| maxBenefitLimit | 최대 혜택한도 | Long |  | Y | 할인받을 수 있는 총 금액 한도 (1 이상 100만원 이하) |
| cardDescription | 카드설명 | String | 255 | N | 카드 설명 입력 (ex. 마트 최대 20% 할인, 주유 할인 등) |
| cardBenefits | 카드 혜택 | List |  | Y | 카테고리 여러 개 입력 가능 |
| categoryId | 카테고리ID | String | 40 | Y |  |
| discountRate | 할인율 | Double |  | Y | 3 ~ 50 사이로 입력 가능 / 단위(%) |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "createCreditCardProduct",

        "transmissionDate": "20240409",

        "transmissionTime": "095900",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createCreditCardProduct",

        "institutionTransactionUniqueNo": "20240215121212123579",

        "apiKey": "<REDACTED_API_KEY>"

    },

    "cardIssuerCode": "1003",

    "cardName": "디지로카 London",

    "baselinePerformance": "700000",

    "maxBenefitLimit": "130000",

    "cardDescription": "생활 20%할인, 교통 10% 할인, 대형마트 5% 할인",

    "cardBenefits": [

        {

            "categoryId": "CG-9ca85f66311a23d",

            "discountRate": "20"

        },

        {

            "categoryId": "CG-4fa85f6455cad4a",

            "discountRate": "10"

        },

        {

            "categoryId": "CG-4fa85f6425ad1d3",

            "discountRate": "5"

        }

    ] 

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC |  |  |  | Y |  |
| cardUniqueNo | 카드 고유번호 | String | 20 | Y |  |
| cardIssuerCode | 카드사코드 | String | 4 | Y |  |
| cardIssuerName | 카드사명 | String | 20 | Y |  |
| cardName | 카드명 | String | 100 | Y |  |
| cardTypeCode | 카드종류 코드 | String | 3 | Y | 1 : 신용카드 |
| cardTypeName | 카드종류 코드명 | String | 4 | Y | 현재 신용카드만 가능 |
| baselinePerformance | 기준실적 | Long |  | Y |  |
| maxBenefitLimit | 최대 혜택한도 | Long |  | Y |  |
| cardDescription | 카드설명 | String | 255 | N |  |
| cardBenefitsInfo | 카드 혜택 정보 | List |  | Y |  |
| categoryId | 카테고리ID | String | 40 | Y |  |
| categoryName | 카테고리명 | String | 255 | Y |  |
| discountRate | 할인율 | Double |  | Y |  |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "createCreditCardProduct",

        "transmissionDate": "20240409",

        "transmissionTime": "095900",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "createCreditCardProduct",

        "institutionTransactionUniqueNo": "20240215121212123579"

    },

    "REC": {


        "cardUniqueNo": "1003-a139e9f23f1a4cc",

        "cardIssuerCode": "1003",

        "cardIssuerName": "롯데카드",

        "cardName": "디지로카 London",

        "cardTypeCode": "1",

        "cardTypeName": "신용카드",

        "baselinePerformance": "700000",

        "maxBenefitLimit": "130000",

        "cardDescription": "생활 20%할인",

        "cardBenefitsInfo": [

            {

                "categoryId": "CG-9ca85f66311a23d",

                "categoryName": "생활",

                "discountRate": "20.0"

            },

            {

                "categoryId": "CG-4fa85f6455cad4a",

                "categoryName": "교통",

                "discountRate": "10.0"

            },

            {

                "categoryId": "CG-4fa85f6425ad1d3",

                "categoryName": "대형마트",

                "discountRate": "5.0"

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
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1042 | 카테고리 ID가 유효하지 않습니다. |  |
| A1044 | 카드사 코드가 유효하지 않습니다. |  |
| A1045 | 카드명이 유효하지 않습니다. |  |
| A1046 | 기준실적이 유효하지 않습니다. |  |
| A1047 | 최대혜택한도가 유효하지 않습니다. |  |
| A1050 | 할인율은 3 ~ 50으로만 입력이 가능합니다. |  |
| A1065 | 카드 혜택이 입력되어야 합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.8.5 카드 상품 조회

##### 설명

카드사별 카드 상품을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireCreditCardList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "inquireCreditCardList",

        "transmissionDate": "20240409",

        "transmissionTime": "100100",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireCreditCardList",

        "institutionTransactionUniqueNo": "20240215121212123553",

        "apiKey": "<REDACTED_API_KEY>"

    }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 카드 상품 리스트 |  |  | Y |  |
| cardUniqueNo | 카드 고유번호 | String | 20 | Y |  |
| cardIssuerCode | 카드사코드 | String | 4 | Y |  |
| cardIssuerName | 카드사명 | String | 20 | Y |  |
| cardName | 카드명 | String | 100 | Y |  |
| cardTypeCode | 카드종류 코드 | String | 3 | Y | 1 : 신용카드 |
| cardTypeName | 카드종류 코드명 | String | 4 | Y | 현재 신용카드만 등록 가능 |
| baselinePerformance | 기준실적 | Long |  | Y |  |
| maxBenefitLimit | 최대 혜택한도 | Long |  | Y |  |
| cardDescription | 카드설명 | String | 255 | N |  |
| cardBenefitsInfo | 카드 혜택 정보 | List |  | Y |  |
| categoryId | 카테고리ID | String | 40 | Y |  |
| categoryName | 카테고리명 | String | 255 | Y |  |
| discountRate | 할인율 | Double |  | Y |  |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireCreditCardList",

        "transmissionDate": "20240409",

        "transmissionTime": "100100",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireCreditCardList",

        "institutionTransactionUniqueNo": "20240215121212123553"

    },

    "REC": [

        {

            "cardUniqueNo": "1003-a139e9f23f1a4cc",

            "cardIssuerCode": "1003",

            "cardIssuerName": "롯데카드",

            "cardName": "디지로카 London",

            "cardTypeCode": "1",

            "cardTypeName": "신용카드",

            "baselinePerformance": "700000",

            "maxBenefitLimit": "130000",

            "cardDescription": "생활 20%할인, 교통 10% 할인, 대형마트 5% 할인",

            "cardBenefitsInfo": [

                {

                    "categoryId": "CG-9ca85f66311a23d",

                    "categoryName": "생활",

                    "discountRate": "20.0"

                },

                {

                    "categoryId": "CG-4fa85f6455cad4a",

                    "categoryName": "교통",

                    "discountRate": "10.0"

                },

                {

                    "categoryId": "CG-4fa85f6425ad1d3",

                    "categoryName": "대형마트",

                    "discountRate": "5.0"

                }

            ]

        },

        {

            "cardUniqueNo": "1005-2d29fc2343024a4",

            "cardIssuerCode": "1005",

            "cardIssuerName": "신한카드",

            "cardName": "신한 TRAVEL 카드",

            "cardTypeCode": "1",

            "cardTypeName": "신용카드",

            "baselinePerformance": "100000",

            "maxBenefitLimit": "100000",

            "cardDescription": "해외 결제시 15% 할인",

            "cardBenefitsInfo": [

                {

                    "categoryId": "CG-8fa85f6425e1123",

                    "categoryName": "해외",

                    "discountRate": "15.0"

                }

            ]

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

#### 2.8.6 카드 생성

##### 설명

카드를 생성합니다.

카드 상품을 조회한 사용자는 카드 고유번호를 통해 카드를 생성할 수 있습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |

| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createCreditCard | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| cardUniqueNo | 카드 고유번호 | String | 20 | Y |  |
| withdrawalAccountNo | 출금계좌번호 | String | 16 | Y | 수시입출금 계좌 (카드대금 지급 계좌) |
| withdrawalDate | 출금날짜 | String | 10 | Y | 월: 1, 화: 2, 수: 3, 목: 4, 금: 5, 토: 6, 일: 7 |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "createCreditCard",

        "transmissionDate": "20240409",

        "transmissionTime": "103500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createCreditCard",

        "institutionTransactionUniqueNo": "20240215121212123556",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "cardUniqueNo": "1003-a139e9f23f1a4cc",

    "withdrawalAccountNo": "032355504232351",

    "withdrawalDate": "4"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 카드 생성 정보 |  |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| cvc | 카드보안코드 | String | 3 | Y |  |
| cardUniqueNo | 카드 고유번호 | String | 20 | Y |  |
| cardIssuerCode | 카드사코드 | String | 4 | Y |  |
| cardIssuerName | 카드사명 | String | 20 | Y |  |
| cardName | 카드명 | String | 100 | Y |  |
| baselinePerformance | 기준실적 | Long |  | Y |  |
| maxBenefitLimit | 최대 혜택한도 | Long |  | Y |  |
| cardDescription | 카드설명 | String | 255 | N |  |
| cardExpiryDate | 카드만료일 | String | 8 | Y | 개설일 + 5년 |
| withdrawalAccountNo | 출금계좌번호 | String | 16 | Y |  |
| withdrawalDate | 출금날짜 | String | 10 | Y | 월: 1, 화: 2, 수: 3, 목: 4, 금: 5, 토: 6, 일: 7 |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "createCreditCard",

        "transmissionDate": "20240409",

        "transmissionTime": "103500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "createCreditCard",

        "institutionTransactionUniqueNo": "20240215121212123556"

    },

    "REC": {

        "cardNo": "1003622654847049",

        "cvc": "713",

        "cardUniqueNo": "1003-a139e9f23f1a4cc",

        "cardIssuerCode": "1003",

        "cardIssuerName": "롯데카드",

        "cardName": "디지로카 SEOUL",

        "baselinePerformance": "0",

        "maxBenefitLimit": "200000",

        "cardDescription": "생활 20%할인",

        "cardExpiryDate": "20290409",

        "withdrawalAccountNo": "032355504232351",

        "withdrawalDate": "4"

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
| A1019 | 없는 상품입니다. 상품 조회를 다시 확인해주세요. |  |
| A1051 | 카드 고유번호가 유효하지 않습니다. |  |
| A1052 | 출금날짜가 유효하지 않습니다. |  |
| A1053 | 출금날짜는 1 ~ 7 로만 입력 가능합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.8.7 내 카드 목록 조회

##### 설명

사용자의 카드 목록 전체를 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireSignUpCreditCardList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "inquireSignUpCreditCardList",

        "transmissionDate": "20240409",

        "transmissionTime": "103600",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireSignUpCreditCardList",

        "institutionTransactionUniqueNo": "20240215121212123557",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 카드 목록 정보 |  |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| cvc | 카드보안코드 | String | 3 | Y |  |
| cardUniqueNo | 카드 고유번호 | String | 20 | Y |  |
| cardIssuerCode | 카드사코드 | String | 4 | Y |  |
| cardIssuerName | 카드사명 | String | 20 | Y |  |
| cardName | 카드명 | String | 100 | Y |  |
| baselinePerformance | 기준실적 | Long |  | Y |  |
| maxBenefitLimit | 최대 혜택한도 | Long |  | Y |  |
| cardDescription | 카드설명 | String | 255 | N |  |
| cardExpiryDate | 카드만료일 | String | 8 | Y | 개설일 + 5년 |
| withdrawalAccountNo | 출금계좌번호 | String | 16 | Y |  |
| withdrawalDate | 출금날짜 | String | 10 | Y | 월: 1, 화: 2, 수: 3, 목: 4, 금: 5, 토: 6, 일: 7 |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireSignUpCreditCardList",

        "transmissionDate": "20240409",

        "transmissionTime": "103600",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireSignUpCreditCardList",

        "institutionTransactionUniqueNo": "20240215121212123557"

    },

    "REC": [

        {

            "cardNo": "1003198565339181",

            "cvc": "149",

            "cardUniqueNo": "1003-a139e9f23f1a4cc",

            "cardIssuerCode": "1003",

            "cardIssuerName": "롯데카드",

            "cardName": "디지로카 SEOUL",

            "baselinePerformance": "0",

            "maxBenefitLimit": "200000",

            "cardDescription": "생활 20%할인",

            "cardExpiryDate": "20290409",

            "withdrawalAccountNo": "032355504232351",

            "withdrawalDate": "4"

        },

        {

            "cardNo": "1005518816096479",


            "cvc": "725",

            "cardUniqueNo": "1005-992db475fbb944c",

            "cardIssuerCode": "1005",

            "cardIssuerName": "신한카드",

            "cardName": "신한 TRAVEL 카드",

            "baselinePerformance": "100000",

            "maxBenefitLimit": "100000",

            "cardDescription": "해외 결제시 15% 할인",

            "cardExpiryDate": "20290403",

            "withdrawalAccountNo": "032355504232351",

            "withdrawalDate": "1"

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

#### 2.8.8 가맹점 목록 조회

##### 설명

카드 결제에 필요한 가맹점 목록을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireMerchantList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y | `userKey` 제외 |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "inquireMerchantList",

        "transmissionDate": "20240408",

        "transmissionTime": "135600",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireMerchantList",

        "institutionTransactionUniqueNo": "20240215121212123551",

        "apiKey": "<REDACTED_API_KEY>"

    }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 가맹점목록 | List |  | Y |  |
| categoryId | 카테고리ID | String | 20 | Y |  |
| categoryName | 카테고리명 | String | 255 | Y |  |
| merchantId | 가맹점ID | Long |  | Y |  |
| merchantName | 가맹점명 | String | 100 | Y |  |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireMerchantList",

        "transmissionDate": "20240408",

        "transmissionTime": "135600",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireMerchantList",

        "institutionTransactionUniqueNo": "20240215121212123551"

    },

    "REC": [

        {

            "categoryId": "CG-4fa85f6425ad1d3",

            "categoryName": "대형마트",

            "merchantId": "1",

            "merchantName": "코스트코"

        },

        {

            "categoryId": "CG-4fa85f6425ad1d3",

            "categoryName": "대형마트",

            "merchantId": "2",

            "merchantName": "홈플러스"

        },

        {

            "categoryId": "CG-8fa85f6425e1123",

            "categoryName": "해외",

            "merchantId": "3",

            "merchantName": "알리 익스프레스"

        },

        {

            "categoryId": "CG-8fa85f6425e1123",

            "categoryName": "해외",

            "merchantId": "4",

            "merchantName": "아마존 익스프레스"

        },

        {

            "categoryId": "CG-7fa85f6425bc311",

            "categoryName": "통신",

            "merchantId": "5",

            "merchantName": "SKT"

        },

        {

            "categoryId": "CG-7fa85f6425bc311",

            "categoryName": "통신",

            "merchantId": "6",

            "merchantName": "LG 유플러스"

        },

        {

            "categoryId": "CG-9ca85f66311a23d",

            "categoryName": "생활",

            "merchantId": "7",

            "merchantName": "스타벅스"

        },

        {

            "categoryId": "CG-9ca85f66311a23d",

            "categoryName": "생활",

            "merchantId": "8",

            "merchantName": "김밥천국"

        },

        {

            "categoryId": "CG-9ca85f66311a23d",

            "categoryName": "생활",

            "merchantId": "9",

            "merchantName": "뚜레쥬르"

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

#### 2.8.9 카드 결제

##### 설명

조회한 가맹점에서 카드 결제합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createCreditCardTransaction | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| cvc | 카드보안코드 | String | 3 | Y |  |
| merchantId | 가맹점ID | Long |  | Y |  |
| paymentBalance | 거래금액 | Long |  | Y |  |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "createCreditCardTransaction",

        "transmissionDate": "20240408",

        "transmissionTime": "135600",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "createCreditCardTransaction",

        "institutionTransactionUniqueNo": "20240215121212123571",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "cardNo": "1005518816096479",

    "cvc": "725",

    "merchantId": "1",

    "paymentBalance": "500000"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC |  |  |  | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| categoryId | 카테고리ID | String | 20 | Y |  |

| categoryName | 카테고리명 | String | 255 | Y |  |
| merchantId | 가맹점ID | Long |  | Y |  |
| merchantName | 가맹점명 | String | 100 | Y |  |
| transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |
| transactionTime | 거래시각 | String | 6 | Y | HHMMSS |
| paymentBalance | 거래금액 | Long |  | Y |  |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "createCreditCardTransaction",

        "transmissionDate": "20240408",

        "transmissionTime": "135600",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "createCreditCardTransaction",

        "institutionTransactionUniqueNo": "20240215121212123571"

    },

    "REC": {

        "transactionUniqueNo": "12",

        "categoryId": "CG-4fa85f6425ad1d3",

        "categoryName": "대형마트",

        "merchantId": "1",

        "merchantName": "코스트코",

        "transactionDate": "20240408",

        "transactionTime": "135242",

        "paymentBalance": "500000"

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
| H1009 | USER_KEY가 유효하지 않습니다. |  |
| H1010 | 기관거래고유번호가 유효하지 않습니다. |  |
| A1054 | 카드번호가 유효하지 않습니다. |  |
| A1055 | CVC 번호가 유효하지 않습니다. |  |
| A1056 | 가맹점 ID가 유효하지 않습니다. |  |
| A1057 | 결제 금액이 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.8.10 카드 결제 내역 조회

##### 설명

카드 결제한 내역을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireCreditCardTransactionList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| cvc | 카드보안코드 | String | 3 | Y |  |
| startDate | 조회 시작일자 | String | 8 | Y | YYYYMMDD |
| endDate | 조회 종료일자 | String | 8 | Y | YYYYMMDD |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "inquireCreditCardTransactionList",

        "transmissionDate": "20240418",

        "transmissionTime": "131500",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireCreditCardTransactionList",

        "institutionTransactionUniqueNo": "20240215121212123507",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "cardNo": "1005518816096479",

    "cvc": "725",

    "startDate": "20240401",

    "endDate": "20240502"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 결제 내역 정보 |  |  | Y |  |
| cardIssuerCode | 카드사코드 | String | 4 | Y |  |
| cardIssuerName | 카드사명 | String | 20 | Y |  |
| cardName | 카드명 | String | 100 | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| estimatedBalance | 청구예정금액 | Long |  | Y |  |
| transactionList | 카드거래내역 | List |  | Y |  |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireCreditCardTransactionList",

        "transmissionDate": "20240418",

        "transmissionTime": "131500",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireCreditCardTransactionList",

        "institutionTransactionUniqueNo": "20240215121212123507"

    },

    "REC": {

        "cardIssuerCode": "1005",

        "cardIssuerName": "신한카드",

        "cardName": "신한 TRAVEL 카드",

        "cardNo": "1005518816096479",

        "estimatedBalance": "2000000",

        "transactionList": [

            {

                "transactionUniqueNo": "20",

                "categoryId": "CG-3fa85f6425e811e",

                "categoryName": "주유",

                "merchantId": "1",

                "merchantName": "SK 에너지",

                "transactionDate": "20240418",

                "transactionTime": "094431",

                "transactionBalance": "1000000",

                "cardStatus": "승인",

                "billStatementsYn": "N",

                "billStatementsStatus": "미결제"

            },

            {

                "transactionUniqueNo": "19",

                "categoryId": "CG-3fa85f6425e811e",

                "categoryName": "주유",

                "merchantId": "1",

                "merchantName": "SK 에너지",

                "transactionDate": "20240418",

                "transactionTime": "094421",

                "transactionBalance": "500000",

                "cardStatus": "승인",

                "billStatementsYn": "N",

                "billStatementsStatus": "미결제"

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
| A1004 | 조회 시작일자가 유효하지 않습니다. |  |
| A1005 | 조회 종료일자가 유효하지 않습니다. |  |
| A1054 | 카드번호가 유효하지 않습니다. |  |
| A1055 | CVC 번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1000 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.8.11 카드 결제 취소

##### 설명

거래 고유번호를 이용하여 결제를 취소합니다.

**청구서가 발행된 거래의 경우 취소가 불가합니다.**

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/deleteTransaction | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |

| Header | 공통 |  |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| cvc | 카드보안코드 | String | 3 | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "deleteTransaction",

        "transmissionDate": "20240408",

        "transmissionTime": "140200",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "deleteTransaction",

        "institutionTransactionUniqueNo": "20240215121212123561",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "cardNo": "1005518816096479",

    "cvc": "725",

    "transactionUniqueNo": "33"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 카드 취소 내역 |  |  | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| categoryId | 카테고리ID | String | 20 | Y |  |
| categoryName | 카테고리명 | String | 255 | Y |  |
| merchantId | 가맹점ID | Long |  | Y |  |
| merchantName | 가맹점명 | String | 100 | Y |  |
| transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |
| transactionTime | 거래시각 | String | 6 | Y | HHMMSS |
| transactionBalance | 거래금액 | Long |  | Y |  |
| status | 청구금액 결제 상태 | String | 20 | Y | CANCEL (취소) |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "deleteTransaction",

        "transmissionDate": "20240408",

        "transmissionTime": "161900",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "deleteTransaction",

        "institutionTransactionUniqueNo": "20240215121212123563"

    },

    "REC": {

          "transactionUniqueNo": "33",

          "categoryId": "CG-4fa85f6425ad1d3",

          "categoryName": "대형마트",

          "merchantId": "2",

          "merchantName": "홈플러스",

          "transactionDate": "20240408",

          "transactionTime": "162147",

          "transactionBalance": "30000",

          "status": "CANCEL"

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
| A1010 | 거래고유번호가 유효하지 않습니다. |  |
| A1054 | 카드번호가 유효하지 않습니다. |  |
| A1055 | CVC 번호가 유효하지 않습니다. |  |
| A1058 | 청구 완료된 거래내역은 취소가 불가합니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.8.12 청구서 조회

##### 설명

카드 청구서를 조회합니다.

카드 청구서는 **월~일(일주일)**에 해당하는 카드 거래 내역을 반영하여

차주 **월요일 07:30**에 발행되며,

출금은 설정한 **출금 날짜 16:00**에 출금 연결 계좌(수시입출금)에서 자동 출금됩니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireBillingStatements | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| cvc | 카드보안코드 | String | 3 | Y |  |
| startMonth | 조회 시작월 | String | 6 | Y | YYYYMM |
| endMonth | 조회 종료월 | String | 6 | Y | YYYYMM |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "inquireBillingStatements",

        "transmissionDate": "20240408",

        "transmissionTime": "140400",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "inquireBillingStatements",

        "institutionTransactionUniqueNo": "20240215121212123501",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "cardNo": "1005518816096479",

    "cvc": "725",

    "startMonth":"202401",

    "endMonth":"202403"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 청구서 정보 |  |  | Y |  |
| billingMonth | 청구년월 | String | 6 | Y | YYYYMM |
| billingList | 청구서 목록 | List |  | Y |  |
| billingWeek | 청구주차 | String | 3 | Y | 1~5 / 월요일 기준으로 주차 산정 |
| billingDate | 청구서 발행일 | String | 8 | Y | YYYYMMDD |
| totalBalance | 청구금액 | Long |  | Y | 카드 혜택(카테고리 할인) 적용된 총 청구금액 |
| status | 청구금액 결제상태 | String | 20 | Y | 결제완료, 미결제 |
| paymentDate | 납입일자 | String | 8 | N | 납입이 이루어진 경우 YYYYMMDD |
| paymentTime | 납입시각 | String | 6 | N | 납입이 이루어진 경우 HHMMSS |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "inquireBillingStatements",

        "transmissionDate": "20240408",

        "transmissionTime": "140400",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "inquireBillingStatements",

        "institutionTransactionUniqueNo": "20240215121212123501"

    },

    "REC": [

        {

            "billingMonth": "202403",

            "billingList": [

                {

                    "billingWeek": "5",

                    "billingDate":"20240326",

                    "totalBalance": "285000",

                    "status": "미결제",

                    "paymentDate": "",

                    "paymentTime": ""

                }

            ]

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
| A1054 | 카드번호가 유효하지 않습니다. |  |
| A1055 | CVC 번호가 유효하지 않습니다. |  |
| A1059 | 조회 시작월이 유효하지 않습니다. |  |

| A1060 | 조회 종료월이 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---

#### 2.8.13 카드 결제 계좌 수정

##### 설명

청구 금액을 자동이체하는 **출금 연결계좌(수시입출금)와 출금 날짜**를 변경합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/updateWithdrawalAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| cvc | 카드보안코드 | String | 3 | Y |  |
| withdrawalAccountNo | 출금계좌번호 | String | 16 | Y |  |
| withdrawalDate | 출금날짜 | String | 10 | Y | 월: 1, 화: 2, 수: 3, 목: 4, 금: 5, 토: 6, 일: 7 |

##### 요청 메시지 형태

```json
{

    "Header": {

        "apiName": "updateWithdrawalAccount",

        "transmissionDate": "20240408",

        "transmissionTime": "140400",

        "institutionCode": "00100",

        "fintechAppNo": "001",

        "apiServiceCode": "updateWithdrawalAccount",

        "institutionTransactionUniqueNo": "20240215121212123561",

        "apiKey": "<REDACTED_API_KEY>",

        "userKey": "<REDACTED_USER_KEY>"

    },

    "cardNo": "1005518816096479",

    "cvc": "725",

    "withdrawalAccountNo": "0011541149756547",

    "withdrawalDate": "1"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 결제 계좌 수정 정보 |  |  | Y |  |
| cardNo | 카드번호 | String | 16 | Y |  |
| cvc | 카드보안코드 | String | 3 | Y |  |
| cardUniqueNo | 카드 고유번호 | String | 20 | Y |  |
| cardIssuerCode | 카드사코드 | String | 4 | Y |  |
| cardIssuerName | 카드사명 | String | 20 | Y |  |
| cardName | 카드명 | String | 100 | Y |  |
| baselinePerformance | 기준실적 | Long |  | Y |  |
| maxBenefitLimit | 최대 혜택한도 | Long |  | Y |  |
| cardDescription | 카드설명 | String | 255 | N |  |
| cardExpiryDate | 카드만료일 | String | 8 | Y | 개설일 + 5년 |
| withdrawalAccountNo | 출금계좌번호 | String | 16 | Y |  |
| withdrawalDate | 출금날짜 | String | 10 | Y | 월: 1, 화: 2, 수: 3, 목: 4, 금: 5, 토: 6, 일: 7 |

##### 응답 메시지 형태

```json
{

    "Header": {

        "responseCode": "H0000",

        "responseMessage": "정상처리 되었습니다.",

        "apiName": "updateWithdrawalAccount",

        "transmissionDate": "20240408",

        "transmissionTime": "140400",

        "institutionCode": "00100",

        "apiKey": "<REDACTED_API_KEY>",

        "apiServiceCode": "updateWithdrawalAccount",

        "institutionTransactionUniqueNo": "20240215121212123561"

    },

    "REC": {

        "cardNo": "1005518816096479",

        "cvc": "725",

        "cardUniqueNo": "1005-992db475fbb944c",

        "cardIssuerCode": "1005",

        "cardIssuerName": "신한카드",

        "cardName": "신한 TRAVEL 카드",

        "baselinePerformance": "10",

        "maxBenefitLimit": "100000",

        "cardDescription": "해외 결제시 15% 할인",

        "cardExpiryDate": "20290403",

        "withdrawalAccountNo": "0011541149756547",

        "withdrawalDate": "1"

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
| A1052 | 출금날짜가 유효하지 않습니다. |  |
| A1053 | 출금날짜는 1 ~ 7 로만 입력 가능합니다. |  |
| A1054 | 카드번호가 유효하지 않습니다. |  |
| A1055 | CVC 번호가 유효하지 않습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---
