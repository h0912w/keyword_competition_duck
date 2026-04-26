# QA 계획

QA는 실제 CLI와 실제 DuckDuckGo 요청으로 수행한다. Mock 기반 DDG QA는 금지한다.

## QA 전용 Google Search API 검증

QA 시에는 **Google Search API**를 사용하여 DDG 측정값의 신뢰성을 검증한다.

### Google API 검증 목적
- DDG 측정값이 실제 검색 결과와 얼마나 일치하는지 확인
- DDG vs Google의 상관관계 분석
- DDG 측정의 편향(bias) 파악

### Google API 사용 제약
- **QA 시에만 사용**: 일반 운영에서는 사용하지 않음
- **할당량 제한**: `QA_MAX_GOOGLE_QUERIES`로 최대 쿼리 수 제한
- **API 키 필요**: `.env`에 `GOOGLE_API_KEY`와 `GOOGLE_SEARCH_ENGINE_ID` 설정 필요

### 비교 방법
1. DDG: 상위 10개 결과 중 title에 키워드가 포함된 수
2. Google API: 전체 검색 결과 수 (approximate)
3. 상관관계 분석: DDG 측정값과 Google 결과 수의 추세 비교

> **주의**: Google API는 전체 결과 수를 반환하지만 DDG는 상위 10개만 측정하므로,
> 직접적인 수치 비교보다는 **추세/상관관계**를 분석한다.

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
`--help`, txt/csv/xlsx 실행, 실제 DDG 요청 로그, DB 생성, 로그 생성, 결과 파일 생성, 컬럼/행 수 검증, 실패 항목 계약, Ctrl+C/재개 검토, **Google API 상관관계 분석**.

## 리포트
`output/qa/qa_report.md`에 실행 일시, 명령어, 입력/출력 파일, DB/로그/컬럼/행 수/실제 DDG 검증, **DDG vs Google 비교 분석**, 문제, 수정 필요 항목, PASS/FAIL을 기록한다.
