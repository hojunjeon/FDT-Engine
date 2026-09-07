# 정기결제

- 제목: 정기결제
- 출처: https://project.ssafy.com/docs/ssafy-finance/api-recurring-payment
- 크롤링 날짜: 2026-08-24
- 범위: 화면에 표시된 정적 문서 본문만 추출했으며, 실제 금융 API 호출·인증·데이터 변경은 수행하지 않았습니다.
- 검증 상태: UNVERIFIED — 라이브 API 동작은 확인하지 않았습니다.
- 요약: 정기결제 등록, 서비스·목록 조회, 수정·취소·일시정지·재개, 이력 조회, 서비스 등록·수정, 즉시 결제, 구독 카테고리 조회·등록·수정/활성화 API의 설명·요청·응답 명세·JSON 예시·에러코드를 정리합니다. 예시 API KEY와 USER KEY 값은 redacted 처리했습니다.

### 2.18 정기결제

---

#### 2.18.1 정기결제 등록

##### 설명

카드와 구독 서비스를 지정하여 정기결제를 등록합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/subscriptionPayment | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| cardNo | 결제 카드번호 | String | 16 | Y | 예: 1005762704428098 |
| serviceId | 서비스 ID | String |  | Y | 예: 23 |
| billingCycle | 결제 주기 | String |  | Y | MONTHLY, DAILY |
| paymentDay | 결제일 | String | 2 | N | 월 결제 시 사용, 예: 31 |
| startDate | 구독 시작일 | String | 8 | Y | YYYYMMDD, 예: 20260731 |
| endDate | 구독 종료일 | String | 8 | N | YYYYMMDD, 빈 문자열 가능 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "subscriptionPayment",

    "transmissionDate": "20260810",

    "transmissionTime": "100100",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "subscriptionPayment",

    "institutionTransactionUniqueNo": "20260810100100000001",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "cardNo": "1234567890123456",

  "serviceId": "3",

  "billingCycle": "MONTHLY",

  "paymentDay": "15",

  "startDate": "20260810",

  "endDate": "20261231"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | HTTP 201, responseCode H0000 |
| REC | 등록된 정기구독 정보 | Object |  | Y | 응답 데이터 |
| subscriptionId | 정기구독 ID | String |  | Y | 예: SUB20260731150347067 |
| cardNo | 마스킹된 결제 카드번호 | String |  | Y | 예: 100576******8098 |
| serviceId | 서비스 ID | String |  | Y | 예: 23 |
| merchantId | 가맹점 ID | String |  | Y | 예: 1 |
| subscriptionName | 정기구독명 | String |  | Y | 예: 구독 789273 |
| paymentAmount | 결제 금액 | String |  | Y | 숫자 문자열, 예: 8900 |
| billingCycle | 결제 주기 | String |  | Y | MONTHLY, DAILY |
| dailyAmount | 일 결제 금액 | String |  | N | 월 결제 시 null |
| paymentDay | 결제일 | String | 2 | N | 월 결제일, 예: 30 |
| nextPaymentDate | 다음 결제일 | String | 8 | Y | YYYYMMDD, 예: 20260930 |
| endDate | 종료일 | String | 8 | N | YYYYMMDD, 미지정 가능 |
| status | 정기구독 상태 | String |  | Y | ACTIVE, PAUSED, CANCELED |
| category | 서비스 카테고리 | String |  | Y | 예: MUSIC |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "subscriptionPayment",

    "transmissionDate": "20260810",

    "transmissionTime": "100100",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "subscriptionPayment",

    "institutionTransactionUniqueNo": "20260810100100000001"

  },

  "REC": {

    "subscriptionId": "SUB20260810103000123",

    "cardNo": "123456******3456",

    "serviceId": "3",

    "merchantId": "1",

    "subscriptionName": "FLO 개인",

    "paymentAmount": "7900",

    "billingCycle": "MONTHLY",

    "dailyAmount": null,

    "paymentDay": "15",

    "nextPaymentDate": "20260915",

    "endDate": "20261231",

    "status": "ACTIVE",

    "category": "MUSIC",

    "createdAt": "20260810103000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4014 | 종료일이 시작일보다 이전 | 정기결제 등록 |
| E4030 | 카드 또는 가상카드의 연결 카드를 찾을 수 없음 | 정기결제 등록 |
| E4031 | 카드 소유자가 아님 | 정기결제 등록 |
| E4032 | 실물 카드가 정상 상태가 아님 | 정기결제 등록 |
| E4033 | 구독 서비스 또는 가맹점을 찾을 수 없음 | 정기결제 등록 |
| E4034 | 동일 카드·서비스의 활성 구독이 이미 존재 | 정기결제 등록 |
| E4035 | 결제일이 올바르지 않음 | 정기결제 등록 |
| E4036 | 카드 유효기간 만료 | 정기결제 등록 |
| E4039 | 요청 필드 타입이 유효하지 않음 | 정기결제 등록 |
| E4045 | 가상카드가 유효하지 않음 | 정기결제 등록 |
| E4046 | 가상카드 또는 카드 결제 한도 초과 | 정기결제 등록 |
| E4047 | 가상카드의 제한 가맹점 불일치 | 정기결제 등록 |
| E4100 | 결제 주기가 올바르지 않음 | 정기결제 등록 |

---

#### 2.18.2 정기결제 서비스 조회

##### 설명

등록된 정기결제 서비스 목록을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireSubscriptionService | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| category | 카테고리 필터 | String |  | N | 예: MUSIC |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireSubscriptionService",

    "transmissionDate": "20260810",

    "transmissionTime": "100200",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireSubscriptionService",

    "institutionTransactionUniqueNo": "20260810100200000002",

    "apiKey": "<REDACTED_API_KEY>"

  },

  "category": "MUSIC"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 서비스 조회 결과 | Object |  | Y | 응답 데이터 |
