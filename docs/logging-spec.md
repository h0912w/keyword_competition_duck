# 로깅 명세

경로: `logs/kcpc.log`

포맷:
```text
[%(asctime)s] [%(levelname)-8s] - %(message)s
```

필수 로그: 시작, 입력 로드 완료, 체크포인트 확인, 측정 시작/완료, DDG 재시도, 측정 실패, 결과 저장, QA 완료.
