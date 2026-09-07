# 마이너스통장

- 제목: 마이너스통장
- 출처: https://project.ssafy.com/docs/ssafy-finance/api-overdraft-account
- 크롤링 날짜: 2026-08-24
- 범위: 화면에 표시된 정적 문서 본문만 추출했으며, 실제 금융 API 호출·인증·데이터 변경은 수행하지 않았습니다.
- 검증 상태: UNVERIFIED — 라이브 API 동작은 확인하지 않았습니다.
- 요약: 마이너스통장 상품 등록·목록 조회, 개설, 출금, 원금 상환, 상세·목록 조회, 해지, 이자·알림·거래 내역 조회, 이자 납부, 한도 변경 API의 설명·요청·응답 명세·JSON 예시·에러코드를 정리합니다. 예시 API KEY와 USER KEY 값은 redacted 처리했습니다.

### 2.17 마이너스통장

---

#### 2.17.1 마이너스통장 상품 등록

##### 설명

은행 코드에 해당하는 마이너스통장 상품을 등록합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/createMinusAccountProduct | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| bankCode | 은행 코드 | String | 3 | Y | 예: 088 |
| accountName | 상품명 | String |  | Y | 예: MINUS-130417 |
| accountDescription | 상품 설명 | String |  | N | 미입력 시 빈 문자열, 예: Swagger MINUS test |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "createMinusAccountProduct",

    "transmissionDate": "20260731",

    "transmissionTime": "140100",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "createMinusAccountProduct",

    "institutionTransactionUniqueNo": "20260731140100100001",

    "apiKey": "<REDACTED_API_KEY>"

  },

  "bankCode": "088",

  "accountName": "SSAFY 마이너스 통장",

  "accountDescription": "필요할 때 쓰고 사용한 금액에 대해서만 이자를 납부하는 한도대출 상품"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| accountTypeUniqueNo | 상품 고유번호 | String |  | Y | 예: 088-6-9267c6896d9f40 |
| bankCode | 은행 코드 | String | 3 | Y | 예: 088 |
| bankName | 은행명 | String |  | Y | 예: 신한은행 |
| accountTypeCode | 계좌 유형 코드 | String |  | Y | 마이너스통장: 6 |
| accountTypeName | 계좌 유형명 | String |  | Y | 예: 마이너스통장 |
| accountName | 상품명 | String |  | Y | 예: MINUS-130417 |
| accountDescription | 상품 설명 | String |  | Y | 미입력 시 빈 문자열 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "createMinusAccountProduct",

    "transmissionDate": "20260731",

    "transmissionTime": "140100",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "createMinusAccountProduct",

    "institutionTransactionUniqueNo": "20260731140100100001"

  },

  "REC": {

    "accountTypeUniqueNo": "088-6-9d7e6c05ae1e47",

    "bankCode": "088",

    "bankName": "신한은행",

    "accountTypeCode": "6",

    "accountTypeName": "마이너스 통장",

    "accountName": "SSAFY 마이너스 통장",

    "accountDescription": "필요할 때 쓰고 사용한 금액에 대해서만 이자를 납부하는 한도대출 상품"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4121 | 요청 필드 타입 또는 요청값이 올바르지 않음 | 마이너스통장 상품 등록 |

---

#### 2.17.2 마이너스통장 상품 목록 조회

##### 설명

등록된 마이너스통장 상품 목록을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccountProductList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireMinusAccountProductList",

    "transmissionDate": "20260731",

    "transmissionTime": "140200",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireMinusAccountProductList",

    "institutionTransactionUniqueNo": "20260731140200100002",

    "apiKey": "<REDACTED_API_KEY>"

  }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Array |  | Y | 정상 처리 결과 |
| └ accountTypeUniqueNo | 상품 고유번호 | String |  | Y | 예: 088-6-9267c6896d9f40 |
| └ bankCode | 은행 코드 | String | 3 | Y | 예: 088 |
| └ bankName | 은행명 | String |  | Y | 예: 신한은행 |
| └ accountTypeCode | 계좌 유형 코드 | String |  | Y | 마이너스통장: 6 |
| └ accountTypeName | 계좌 유형명 | String |  | Y | 예: 마이너스통장 |
| └ accountName | 상품명 | String |  | Y | 예: MINUS-130417 |
| └ accountDescription | 상품 설명 | String |  | Y | 미입력 시 빈 문자열 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireMinusAccountProductList",

    "transmissionDate": "20260731",

    "transmissionTime": "140200",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireMinusAccountProductList",

    "institutionTransactionUniqueNo": "20260731140200100002"

  },

  "REC": [

    {

      "accountTypeUniqueNo": "088-6-9d7e6c05ae1e47",

      "bankCode": "088",

      "bankName": "신한은행",

      "accountTypeCode": "6",

      "accountTypeName": "마이너스 통장",

      "accountName": "SSAFY 마이너스 통장",

      "accountDescription": "필요할 때 쓰고 사용한 금액에 대해서만 이자를 납부하는 한도대출 상품"

    }

  ]

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| - | 기능 전용 오류 없음 | 마이너스통장 상품 목록 조회 |

