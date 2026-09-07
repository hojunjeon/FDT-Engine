# 사용자 로그인

- 출처: https://project.ssafy.com/docs/ssafy-finance/api-login
- 크롤링 날짜: 2026-08-24
- 범위: 화면에 표시된 정적 문서 본문만 추출했으며, 실제 API 호출·인증·데이터 변경은 수행하지 않았습니다.
- 요약: 사용자 계정 생성과 계정 조회 API의 요청·응답 필드, JSON 예시, 엔드포인트 및 오류코드를 정리합니다. 예시 API KEY와 USER KEY 값은 redacted 처리했습니다.

### 2.2 사용자 로그인

#### 2.2.1 사용자 계정 생성

##### 설명

앱을 이용하기 위한 사용자 회원가입 API 입니다. 회원가입을 통해 사용자 계정을 생성합니다.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/member/ | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| apiKey | API 키 | String | 10 | Y | 앱 관리자가 SSAFY 개발 센터에서 발급 받은 API KEY |
| userId | 사용자 ID | String | 40 | Y | 이메일 형식 |

##### 요청 메시지 형태

```json
{
  "apiKey": "<REDACTED_API_KEY>",
  "userId": "test@ssafy.co.kr"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| userId | 사용자 ID | String | 40 | Y | |
| username | 이름 | String | 10 | Y | 이메일 주소의 사용자명(@ 앞)에 해당 |
| institutionCode | 기관코드 | String | 40 | Y | '00100'로 고정 |
| userKey | 사용자 키 | String | 60 | Y | 랜덤 UUID |
| created | 생성일 | String | 10 | Y | |
| modified | 수정일 | String | 10 | Y | |

##### 응답 메시지 형태

```json
{
  "userId": "test@ssafy.co.kr",
  "userName": "test",
  "institutionCode": "00100",
  "userKey": "<REDACTED_USER_KEY>",
  "created": "2024-03-04T12:41:30.921299+09:00",
  "modified": "2024-03-04T12:41:30.921295+09:00"
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4001 | 빈 데이터이거나 형식에 맞지 않는 데이터입니다. | |
| E4002 | 이미 존재하는 ID입니다. | |
| E4004 | 존재하지 않는 API KEY입니다. | |
| Q1000 | 그 이외에 에러 메시지 | |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. | |

#### 2.2.2 사용자 계정 조회

##### 설명

앱에 등록된 사용자의 정보를 조회합니다. 입력 파라미터(userId)와 정확히 일치하는 결과만 조회합니다. 금융망에 등록된 사용자 계정 정보(email)는 고유하기 때문에 동일 email에 대해 중복하여 계정을 생성할 수 없습니다. 앱(서비스)에서 사용자로부터 입력받은 email이 금융망에 존재하는 것으로 확인될 경우, 다른 email을 사용하도록 안내하시기 바랍니다. 사용자의 email 등록 여부는 다음과 같이 확인할 수 있습니다:

- **사용자 계정 생성 API**를 호출하였을 때의 에러코드 확인:
- 에러코드 4003을 응답받는 경우: 다른 서비스를 통해 이미 등록된 email임을 의미.
- 에러코드 4003을 응답받는 경우: 등록되지 않은 email임을 의미.

##### 요청 메시지 URL

| HTTP URL | HTTP Method |
| --- | --- |
| https://finopenapi.ssafy.io/ssafy/api/v1/member/search | POST |

##### 요청 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| userId | 사용자 ID | String | 40 | Y | 이메일 형식 |
| apiKey | API 키 | String | 10 | Y | 앱 관리자가 SSAFY 개발 센터에서 발급 받은 API KEY |

##### 요청 메시지 형태

```json
{
  "userId": "test@ssafy.co.kr",
  "apiKey": "<REDACTED_API_KEY>"
}
```

##### 응답 메시지 명세

| 변수명 | 설명 | TYPE | 길이 | 필수 | 비고 |
| --- | --- | --- | --- | --- | --- |
| userId | 사용자 ID | String | 40 | Y | |
| username | 이름 | String | 10 | Y | 이메일 주소의 사용자명(@ 앞)에 해당 |
| institutionCode | 기관코드 | String | 40 | Y | '00100'로 고정 |
| userKey | 사용자 키 | String | 60 | Y | |
| created | 생성일 | String | 10 | Y | |
| modified | 수정일 | String | 10 | Y | |

```json
{
  "userId": "test@ssafy.co.kr",
  "userName": "test",
  "institutionCode": "00100",
  "userKey": "<REDACTED_USER_KEY>",
  "created": "2024-03-04T12:41:30.921299+09:00",
  "modified": "2024-03-04T12:41:30.921295+09:00"
}
```

##### 에러코드 목록

| 코드 | 설명 | 비고 |
| --- | --- | --- |
| E4001 | 빈 데이터이거나 형식에 맞지 않는 데이터입니다. | |
| E4002 | 이미 존재하는 ID입니다. | |
| E4003 | 존재하지 않는 ID입니다. | |
| E4004 | 존재하지 않는 API KEY입니다. | |
| Q1000 | 그 이외에 에러 메시지 | |
| Q1001 | 요청 본문의 형식이 잘못되었습니다. JSON 형식 또는 데이터 타입을 확인해 주세요. | |
