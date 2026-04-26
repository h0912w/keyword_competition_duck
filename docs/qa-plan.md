# QA 계획

QA는 실제 CLI와 실제 DuckDuckGo 요청으로 수행한다. Mock 기반 DDG QA는 금지한다.

## 테스트 키워드
```text
seo
keyword research
ultra rare xyzqwerty123seo
best project management software
ai writing tool
```

## 필수 입력 파일
- `input/qa/test_keywords.txt`
- `input/qa/test_keywords.csv`
- `input/qa/test_keywords.xlsx`

## 필수 검증
`--help`, txt/csv/xlsx 실행, 실제 DDG 요청 로그, DB 생성, 로그 생성, 결과 파일 생성, 컬럼/행 수 검증, 실패 항목 계약, Ctrl+C/재개 검토.

## 리포트
`output/qa/qa_report.md`에 실행 일시, 명령어, 입력/출력 파일, DB/로그/컬럼/행 수/실제 DDG 검증, 문제, 수정 필요 항목, PASS/FAIL을 기록한다.
