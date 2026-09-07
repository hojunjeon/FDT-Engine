# 거래내역 메모

- Source URL: https://project.ssafy.com/docs/ssafy-finance/api-transaction-memo
- Crawl date: 2026-08-24
- Scope: Visible documentation only; no live API calls, authentication, or data-changing requests were made.
- Summary: 원화·외화 수시입출금 거래내역 메모를 작성·수정하는 POST API의 요청·응답 필드와 오류 코드를 정리합니다.

# 거래내역 메모

### 2.13 거래내역 메모

---

#### 2.13.1 거래내역 메모

##### 설명

**원화 및 외화 수시입출금 거래내역에 대한 메모를 작성하고 수정**할 수 있습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/transactionMemo | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| transactionUniqueNo | 거래고유번호 | Long |  | Y |  |
| transactionMemo | 메모 | String | 255 | N |  |

##### 요청 메시지 형태

```json
{
    "Header": {
        "apiName": "transactionMemo",
        "transmissionDate": "20240723",
        "transmissionTime": "152545",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "transactionMemo",
        "institutionTransactionUniqueNo": "20240723152545874018",
        "apiKey": "<REDACTED_API_KEY>",
        "userKey": "<REDACTED_USER_KEY>"
    },
    "accountNo": "0011214764051239",
    "transactionUniqueNo": "6",
    "transactionMemo": "적금 만기"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Header | 공통 |  |  | Y |  |
| REC | 거래내역 메모 정보 | List |  | Y |  |
| memoUniqueNo | 메모 고유번호 | Long |  | Y |  |
| accountNo | 계좌번호 | String | 16 | Y |  |
| transactionUniqueNo | 거래 고유번호 | Long |  | Y |  |
| transactionMemo | 메모 | String | 255 | N |  |
| created | 생성일 | String | 10 | Y |  |

##### 응답 메시지 형태

```json
{
    "Header": {
        "apiName": "createTransactionMemo",
        "transmissionDate": "20240723",
        "transmissionTime": "152545",
        "institutionCode": "00100",
        "fintechAppNo": "001",
        "apiServiceCode": "createTransactionMemo",
        "institutionTransactionUniqueNo": "20240723152545874018",
        "apiKey": "<REDACTED_API_KEY>",
        "userKey": "<REDACTED_USER_KEY>"
    },
    "REC": {
        "memoUniqueNo": "2",
        "accountNo": "0011214764051239",
        "transactionUniqueNo": 6,
        "transactionMemo": "적금 만기",
        "created": "2024-07-23T15:25:45.382886700+09:00[Asia/Seoul]"
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
| A1003 | 계좌번호가 유효하지 않습니다. |  |
| A1010 | 거래고유번호가 유효하지 않습니다. |  |
| A1091 | 거래 메모 길이가 초과되었습니다. |  |
| Q1000 | 그 이외에 에러 메시지 |  |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. |  |

---
