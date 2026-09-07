# 대용량 업로드

- 출처: https://project.ssafy.com/docs/ssafy-finance/api-bulk-upload
- 크롤링 날짜: 2026-08-24
- 범위: 화면에 표시된 정적 문서 본문만 추출했으며, 실제 API 호출·인증·데이터 변경은 수행하지 않았습니다.
- 요약: JSON Body·JSON File·CSV File 대용량 업로드의 공통 형식과 2.22.1~2.22.22 상품·계좌·거래·카드·외화·회원 일괄 API의 요청·응답·오류 명세를 정리합니다. 예시 API KEY와 USER KEY 값은 redacted 처리했습니다.

### 2.22 대용량 업로드

#### 공통 요청 형식

대용량 업로드 API는 JSON Body, JSON File, CSV File 방식을 지원합니다.

| 방식 | Content-Type | 옵션 위치 | 업무 데이터 위치 |
| --- | --- | --- | --- |
| JSON Body | `application/json` | JSON 최상위 | `items[].payload` |
| JSON File | `multipart/form-data` | form-data 필드 | JSON 파일의 배열 요소 |
| CSV File | `multipart/form-data` | form-data 필드 | CSV 파일의 각 행 |

`validation`, `continueOnError`, `reference`는 JSON Body 방식에서는 JSON 최상위에 포함하고, JSON File 및 CSV File 방식에서는 form-data 필드로 전달합니다. `file` 필드는 JSON File 및 CSV File 방식에서만 필수이며 JSON Body 방식에서는 사용하지 않습니다.

##### 요청 형식별 예제 (수시입출금 상품 등록, 1건)

**JSON Body**

```
{
  "validation": "N",
  "continueOnError": true,
  "reference": "bulk-register-01",
  "items": [
    {
      "payload": {
        "Header": {
          "institutionCode": "00100",
          "fintechAppNo": "001",
          "apiKey": "<REDACTED_API_KEY>",
          "userKey": "<REDACTED_USER_KEY>",
          "institutionTransactionUniqueNo": "20260811000000000001"
        },
        "bankCode": "001",
        "accountName": "벌크 수시입출금",
        "accountDescription": "벌크 테스트 상품"
      }
    }
  ]
}
```

**JSON File**

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-01
file=demand-deposit-products.json (application/json, UTF-8)
```

```
[
  {
    "Header": {
      "institutionCode": "00100",
      "fintechAppNo": "001",
      "apiKey": "<REDACTED_API_KEY>",
      "userKey": "<REDACTED_USER_KEY>",
      "institutionTransactionUniqueNo": "20260811000000000001"
    },
    "bankCode": "001",
    "accountName": "벌크 수시입출금",
    "accountDescription": "벌크 테스트 상품"
  }
]
```

**CSV File**

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-01
file=demand-deposit-products.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,bankCode,accountName,accountDescription
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000001,001,벌크 수시입출금,벌크 테스트 상품
```

#### 2.22.1 수시입출금 상품 일괄 등록

##### 설명

수시입출금 상품 일괄 등록 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/demandDeposit/products | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.bankCode | 은행코드 | String | 3 | Y |  |
| CSV.accountName | 상품명 | String | 20 | Y |  |
| CSV.accountDescription | 상품설명 | String | 255 | N |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-01
file=01. 수시입출금상품일괄등록.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.institutionTransactionUniqueNo,bankCode,accountName,accountDescription
00100,001,<REDACTED_API_KEY>,20260811000000000001,001,벌크 수시입출금,벌크 테스트용 원화 수시입출금 상품
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| results[].data.bankCode | 은행코드 | String | 3 | Y |  |
| results[].data.bankName | 은행명 | String | 20 | Y |  |
| results[].data.accountTypeCode | 상품구분코드 | String | 3 | Y | 1 : 수시입출금, 2: 정기예금, 3 : 정기적금, 4: 대출 |
| results[].data.accountTypeName | 상품구분명 | String | 20 | Y |  |
| results[].data.accountName | 상품명 | String | 20 | Y |  |
| results[].data.accountDescription | 상품설명 | String | 255 | N |  |
| results[].data.accountType | 통화 | String | 255 | Y | DOMESTIC: 원화, OVERSEAS: 외화 |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-01",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-01",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.2 수시입출금 계좌 일괄 생성

##### 설명

수시입출금 계좌 일괄 생성 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/demandDeposit/accounts | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-02
file=02. 수시입출금계좌일괄생성.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,accountTypeUniqueNo
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000002,00110000000000000001
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.bankCode | 은행코드 | String | 3 | Y |  |
| results[].data.accountNo | 계좌번호 | String | 16 | Y |  |
| results[].data.currency |  | List |  | Y |  |
| results[].data.currency | 통화코드 | String | 8 | Y |  |
| results[].data.currencyName | 통화명 | String | 16 | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-02",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
        "bankCode": "001",
        "accountNo": "0016174648358792",
        "currency": {
          "currency": "KRW",
          "currencyName": "원화"
        }
      }
    }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-02",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.3 수시입출금 계좌 일괄 출금

##### 설명

