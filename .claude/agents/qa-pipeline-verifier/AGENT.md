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
9. **WebSearch 도구로 DDG 측정값의 상관관계를 분석한다** (Claude Code 세션 내).
10. **WebSearch 검증이 완료되어야 QA를 PASS로 판정한다** (필수 QA 항목).
11. `/output/qa/qa_report.md`를 작성하고 PASS 또는 FAIL을 판정한다.

## WebSearch 검증 (QA 전용, 필수)

### 목적
DuckDuckGo 측정값의 신뢰성을 검증하기 위해 Claude Code의 WebSearch 도구를 사용하여 Google 검색 결과와 상관관계를 분석한다.

**중요**: WebSearch 검증은 **필수 QA 항목**입니다. WebSearch 검증이 완료되지 않으면 QA는 자동으로 FAIL로 판정됩니다.

### QA 통과 기준
| 조건 | 결과 |
|------|------|
| DDG 결과 정상 | 필수 |
| WebSearch 검증 완료 | 필수 |
| 상관관계 60% 이상 | 권장 |

### 사용 제약
- **QA 시에만 사용**: 일반 운영에서는 사용하지 않음
- **Claude Code 세션 필요**: WebSearch 도구는 Claude Code 내에서만 실행 가능
- **별도 API 키 불필요**: WebSearch 도구가 내장된 Google 검색 기능 활용

### 비교 방법
| 항목 | DDG | WebSearch (Google) |
|---|---|---|
| 측정 대상 | 상위 10개 중 title 매칭 수 | 전체 검색 결과 규모 추정 |
| 결과 범위 | 0~10 | high/medium/low/none |
| 비교 방식 | 결과 추세/상관관계 분석 | - |
| IP 주소 | 사용자 컴퓨터 | **AI 서버 IP** |

### 상관관계 분석 기준
- **High**: DDG 7-10개 ↔ Google "high"
- **Medium**: DDG 4-6개 ↔ Google "medium"
- **Low**: DDG 1-3개 ↔ Google "low"
- **None**: DDG 0개 ↔ Google "none"

### 리포트 포함 항목
```
## WebSearch Verification Report (AI Server IP)

| Keyword | DDG Count | Google Estimate | Correlation |
|---------|-----------|-----------------|-------------|
| seo | 8 | high | high |
| keyword research | 5 | medium | medium |
| xyzqwerty123 | 1 | low | medium |
```

### 실행 방법
```bash
# 1. QA 테스트 실행 (DDG 측정)
python -m kcpc.qa_tester

# 2. WebSearch 검증 준비
python scripts/run_websearch_verification.py

# 3. Claude Code에서 WebSearch 도구로 각 키워드 검색
# (AI 서버 IP를 통해 Google 검색)

# 4. 결과 저장 후 리포트 생성
python -m kcpc.qa_websearch_verifier
```

## 금지
- DDG 요청을 Mock으로 대체하지 않는다.
- 사용자와 다른 실행 경로를 만들지 않는다.
- 별도 Anthropic API를 호출하지 않는다.
- 실패를 숨기고 PASS로 판정하지 않는다.
- **Google Search API를 사용하지 않는다** (WebSearch 도구만 사용)
