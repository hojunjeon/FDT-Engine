# 금·은 실물

- 제목: 금·은 실물
- 출처: https://project.ssafy.com/docs/ssafy-finance/api-physical-gold-silver
- 크롤링 날짜: 2026-08-24
- 범위: 화면에 표시된 정적 문서 본문만 추출했으며, 실제 금융 API 호출·인증·데이터 변경은 수행하지 않았습니다.
- 요약: 금·은 실물 주문 생성, 현재가·가격 이력·보유 자산·주문 내역 조회, 주문 취소, 자산 평가 API의 설명·요청·응답 명세·JSON 예시·에러코드를 정리합니다. 예시 API KEY와 USER KEY 값은 redacted 처리했습니다.

### 2.21 금·은 실물

#### 2.21.1 금·은 실물 주문 생성

##### 설명

보유 계좌를 이용하여 금·은 실물 매수 또는 매도 주문을 생성합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/createPreciousMetalOrder | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| metalType | 금·은 실물 유형 | String | 2 | Y | AU / AG |
| orderType | 주문 유형 | String | 4 | Y | BUY / SELL |
| orderMethod | 주문 방식 | String |  | Y | WEIGHT / AMOUNT |
| orderWeight | 주문 중량 | String |  | N |  |
| orderAmount | 주문 금액 | String |  | N |  |
| priceType | 가격 유형 | String | 6 | Y | MARKET / LIMIT |
| limitPrice | 지정가 | String |  | N |  |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "createPreciousMetalOrder",

    "transmissionDate": "20260810",

    "transmissionTime": "130000",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "createPreciousMetalOrder",

    "institutionTransactionUniqueNo": "20260810130000000001",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "accountNo": "0011234567890123",

  "metalType": "AU",

  "orderType": "BUY",

  "orderMethod": "AMOUNT",

  "orderWeight": null,

  "orderAmount": "100000",

  "priceType": "MARKET",

  "limitPrice": null

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 응답 데이터 | Object |  | Y |  |
| orderId | 금·은 실물 주문 ID | String |  | Y |  |
| metalType | 금·은 실물 유형 | String | 2 | Y | AU / AG |
| metalName | 금·은 실물명 | String |  | Y |  |
| orderType | 주문 유형 | String | 4 | Y | BUY / SELL |
| executedWeight | 체결 중량 | String |  | Y |  |
| executedPrice | 체결 가격 | String |  | Y |  |
| totalAmount | 총 거래금액 | String |  | Y |  |
| fee | 수수료 | String |  | Y |  |
| netAmount | 실 결제금액 | String |  | Y |  |
| executedAt | 체결 일시 | String | 14 | N |  |
| status | 주문 상태 | String | 8 | Y | EXECUTED / WAITING / CANCELED |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "createPreciousMetalOrder",

    "transmissionDate": "20260810",

    "transmissionTime": "130000",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "createPreciousMetalOrder",

    "institutionTransactionUniqueNo": "20260810130000000001"

  },

  "REC": {

    "orderId": "PMO20260810130000123",

    "metalType": "AU",

    "metalName": "금",

    "orderType": "BUY",

    "executedWeight": "1.0000",

    "executedPrice": "100000",

    "totalAmount": "100000",

    "fee": "1000",

    "netAmount": "101000",

    "executedAt": "20260810130000",

    "status": "EXECUTED"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4080 | 결제 계좌를 찾을 수 없거나 거래 가능한 원화 계좌가 아님 | 금·은 실물 주문 |
| E4081 | 계좌 소유자가 아님 | 금·은 실물 주문 |
| E4082 | 매수에 필요한 계좌 잔액 부족 | 금·은 실물 주문 |
| E4083 | 매도할 금·은 실물 보유 중량 부족 | 금·은 실물 주문 |
| E4084 | 주문 중량이 최소 거래 단위 미만 | 금·은 실물 주문 |
| E4085 | 지정가가 올바르지 않음 | 금·은 실물 주문 |
| E4086 | 지원하지 않는 금속 종류 | 금·은 실물 주문 |
| E4088 | 요청 필드 타입이 유효하지 않음 | 금·은 실물 주문 |

#### 2.21.2 금·은 실물 현재가 조회

##### 설명

금속 종류별 현재 매수가와 매도가를 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/inquirePreciousMetalPrice | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| metalType | 금·은 실물 유형 | String | 2 | N | AU / AG |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquirePreciousMetalPrice",

    "transmissionDate": "20260810",

    "transmissionTime": "130100",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquirePreciousMetalPrice",

    "institutionTransactionUniqueNo": "20260810130100000002",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "metalType": "AU"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 응답 데이터 | Object |  | Y |  |
| prices[] | 금·은 실물 시세 목록 | Array |  | Y |  |
| ↳ metalType | 금·은 실물 유형 | String | 2 | Y | AU / AG |
| ↳ metalName | 금·은 실물명 | String |  | Y | 예: 금 / 은 |
| ↳ minimumWeight | 최소 주문 중량(g) | String |  | Y | 예: 0.0001 |
| ↳ buyPrice | 매수가 | String |  | Y |  |
| ↳ sellPrice | 매도가 | String |  | Y |  |
| ↳ updatedAt | 시세 갱신 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquirePreciousMetalPrice",

    "transmissionDate": "20260810",

    "transmissionTime": "130100",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquirePreciousMetalPrice",

    "institutionTransactionUniqueNo": "20260810130100000002"

  },

  "REC": {

    "prices": [

      {

        "metalType": "AU",

        "metalName": "금",

        "minimumWeight": "0.0001",

        "buyPrice": "100000",

        "sellPrice": "98000",

        "updatedAt": "20260810130000"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4086 | 지원하지 않는 금속 종류 | 금·은 시세 조회 |
| E4088 | 요청 필드 타입이 유효하지 않음 | 금·은 시세 조회 |

#### 2.21.3 금·은 실물 가격 이력 조회

##### 설명

지정한 기간의 금·은 실물 매수가와 매도가 이력을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/inquirePreciousMetalPriceHistory | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| metalType | 금·은 실물 유형 | String | 2 | Y | AU / AG |
| startDate | 시작일(YYYYMMDD) | String | 8 | Y |  |
| endDate | 종료일(YYYYMMDD) | String | 8 | Y |  |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquirePreciousMetalPriceHistory",

    "transmissionDate": "20260810",

    "transmissionTime": "130200",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquirePreciousMetalPriceHistory",

    "institutionTransactionUniqueNo": "20260810130200000003",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "metalType": "AU",

  "startDate": "20260808",

  "endDate": "20260810"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 응답 데이터 | Object |  | Y |  |
| history[] | 금·은 실물 가격 이력 | Array |  | Y |  |
| ↳ priceDate | 시세 일자 | String | 8 | Y |  |
| ↳ buyPrice | 매수가 | String |  | Y |  |
| ↳ sellPrice | 매도가 | String |  | Y |  |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquirePreciousMetalPriceHistory",

    "transmissionDate": "20260810",

    "transmissionTime": "130200",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquirePreciousMetalPriceHistory",

    "institutionTransactionUniqueNo": "20260810130200000003"

  },

  "REC": {

    "history": [

      {

        "priceDate": "20260808",

        "buyPrice": "99000",

        "sellPrice": "97000"

      },

      {

        "priceDate": "20260809",

        "buyPrice": "99500",

        "sellPrice": "97500"

      },

      {

        "priceDate": "20260810",

        "buyPrice": "100000",

        "sellPrice": "98000"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4086 | 지원하지 않는 금속 종류 | 금·은 시세 이력 조회 |
| E4088 | 요청 필드 타입이 유효하지 않음 | 금·은 시세 이력 조회 |

#### 2.21.4 보유 금·은 실물 조회

##### 설명

사용자가 보유한 금·은 실물의 중량과 평균 매수가를 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/inquireMyPreciousMetalHoldings | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| metalType | 금·은 실물 유형 | String | 2 | N | AU / AG |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireMyPreciousMetalHoldings",

    "transmissionDate": "20260810",

    "transmissionTime": "130300",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireMyPreciousMetalHoldings",

    "institutionTransactionUniqueNo": "20260810130300000004",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "metalType": "AU"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 응답 데이터 | Object |  | Y |  |
| holdings[] | 보유 금·은 실물 목록 | Array |  | Y |  |
| ↳ metalType | 금·은 실물 유형 | String | 2 | Y | AU / AG |
| ↳ totalWeight | 총 보유 중량 | String |  | Y |  |
| ↳ avgBuyPrice | 평균 매수가 | String |  | Y |  |
| ↳ totalInvested | 총 투자금액 | String |  | Y |  |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireMyPreciousMetalHoldings",

    "transmissionDate": "20260810",

    "transmissionTime": "130300",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireMyPreciousMetalHoldings",

    "institutionTransactionUniqueNo": "20260810130300000004"

  },

  "REC": {

    "holdings": [

      {

        "metalType": "AU",

        "totalWeight": "1.0000",

        "avgBuyPrice": "100000",

        "totalInvested": "100000"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4086 | 지원하지 않는 금속 종류 | 금·은 보유 자산 조회 |
| E4088 | 요청 필드 타입이 유효하지 않음 | 금·은 보유 자산 조회 |

#### 2.21.5 금·은 실물 주문 내역 조회

##### 설명

사용자의 금·은 실물 주문 내역을 금속 종류와 주문 상태로 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/inquirePreciousMetalOrders | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| metalType | 금·은 실물 유형 | String | 2 | N | AU / AG |
| status | 주문 상태 | String | 8 | N | EXECUTED / WAITING / CANCELED |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquirePreciousMetalOrders",

    "transmissionDate": "20260810",

    "transmissionTime": "130400",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquirePreciousMetalOrders",

    "institutionTransactionUniqueNo": "20260810130400000005",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "metalType": "AU",

  "status": "EXECUTED"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 응답 데이터 | Object |  | Y |  |
| orders[] | 금·은 실물 주문 목록 | Array |  | Y |  |
| ↳ orderId | 금·은 실물 주문 ID | String |  | Y |  |
| ↳ metalType | 금·은 실물 유형 | String | 2 | Y | AU / AG |
| ↳ orderType | 주문 유형 | String | 4 | Y | BUY / SELL |
| ↳ orderMethod | 주문 방식 | String |  | Y | WEIGHT / AMOUNT |
| ↳ priceType | 가격 유형 | String | 6 | Y | MARKET / LIMIT |
| ↳ orderWeight | 주문 중량 | String |  | N |  |
| ↳ orderAmount | 주문 금액 | String |  | N |  |
| ↳ limitPrice | 지정가 | String |  | N |  |
| ↳ executedWeight | 체결 중량 | String |  | Y |  |
| ↳ executedPrice | 체결 가격 | String |  | Y |  |
| ↳ totalAmount | 총 거래금액 | String |  | Y |  |
| ↳ status | 주문 상태 | String | 8 | Y | EXECUTED / WAITING / CANCELED |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquirePreciousMetalOrders",

    "transmissionDate": "20260810",

    "transmissionTime": "130400",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquirePreciousMetalOrders",

    "institutionTransactionUniqueNo": "20260810130400000005"

  },

  "REC": {

    "orders": [

      {

        "orderId": "PMO20260810130000123",

        "metalType": "AU",

        "orderType": "BUY",

        "orderMethod": "AMOUNT",

        "priceType": "MARKET",

        "orderWeight": null,

        "orderAmount": "100000",

        "limitPrice": null,

        "executedWeight": "1.0000",

        "executedPrice": "100000",

        "totalAmount": "100000",

        "status": "EXECUTED"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4086 | 지원하지 않는 금속 종류 | 금·은 주문 내역 조회 |
| E4088 | 요청 필드 타입이 유효하지 않음 | 금·은 주문 내역 조회 |

#### 2.21.6 금·은 실물 주문 취소

##### 설명

체결 대기 중인 금·은 실물 지정가 주문을 취소합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/cancelPreciousMetalOrder | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| orderId | 금·은 실물 주문 ID | String |  | Y |  |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "cancelPreciousMetalOrder",

    "transmissionDate": "20260810",

    "transmissionTime": "130500",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "cancelPreciousMetalOrder",

    "institutionTransactionUniqueNo": "20260810130500000006",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "orderId": "PMO20260810130500456"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 응답 데이터 | Object |  | Y |  |
| orderId | 금·은 실물 주문 ID | String |  | Y |  |
| status | 주문 상태 | String | 8 | Y | EXECUTED / WAITING / CANCELED |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "cancelPreciousMetalOrder",

    "transmissionDate": "20260810",

    "transmissionTime": "130500",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "cancelPreciousMetalOrder",

    "institutionTransactionUniqueNo": "20260810130500000006"

  },

  "REC": {

    "orderId": "PMO20260810130500456",

    "status": "CANCELED"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4087 | 주문을 찾을 수 없거나 소유자가 아니거나 취소할 수 없는 상태 | 금·은 지정가 주문 취소 |
| E4088 | 요청 필드 타입이 유효하지 않음 | 금·은 지정가 주문 취소 |

#### 2.21.7 금·은 실물 자산 평가

##### 설명

보유 금·은 실물의 투자금액, 현재가치, 평가손익과 수익률을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/evaluatePreciousMetalAsset | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| metalType | 금·은 실물 유형 | String | 2 | N | AU / AG |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "evaluatePreciousMetalAsset",

    "transmissionDate": "20260810",

    "transmissionTime": "130600",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "evaluatePreciousMetalAsset",

    "institutionTransactionUniqueNo": "20260810130600000007",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "metalType": "AU"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 응답 데이터 | Object |  | Y |  |
| totalInvested | 총 투자금액 | String |  | Y |  |
| currentValue | 현재 평가금액 | String |  | Y |  |
| profitLoss | 평가손익 | String |  | Y |  |
| profitRate | 수익률 | String |  | Y |  |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "evaluatePreciousMetalAsset",

    "transmissionDate": "20260810",

    "transmissionTime": "130600",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "evaluatePreciousMetalAsset",

    "institutionTransactionUniqueNo": "20260810130600000007"

  },

  "REC": {

    "totalInvested": "100000",

    "currentValue": "98000",

    "profitLoss": "-2000",

    "profitRate": "-2.00"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4086 | 지원하지 않는 금속 종류 또는 시세 정보 없음 | 금·은 보유 자산 평가 |
| E4088 | 요청 필드 타입이 유효하지 않음 | 금·은 보유 자산 평가 |

