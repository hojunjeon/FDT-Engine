# SSAFY 금융망 API 크롤링 문서

- 크롤링 날짜: 2026-08-24
- 방식: 인앱 브라우저에서 각 문서를 실제로 열고 최종 `article` 본문을 정적 추출
- 범위: Home 1개 + API 22개 + ERROR 1개
- 검증: 총 24개 개별 문서 생성, 실제 API 호출·인증·금융 데이터 변경 없음
- 보안: 예시 `apiKey`·`userKey`·`API_KEY`·`USER_KEY` 값은 모두 마스킹

## 사용 방법

이 파일을 시작점으로 삼아 필요한 도메인 문서를 연다. 각 개별 문서는 원문 페이지의 제목·설명·엔드포인트·요청/응답 명세·JSON 예시·에러코드 표를 포함한다.

## 진입 페이지

| 페이지 | 개별 문서 |
| --- | --- |
| Home — 전체 API 목록·개요·용어 | [home.md](home.md) |
| ERROR — 공통 에러코드 | [error.md](error.md) |

## API 라우팅

Home에서 확인한 API 정의는 168개이며, 아래 22개 문서로 분리했다.

| 순서 | 도메인 | 엔드포인트 정의 수 | 개별 문서 |
| ---: | --- | ---: | --- |
| 1 | 앱 관리자 API KEY 발급 | 2 | [api-key.md](api/api-key.md) |
| 2 | 사용자 로그인 | 2 | [api-login.md](api/api-login.md) |
| 3 | 공통 | 2 | [api-common.md](api/api-common.md) |
| 4 | 수시입출금 | 14 | [api-demand-deposit.md](api/api-demand-deposit.md) |
| 5 | 예금 | 9 | [api-deposit.md](api/api-deposit.md) |
| 6 | 적금 | 9 | [api-savings.md](api/api-savings.md) |
| 7 | 대출 | 10 | [api-loan.md](api/api-loan.md) |
| 8 | 카드 | 13 | [api-credit-card.md](api/api-credit-card.md) |
| 9 | 1원 인증 | 2 | [api-account-auth.md](api/api-account-auth.md) |
| 10 | 환율 | 2 | [api-exchange-rate.md](api/api-exchange-rate.md) |
| 11 | 환전 | 3 | [api-exchange.md](api/api-exchange.md) |
| 12 | 외화 수시입출금 | 14 | [api-demand-deposit-foreign-currency.md](api/api-demand-deposit-foreign-currency.md) |
| 13 | 거래내역 메모 | 1 | [api-transaction-memo.md](api/api-transaction-memo.md) |
| 14 | 가상계좌 | 7 | [api-virtual-account.md](api/api-virtual-account.md) |
| 15 | 비대면 계좌개설 | 5 | [api-account-opening-untact.md](api/api-account-opening-untact.md) |
| 16 | 예약이체 | 7 | [api-scheduled-transfer.md](api/api-scheduled-transfer.md) |
| 17 | 마이너스통장 | 14 | [api-overdraft-account.md](api/api-overdraft-account.md) |
| 18 | 정기결제 | 13 | [api-recurring-payment.md](api/api-recurring-payment.md) |
| 19 | 가상카드 | 6 | [api-virtual-card.md](api/api-virtual-card.md) |
| 20 | 카드 한도 증액 | 4 | [api-card-limit-increase.md](api/api-card-limit-increase.md) |
| 21 | 금·은 실물 | 7 | [api-physical-gold-silver.md](api/api-physical-gold-silver.md) |
| 22 | 대용량 업로드 | 22 | [api-bulk-upload.md](api/api-bulk-upload.md) |

## 원문 기준

- [SSAFY 금융망 Home](https://project.ssafy.com/docs/ssafy-finance/index)
- [SSAFY 금융망 API 메뉴](https://project.ssafy.com/docs/ssafy-finance/api-key)
- [SSAFY 금융망 ERROR](https://project.ssafy.com/docs/ssafy-finance/error)

원문과 개별 문서가 달라질 수 있으므로 배포 전 원문에서 최신 필드와 오류코드를 다시 확인한다. 이 묶음은 문서 크롤링 결과이며 라이브 성공을 의미하지 않는다.
