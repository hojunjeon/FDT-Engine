# SSAFY 교육용 금융망 API 개발 가이드

- 출처: https://project.ssafy.com/docs/ssafy-finance/index
- 크롤링 날짜: 2026-08-24
- 범위: 화면에 표시된 정적 문서 본문만 추출했으며, 실제 API 호출·인증·데이터 변경은 수행하지 않았습니다.
- 요약: SSAFY 교육용 금융망 API 목록, 공통 요청·응답 규칙, 약어와 용어 정의를 정리합니다. 예시 API KEY와 USER KEY 값은 redacted 처리했습니다.

## 1. API 목록

| **구분** | **API 명** | **URL** | **HTTP Method** |
| --- | --- | --- | --- |
| MANAGER | APP KEY 발급 API | https://finopenapi.ssafy.io/ssafy/api/v1/edu/app/issuedApiKey | POST |
| MANAGER | APP KEY 재발급 API | https://finopenapi.ssafy.io/ssafy/api/v1/edu/app/reIssuedApiKey | POST |
| MEMBER | 계정 생성 | https://finopenapi.ssafy.io/ssafy/api/v1/member | POST |
| MEMBER | 계정 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/member/search | POST |
| 공통 Header | 은행코드 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/inquireBankCodes | POST |
| 공통 Header | 통화코드 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/inquireBankCurrency | POST |
| DEMAND DEPOSIT | 상품 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/createDemandDeposit | POST |
| DEMAND DEPOSIT | 상품 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositList | POST |
| DEMAND DEPOSIT | 계좌 생성 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/createDemandDepositAccount | POST |
| DEMAND DEPOSIT | 계좌 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccountList | POST |
| DEMAND DEPOSIT | 계좌 조회(단건) | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccount | POST |
| DEMAND DEPOSIT | 예금주 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccountHolderName | POST |
| DEMAND DEPOSIT | 계좌 잔액 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccountBalance | POST |
| DEMAND DEPOSIT | 계좌 출금 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/updateDemandDepositAccountWithdrawal | POST |
| DEMAND DEPOSIT | 계좌 입금 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/updateDemandDepositAccountDeposit | POST |
| DEMAND DEPOSIT | 계좌 이체 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/updateDemandDepositAccountTransfer | POST |
| DEMAND DEPOSIT | 이체 한도 변경 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/updateTransferLimit | POST |
| DEMAND DEPOSIT | 계좌 거래 내역 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireTransactionHistoryList | POST |
| DEMAND DEPOSIT | 계좌 거래 내역 조회(단건) | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/inquireTransactionHistory | POST |
| DEMAND DEPOSIT | 계좌 해지 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/deleteDemandDepositAccount | POST |
| DEPOSIT | 예금 상품 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/createDepositProduct | POST |
| DEPOSIT | 예금 상품 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositProducts | POST |
| DEPOSIT | 예금 계좌 생성 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/createDepositAccount | POST |
| DEPOSIT | 예금 계좌 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositInfoList | POST |
| DEPOSIT | 예금 계좌 조회(단건) | https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositInfoDetail | POST |
| DEPOSIT | 예금 납입 상세 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositPayment | POST |
| DEPOSIT | 예금 만기 이자 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositExpiryInterest | POST |
| DEPOSIT | 예금 중도 해지 이자 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/inquireDepositEarlyTerminationInterest | POST |
| DEPOSIT | 예금 계좌 해지 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/deposit/deleteDepositAccount | POST |
| SAVINGS | 적금 상품 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/createProduct | POST |
| SAVINGS | 적금 상품 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquireSavingsProducts | POST |
| SAVINGS | 적금 계좌 생성 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/createAccount | POST |
| SAVINGS | 적금 계좌 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquireAccountList | POST |
| SAVINGS | 적금 계좌 조회(단건) | https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquireAccount | POST |
| SAVINGS | 적금 납입 회차 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquirePayment | POST |
| SAVINGS | 적금 만기 이자 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquireExpiryInterest | POST |
| SAVINGS | 적금 중도 해지 이자 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/inquireEarlyTerminationInterest | POST |
| SAVINGS | 적금 계좌 해지 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/savings/deleteAccount | POST |
| LOAN | 신용등급 기준 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireAssetBasedCreditRatingList | POST |
| LOAN | 대출 상품 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/createLoanProduct | POST |
| LOAN | 대출 상품 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireLoanProductList | POST |
| LOAN | 내 신용등급 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMyCreditRating | POST |
| LOAN | 대출심사 신청 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/createLoanApplication | POST |
| LOAN | 대출심사 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireLoanApplicationList | POST |
| LOAN | 대출 상품 가입 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/createLoanAccount | POST |
| LOAN | 대출 상품 가입 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireLoanAccountList | POST |
| LOAN | 대출 상환 내역 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireRepaymentRecords | POST |
| LOAN | 대출 일시납 상환 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/updateRepaymentLoanBalanceInFull | POST |
| CREDIT CARD | 카테고리 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireCategoryList | POST |
| CREDIT CARD | 가맹점 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createMerchant | POST |
| CREDIT CARD | 카드사 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireCardIssuerCodesList | POST |
| CREDIT CARD | 카드 상품 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createCreditCardProduct | POST |
| CREDIT CARD | 카드 상품 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireCreditCardList | POST |
| CREDIT CARD | 카드 생성 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createCreditCard | POST |
| CREDIT CARD | 내 카드 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireSignUpCreditCardList | POST |
| CREDIT CARD | 가맹점 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireMerchantList | POST |
| CREDIT CARD | 카드 결제 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createCreditCardTransaction | POST |
| CREDIT CARD | 카드 결제 내역 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireCreditCardTransactionList | POST |
| CREDIT CARD | 카드 결제 취소 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/deleteTransaction | POST |
| CREDIT CARD | 청구서 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireBillingStatements | POST |
| CREDIT CARD | 카드 결제 계좌 수정 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/updateWithdrawalAccount | POST |
| AUTH | 1원 송금 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/accountAuth/openAccountAuth | POST |
| AUTH | 1원 송금 검증 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/accountAuth/checkAuthCode | POST |
| EXCHANGE RATE | 환율 전체 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/exchangeRate | POST |
| EXCHANGE RATE | 환율 단건 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/exchangeRate/exchangeRateSearch | POST |
| EXCHANGE | 환전 예상 금액 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/exchange/estimate | POST |
| EXCHANGE | 환전 신청 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/exchange | POST |
| EXCHANGE | 환전 신청 내역 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/exchange/exchangeHistory | POST |
| DEMAND DEPOSIT FOREIGN | 외화 상품 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/createForeignCurrencyDemandDeposit | POST |
| DEMAND DEPOSIT FOREIGN | 외화 상품 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyDemandDepositList | POST |
| DEMAND DEPOSIT FOREIGN | 외화 계좌 생성 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/createForeignCurrencyDemandDepositAccount | POST |
| DEMAND DEPOSIT FOREIGN | 외화 계좌 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyDemandDepositAccountList | POST |
| DEMAND DEPOSIT FOREIGN | 외화 계좌 조회(단건) | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyDemandDepositAccount | POST |
| DEMAND DEPOSIT FOREIGN | 외화 예금주 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyDemandDepositAccountHolderName | POST |
| DEMAND DEPOSIT FOREIGN | 외화 계좌 잔액 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyDemandDepositAccountBalance | POST |
| DEMAND DEPOSIT FOREIGN | 외화 계좌 출금 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/updateForeignCurrencyDemandDepositAccountWithdrawal | POST |
| DEMAND DEPOSIT FOREIGN | 외화 계좌 입금 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/updateForeignCurrencyDemandDepositAccountDeposit | POST |
| DEMAND DEPOSIT FOREIGN | 외화 계좌 이체 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/updateForeignCurrencyDemandDepositAccountTransfer | POST |
| DEMAND DEPOSIT FOREIGN | 외화 이체 한도 변경 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/updateForeignCurrencyTransferLimit | POST |
| DEMAND DEPOSIT FOREIGN | 외화 계좌 거래 내역 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyTransactionHistoryList | POST |
| DEMAND DEPOSIT FOREIGN | 외화 계좌 거래 내역 조회(단건) | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/inquireForeignCurrencyTransactionHistory | POST |
| DEMAND DEPOSIT FOREIGN | 외화 계좌 해지 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/demandDeposit/foreignCurrency/deleteForeignCurrencyDemandDepositAccount | POST |
| MEMO | 거래내역 메모 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/transactionMemo | POST |
| VIRTUAL ACCOUNT | 가상계좌 발급 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/createVirtualAccount | POST |
| VIRTUAL ACCOUNT | 가상계좌 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/inquireVirtualAccountList | POST |
| VIRTUAL ACCOUNT | 가상계좌 상세 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/inquireVirtualAccount | POST |
| VIRTUAL ACCOUNT | 가상계좌 입금 내역 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/inquireVirtualAccountDeposits | POST |
| VIRTUAL ACCOUNT | 가상계좌 해지 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/closeVirtualAccount | POST |
| VIRTUAL ACCOUNT | 가상계좌 유효기간 연장 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/extendVirtualAccount | POST |
| VIRTUAL ACCOUNT | 가상계좌 보류금 정산 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/settleVirtualAccount | POST |
| NON FACE ACCOUNT | 비대면 계좌개설 1원 인증 요청 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/openAccountAuth | POST |
| NON FACE ACCOUNT | 비대면 계좌 개설 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/createNonFaceAccount | POST |
| NON FACE ACCOUNT | 1원 인증 상태 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/inquireOpenAccountAuth | POST |
| NON FACE ACCOUNT | 계좌 상품 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/inquireAccountProducts | POST |
| NON FACE ACCOUNT | 1원 인증 재요청 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/account/reopenAccountAuth | POST |
| TRANSFER RESERVATION | 예약이체 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/transferReservation | POST |
| TRANSFER RESERVATION | 예약이체 실행 내역 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/inquireTransferReservationHistory | POST |
| TRANSFER RESERVATION | 예약이체 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/inquireTransferReservation | POST |
| TRANSFER RESERVATION | 예약이체 상세 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/inquireTransferReservationDetail | POST |
| TRANSFER RESERVATION | 예약이체 수정 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/updateTransferReservation | POST |
| TRANSFER RESERVATION | 예약이체 취소 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/cancelTransferReservation | POST |
| TRANSFER RESERVATION | 예약이체 일시정지·재개 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/bank/pauseTransferReservation | POST |
| MINUS ACCOUNT | 마이너스통장 상품 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/createMinusAccountProduct | POST |
| MINUS ACCOUNT | 마이너스통장 상품 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccountProductList | POST |
| MINUS ACCOUNT | 마이너스통장 개설 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/createMinusAccount | POST |
| MINUS ACCOUNT | 마이너스통장 출금 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/minusAccountWithdraw | POST |
| MINUS ACCOUNT | 마이너스통장 원금 상환 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/minusAccountRepay | POST |
| MINUS ACCOUNT | 마이너스통장 상세 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccount | POST |
| MINUS ACCOUNT | 마이너스통장 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccountList | POST |
| MINUS ACCOUNT | 마이너스통장 해지 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/closeMinusAccount | POST |
| MINUS ACCOUNT | 마이너스통장 이자 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccountInterest | POST |
| MINUS ACCOUNT | 마이너스통장 알림 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccountAlerts | POST |
| MINUS ACCOUNT | 마이너스통장 알림 읽음 처리 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/readMinusAccountAlert | POST |
| MINUS ACCOUNT | 마이너스통장 이자 납부 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/payMinusAccountInterest | POST |
| MINUS ACCOUNT | 마이너스통장 거래 내역 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/inquireMinusAccountHistory | POST |
| MINUS ACCOUNT | 마이너스통장 한도 변경 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/loan/updateMinusAccountLimit | POST |
| SUBSCRIPTION | 정기결제 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/subscriptionPayment | POST |
| SUBSCRIPTION | 정기결제 서비스 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireSubscriptionService | POST |
| SUBSCRIPTION | 정기결제 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireSubscriptionList | POST |
| SUBSCRIPTION | 정기결제 수정 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/updateSubscription | POST |
| SUBSCRIPTION | 정기결제 취소 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/cancelSubscription | POST |
| SUBSCRIPTION | 정기결제 일시정지·재개 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/pauseSubscription | POST |
| SUBSCRIPTION | 정기결제 이력 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireSubscriptionHistory | POST |
| SUBSCRIPTION | 정기결제 서비스 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createSubscriptionService | POST |
| SUBSCRIPTION | 정기결제 서비스 수정 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/updateSubscriptionService | POST |
| SUBSCRIPTION | 정기결제 즉시 결제 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/paySubscriptionNow | POST |
| SUBSCRIPTION | 구독 카테고리 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireSubscriptionCategory | POST |
| SUBSCRIPTION | 구독 카테고리 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createSubscriptionCategory | POST |
| SUBSCRIPTION | 구독 카테고리 수정/활성화 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/updateSubscriptionCategory | POST |
| VIRTUAL CARD | 가상카드 발급 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/createVirtualCardNumber | POST |
| VIRTUAL CARD | 가상카드 목록 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireVirtualCardList | POST |
| VIRTUAL CARD | 가상카드 상세 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireVirtualCardDetails | POST |
| VIRTUAL CARD | 가상카드 폐기 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/revokeVirtualCard | POST |
| VIRTUAL CARD | 가상카드 결제 검증 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/validateVirtualCardPayment | POST |
| VIRTUAL CARD | 가상카드 결제 내역 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireVirtualCardTransactionList | POST |
| CARD LIMIT | 카드 한도 일시 증액 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/temporaryLimitIncrease | POST |
| CARD LIMIT | 카드 한도 증액 이력 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireLimitIncreaseHistory | POST |
| CARD LIMIT | 카드 한도 증액 취소 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/cancelLimitIncrease | POST |
| CARD LIMIT | 카드 한도 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/creditCard/inquireCardLimit | POST |
| PRECIOUS METAL | 주문 생성 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/createPreciousMetalOrder | POST |
| PRECIOUS METAL | 금·은 실물 현재가 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/inquirePreciousMetalPrice | POST |
| PRECIOUS METAL | 금·은 실물 가격 이력 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/inquirePreciousMetalPriceHistory | POST |
| PRECIOUS METAL | 보유 금·은 실물 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/inquireMyPreciousMetalHoldings | POST |
| PRECIOUS METAL | 금·은 실물 주문 내역 조회 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/inquirePreciousMetalOrders | POST |
| PRECIOUS METAL | 주문 취소 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/cancelPreciousMetalOrder | POST |
| PRECIOUS METAL | 금·은 실물 자산 평가 | https://finopenapi.ssafy.io/ssafy/api/v1/edu/asset/evaluatePreciousMetalAsset | POST |
| BULK | 수시입출금 상품 일괄 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/demandDeposit/products | POST |
| BULK | 수시입출금 계좌 일괄 생성 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/demandDeposit/accounts | POST |
| BULK | 수시입출금 계좌 일괄 출금 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/demandDeposit/withdrawals | POST |
| BULK | 수시입출금 계좌 일괄 입금 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/demandDeposit/deposits | POST |
| BULK | 수시입출금 계좌 일괄 이체 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/demandDeposit/transfers | POST |
| BULK | 예금 상품 일괄 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/deposit/products | POST |
| BULK | 예금 계좌 일괄 생성 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/deposit/accounts | POST |
| BULK | 적금 상품 일괄 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/savings/products | POST |
| BULK | 적금 계좌 일괄 생성 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/savings/accounts | POST |
| BULK | 대출 상품 일괄 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/loan/products | POST |
| BULK | 대출 심사 일괄 신청 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/loan/applications | POST |
| BULK | 대출 상품 일괄 가입 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/loan/accounts | POST |
| BULK | 신용카드 가맹점 일괄 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/creditCard/merchants | POST |
| BULK | 신용카드 상품 일괄 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/creditCard/products | POST |
| BULK | 신용카드 일괄 발급 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/creditCard/cards | POST |
| BULK | 신용카드 결제 일괄 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/creditCard/transactions | POST |
| BULK | 외화 수시입출금 상품 일괄 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/foreignCurrency/products | POST |
| BULK | 외화 수시입출금 계좌 일괄 생성 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/foreignCurrency/accounts | POST |
| BULK | 외화 수시입출금 계좌 일괄 출금 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/foreignCurrency/withdrawals | POST |
| BULK | 외화 수시입출금 계좌 일괄 입금 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/foreignCurrency/deposits | POST |
| BULK | 외화 수시입출금 계좌 일괄 이체 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/foreignCurrency/transfers | POST |
| BULK | 회원 일괄 등록 | https://finopenapi.ssafy.io/ssafy/api/v1/bulk/members | POST |