---

#### 2.17.3 마이너스통장 개설

##### 설명

상품·한도·연결계좌·기간·금리·상환 조건을 지정해 마이너스통장을 개설합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/createMinusAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| accountTypeUniqueNo | 상품 고유번호 | String |  | Y | 예: 088-6-9267c6896d9f40 |
| creditLimit | 신용 한도 | String |  | Y | 숫자 문자열, 예: 500000 |
| linkedAccountNo | 연결 계좌번호 | String | 16 | Y | 예: 0881816422703833 |
| loanPeriodMonths | 대출 기간(개월) | String |  | Y | 예: 12 |
| interestRate | 적용 금리 | String |  | Y | 예: 4.5 |
| repaymentType | 상환 방식 | String |  | Y | FREE_REPAYMENT 또는 AUTO_REPAYMENT |
| interestPaymentDay | 이자 납입일 | String | 2 | Y | 예: 25 |
| autoRepaymentDay | 자동 상환일 | String | 2 | N | 자동 상환 시 사용, 예: 25 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "createMinusAccount",

    "transmissionDate": "20260731",

    "transmissionTime": "140300",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "createMinusAccount",

    "institutionTransactionUniqueNo": "20260731140300100003",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "accountTypeUniqueNo": "088-6-9d7e6c05ae1e47",

  "creditLimit": "10000000",

  "linkedAccountNo": "0011234567890123",

  "loanPeriodMonths": "12",

  "interestRate": "4.5",

  "repaymentType": "FREE_REPAYMENT",

  "interestPaymentDay": "25",

  "autoRepaymentDay": "25"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7011002504332250 |