수시입출금 계좌 일괄 출금 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/demandDeposit/withdrawals | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.accountNo | 계좌번호 | String | 16 | Y |  |
| CSV.transactionBalance | 출금금액 | Long |  | Y |  |
| CSV.transactionSummary | 출금계좌요약 | String | 255 | N |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-03
file=03. 수시입출금계좌일괄출금.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,accountNo,transactionBalance,transactionSummary
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000003,0019763592900582,1000,벌크 테스트 출금
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| results[].data.transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-03",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
        "transactionUniqueNo": "60",
        "transactionDate": "20240401"
      }
    }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-03",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.4 수시입출금 계좌 일괄 입금

##### 설명

수시입출금 계좌 일괄 입금 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/demandDeposit/deposits | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.accountNo | 계좌번호 | String | 16 | Y |  |
| CSV.transactionBalance | 입금금액 | Long |  | Y |  |
| CSV.transactionSummary | 입금계좌요약 | String | 255 | N |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-04
file=04. 수시입출금계좌일괄입금.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,accountNo,transactionBalance,transactionSummary
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000004,0019763592900583,1000,벌크 테스트 입금
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| results[].data.transactionDate | 거래일자 | String | 8 | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-04",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
        "transactionUniqueNo": "59",
        "transactionDate": "20240401"
      }
    }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-04",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.5 수시입출금 계좌 일괄 이체

##### 설명