| services[] | 구독 서비스 목록 | Array |  | Y | 카테고리 조건에 맞는 서비스 |
| └ serviceId | 서비스 ID | String |  | Y | 예: 23 |
| └ merchantId | 가맹점 ID | String |  | Y | 예: 1 |
| └ serviceName | 서비스명 | String |  | Y | 예: 구독 789273 |
| └ category | 서비스 카테고리 | String |  | Y | 예: MUSIC |
| └ planName | 요금제명 | String |  | Y | 예: 개인 |
| └ monthlyPrice | 월 이용금액 | String |  | Y | 숫자 문자열, 예: 8900 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireSubscriptionService",

    "transmissionDate": "20260810",

    "transmissionTime": "100200",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireSubscriptionService",

    "institutionTransactionUniqueNo": "20260810100200000002"

  },

  "REC": {

    "services": [

      {

        "serviceId": "3",

        "merchantId": "1",

        "serviceName": "FLO",

        "planName": "개인",

        "monthlyPrice": "7900",

        "category": "MUSIC"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4039 | 요청 필드 타입이 유효하지 않음 | 정기결제 서비스 조회 |

---

#### 2.18.3 정기결제 목록 조회

##### 설명

사용자의 정기결제 목록과 월 총 결제금액을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireSubscriptionList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| status | 상태 필터 | String |  | N | ACTIVE, PAUSED, CANCELED |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireSubscriptionList",

    "transmissionDate": "20260810",

    "transmissionTime": "100300",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireSubscriptionList",

    "institutionTransactionUniqueNo": "20260810100300000003",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "status": "ACTIVE"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 구독 목록 조회 결과 | Object |  | Y | 응답 데이터 |
| totalMonthlyAmount | 월 총 결제금액 | String |  | Y | 활성 구독의 월 환산 합계 |
| activeCount | 활성 정기구독 수 | String |  | Y | 예: 3 |
| subscriptions[] | 정기구독 목록 | Array |  | Y | 상태 필터 적용 목록 |
| └ subscriptionId | 정기구독 ID | String |  | Y | 예: SUB20260731150347067 |
| └ subscriptionName | 정기구독명 | String |  | Y | 예: 구독 789273 |
| └ paymentAmount | 결제 금액 | String |  | Y | 숫자 문자열, 예: 8900 |
| └ billingCycle | 결제 주기 | String |  | Y | 예: MONTHLY |
| └ dailyAmount | 일 결제 금액 | String |  | N | 월 결제 시 null |
| └ nextPaymentDate | 다음 결제일 | String | 8 | Y | YYYYMMDD |
| └ status | 정기구독 상태 | String |  | Y | 예: ACTIVE |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireSubscriptionList",

    "transmissionDate": "20260810",

    "transmissionTime": "100300",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireSubscriptionList",

    "institutionTransactionUniqueNo": "20260810100300000003"

  },

  "REC": {

    "totalMonthlyAmount": "7900",

    "activeCount": "1",

    "subscriptions": [

      {

        "subscriptionId": "SUB20260810103000123",

        "subscriptionName": "FLO 개인",

        "paymentAmount": "7900",

        "billingCycle": "MONTHLY",

        "dailyAmount": null,

        "nextPaymentDate": "20260915",

        "status": "ACTIVE"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4039 | 요청 필드 타입이 유효하지 않음 | 정기결제 목록 조회 |

---

#### 2.18.4 정기결제 수정

##### 설명

정기결제의 카드, 결제일 또는 종료일을 수정합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/updateSubscription | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| subscriptionId | 정기구독 ID | String |  | Y | 수정 대상 식별자 |
| cardNo | 변경할 카드번호 | String | 16 | N | 미입력 시 기존 카드 유지 |
| paymentDay | 변경할 결제일 | String | 2 | N | 미입력 시 기존 결제일 유지 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "updateSubscription",

    "transmissionDate": "20260810",

    "transmissionTime": "100400",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "updateSubscription",

    "institutionTransactionUniqueNo": "20260810100400000004",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "subscriptionId": "SUB20260810103000123",

  "cardNo": "9876543210987654",

  "paymentDay": "20"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 수정된 정기구독 정보 | Object |  | Y | 응답 데이터 |
| subscriptionId | 정기구독 ID | String |  | Y | 예: SUB20260731150347067 |
| cardNo | 마스킹된 결제 카드번호 | String |  | Y | 예: 100576******8098 |
| serviceId | 서비스 ID | String |  | Y | 예: 23 |
| merchantId | 가맹점 ID | String |  | Y | 예: 1 |
| subscriptionName | 정기구독명 | String |  | Y | 예: 구독 789273 |
| paymentAmount | 결제 금액 | String |  | Y | 숫자 문자열, 예: 8900 |
| billingCycle | 결제 주기 | String |  | Y | 예: MONTHLY |
| dailyAmount | 일 결제 금액 | String |  | N | 월 결제 시 null |
| paymentDay | 결제일 | String | 2 | N | 월 결제일, 예: 30 |
| nextPaymentDate | 다음 결제일 | String | 8 | Y | YYYYMMDD, 예: 20260930 |
| endDate | 종료일 | String | 8 | N | YYYYMMDD, 미지정 가능 |
| status | 정기구독 상태 | String |  | Y | ACTIVE, PAUSED, CANCELED |
| category | 서비스 카테고리 | String |  | Y | 예: MUSIC |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "updateSubscription",

    "transmissionDate": "20260810",

    "transmissionTime": "100400",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "updateSubscription",

    "institutionTransactionUniqueNo": "20260810100400000004"

  },

  "REC": {

    "subscriptionId": "SUB20260810103000123",

    "cardNo": "987654******7654",

    "serviceId": "3",

    "merchantId": "1",

    "subscriptionName": "FLO 개인",

    "paymentAmount": "7900",

    "billingCycle": "MONTHLY",

    "dailyAmount": null,

    "paymentDay": "20",

    "nextPaymentDate": "20260920",

    "endDate": "20261231",

    "status": "ACTIVE",

    "category": "MUSIC",

    "createdAt": "20260810103000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4030 | 카드 또는 연결 카드를 찾을 수 없음 | 정기결제 수정 |
| E4031 | 카드 소유자가 아님 | 정기결제 수정 |
| E4032 | 실물 카드가 정상 상태가 아님 | 정기결제 수정 |
| E4033 | 연결된 구독 서비스 또는 가맹점을 찾을 수 없음 | 정기결제 수정 |
| E4035 | 결제일이 올바르지 않음 | 정기결제 수정 |
| E4036 | 카드 유효기간 만료 | 정기결제 수정 |
| E4037 | 구독을 찾을 수 없거나 이미 해지됨 | 정기결제 수정 |
| E4038 | 구독 소유자가 아님 | 정기결제 수정 |
| E4039 | 요청 필드 타입이 유효하지 않음 | 정기결제 수정 |
| E4045 | 가상카드가 유효하지 않음 | 정기결제 수정 |
| E4046 | 가상카드 결제 한도 초과 | 정기결제 수정 |
| E4047 | 가상카드의 제한 가맹점 불일치 | 정기결제 수정 |

---

#### 2.18.5 정기결제 취소

##### 설명

등록된 정기결제를 취소합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/cancelSubscription | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| subscriptionId | 정기구독 ID | String |  | Y | 해지 대상 식별자 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "cancelSubscription",

    "transmissionDate": "20260810",

    "transmissionTime": "100500",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "cancelSubscription",

    "institutionTransactionUniqueNo": "20260810100500000005",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "subscriptionId": "SUB20260810103000123"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 해지된 정기구독 정보 | Object |  | Y | status가 CANCELED로 변경 |
| subscriptionId | 정기구독 ID | String |  | Y | 예: SUB20260731150347067 |
| cardNo | 마스킹된 결제 카드번호 | String |  | Y | 예: 100576******8098 |
| serviceId | 서비스 ID | String |  | Y | 예: 23 |
| merchantId | 가맹점 ID | String |  | Y | 예: 1 |
| subscriptionName | 정기구독명 | String |  | Y | 예: 구독 789273 |
| paymentAmount | 결제 금액 | String |  | Y | 숫자 문자열, 예: 8900 |
| billingCycle | 결제 주기 | String |  | Y | 예: MONTHLY |
| dailyAmount | 일 결제 금액 | String |  | N | 월 결제 시 null |
| paymentDay | 결제일 | String | 2 | N | 월 결제일, 예: 30 |
| nextPaymentDate | 다음 결제일 | String | 8 | Y | YYYYMMDD, 예: 20260930 |
| endDate | 종료일 | String | 8 | N | YYYYMMDD, 미지정 가능 |
| status | 정기구독 상태 | String |  | Y | ACTIVE, PAUSED, CANCELED |
| category | 서비스 카테고리 | String |  | Y | 예: MUSIC |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "cancelSubscription",

    "transmissionDate": "20260810",

    "transmissionTime": "100500",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "cancelSubscription",

    "institutionTransactionUniqueNo": "20260810100500000005"

  },

  "REC": {

    "subscriptionId": "SUB20260810103000123",

    "cardNo": "123456******3456",

    "serviceId": "3",

    "merchantId": "1",

    "subscriptionName": "FLO 개인",

    "paymentAmount": "7900",

    "billingCycle": "MONTHLY",

    "dailyAmount": null,

    "paymentDay": "15",

    "nextPaymentDate": "20260915",

    "endDate": "20261231",

    "status": "CANCELED",

    "category": "MUSIC",

    "createdAt": "20260810103000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4033 | 연결된 구독 서비스 또는 가맹점을 찾을 수 없음 | 정기결제 해지 |
| E4037 | 구독을 찾을 수 없음 | 정기결제 해지 |
| E4038 | 구독 소유자가 아님 | 정기결제 해지 |
| E4039 | 요청 필드 타입이 유효하지 않음 | 정기결제 해지 |

---

#### 2.18.6 정기결제 일시정지·재개

##### 설명

정기결제를 일시정지하거나 재개합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/pauseSubscription | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| subscriptionId | 정기구독 ID | String |  | Y | 처리 대상 식별자 |
| action | 처리 상태 | String |  | Y | PAUSED: 정지, ACTIVE: 재개 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "pauseSubscription",

    "transmissionDate": "20260810",

    "transmissionTime": "100600",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "pauseSubscription",

    "institutionTransactionUniqueNo": "20260810100600000006",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "subscriptionId": "SUB20260810103000123",

  "action": "PAUSED"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 상태 변경된 정기구독 정보 | Object |  | Y | 응답 데이터 |
| subscriptionId | 정기구독 ID | String |  | Y | 예: SUB20260731150347067 |
| cardNo | 마스킹된 결제 카드번호 | String |  | Y | 예: 100576******8098 |
| serviceId | 서비스 ID | String |  | Y | 예: 23 |
| merchantId | 가맹점 ID | String |  | Y | 예: 1 |
| subscriptionName | 정기구독명 | String |  | Y | 예: 구독 789273 |
| paymentAmount | 결제 금액 | String |  | Y | 숫자 문자열, 예: 8900 |
| billingCycle | 결제 주기 | String |  | Y | 예: MONTHLY |
| dailyAmount | 일 결제 금액 | String |  | N | 월 결제 시 null |
| paymentDay | 결제일 | String | 2 | N | 월 결제일, 예: 30 |
| nextPaymentDate | 다음 결제일 | String | 8 | Y | YYYYMMDD, 예: 20260930 |
| endDate | 종료일 | String | 8 | N | YYYYMMDD, 미지정 가능 |
| status | 정기구독 상태 | String |  | Y | ACTIVE, PAUSED, CANCELED |
| category | 서비스 카테고리 | String |  | Y | 예: MUSIC |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "pauseSubscription",

    "transmissionDate": "20260810",

    "transmissionTime": "100600",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "pauseSubscription",

    "institutionTransactionUniqueNo": "20260810100600000006"

  },

  "REC": {

    "subscriptionId": "SUB20260810103000123",

    "cardNo": "123456******3456",

    "serviceId": "3",

    "merchantId": "1",

    "subscriptionName": "FLO 개인",

    "paymentAmount": "7900",

    "billingCycle": "MONTHLY",

    "dailyAmount": null,

    "paymentDay": "15",

    "nextPaymentDate": "20260915",

    "endDate": "20261231",

    "status": "PAUSED",

    "category": "MUSIC",

    "createdAt": "20260810103000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4033 | 연결된 구독 서비스 또는 가맹점을 찾을 수 없음 | 정기결제 일시정지·재개 |
| E4037 | 구독을 찾을 수 없거나 이미 해지됨 | 정기결제 일시정지·재개 |
| E4038 | 구독 소유자가 아님 | 정기결제 일시정지·재개 |
| E4039 | 요청 필드 타입이 유효하지 않음 | 정기결제 일시정지·재개 |

---

#### 2.18.7 정기결제 이력 조회

##### 설명

정기결제의 실제 결제 이력을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireSubscriptionHistory | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| subscriptionId | 정기구독 ID | String |  | Y | 조회 대상 식별자 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireSubscriptionHistory",

    "transmissionDate": "20260810",

    "transmissionTime": "100700",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireSubscriptionHistory",

    "institutionTransactionUniqueNo": "20260810100700000007",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "subscriptionId": "SUB20260810103000123"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 결제 이력 조회 결과 | Object |  | Y | 응답 데이터 |
| history[] | 결제 이력 | Array |  | Y | 해당 구독의 결제 시도 내역 |
| └ paymentDate | 결제일자 | String | 8 | Y | YYYYMMDD |
| └ paymentAmount | 결제 금액 | String |  | Y | 숫자 문자열, 예: 8900 |
| └ resultCode | 처리 결과코드 | String |  | Y | 정상 처리: H0000 |
| └ retryCount | 재시도 횟수 | String |  | Y | 예: 0 |
| └ resultMessage | 처리 결과메시지 | String |  | Y | 예: 정상처리 되었습니다. |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireSubscriptionHistory",

    "transmissionDate": "20260810",

    "transmissionTime": "100700",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireSubscriptionHistory",

    "institutionTransactionUniqueNo": "20260810100700000007"

  },

  "REC": {

    "history": [

      {

        "paymentDate": "20260810",

        "paymentAmount": "7900",

        "resultCode": "H0000",

        "retryCount": "0",

        "resultMessage": "정상처리 되었습니다."

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4037 | 구독을 찾을 수 없음 | 정기결제 이력 조회 |
| E4038 | 구독 소유자가 아님 | 정기결제 이력 조회 |
| E4039 | 요청 필드 타입이 유효하지 않음 | 정기결제 이력 조회 |

---

#### 2.18.8 정기결제 서비스 등록

##### 설명

가맹점의 정기결제 서비스를 신규 등록합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createSubscriptionService | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| serviceName | 서비스명 | String |  | Y | 예: 구독 789273 |
| merchantId | 가맹점 ID | String |  | Y | 예: 1 |
| category | 카테고리 | String |  | Y | 활성 카테고리 코드, 예: MUSIC |
| planName | 요금제명 | String |  | Y | 예: 개인 |
| monthlyPrice | 월 이용금액 | String |  | Y | 숫자 문자열, 예: 7900 |
| logoUrl | 로고 URL | String |  | N | 예: https://example.com/subscription.png |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "createSubscriptionService",

    "transmissionDate": "20260810",

    "transmissionTime": "100800",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "createSubscriptionService",

    "institutionTransactionUniqueNo": "20260810100800000008",

    "apiKey": "<REDACTED_API_KEY>"

  },

  "serviceName": "FLO",

  "merchantId": "1",

  "category": "MUSIC",

  "planName": "개인",

  "monthlyPrice": "7900",

  "logoUrl": "https://example.com/flo.png"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y |  |
| REC | 등록된 서비스 정보 | Object |  | Y | 응답 데이터 |
| serviceId | 서비스 ID | String |  | Y | 예: 23 |
| merchantId | 가맹점 ID | String |  | Y | 예: 1 |
| serviceName | 서비스명 | String |  | Y | 예: 구독 789273 |
| category | 서비스 카테고리 | String |  | Y | 예: MUSIC |
| planName | 요금제명 | String |  | Y | 예: 개인 |
| monthlyPrice | 월 이용금액 | String |  | Y | 숫자 문자열, 예: 8900 |
| dailyPriceSample | 일 환산 예시금액 | String |  | Y | 월 금액÷30 반올림, 예: 297 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "createSubscriptionService",

    "transmissionDate": "20260810",

    "transmissionTime": "100800",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "createSubscriptionService",

    "institutionTransactionUniqueNo": "20260810100800000008"

  },

  "REC": {

    "serviceId": "3",

    "merchantId": "1",

    "serviceName": "FLO",

    "category": "MUSIC",

    "planName": "개인",

    "monthlyPrice": "7900",

    "dailyPriceSample": "263"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4033 | 가맹점을 찾을 수 없음 | 구독 서비스 등록 |
| E4039 | 요청 필드 타입이 유효하지 않음 | 구독 서비스 등록 |
| E4102 | 동일한 구독 서비스가 이미 존재 | 구독 서비스 등록 |
| E4104 | 등록되지 않았거나 비활성화된 구독 카테고리 | 구독 서비스 등록 |

---

#### 2.18.9 정기결제 서비스 수정

##### 설명

등록된 정기결제 서비스의 정보를 수정합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/updateSubscriptionService | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| serviceId | 서비스 ID | String |  | Y | 수정 대상 식별자 |
| serviceName | 변경할 서비스명 | String |  | N | 미입력 시 기존 값 유지 |
| merchantId | 변경할 가맹점 ID | String |  | N | 미입력 시 기존 값 유지 |
| category | 변경할 카테고리 | String |  | N | 활성 카테고리 코드 |
| planName | 변경할 요금제명 | String |  | N | 미입력 시 기존 값 유지 |
| monthlyPrice | 변경할 월 이용금액 | String |  | N | 숫자 문자열, 예: 8900 |
| logoUrl | 변경할 로고 URL | String |  | N | 미입력 시 기존 값 유지 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "updateSubscriptionService",

    "transmissionDate": "20260810",

    "transmissionTime": "100900",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "updateSubscriptionService",

    "institutionTransactionUniqueNo": "20260810100900000009",

    "apiKey": "<REDACTED_API_KEY>"

  },

  "serviceId": "3",

  "serviceName": "FLO",

  "merchantId": "1",

  "category": "MUSIC",

  "planName": "프리미엄",

  "monthlyPrice": "8900",

  "logoUrl": "https://example.com/flo-premium.png"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 수정된 서비스 정보 | Object |  | Y | 응답 데이터 |
| serviceId | 서비스 ID | String |  | Y | 예: 23 |
| merchantId | 가맹점 ID | String |  | Y | 예: 1 |
| serviceName | 서비스명 | String |  | Y | 예: 구독 789273 |
| category | 서비스 카테고리 | String |  | Y | 예: MUSIC |
| planName | 요금제명 | String |  | Y | 예: 개인 |
| monthlyPrice | 월 이용금액 | String |  | Y | 숫자 문자열, 예: 8900 |
| dailyPriceSample | 일 환산 예시금액 | String |  | Y | 월 금액÷30 반올림, 예: 297 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "updateSubscriptionService",

    "transmissionDate": "20260810",

    "transmissionTime": "100900",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "updateSubscriptionService",

    "institutionTransactionUniqueNo": "20260810100900000009"

  },

  "REC": {

    "serviceId": "3",

    "merchantId": "1",

    "serviceName": "FLO",

    "category": "MUSIC",

    "planName": "프리미엄",

    "monthlyPrice": "8900",

    "dailyPriceSample": "297"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4033 | 가맹점을 찾을 수 없음 | 구독 서비스 수정 |
| E4039 | 요청 필드 타입이 유효하지 않음 | 구독 서비스 수정 |
| E4102 | 동일한 구독 서비스가 이미 존재 | 구독 서비스 수정 |
| E4103 | 구독 서비스를 찾을 수 없음 | 구독 서비스 수정 |
| E4104 | 등록되지 않았거나 비활성화된 구독 카테고리 | 구독 서비스 수정 |

---

#### 2.18.10 정기결제 즉시 결제

##### 설명

활성 정기결제를 지정일에 즉시 결제합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/paySubscriptionNow | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| subscriptionId | 정기구독 ID | String |  | Y | 결제 대상 식별자 |
| amount | 결제 금액 | String |  | N | 미입력 시 서비스 결제 금액 |
| payDate | 결제 기준일 | String | 8 | N | YYYYMMDD, 미입력 시 당일 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "paySubscriptionNow",

    "transmissionDate": "20260810",

    "transmissionTime": "101000",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "paySubscriptionNow",

    "institutionTransactionUniqueNo": "20260810101000000010",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "subscriptionId": "SUB20260810103000123",

  "amount": "7900",

  "payDate": "20260810"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 즉시 결제 결과 | Object |  | Y | 응답 데이터 |
| subscriptionId | 정기구독 ID | String |  | Y | 요청한 구독 ID |
| paidAmount | 결제 완료금액 | String |  | Y | 예: 8900 |
| paymentDate | 결제일자 | String | 8 | Y | YYYYMMDD |
| resultCode | 처리 결과코드 | String |  | Y | 정상 처리: H0000 |
| resultMessage | 처리 결과메시지 | String |  | Y | 예: 정상처리 되었습니다. |
| nextPaymentDate | 다음 결제일 | String | 8 | Y | YYYYMMDD |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "paySubscriptionNow",

    "transmissionDate": "20260810",

    "transmissionTime": "101000",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "paySubscriptionNow",

    "institutionTransactionUniqueNo": "20260810101000000010"

  },

  "REC": {

    "subscriptionId": "SUB20260810103000123",

    "paidAmount": "7900",

    "paymentDate": "20260810",

    "resultCode": "H0000",

    "resultMessage": "정상처리 되었습니다.",

    "nextPaymentDate": "20260915"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4014 | 구독 종료일 관련 날짜 오류 | 정기결제 즉시 결제 |
| E4030 | 카드 또는 연결 카드를 찾을 수 없음 | 정기결제 즉시 결제 |
| E4031 | 카드 소유자가 아님 | 정기결제 즉시 결제 |
| E4032 | 실물 카드가 정상 상태가 아님 | 정기결제 즉시 결제 |
| E4036 | 카드 유효기간 만료 | 정기결제 즉시 결제 |
| E4037 | 구독을 찾을 수 없음 | 정기결제 즉시 결제 |
| E4038 | 구독 소유자가 아님 | 정기결제 즉시 결제 |
| E4039 | 요청 필드 타입이 유효하지 않음 | 정기결제 즉시 결제 |
| E4045 | 가상카드가 유효하지 않음 | 정기결제 즉시 결제 |
| E4046 | 결제 한도 초과 | 정기결제 즉시 결제 |
| E4047 | 가상카드의 제한 가맹점 불일치 | 정기결제 즉시 결제 |
| E4100 | 결제 주기가 올바르지 않음 | 정기결제 즉시 결제 |
| E4101 | 활성 구독이 아님 | 정기결제 즉시 결제 |

---

#### 2.18.11 구독 카테고리 조회

##### 설명

등록된 구독 카테고리 목록과 사용 여부를 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireSubscriptionCategory | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireSubscriptionCategory",

    "transmissionDate": "20260810",

    "transmissionTime": "101100",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireSubscriptionCategory",

    "institutionTransactionUniqueNo": "20260810101100000011",

    "apiKey": "<REDACTED_API_KEY>"

  }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 카테고리 조회 결과 | Object |  | Y | 응답 데이터 |
| categories[] | 구독 카테고리 목록 | Array |  | Y | 카테고리 코드 오름차순 |
| └ category | 구독 카테고리 코드 | String | 20 | Y | 예: MUSIC |
| └ categoryName | 구독 카테고리명 | String | 50 | Y | 예: 음악 |
| └ active | 사용 여부 | Boolean |  | Y | true: 사용, false: 미사용 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireSubscriptionCategory",

    "transmissionDate": "20260810",

    "transmissionTime": "101100",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireSubscriptionCategory",

    "institutionTransactionUniqueNo": "20260810101100000011"

  },

  "REC": {

    "categories": [

      {

        "category": "MUSIC",

        "categoryName": "음악",

        "active": true

      },

      {

        "category": "VIDEO",

        "categoryName": "영상",

        "active": true

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| - | 기능 전용 오류 없음 | 구독 카테고리 조회 |

---

#### 2.18.12 구독 카테고리 등록

##### 설명

새 구독 카테고리를 등록하며 등록 시 사용 상태로 생성합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createSubscriptionCategory | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| category | 구독 카테고리 코드 | String | 20 | Y | 영문 대문자·숫자·밑줄 |
| categoryName | 구독 카테고리명 | String | 50 | Y | 예: API 명세 테스트 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "createSubscriptionCategory",

    "transmissionDate": "20260810",

    "transmissionTime": "101200",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "createSubscriptionCategory",

    "institutionTransactionUniqueNo": "20260810101200000012",

    "apiKey": "<REDACTED_API_KEY>"

  },

  "category": "EDUCATION",

  "categoryName": "교육"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | HTTP 201, responseCode H0000 |
| REC | 등록된 카테고리 정보 | Object |  | Y | 응답 데이터 |
| category | 구독 카테고리 코드 | String | 20 | Y | 예: DOC_API_747548 |
| categoryName | 구독 카테고리명 | String | 50 | Y | 예: API 명세 테스트 |
| active | 사용 여부 | Boolean |  | Y | 등록 시 true |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "createSubscriptionCategory",

    "transmissionDate": "20260810",

    "transmissionTime": "101200",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "createSubscriptionCategory",

    "institutionTransactionUniqueNo": "20260810101200000012"

  },

  "REC": {

    "category": "EDUCATION",

    "categoryName": "교육",

    "active": true

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4105 | 동일한 구독 카테고리가 이미 존재 | 구독 카테고리 등록 |

---

#### 2.18.13 구독 카테고리 수정/활성화

##### 설명

구독 카테고리명 또는 사용 여부를 수정합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/updateSubscriptionCategory | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| category | 구독 카테고리 코드 | String | 20 | Y | 수정 대상 식별자 |
| categoryName | 변경할 카테고리명 | String | 50 | N | 미입력 시 기존 이름 유지 |
| active | 사용 여부 | Boolean |  | N | 예: false |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "updateSubscriptionCategory",

    "transmissionDate": "20260810",

    "transmissionTime": "101300",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "updateSubscriptionCategory",

    "institutionTransactionUniqueNo": "20260810101300000013",

    "apiKey": "<REDACTED_API_KEY>"

  },

  "category": "EDUCATION",

  "categoryName": "온라인 교육",

  "active": false

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 수정된 카테고리 정보 | Object |  | Y | 응답 데이터 |
| category | 구독 카테고리 코드 | String | 20 | Y | 요청한 카테고리 코드 |
| categoryName | 구독 카테고리명 | String | 50 | Y | 수정 후 표시 이름 |
| active | 사용 여부 | Boolean |  | Y | 예: false |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "updateSubscriptionCategory",

    "transmissionDate": "20260810",

    "transmissionTime": "101300",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "updateSubscriptionCategory",

    "institutionTransactionUniqueNo": "20260810101300000013"

  },

  "REC": {

    "category": "EDUCATION",

    "categoryName": "온라인 교육",

    "active": false

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4105 | 변경할 코드와 동일한 구독 카테고리가 이미 존재 | 구독 카테고리 수정·활성화 |
| E4106 | 구독 카테고리를 찾을 수 없음 | 구독 카테고리 수정·활성화 |

---