| linkedAccountNo | 연결 계좌번호 | String | 16 | Y | 예: 0881816422703833 |
| productName | 상품명 | String |  | Y | 예: MINUS-130417 |
| creditLimit | 신용 한도 | String |  | Y | 예: 500000 |
| usedAmount | 사용 금액 | String |  | Y | 예: 0 |
| availableAmount | 출금 가능 금액 | String |  | Y | 예: 500000 |
| interestRate | 적용 금리 | String |  | Y | 예: 4.5 |
| accruedInterest | 누적 이자 | String |  | Y | 예: 0 |
| interestPaymentDay | 이자 납입일 | String | 2 | Y | 예: 25 |
| repaymentType | 상환 방식 | String |  | Y | 예: FREE_REPAYMENT |
| nextInterestDate | 다음 이자 납입일 | String | 8 | Y | YYYYMMDD, 예: 20260825 |
| startDate | 대출 시작일 | String | 8 | Y | YYYYMMDD, 예: 20260731 |
| maturityDate | 만기일 | String | 8 | Y | YYYYMMDD, 예: 20270731 |
| status | 계좌 상태 | String |  | Y | NORMAL, OVERDUE, CLOSED |
| overdueDays | 연체 일수 | String |  | Y | 예: 0 |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss, 예: 20260731131608 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "createMinusAccount",

    "transmissionDate": "20260731",

    "transmissionTime": "140300",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "createMinusAccount",

    "institutionTransactionUniqueNo": "20260731140300100003"

  },

  "REC": {

    "loanAccountNo": "7012345678901234",

    "linkedAccountNo": "0011234567890123",

    "productName": "SSAFY 마이너스 통장",

    "creditLimit": "10000000",

    "usedAmount": "1500000",

    "availableAmount": "8500000",

    "interestRate": "4.5",

    "accruedInterest": "36960",

    "interestPaymentDay": "25",

    "repaymentType": "FREE_REPAYMENT",

    "nextInterestDate": "20260725",

    "startDate": "20260716",

    "maturityDate": "20270716",

    "status": "NORMAL",

    "overdueDays": "0",

    "createdAt": "20260716143000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4110 | 연결 계좌를 찾을 수 없거나 정상 상태가 아님 | 마이너스통장 개설 |
| E4111 | 계좌 소유자가 아님 | 마이너스통장 개설 |
| E4113 | 상품을 찾을 수 없음 | 마이너스통장 개설 |
| E4114 | 대출 기간이 올바르지 않음 | 마이너스통장 개설 |
| E4118 | 이자 납입일이 올바르지 않음 | 마이너스통장 개설 |
| E4121 | 요청 필드 타입 또는 금액·이자율 등의 요청값이 올바르지 않음 | 마이너스통장 개설 |

---

#### 2.17.4 마이너스통장 출금

##### 설명

마이너스통장 한도에서 금액을 출금하고 사용액과 가용액을 갱신합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/minusAccountWithdraw | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7011002504332250 |
| amount | 출금 금액 | String |  | Y | 숫자 문자열, 예: 100000 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "minusAccountWithdraw",

    "transmissionDate": "20260731",

    "transmissionTime": "140400",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "minusAccountWithdraw",

    "institutionTransactionUniqueNo": "20260731140400100004",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "loanAccountNo": "7012345678901234",

  "amount": "500000"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| usedAmount | 출금 후 사용 금액 | String |  | Y | 예: 100000 |
| availableAmount | 출금 후 가용 금액 | String |  | Y | 예: 400000 |
| transactionId | 거래 고유번호 | String |  | Y | 예: MTX20260731131616464 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "minusAccountWithdraw",

    "transmissionDate": "20260731",

    "transmissionTime": "140400",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "minusAccountWithdraw",

    "institutionTransactionUniqueNo": "20260731140400100004"

  },

  "REC": {

    "usedAmount": "1500000",

    "availableAmount": "8500000",

    "transactionId": "MTX20260716143000123"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4110 | 연결 계좌를 찾을 수 없거나 정상 상태가 아님 | 마이너스통장 출금 |
| E4111 | 계좌 소유자가 아님 | 마이너스통장 출금 |
| E4115 | 출금 가능 금액 초과 | 마이너스통장 출금 |
| E4117 | 연체 상태에서 추가 출금 시도 | 마이너스통장 출금 |
| E4121 | 요청 필드 타입 또는 출금액이 올바르지 않음 | 마이너스통장 출금 |

---

#### 2.17.5 마이너스통장 원금 상환

##### 설명

연결 또는 지정 계좌에서 금액을 출금해 마이너스통장 원금을 상환합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/minusAccountRepay | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7011002504332250 |
| repayAccountNo | 상환 출금 계좌번호 | String | 16 | N | 미입력 시 연결 계좌 사용 |
| amount | 상환 금액 | String |  | Y | 숫자 문자열, 예: 100000 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "minusAccountRepay",

    "transmissionDate": "20260731",

    "transmissionTime": "140500",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "minusAccountRepay",

    "institutionTransactionUniqueNo": "20260731140500100005",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "loanAccountNo": "7012345678901234",

  "repayAccountNo": "0011234567890123",

  "amount": "100000"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| repaidInterest | 상환된 이자 | String |  | Y | 예: 0 |
| repaidPrincipal | 상환된 원금 | String |  | Y | 예: 100000 |
| usedAmount | 상환 후 사용 금액 | String |  | Y | 예: 0 |
| status | 계좌 상태 | String |  | Y | 예: NORMAL |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "minusAccountRepay",

    "transmissionDate": "20260731",

    "transmissionTime": "140500",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "minusAccountRepay",

    "institutionTransactionUniqueNo": "20260731140500100005"

  },

  "REC": {

    "repaidInterest": "3000",

    "repaidPrincipal": "97000",

    "usedAmount": "1403000",

    "status": "NORMAL"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4110 | 상환 계좌를 찾을 수 없거나 정상 상태가 아님 | 마이너스통장 원금 상환 |
| E4111 | 계좌 소유자가 아님 | 마이너스통장 원금 상환 |
| E4116 | 상환 금액이 대출 잔액과 이자의 합을 초과 | 마이너스통장 원금 상환 |
| E4120 | 이자·원금 납입 계좌 잔액 부족 | 마이너스통장 원금 상환 |
| E4121 | 요청 필드 타입 또는 상환액이 올바르지 않음 | 마이너스통장 원금 상환 |

---

#### 2.17.6 마이너스통장 상세 조회

##### 설명

마이너스통장 계좌의 한도·사용액·이자·상태·기간 정보를 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7089580150942578 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireMinusAccount",

    "transmissionDate": "20260731",

    "transmissionTime": "140600",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireMinusAccount",

    "institutionTransactionUniqueNo": "20260731140600100006",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "loanAccountNo": "7012345678901234"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7011002504332250 |
| linkedAccountNo | 연결 계좌번호 | String | 16 | Y | 예: 0881816422703833 |
| productName | 상품명 | String |  | Y | 예: MINUS-130417 |
| creditLimit | 신용 한도 | String |  | Y | 예: 500000 |
| usedAmount | 사용 금액 | String |  | Y | 예: 0 |
| availableAmount | 출금 가능 금액 | String |  | Y | 예: 500000 |
| interestRate | 적용 금리 | String |  | Y | 예: 4.5 |
| accruedInterest | 누적 이자 | String |  | Y | 예: 0 |
| interestPaymentDay | 이자 납입일 | String | 2 | Y | 예: 25 |
| repaymentType | 상환 방식 | String |  | Y | 예: FREE_REPAYMENT |
| nextInterestDate | 다음 이자 납입일 | String | 8 | Y | YYYYMMDD, 예: 20260825 |
| startDate | 대출 시작일 | String | 8 | Y | YYYYMMDD, 예: 20260731 |
| maturityDate | 만기일 | String | 8 | Y | YYYYMMDD, 예: 20270731 |
| status | 계좌 상태 | String |  | Y | NORMAL, OVERDUE, CLOSED |
| overdueDays | 연체 일수 | String |  | Y | 예: 0 |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss, 예: 20260731131608 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireMinusAccount",

    "transmissionDate": "20260731",

    "transmissionTime": "140600",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireMinusAccount",

    "institutionTransactionUniqueNo": "20260731140600100006"

  },

  "REC": {

    "loanAccountNo": "7012345678901234",

    "linkedAccountNo": "0011234567890123",

    "productName": "SSAFY 마이너스 통장",

    "creditLimit": "10000000",

    "usedAmount": "1500000",

    "availableAmount": "8500000",

    "interestRate": "4.5",

    "accruedInterest": "36960",

    "interestPaymentDay": "25",

    "repaymentType": "FREE_REPAYMENT",

    "nextInterestDate": "20260725",

    "startDate": "20260716",

    "maturityDate": "20270716",

    "status": "NORMAL",

    "overdueDays": "0",

    "createdAt": "20260716143000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4111 | 계좌 소유자가 아님 | 마이너스통장 상세 조회 |
| E4113 | 상품을 찾을 수 없음 | 마이너스통장 상세 조회 |
| E4121 | 요청 필드 타입이 유효하지 않음 | 마이너스통장 상세 조회 |

---

#### 2.17.7 마이너스통장 목록 조회

##### 설명

사용자의 마이너스통장 계좌 목록과 각 계좌의 현재 상태를 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccountList | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireMinusAccountList",

    "transmissionDate": "20260731",

    "transmissionTime": "140700",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireMinusAccountList",

    "institutionTransactionUniqueNo": "20260731140700100007",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  }

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| accounts[] | 마이너스통장 계좌 목록 | Array |  | Y | 사용자 보유 계좌 |
| └ loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7011002504332250 |
| └ linkedAccountNo | 연결 계좌번호 | String | 16 | Y | 예: 0881816422703833 |
| └ productName | 상품명 | String |  | Y | 예: MINUS-130417 |
| └ creditLimit | 신용 한도 | String |  | Y | 예: 500000 |
| └ usedAmount | 사용 금액 | String |  | Y | 예: 0 |
| └ availableAmount | 출금 가능 금액 | String |  | Y | 예: 500000 |
| └ interestRate | 적용 금리 | String |  | Y | 예: 4.5 |
| └ accruedInterest | 누적 이자 | String |  | Y | 예: 0 |
| └ interestPaymentDay | 이자 납입일 | String | 2 | Y | 예: 25 |
| └ repaymentType | 상환 방식 | String |  | Y | 예: FREE_REPAYMENT |
| └ nextInterestDate | 다음 이자 납입일 | String | 8 | Y | YYYYMMDD, 예: 20260825 |
| └ startDate | 대출 시작일 | String | 8 | Y | YYYYMMDD, 예: 20260731 |
| └ maturityDate | 만기일 | String | 8 | Y | YYYYMMDD, 예: 20270731 |
| └ status | 계좌 상태 | String |  | Y | NORMAL, OVERDUE, CLOSED |
| └ overdueDays | 연체 일수 | String |  | Y | 예: 0 |
| └ createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss, 예: 20260731131608 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireMinusAccountList",

    "transmissionDate": "20260731",

    "transmissionTime": "140700",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireMinusAccountList",

    "institutionTransactionUniqueNo": "20260731140700100007"

  },

  "REC": {

    "accounts": [

      {

        "loanAccountNo": "7012345678901234",

        "linkedAccountNo": "0011234567890123",

        "productName": "SSAFY 마이너스 통장",

        "creditLimit": "10000000",

        "usedAmount": "1500000",

        "availableAmount": "8500000",

        "interestRate": "4.5",

        "accruedInterest": "36960",

        "interestPaymentDay": "25",

        "repaymentType": "FREE_REPAYMENT",

        "nextInterestDate": "20260725",

        "startDate": "20260716",

        "maturityDate": "20270716",

        "status": "NORMAL",

        "overdueDays": "0",

        "createdAt": "20260716143000"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4113 | 연결된 상품을 찾을 수 없음 | 마이너스통장 목록 조회 |
| E4121 | 요청 필드 타입이 유효하지 않음 | 마이너스통장 목록 조회 |

---

#### 2.17.8 마이너스통장 해지

##### 설명

사용액과 미납 이자가 없는 마이너스통장 계좌를 해지합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/closeMinusAccount | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y | apiName: closeMinusAccount |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 사용액·미납 이자가 0인 계좌 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "closeMinusAccount",

    "transmissionDate": "20260731",

    "transmissionTime": "140800",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "closeMinusAccount",

    "institutionTransactionUniqueNo": "20260731140800100008",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "loanAccountNo": "7012345678901234"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7011002504332250 |
| linkedAccountNo | 연결 계좌번호 | String | 16 | Y | 예: 0881816422703833 |
| productName | 상품명 | String |  | Y | 예: MINUS-130417 |
| creditLimit | 신용 한도 | String |  | Y | 예: 500000 |
| usedAmount | 사용 금액 | String |  | Y | 예: 0 |
| availableAmount | 출금 가능 금액 | String |  | Y | 예: 500000 |
| interestRate | 적용 금리 | String |  | Y | 예: 4.5 |
| accruedInterest | 누적 이자 | String |  | Y | 예: 0 |
| interestPaymentDay | 이자 납입일 | String | 2 | Y | 예: 25 |
| repaymentType | 상환 방식 | String |  | Y | 예: FREE_REPAYMENT |
| nextInterestDate | 다음 이자 납입일 | String | 8 | Y | YYYYMMDD, 예: 20260825 |
| startDate | 대출 시작일 | String | 8 | Y | YYYYMMDD, 예: 20260731 |
| maturityDate | 만기일 | String | 8 | Y | YYYYMMDD, 예: 20270731 |
| status | 계좌 상태 | String |  | Y | NORMAL, OVERDUE, CLOSED |
| overdueDays | 연체 일수 | String |  | Y | 예: 0 |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss, 예: 20260731131608 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "closeMinusAccount",

    "transmissionDate": "20260731",

    "transmissionTime": "140800",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "closeMinusAccount",

    "institutionTransactionUniqueNo": "20260731140800100008"

  },

  "REC": {

    "loanAccountNo": "7012345678901234",

    "linkedAccountNo": "0011234567890123",

    "productName": "SSAFY 마이너스 통장",

    "creditLimit": "10000000",

    "usedAmount": "0",

    "availableAmount": "10000000",

    "interestRate": "4.5",

    "accruedInterest": "0",

    "interestPaymentDay": "25",

    "repaymentType": "FREE_REPAYMENT",

    "nextInterestDate": "20260725",

    "startDate": "20260716",

    "maturityDate": "20270716",

    "status": "CLOSED",

    "overdueDays": "0",

    "createdAt": "20260716143000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4111 | 계좌 소유자가 아님 | 마이너스통장 해지 |
| E4113 | 상품을 찾을 수 없음 | 마이너스통장 해지 |
| E4121 | 요청 필드 타입이 유효하지 않음 | 마이너스통장 해지 |
| E4122 | 상환되지 않은 사용 금액 존재 | 마이너스통장 해지 |
| E4123 | 납입되지 않은 이자 존재 | 마이너스통장 해지 |
| E4124 | 이미 해지된 마이너스통장 | 마이너스통장 해지 |

---

#### 2.17.9 마이너스통장 이자 내역 조회

##### 설명

지정 기간의 일별 이자 발생 내역과 누적 이자를 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccountInterest | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7011002504332250 |
| startDate | 조회 시작일 | String | 8 | N | YYYYMMDD, 예: 20260731 |
| endDate | 조회 종료일 | String | 8 | N | YYYYMMDD, 예: 20260731 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireMinusAccountInterest",

    "transmissionDate": "20260731",

    "transmissionTime": "140900",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireMinusAccountInterest",

    "institutionTransactionUniqueNo": "20260731140900100009",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "loanAccountNo": "7012345678901234",

  "startDate": "20260701",

  "endDate": "20260731"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| accruedInterest | 누적 이자 | String |  | Y | 예: 12 |
| ledger[] | 일자별 이자 원장 | Array |  | Y | 조회 기간 내 이자 내역 |
| └ accrueDate | 이자 발생일 | String | 8 | Y | YYYYMMDD, 예: 20260731 |
| └ usedAmount | 기준 사용 금액 | String |  | Y | 예: 100000 |
| └ dailyInterest | 일 이자 | String |  | Y | 예: 12 |
| └ accruedTotal | 누적 이자 합계 | String |  | Y | 예: 12 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireMinusAccountInterest",

    "transmissionDate": "20260731",

    "transmissionTime": "140900",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireMinusAccountInterest",

    "institutionTransactionUniqueNo": "20260731140900100009"

  },

  "REC": {

    "accruedInterest": "36960",

    "ledger": [

      {

        "accrueDate": "20260716",

        "usedAmount": "1500000",

        "dailyInterest": "1849",

        "accruedTotal": "36960"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4111 | 계좌 소유자가 아님 | 마이너스통장 이자 조회 |
| E4121 | 요청 필드 타입이 유효하지 않음 | 마이너스통장 이자 조회 |

---

#### 2.17.10 마이너스통장 알림 조회

##### 설명

마이너스통장 이자 발생·납입 등 계좌 알림 목록을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccountAlerts | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7011002504332250 |
| unreadOnly | 미읽음 알림만 조회 여부 | Boolean |  | N | 예: false |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireMinusAccountAlerts",

    "transmissionDate": "20260731",

    "transmissionTime": "141000",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireMinusAccountAlerts",

    "institutionTransactionUniqueNo": "20260731141000100010",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "loanAccountNo": "7012345678901234",

  "unreadOnly": false

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| alerts[] | 알림 목록 | Array |  | Y | 조건에 맞는 알림 |
| └ alertId | 알림 고유번호 | String |  | Y | 예: ALT20260731131655116 |
| └ alertType | 알림 유형 | String |  | Y | 예: INTEREST_ACCRUAL |
| └ title | 알림 제목 | String |  | Y | 예: 이자 발생 |
| └ message | 알림 내용 | String |  | Y | 예: 오늘 이자 12원이 발생했습니다. |
| └ amount | 관련 금액 | String |  | Y | 예: 12 |
| └ isRead | 읽음 여부 | Boolean |  | Y | 예: false |
| └ createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireMinusAccountAlerts",

    "transmissionDate": "20260731",

    "transmissionTime": "141000",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireMinusAccountAlerts",

    "institutionTransactionUniqueNo": "20260731141000100010"

  },

  "REC": {

    "alerts": [

      {

        "alertId": "ALT20260716000000123",

        "alertType": "INTEREST_ACCRUAL",

        "title": "이자 발생 안내",

        "message": "현재까지 발생한 이자는 36,960원입니다.",

        "amount": "36960",

        "isRead": false,

        "createdAt": "20260716180000"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4111 | 계좌 소유자가 아님 | 마이너스통장 알림 조회 |
| E4121 | 요청 필드 타입 또는 읽음 필터가 올바르지 않음 | 마이너스통장 알림 조회 |

---

#### 2.17.11 마이너스통장 알림 읽음 처리

##### 설명

알림 ID에 해당하는 마이너스통장 알림을 읽음 상태로 변경합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/readMinusAccountAlert | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| alertId | 알림 고유번호 | String |  | Y | 예: ALT20260731131655116 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "readMinusAccountAlert",

    "transmissionDate": "20260731",

    "transmissionTime": "141100",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "readMinusAccountAlert",

    "institutionTransactionUniqueNo": "20260731141100100011",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "alertId": "ALT20260716000000123"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| alertId | 알림 고유번호 | String |  | Y | 요청한 alertId |
| isRead | 읽음 여부 | Boolean |  | Y | 정상 처리 시 true |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "readMinusAccountAlert",

    "transmissionDate": "20260731",

    "transmissionTime": "141100",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "readMinusAccountAlert",

    "institutionTransactionUniqueNo": "20260731141100100011"

  },

  "REC": {

    "alertId": "ALT20260716000000123",

    "isRead": true

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4111 | 계좌 소유자가 아님 | 마이너스통장 알림 읽음 처리 |
| E4121 | 요청 필드 타입 또는 알림 ID가 올바르지 않음 | 마이너스통장 알림 읽음 처리 |

---

#### 2.17.12 마이너스통장 이자 납부

##### 설명

연결 또는 지정 계좌에서 누적 이자를 즉시 납부합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/payMinusAccountInterest | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7011002504332250 |
| paymentAccountNo | 이자 납부 계좌번호 | String | 16 | N | 미입력 시 연결 계좌 사용 |
| amount | 납부 금액 | String |  | N | 미입력 시 누적 이자 전액 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "payMinusAccountInterest",

    "transmissionDate": "20260731",

    "transmissionTime": "141200",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "payMinusAccountInterest",

    "institutionTransactionUniqueNo": "20260731141200100012",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "loanAccountNo": "7012345678901234",

  "paymentAccountNo": "0011234567890123",

  "amount": "36960"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| paidAmount | 납부 금액 | String |  | Y | 예: 12 |
| accruedInterest | 납부 후 누적 이자 | String |  | Y | 예: 0 |
| status | 계좌 상태 | String |  | Y | 예: NORMAL |
| transactionId | 거래 고유번호 | String |  | Y | 예: MTX20260731131805397 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "payMinusAccountInterest",

    "transmissionDate": "20260731",

    "transmissionTime": "141200",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "payMinusAccountInterest",

    "institutionTransactionUniqueNo": "20260731141200100012"

  },

  "REC": {

    "paidAmount": "36960",

    "accruedInterest": "0",

    "status": "NORMAL",

    "transactionId": "MTX20260725100000456"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4110 | 납입 계좌를 찾을 수 없거나 정상 상태가 아님 | 마이너스통장 이자 납부 |
| E4111 | 계좌 소유자가 아님 | 마이너스통장 이자 납부 |
| E4119 | 납입할 이자가 없거나 납입액이 발생 이자를 초과 | 마이너스통장 이자 납부 |
| E4120 | 이자 납입 계좌 잔액 부족 | 마이너스통장 이자 납부 |
| E4121 | 요청 필드 타입 또는 납입액이 올바르지 않음 | 마이너스통장 이자 납부 |

---

#### 2.17.13 마이너스통장 거래 내역 조회

##### 설명

지정 기간의 마이너스통장 출금·상환 거래 내역을 조회합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccountHistory | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7089580150942578 |
| startDate | 조회 시작일 | String | 8 | N | YYYYMMDD, 예: 20260731 |
| endDate | 조회 종료일 | String | 8 | N | YYYYMMDD, 예: 20260731 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "inquireMinusAccountHistory",

    "transmissionDate": "20260731",

    "transmissionTime": "141300",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "inquireMinusAccountHistory",

    "institutionTransactionUniqueNo": "20260731141300100013",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "loanAccountNo": "7012345678901234",

  "startDate": "20260701",

  "endDate": "20260731"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| history[] | 거래 내역 | Array |  | Y | 출금·상환 내역 |
| └ transactionType | 거래 유형 | String | 1 | Y | W: 출금, R: 상환, I: 이자 납입 |
| └ amount | 거래 금액 | String |  | Y | 예: 100000 |
| └ balanceAfter | 거래 후 사용 금액 | String |  | Y | 예: 60000 |
| └ transactionAt | 거래 일시 | String | 14 | Y | YYYYMMDDHHmmss |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "inquireMinusAccountHistory",

    "transmissionDate": "20260731",

    "transmissionTime": "141300",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "inquireMinusAccountHistory",

    "institutionTransactionUniqueNo": "20260731141300100013"

  },

  "REC": {

    "history": [

      {

        "transactionType": "W",

        "amount": "500000",

        "balanceAfter": "1500000",

        "transactionAt": "20260716143000"

      }

    ]

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4111 | 계좌 소유자가 아님 | 마이너스통장 거래 내역 조회 |
| E4121 | 요청 필드 타입이 유효하지 않음 | 마이너스통장 거래 내역 조회 |

---

#### 2.17.14 마이너스통장 한도 변경

##### 설명

사용액 이상 범위에서 마이너스통장 신용 한도를 변경합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/updateMinusAccountLimit | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 요청 헤더 | Object |  | Y |  |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7089580150942578 |
| newCreditLimit | 변경 후 신용 한도 | String |  | Y | 현재 사용액 이상, 예: 1200000 |

##### 요청 메시지 형태

```json
{

  "Header": {

    "apiName": "updateMinusAccountLimit",

    "transmissionDate": "20260731",

    "transmissionTime": "141400",

    "institutionCode": "00100",

    "fintechAppNo": "001",

    "apiServiceCode": "updateMinusAccountLimit",

    "institutionTransactionUniqueNo": "20260731141400100014",

    "apiKey": "<REDACTED_API_KEY>",

    "userKey": "<REDACTED_USER_KEY>"

  },

  "loanAccountNo": "7012345678901234",

  "newCreditLimit": "20000000"

}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 응답 헤더 | Object |  | Y | responseCode H0000: 정상 처리 |
| REC | 응답 데이터 | Object |  | Y | 정상 처리 결과 |
| loanAccountNo | 마이너스통장 계좌번호 | String | 16 | Y | 예: 7011002504332250 |
| linkedAccountNo | 연결 계좌번호 | String | 16 | Y | 예: 0881816422703833 |
| productName | 상품명 | String |  | Y | 예: MINUS-130417 |
| creditLimit | 신용 한도 | String |  | Y | 예: 500000 |
| usedAmount | 사용 금액 | String |  | Y | 예: 0 |
| availableAmount | 출금 가능 금액 | String |  | Y | 예: 500000 |
| interestRate | 적용 금리 | String |  | Y | 예: 4.5 |
| accruedInterest | 누적 이자 | String |  | Y | 예: 0 |
| interestPaymentDay | 이자 납입일 | String | 2 | Y | 예: 25 |
| repaymentType | 상환 방식 | String |  | Y | 예: FREE_REPAYMENT |
| nextInterestDate | 다음 이자 납입일 | String | 8 | Y | YYYYMMDD, 예: 20260825 |
| startDate | 대출 시작일 | String | 8 | Y | YYYYMMDD, 예: 20260731 |
| maturityDate | 만기일 | String | 8 | Y | YYYYMMDD, 예: 20270731 |
| status | 계좌 상태 | String |  | Y | NORMAL, OVERDUE, CLOSED |
| overdueDays | 연체 일수 | String |  | Y | 예: 0 |
| createdAt | 생성 일시 | String | 14 | Y | YYYYMMDDHHmmss, 예: 20260731131608 |

##### 응답 메시지 형태

```json
{

  "Header": {

    "responseCode": "H0000",

    "responseMessage": "정상처리 되었습니다.",

    "apiName": "updateMinusAccountLimit",

    "transmissionDate": "20260731",

    "transmissionTime": "141400",

    "institutionCode": "00100",

    "apiKey": "<REDACTED_API_KEY>",

    "apiServiceCode": "updateMinusAccountLimit",

    "institutionTransactionUniqueNo": "20260731141400100014"

  },

  "REC": {

    "loanAccountNo": "7012345678901234",

    "linkedAccountNo": "0011234567890123",

    "productName": "SSAFY 마이너스 통장",

    "creditLimit": "20000000",

    "usedAmount": "1500000",

    "availableAmount": "18500000",

    "interestRate": "4.5",

    "accruedInterest": "36960",

    "interestPaymentDay": "25",

    "repaymentType": "FREE_REPAYMENT",

    "nextInterestDate": "20260725",

    "startDate": "20260716",

    "maturityDate": "20270716",

    "status": "NORMAL",

    "overdueDays": "0",

    "createdAt": "20260716143000"

  }

}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4111 | 계좌 소유자가 아님 | 마이너스통장 한도 변경 |
| E4113 | 상품을 찾을 수 없음 | 마이너스통장 한도 변경 |
| E4115 | 새 한도가 현재 사용 금액보다 작음 | 마이너스통장 한도 변경 |
| E4121 | 요청 필드 타입 또는 한도 금액이 올바르지 않음 | 마이너스통장 한도 변경 |
| E4125 | 해지된 마이너스통장의 한도 변경 시도 | 마이너스통장 한도 변경 |

---