수시입출금 계좌 일괄 이체 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/demandDeposit/transfers | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.depositAccountNo | 입금계좌번호 | String | 16 | Y | 원화, 외화 계좌 가능 |
| CSV.depositTransactionSummary | 거래 요약내용 (입금계좌) | String | 255 | N |  |
| CSV.transactionBalance | 거래금액 | Long |  | Y | 출금할 금액 입력 |
| CSV.withdrawalAccountNo | 출금계좌번호 | String | 16 | Y | 원화 계좌만 가능 |
| CSV.withdrawalTransactionSummary | 거래 요약내용 (출금계좌) | String | 255 | N |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-05
file=05. 수시입출금계좌일괄이체.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,depositAccountNo,transactionBalance,withdrawalAccountNo,depositTransactionSummary,withdrawalTransactionSummary
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000005,0019763592900583,1000,0019763592900582,벌크 테스트 입금,벌크 테스트 출금
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data[].transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| results[].data[].accountNo | 계좌번호 | String | 16 | Y |  |
| results[].data[].transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |
| results[].data[].transactionType | 거래유형 | String | 1 | Y | `1, 2 |
| results[].data[].transactionTypeName | 거래유형명 | String | 8 | Y | 출금(이체), 입금(이체) |
| results[].data[].transactionAccountNo | 거래 계좌번호 | String | 16 | Y | 이체 거래에 대한 계좌번호 |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-05",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": [
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-05",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.6 예금 상품 일괄 등록

##### 설명

예금 상품 일괄 등록 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/deposit/products | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.bankCode | 은행코드 | String | 3 | Y |  |
| CSV.accountName | 상품명 | String | 20 | Y | 예금 상품명 입력 (ex. 7일 예금) |
| CSV.accountDescription | 상품설명 | String | 255 | N | 예금 상품 설명 입력 (ex. 최대 10% 이자를 지급하는 특별 예금) |
| CSV.subscriptionPeriod | 가입기간 | String | 20 | Y | 2 이상 ~ 365일이하 / 단위(일) |
| CSV.minSubscriptionBalance | 최소가입가능금액 | Long |  | Y | 1 이상 / 단위(원) |
| CSV.maxSubscriptionBalance | 최대가입가능금액 | Long |  | Y | 100000000(1억) 이하 / 단위(원) |
| CSV.interestRate | 이자율 | double |  | Y | 0.1 이상 ~ 20 이하/ 단위(%) |
| CSV.rateDescription | 이자율 설명 | String | 255 | N |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-06
file=06. 예금상품일괄등록.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.institutionTransactionUniqueNo,bankCode,accountName,accountDescription,accountType,subscriptionPeriod,minSubscriptionBalance,maxSubscriptionBalance,interestRate,rateDescription
00100,001,<REDACTED_API_KEY>,20260811000000000006,001,벌크 정기예금,벌크 테스트용 정기예금,DOMESTIC,30,10000,3000000,3.5,30일 만기 연 3.5%
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| results[].data.bankCode | 은행코드 | String | 3 | Y |  |
| results[].data.bankName | 은행명 | String | 20 | Y |  |
| results[].data.accountTypeCode | 상품구분코드 | String | 3 | Y | 1 : 수시입출금, 2: 정기예금, 3 : 정기적금, 4: 대출 |
| results[].data.accountTypeName | 상품구분명 | String | 20 | Y |  |
| results[].data.accountName | 상품명 | String | 20 | Y |  |
| results[].data.accountDescription | 상품설명 | String | 255 | N |  |
| results[].data.subscriptionPeriod | 가입기간 | String | 20 | Y |  |
| results[].data.minSubscriptionBalance | 최소 가입 가능금액 | Long |  | Y |  |
| results[].data.maxSubscriptionBalance | 최대 가입 가능금액 | Long |  | Y |  |
| results[].data.interestRate | 이자율 | double |  | Y |  |
| results[].data.rateDescription | 이자율 설명 | String | 255 | N |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-06",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-06",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.7 예금 계좌 일괄 생성

##### 설명

예금 계좌 일괄 생성 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/deposit/accounts | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.withdrawalAccountNo | 출금계좌번호 | String | 20 | Y | 출금할 수시입출금 계좌번호 기입 |
| CSV.accountTypeUniqueNo | 상품고유번호 | String | 20 | Y | 가입할 예금 상품고유번호 기입 |
| CSV.depositBalance | 가입금액 | Long |  | Y | 가입할 예금의 가입 가능금액 범위 내 기입 |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-07
file=07. 예금계좌일괄생성.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,withdrawalAccountNo,accountTypeUniqueNo,depositBalance
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000007,0019763592900582,00120000000000000001,10000
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.bankCode | 은행코드 | String | 3 | Y |  |
| results[].data.bankName | 은행명 | String | 20 | Y |  |
| results[].data.accountNo | 계좌번호 | String | 16 | Y |  |
| results[].data.accountName | 상품명 | String | 20 | Y |  |
| results[].data.withdrawalBankCode | 출금은행코드 | String | 3 | Y |  |
| results[].data.withdrawalAccountNo | 출금은행계좌 | String | 16 | Y |  |
| results[].data.subscriptionPeriod | 가입기간 | String | 20 | Y |  |
| results[].data.depositBalance | 가입금액 | Long |  | Y |  |
| results[].data.interestRate | 가입적용금리 | double |  | Y |  |
| results[].data.accountCreateDate | 계좌 개설일 | String | 8 | Y |  |
| results[].data.accountExpiryDate | 계좌 만기일 | String | 8 | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-07",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-07",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.8 적금 상품 일괄 등록

##### 설명

적금 상품 일괄 등록 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/savings/products | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.bankCode | 은행코드 | String | 3 | Y |  |
| CSV.accountName | 상품명 | String | 20 | Y | 적금 상품명 입력 (ex. 7일 적금) |
| CSV.accountDescription | 상품설명 | String | 255 | N | 적금 상품 설명 입력 (ex. 최대 19.5% 이자를 지급하는 특별 적금) |
| CSV.subscriptionPeriod | 가입 기간 | String | 20 | Y | 2일 이상 ~ 365일 이하 |
| CSV.minSubscriptionBalance | 최소 가입 가능금액 | Long |  | Y | 1 이상 단위(원) |
| CSV.maxSubscriptionBalance | 최대 가입 가능금액 | Long |  | Y | 1000000(1백만) 이하 단위(원) |
| CSV.interestRate | 이자율 | double |  | Y | 0.1 이상 ~ 20 이하 단위(%) |
| CSV.rateDescription | 이자율 설명 | String | 255 | N |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-08
file=08. 적금상품일괄등록.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,bankCode,accountName,accountDescription,accountType,subscriptionPeriod,minSubscriptionBalance,maxSubscriptionBalance,interestRate,rateDescription
00100,001,<REDACTED_API_KEY>,20260811000000000008,001,벌크 정기적금,벌크 테스트용 정기적금,DOMESTIC,30,10000,1000000,3.5,30일 만기 연 3.5%
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| results[].data.bankCode | 은행코드 | String | 3 | Y |  |
| results[].data.bankName | 은행명 | String | 20 | Y |  |
| results[].data.accountTypeCode | 상품구분코드 | String | 3 | Y | 1 : 수시입출금, 2: 정기예금, 3 : 정기적금, 4: 대출 |
| results[].data.accountTypeName | 상품구분명 | String | 20 | Y |  |
| results[].data.accountName | 상품명 | String | 20 | Y |  |
| results[].data.accountDescription | 상품설명 | String | 255 | N |  |
| results[].data.subscriptionPeriod | 가입 가능기간 | String | 20 | Y |  |
| results[].data.minSubscriptionBalance | 최소 가입 가능금액 | Long |  | Y |  |
| results[].data.maxSubscriptionBalance | 최대 가입 가능금액 | Long |  | Y |  |
| results[].data.interestRate | 이자율 | double |  | Y |  |
| results[].data.rateDescription | 이자율 설명 | String | 255 | N |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-08",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-08",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.9 적금 계좌 일괄 생성

##### 설명

적금 계좌 일괄 생성 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/savings/accounts | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.withdrawalAccountNo | 출금계좌번호 | String | 16 | Y | 가입 금액에 대해 자동이체할 수시입출금 계좌번호 기입 |
| CSV.accountTypeUniqueNo | 상품고유번호 | String | 20 | Y | 가입할 적금 상품고유번호 기입 |
| CSV.depositBalance | 가입금액 | Long |  | Y | 가입할 적금의 가입 가능금액 범위 내 기입 |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-09
file=09. 적금계좌일괄생성.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,withdrawalAccountNo,accountTypeUniqueNo,depositBalance
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000009,0019763592900582,00130000000000000001,10000
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.bankCode | 은행코드 | String | 3 | Y |  |
| results[].data.bankName | 은행명 | String | 20 | Y |  |
| results[].data.accountNo | 계좌번호 | String | 16 | Y |  |
| results[].data.accountName | 상품명 | String | 20 | Y |  |
| results[].data.withdrawalBankCode | 출금은행코드 | String | 3 | Y |  |
| results[].data.withdrawalAccountNo | 출금은행계좌 | String | 16 | Y | 자동이체 수시입출금 계좌번호 |
| results[].data.subscription_period | 가입 기간 | String | 20 | Y |  |
| results[].data.depositBalance | 가입금액 | Long |  | Y |  |
| results[].data.interestRate | 가입적용금리 | double |  | Y |  |
| results[].data.accountCreateDate | 계좌 개설일 | String | 8 | Y |  |
| results[].data.accountExpiryDate | 계좌 만기일 | String | 8 | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-09",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {}
    }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-09",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.10 대출 상품 일괄 등록

##### 설명

대출 상품 일괄 등록 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/loan/products | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.bankCode | 은행코드 | String | 16 | Y |  |
| CSV.accountName | 상품명 | String | 20 | Y | 대출 상품명 입력 (ex. 한국은행 저금리 대출, 신용대출플러스) |
| CSV.accountDescription | 상품설명 | String | 255 | N | 대출 상품명 입력 (ex. 2%대의 이자를 지원하는 저금리 대출, 고정금리대출) |
| CSV.ratingUniqueNo | 신용등급 기준 고유번호 | String | 20 | Y |  |
| CSV.loanPeriod | 대출기간 | int |  | Y | 2 ~ 365 / 단위(일) |
| CSV.minLoanBalance | 최소 대출 금액 | Long |  | Y | 1000 이상 / 단위(원) |
| CSV.maxLoanBalance | 최대 대출 금액 | Long |  | Y | 300000000(3억) 이하 / 단위(원) |
| CSV.interestRate | 기본 금리 | double |  | Y | 0.1 이상 ~ 20 이하 단위(%) |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-10
file=10. 대출상품일괄등록.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.institutionTransactionUniqueNo,bankCode,accountName,accountDescription,ratingUniqueNo,loanPeriod,minLoanBalance,maxLoanBalance,interestRate
00100,001,<REDACTED_API_KEY>,20260811000000000010,001,벌크 신용대출,벌크 테스트용 신용대출,RT-a335h7aa7f3x74ag5,30,10000,3000000,5.0
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| results[].data.bankCode | 은행코드 | String | 3 | Y |  |
| results[].data.bankName | 은행명 | String | 20 | Y |  |
| results[].data.ratingUniqueNo | 신용등급 기준 고유번호 | String | 20 | Y |  |
| results[].data.ratingName | 신용등급명 | String | 20 | Y |  |
| results[].data.accountName | 상품명 | String | 20 | Y |  |
| results[].data.loanPeriod | 대출기간 | int |  | Y |  |
| results[].data.minLoanBalance | 최소 대출 금액 | Long |  | Y |  |
| results[].data.maxLoanBalance | 최대 대출 금액 | Long |  | Y |  |
| results[].data.interestRate | 기본 금리 | double |  | Y |  |
| results[].data.accountDescription | 상품설명 | String | 255 | N |  |
| results[].data.accountTypeCode | 상품구분코드 | String | 3 | Y | 1 : 수시입출금, 2: 정기예금, 3 : 정기적금 , 4 : 대출 |
| results[].data.accountTypeName | 상품구분명 | String | 20 | Y |  |
| results[].data.loanTypeCode | 대출 구분 코드 | String | 3 | Y | 001 : 신용대출 |
| results[].data.loanTypeName | 대출 구분 코드명 | String | 20 | Y |  |
| results[].data.repaymentMethodTypeCode | 대출상환방법 코드 | String | 4 | Y | 0001 : 원리금균등상환 |
| results[].data.repaymentMethodTypeName | 대출상환방법 코드명 | String | 20 | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-10",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-10",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.11 대출 심사 일괄 신청

##### 설명

대출 심사 일괄 신청 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/loan/applications | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-11
file=11. 대출심사일괄신청.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,accountTypeUniqueNo
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000011,00140000000000000001
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| results[].data.status | 심사 상태 | String | 20 | Y | 승인, 거절(대출 상품 신용등급에 사용자의 신용등급 기준 미달 시) |
| results[].data.bankCode | 은행코드 | String | 3 | Y |  |
| results[].data.bankName | 은행명 | String | 20 | Y |  |
| results[].data.ratingUniqueNo | 신용등급 기준 고유번호 | String | 20 | Y |  |
| results[].data.ratingName | 신용등급명 | String | 20 | Y |  |
| results[].data.accountName | 상품명 | String | 20 | Y |  |
| results[].data.loanPeriod | 대출기간 | int |  | Y |  |
| results[].data.minLoanBalance | 최소 대출 금액 | Long |  | Y |  |
| results[].data.maxLoanBalance | 최대 대출 금액 | Long |  | Y |  |
| results[].data.interestRate | 기본 금리 | double |  | Y |  |
| results[].data.accountDescription | 상품설명 | String | 255 | N |  |
| results[].data.applicationDate | 심사 신청 날짜 | String | 8 | Y |  |
| results[].data.applicationTime | 심사 신청 시간 | String | 6 | Y |  |
| results[].data.decisionDate | 심사 날짜 | String | 8 | Y |  |
| results[].data.decisionTime | 심사 시간 | String | 6 | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-11",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
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
      }
    }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-11",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.12 대출 상품 일괄 가입

##### 설명

대출 상품 일괄 가입 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. 대출 심사에서 승인된 상품만 가입할 수 있습니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/loan/accounts | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y | 가입할 대출 상품 고유번호 |
| CSV.loanBalance | 대출금 | Long |  | Y | 해당 상품의 대출 가능 금액 범위 내 입력 |
| CSV.withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y | 대출금 지급 및 상환에 사용할 수시입출금 계좌번호 |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-12
file=12. 대출상품일괄가입.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,accountTypeUniqueNo,loanBalance,withdrawalAccountNo
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260814120100000000,001-4-0f81b43cec324b,10000,0019763592900582
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.accountNo | 계좌번호 | String | 16 | Y |  |
| results[].data.accountName | 상품명 | String | 20 | Y |  |
| results[].data.status | 계좌 상태 | String | 20 | Y | 개설, 상환중, 연체 |
| results[].data.accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| results[].data.loanPeriod | 대출기간 | int |  | Y | 단위(일) |
| results[].data.loanDate | 대출 시작일 | String | 8 | Y | YYYYMMDD |
| results[].data.maturityDate | 대출 만기일 | String | 8 | Y | YYYYMMDD |
| results[].data.loanBalance | 대출금 | Long |  | Y |  |
| results[].data.interestRate | 기본 금리 | double |  | Y | 단위(%) |
| results[].data.withdrawalAccountNo | 출금 계좌번호 | String | 16 | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-12",
  "registeredDate": "20260814",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
        "accountNo": "0014815881614041",
        "accountName": "벌크 신용대출",
        "status": "개설",
        "accountTypeUniqueNo": "001-4-0f81b43cec324b",
        "loanPeriod": "30",
        "loanDate": "20260814",
        "maturityDate": "20260913",
        "loanBalance": "10000",
        "interestRate": "5",
        "withdrawalAccountNo": "0019763592900582"
      }
    }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| A1019 | 없는 상품입니다. 상품 조회를 다시 확인해주세요. |  |
| A1023 | 상품고유번호가 유효하지 않습니다. |  |
| A1030 | 가입금액이 유효하지 않습니다. |  |
| A1037 | 해당 상품에 가입 가능한 금액이 아닙니다. |  |
| A1063 | 대출 심사에 통과한 상품만 가입이 가능합니다. |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-12",
  "registeredDate": "20260814",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.13 신용카드 가맹점 일괄 등록

##### 설명

신용카드 가맹점 일괄 등록 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/creditCard/merchants | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.categoryId | 카테고리ID | String | 20 | Y |  |
| CSV.merchantName | 가맹점명 | String | 100 | Y | 카테고리에 맞는 가맹점명 입력 (ex. 이마트, 에쓰오일, 지하철, 사피학원, 핸드폰요금 등) |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-13
file=13. 신용카드가맹점일괄등록.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.institutionTransactionUniqueNo,categoryId,merchantName
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000013,CG-3fa85f6425e811e,벌크 테스트 주유소
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data[].categoryId | 카테고리ID | String | 20 | Y |  |
| results[].data[].categoryName | 카테고리명 | String | 255 | Y |  |
| results[].data[].merchantId | 가맹점ID | Long |  | Y |  |
| results[].data[].merchantName | 가맹점명 | String | 100 | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-13",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": [
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-13",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.14 신용카드 상품 일괄 등록

##### 설명

신용카드 상품 일괄 등록 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/creditCard/products | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.cardIssuerCode | 카드사코드 | String | 4 | Y |  |
| CSV.cardName | 카드명 | String | 20 | Y | 카드 상품명 입력 (ex. 트래블플러스 카드, 교통할인카드 등) |
| CSV.baselinePerformance | 기준실적 | Long |  | Y | 카드 혜택을 받기 위한 전월 기준실적 0이상 200만원 이하 입력 / 단위(원) |
| CSV.maxBenefitLimit | 최대 혜택한도 | Long |  | Y | 할인받을 수 있는 총 금액 한도 1이상 100만원이하 입력 / 단위(원) |
| CSV.cardDescription | 카드설명 | String | 255 | N | 카드 설명 입력 (ex. 마트 최대 20% 할인, 주유 할인 등) |
| CSV.cardBenefits | 카드 혜택 | List |  | Y | 카테고리 여러개 입력 가능 |
| CSV.categoryId | 카테고리ID | String | 40 | Y |  |
| CSV.discountRate | 할인율 | double |  | Y | 3 ~ 50 사이로 입력 가능 / 단위(%) |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-14
file=14. 신용카드상품일괄등록.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.institutionTransactionUniqueNo,cardIssuerCode,cardName,baselinePerformance,maxBenefitLimit,cardDescription,cardBenefits
00100,001,<REDACTED_API_KEY>,20260811000000000014,1001,벌크 테스트카드,500000,1000000,생활 업종 할인 테스트 카드,"[{""categoryId"":""CG-9ca85f66311a23d"",""discountRate"":""10""}]"
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.cardUniqueNo | 카드 고유번호 | String | 20 | Y |  |
| results[].data.cardIssuerCode | 카드사코드 | String | 4 | Y |  |
| results[].data.cardIssuerName | 카드사명 | String | 20 | Y |  |
| results[].data.cardName | 카드명 | String | 100 | Y |  |
| results[].data.cardTypeCode | 카드종류 코드 | String | 3 | Y | 1 : 신용카드 |
| results[].data.cardTypeName | 카드종류 코드명 | String | 4 | Y | 현재 신용카드만 가능 |
| results[].data.baselinePerformance | 기준실적 | Long |  | Y |  |
| results[].data.maxBenefitLimit | 최대 혜택한도 | Long |  | Y |  |
| results[].data.cardDescription | 카드설명 | String | 255 | N |  |
| results[].data.cardBenefitsInfo | 카드 혜택 정보 | List |  | Y |  |
| results[].data.categoryId | 카테고리ID | String | 40 | Y |  |
| results[].data.categoryName | 카테고리명 | String | 255 | Y |  |
| results[].data.discountRate | 할인율 | double |  | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-14",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-14",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.15 신용카드 일괄 발급

##### 설명

신용카드 일괄 발급 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/creditCard/cards | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.cardUniqueNo | 카드 고유번호 | String | 20 | Y |  |
| CSV.withdrawalAccountNo | 출금계좌번호 | String | 16 | Y | 수시입출금 계좌(수시입출금 계좌로 카드대금 지급) |
| CSV.withdrawalDate | 출금날짜 | String | 10 | Y | 월: 1, 화: 2, 수: 3, 목: 4, 금: 5, 토: 6, 일: 7 |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-15
file=15. 신용카드일괄발급.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,cardUniqueNo,withdrawalAccountNo,withdrawalDate
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000015,10010000000000000001,0019763592900582,5
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.cardNo | 카드번호 | String | 16 | Y |  |
| results[].data.cvc | 카드보안코드 | String | 3 | Y |  |
| results[].data.cardUniqueNo | 카드고유번호 | String | 20 | Y |  |
| results[].data.cardIssuerCode | 카드사코드 | String | 4 | Y |  |
| results[].data.cardIssuerName | 카드사명 | String | 20 | Y |  |
| results[].data.cardName | 카드명 | String | 100 | Y |  |
| results[].data.baselinePerformance | 기준실적 | Long |  | Y |  |
| results[].data.maxBenefitLimit | 최대 혜택한도 | Long |  | Y |  |
| results[].data.cardDescription | 카드설명 | String | 255 | N |  |
| results[].data.cardExpiryDate | 카드만료일 | String | 8 | Y | 개설일 + 5년 |
| results[].data.withdrawalAccountNo | 출금계좌번호 | String | 16 | Y |  |
| results[].data.withdrawalDate | 출금날짜 | String | 10 | Y | 월: 1, 화: 2, 수: 3, 목: 4, 금: 5, 토: 6, 일: 7 |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-15",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-15",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.16 신용카드 결제 일괄 등록

##### 설명

신용카드 결제 일괄 등록 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/creditCard/transactions | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.cardNo | 카드번호 | String | 16 | Y |  |
| CSV.cvc | 카드보안코드 | String | 3 | Y |  |
| CSV.merchantId | 가맹점ID | Long |  | Y |  |
| CSV.paymentBalance | 거래금액 | Long |  | Y |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-16
file=16. 신용카드결제일괄등록.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,cardNo,cvc,merchantId,paymentBalance
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000016,1001123456789012,123,1,10000
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| results[].data.categoryId | 카테고리ID | String | 20 | Y |  |
| results[].data.categoryName | 카테고리명 | String | 255 | Y |  |
| results[].data.merchantId | 가맹점ID | Long |  | Y |  |
| results[].data.merchantName | 가맹점명 | String | 100 | Y |  |
| results[].data.transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |
| results[].data.transactionTime | 거래시각 | String | 6 | Y | HHMMSS |
| results[].data.paymentBalance | 거래금액 | Long |  | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-16",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-16",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.17 외화 수시입출금 상품 일괄 등록

##### 설명

외화 수시입출금 상품 일괄 등록 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/foreignCurrency/products | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.bankCode | 은행코드 | String | 3 | Y |  |
| CSV.accountName | 상품명 | String | 20 | Y |  |
| CSV.accountDescription | 상품설명 | String | 255 | N |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-17
file=17. 외화수시입출금상품일괄등록.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.institutionTransactionUniqueNo,bankCode,accountName,accountDescription
00100,001,<REDACTED_API_KEY>,20260811000000000017,001,벌크 외화입출금,벌크 테스트용 외화 수시입출금 상품
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| results[].data.bankCode | 은행코드 | String | 3 | Y |  |
| results[].data.bankName | 은행명 | String | 20 | Y |  |
| results[].data.accountTypeCode | 상품구분코드 | String | 3 | Y | 1 : 수시입출금, 2: 정기예금, 3 : 정기적금, 4: 대출 |
| results[].data.accountTypeName | 상품구분명 | String | 20 | Y |  |
| results[].data.accountName | 상품명 | String | 20 | Y |  |
| results[].data.accountDescription | 상품설명 | String | 255 | N |  |
| results[].data.accountType | 통화 | String | 255 | Y | DOMESTIC: 원화, OVERSEAS: 외화 |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-17",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-17",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.18 외화 수시입출금 계좌 일괄 생성

##### 설명

외화 수시입출금 계좌 일괄 생성 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/foreignCurrency/accounts | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.accountTypeUniqueNo | 상품 고유번호 | String | 20 | Y |  |
| CSV.currency | 통화 | String | 3 | Y |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-18
file=18. 외화수시입출금계좌일괄생성.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,accountTypeUniqueNo,currency
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000018,00110000000000000002,USD
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.bankCode | 은행코드 | String | 3 | Y |  |
| results[].data.accountNo | 계좌번호 | String | 16 | Y |  |
| results[].data.currency |  | List |  | Y |  |
| results[].data.currency | 통화코드 | String | 8 | Y |  |
| results[].data.currencyName | 통화명 | String | 16 | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-18",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
        "bankCode": "001",
        "accountNo": "0016174648358792",
        "currency": {
          "currency": "KRW",
          "currencyName": "원화"
        }
      }
    }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-18",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.19 외화 수시입출금 계좌 일괄 출금

##### 설명

외화 수시입출금 계좌 일괄 출금 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/foreignCurrency/withdrawals | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.accountNo | 계좌번호 | String | 16 | Y |  |
| CSV.transactionBalance | 출금금액 | Long |  | Y |  |
| CSV.transactionSummary | 출금계좌요약 | String | 255 | N |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-19
file=19. 외화수시입출금계좌일괄출금.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,accountNo,transactionBalance,transactionSummary
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000019,0013165285688973,10,벌크 테스트 외화 출금
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| results[].data.transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-19",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
        "transactionUniqueNo": "60",
        "transactionDate": "20240401"
      }
    }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-19",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.20 외화 수시입출금 계좌 일괄 입금

##### 설명

외화 수시입출금 계좌 일괄 입금 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/foreignCurrency/deposits | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.accountNo | 계좌번호 | String | 16 | Y |  |
| CSV.transactionBalance | 입금금액 | Long |  | Y |  |
| CSV.transactionSummary | 입금계좌요약 | String | 255 | N |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-20
file=20. 외화수시입출금계좌일괄입금.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,accountNo,transactionBalance,transactionSummary
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000020,0013165285688973,10,벌크 테스트 외화 입금
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| results[].data.transactionDate | 거래일자 | String | 8 | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-20",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
        "transactionUniqueNo": "59",
        "transactionDate": "20240401"
      }
    }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-20",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.21 외화 수시입출금 계좌 일괄 이체

##### 설명

외화 수시입출금 계좌 일괄 이체 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. Header.apiName, Header.apiServiceCode, Header.transmissionDate, Header.transmissionTime은 서버가 설정하며, Header.institutionTransactionUniqueNo는 클라이언트가 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/foreignCurrency/transfers | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| Header.institutionCode | 기관코드 | String | 5 | Y | '00100'로 고정 |
| Header.fintechAppNo | 핀테크 앱 일련번호 | String | 3 | Y | '001'로 고정 |
| Header.apiKey | API KEY | String | 40 | Y | 앱 관리자가 발급받은 API KEY |
| Header.userKey | 사용자 KEY | String | 40 | Y | 회원가입 시 발급받은 USER KEY |
| Header.institutionTransactionUniqueNo | 기관 거래 고유번호 | String | 20 | Y | 클라이언트 입력, 재시도 시 동일 값 사용 |
| CSV.depositAccountNo | 입금계좌번호 | String | 16 | Y | 원화, 외화 계좌 가능 |
| CSV.depositTransactionSummary | 거래 요약내용 (입금계좌) | String | 255 | N |  |
| CSV.transactionBalance | 거래금액 | Long |  | Y | 출금할 금액 입력 |
| CSV.withdrawalAccountNo | 출금계좌번호 | String | 16 | Y | 원화 계좌만 가능 |
| CSV.withdrawalTransactionSummary | 거래 요약내용 (출금계좌) | String | 255 | N |  |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-21
file=21. 외화수시입출금계좌일괄이체.csv (text/csv, UTF-8)

Header.institutionCode,Header.fintechAppNo,Header.apiKey,Header.userKey,Header.institutionTransactionUniqueNo,depositAccountNo,transactionBalance,withdrawalAccountNo,depositTransactionSummary,withdrawalTransactionSummary
00100,001,<REDACTED_API_KEY>,<REDACTED_USER_KEY>,20260811000000000021,0017621525990878,10,0013165285688973,벌크 테스트 외화 입금,벌크 테스트 외화 출금
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data[].transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| results[].data[].accountNo | 계좌번호 | String | 16 | Y |  |
| results[].data[].transactionDate | 거래일자 | String | 8 | Y | YYYYMMDD |
| results[].data[].transactionType | 거래유형 | String | 1 | Y | `1, 2 |
| results[].data[].transactionTypeName | 거래유형명 | String | 8 | Y | 출금(이체), 입금(이체) |
| results[].data[].transactionAccountNo | 거래 계좌번호 | String | 16 | Y | 이체 거래에 대한 계좌번호 |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-21",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": [
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
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-21",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

#### 2.22.22 회원 일괄 등록

##### 설명

회원 일괄 등록 API입니다. UTF-8 CSV 파일로 최대 1,000건을 일괄 처리합니다. 회원 CSV는 공통 Header 없이 apiKey와 userId를 입력합니다. 아래 요청 메시지 명세와 예시는 CSV File 방식을 기준으로 작성되었습니다. JSON Body 및 JSON File 요청 형식은 「2.22 대용량 업로드 공통 요청 형식」을 참고하세요.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/bulk/members | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| validation | 검증만 수행 여부 | String | 1 | N | 기본값 Y, Y/N |
| continueOnError | 항목 실패 후 계속 처리 여부 | Boolean |  | N | 기본값 false |
| reference | 일괄 요청 참조값 | String |  | N | 요청값 그대로 반환 |
| file | 일괄 등록 CSV 파일 | File |  | Y | UTF-8, text/csv, 1~1,000행 |
| CSV.apiKey | api 키 | String | 10 | Y | 앱 관리자가 SSAFY 개발 센터에서 발급 받은 API KEY |
| CSV.userId | 사용자 ID | String | 40 | Y | 이메일 형식 |

##### 요청 메시지 형태

```
Content-Type: multipart/form-data
validation=N
continueOnError=true
reference=bulk-register-22
file=22. 회원일괄등록.csv (text/csv, UTF-8)

apiKey,userId
<REDACTED_API_KEY>,bulk.sample.002@ssafy.com
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| totalCount | 요청된 전체 항목 수 | Integer |  | Y | 1~1,000 |
| successCount | 성공한 항목 수 | Integer |  | Y |  |
| failCount | 실패한 항목 수 | Integer |  | Y |  |
| continueOnError | 실패 후 계속 처리 여부 | Boolean |  | Y | 요청 옵션 반환 |
| reference | 요청 참조값 | String |  | N | 요청값 반환 |
| registeredDate | 서버 처리일 | String | 8 | Y | YYYYMMDD, 한 요청의 모든 항목에 동일 적용 |
| results[] | 항목별 처리 결과 | Array |  | Y | CSV 행 순서 |
| results[].index | CSV 행 인덱스 | Integer |  | Y | 0부터 시작 |
| results[].success | 처리 성공 여부 | Boolean |  | Y |  |
| results[].data | 성공 항목 응답 데이터 | Object |  | N | validation=Y이면 생략 가능 |
| results[].data.userId | 사용자 ID | String | 40 | Y |  |
| results[].data.username | 이름 | String | 10 | Y | 이메일 주소의 사용자명(@ 앞)에 해당 |
| results[].data.institutionCode | 기관코드 | String | 40 | Y | 00100'로 고정 |
| results[].data.userKey | user 키 | String | 60 | Y | 랜덤 UUID |
| results[].data.created | 생성일 | String | 10 | Y |  |
| results[].data.modified | 수정일 | String | 10 | Y |  |
| results[].errorCode | 실패 항목 오류 코드 | String |  | N | 성공 시 생략 |
| results[].errorMessages[] | 실패 상세 메시지 | Array |  | N | 성공 시 생략 |

##### 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 1,
  "failCount": 0,
  "continueOnError": true,
  "reference": "bulk-register-22",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": true,
      "data": {
        "userId": "test@ssafy.co.kr",
        "userName": "test",
        "institutionCode": "00100",
        "userKey": "<REDACTED_USER_KEY>",
        "created": "2024-03-04T12:41:30.921299+09:00",
        "modified": "2024-03-04T12:41:30.921295+09:00"
      }
    }
  ]
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| Q1001 | CSV 요청 파일 오류 |  |
| H1000~H1010 | 공통 요청 헤더 검증 오류 |  |
| INVALID_REQUEST | 일괄 요청 형식 또는 검증 오류 |  |
| BIZ_ERROR | 도메인 처리 오류 |  |
| INTERNAL_ERROR | 처리 중 내부 오류 |  |

##### 오류 응답 메시지 형태

```
{
  "totalCount": 1,
  "successCount": 0,
  "failCount": 1,
  "continueOnError": true,
  "reference": "bulk-register-22",
  "registeredDate": "20260810",
  "results": [
    {
      "index": 0,
      "success": false,
      "errorCode": "INVALID_REQUEST",
      "errorMessages": [
        "CSV 요청 항목을 확인해 주세요."
      ]
    }
  ]
}
```

---

