# 앱 관리자(개발자) API KEY 발급

- 출처: https://project.ssafy.com/docs/ssafy-finance/api-key
- 크롤링 날짜: 2026-08-24
- 범위: 화면에 표시된 정적 문서 본문만 추출했으며, 실제 API 호출·인증·데이터 변경은 수행하지 않았습니다.
- 요약: 앱 관리자(개발자) API KEY 발급과 재발급 API의 설명, 요청·응답 명세, JSON 예시, 엔드포인트 및 오류코드를 정리합니다. 예시 자격증명 값은 redacted 처리했습니다.

### 2.1 앱 관리자(개발자) API KEY 발급

#### 2.1.1 앱 API KEY 발급

##### 설명

OPEN API를 사용하기 전 API KEY를 발급 받는 API 입니다. 발급받은 API 키를 통해 관리자(개발자)는 앱을 생성합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/app/issuedApiKey | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| managerId | 관리자 ID | String | 30 | Y | 이메일 형식 |

##### 요청 메시지 형태

```json
{
  "managerId": "ssafy@ssafy.co.kr"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| managerId | 관리자 ID | String | 30 | Y | 이메일 형식 |
| apiKey | API 키 | String | 40 | Y | UUID 40 |
| creationDate | 생성일 | String | 8 | Y | 계정 생성일 |
| expirationDate | 만료일 | String | 8 | Y | 계정 만료일 |

##### 응답 메시지 형태

```json
{
  "managerId": "ssafy@ssafy.co.kr",
  "apiKey": "<REDACTED_API_KEY>",
  "creationDate": "20240415",
  "expirationDate": "20250415"
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E3000 | 이미 존재하는 관리자 ID입니다. | |
| E3002 | 관리자 ID가 유효하지 않습니다. | |
| A1080 | 등록되지 않은 관리자 이메일입니다. | |
| Q1000 | 그 이외에 에러 메시지 | |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. | |
| --- |  |  |

#### 2.1.2 앱 API KEY 재발급

##### 설명

현재 사용 중인 API KEY를 확인하거나, 필요한 경우 새로운 API KEY를 생성할 수 있습니다. 재발급 이후 기존 API KEY는 더 이상 사용되지 않습니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/edu/app/reIssuedApiKey | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| managerId | 관리자 ID | String | 30 | Y | 이메일 형식 |

##### 요청 메시지 형태

```json
{
  "managerId": "ssafy@ssafy.co.kr"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| managerId | 관리자 ID | String | 30 | Y | 이메일 형식 |
| apiKey | API 키 | String | 40 | Y | UUID 40 |

##### 응답 메시지 형태

```json
{
  "managerId": "ssafy@ssafy.co.kr",
  "apiKey": "<REDACTED_API_KEY>"
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E3001 | 존재하지 않는 관리자 ID입니다. | |
| E3002 | 관리자 ID가 유효하지 않습니다. | |
| E3003 | 현재 사용중인 API KEY가 만료되어 재발급이 불가합니다. | |
| Q1000 | 그 이외에 에러 메시지 | |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. | |