---

### 1.1 개요

#### 목적

본 문서는 SSAFY 교육용 금융망 API 명세에 대한 기술을 담고 있습니다.
 SSAFY 교육용 금융망 이용승인을 받은 핀테크 기업(이하 "이용기관")은 SSAFY 교육용 금융망이 제공하는 API를 활용하여 이용기관용 응용프로그램(이하 "앱")을 개발할 수 있습니다.

---

### 1.2 용어 정리

| **용어** | **설명** |
| --- | --- |
| **API** | API(애플리케이션 프로그래밍 인터페이스)는 SSAFY 교육용 금융망과 데이터 보유자 간 개인 신용정보를 주고받기 위한 전송 규격을 따름 |
| **URI** | 웹 상의 자원을 유일하게 식별할 수 있는 식별자 또는 주소를 의미 |
| **사용자** | SSAFY 교육용 금융망 업무를 통해 제공되는 서비스를 활용하는 개인 고객 |
| **이용기관 (앱 관리자)** | SSAFY 교육용 금융망 업무 이용 승인을 받아 SSAFY와 이용 계약을 체결한 자 (앱 관리자라 함은 앱 개발자를 뜻함) |
| **SSAFY 교육용 금융망** | SSAFY 교육용 금융망 업무를 위하여 SSAFY에 이용기관 및 정보제공자의 처리시스템을 연결하여 상호간에 정보를 교환하는 시스템. 금융정보 제공 등의 업무를 처리하는 기관. |
| **기관코드** | 기관 약정 시 발급된 핀테크 기관코드를 말함 (‘00100’으로 고정) |
| **핀테크 앱 일렬번호** | 핀테크 서비스 약정 시 발급된 핀테크 앱 일렬번호를 말함 (‘001’로 고정) |
| **기관거래고유번호** | 핀테크 서비스별 거래 고유번호. 새로운 번호로 임의 채번 (YYYYMMDD + HHMMSS + 일련번호 6자리) 또는 20자리의 난수. API 요청 시 항상 새로운 번호로 임의 채번해야 함 |
| **apiKey** | 앱 관리자(개발자)가 발급받은 API KEY |
| **userKey** | 앱 사용자가 회원가입할 때 발급받은 USER KEY |

---

