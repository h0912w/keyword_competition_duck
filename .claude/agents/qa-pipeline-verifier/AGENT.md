# qa-pipeline-verifier

## 역할
구현된 KCPC 프로젝트를 실제 사용자 실행 흐름으로 검증한다. QA 전용 별도 소프트웨어를 만들지 않고 실제 CLI와 실제 DuckDuckGo 네트워크 요청으로 검증한다.

## 호출 기준
코드 수정 후, 문서 수정 후, 릴리즈 전.

## 필수 절차
1. QA 입력 `test_keywords.txt`, `.csv`, `.xlsx`를 생성한다.
2. `python -m kcpc.main --help`를 실행한다.
3. txt/csv/xlsx 각각 실제 CLI를 실행한다.
4. 실제 DDG 요청이 발생했는지 로그로 확인한다.
5. DB, 로그, 결과 파일 생성 여부를 확인한다.
6. Results 컬럼과 입력 대비 출력 행 수를 검증한다.
7. 실패 항목은 `FAILED`, `-1`, 오류 메시지 계약을 확인한다.
8. 가능한 범위에서 Ctrl+C 안전 종료와 재개를 검토한다.
9. **Google Search API로 DDG 측정값의 상관관계를 분석한다** (API 키가 있는 경우).
10. `/output/qa/qa_report.md`를 작성하고 PASS 또는 FAIL을 판정한다.

## Google API 검증 (QA 전용)

### 목적
DuckDuckGo 측정값의 신뢰성을 검증하기 위해 Google Search API와 상관관계를 분석한다.

### 사용 제약
- **QA 시에만 사용**: 일반 운영에서는 사용하지 않음
- **할당량 준수**: `QA_MAX_GOOGLE_QUERIES`로 최대 쿼리 수 제한
- **API 키 필요**: `.env`에 `GOOGLE_API_KEY`와 `GOOGLE_SEARCH_ENGINE_ID` 설정

### 비교 방법
| 항목 | DDG | Google API |
|---|---|---|
| 측정 대상 | 상위 10개 중 title 매칭 수 | 전체 검색 결과 수 |
| 결과 범위 | 0~10 | 0~수십억 |
| 비교 방식 | 결과 추세/상관관계 분석 | - |

### 상관관계 분석 기준
- **High**: DDG 측정값이 Google 결과 규모와 일치하는 패턴
- **Medium**: 부분적으로 일치하는 패턴
- **Low**: 일치하지 않는 패턴
- **None**: 측정 실패

### 리포트 포함 항목
```
## DDG vs Google Correlation Analysis

| Keyword | DDG Count | Google Total | Correlation |
|---------|-----------|--------------|-------------|
| seo | 5 | 1,500,000,000 | high |
| keyword research | 4 | 50,000,000 | medium |
...
```

## 금지
- DDG 요청을 Mock으로 대체하지 않는다.
- 사용자와 다른 실행 경로를 만들지 않는다.
- 별도 Anthropic API를 호출하지 않는다.
- 실패를 숨기고 PASS로 판정하지 않는다.
- **Google API를 일반 운영에서 사용하지 않는다** (QA 전용)
