# QA 계획 v2.1

QA는 실제 CLI와 실제 DuckDuckGo 요청으로 수행한다. Mock 기반 DDG QA는 금지한다.

## QA 원칙 (절대 위배 금지)

**QA는 별도 QA 전용 소프트웨어가 아니라, 실제 사용자가 실행하는 동일한 파이프라인을 QA 에이전트가 직접 수행하는 방식으로 진행한다.**

| 원칙 | 설명 | 위반 예시 |
|---|---|---|
| **실제 파이프라인 사용** | `subprocess.run()` 등을 통해 실제 `kcpc.main` 모듈 실행 | `random.randint()`로 DDG 결과 시뮬레이션 |
| **실제 DDG 요청** | duckduckgo_search 라이브러리로 실제 검색 | Mock 함수로 가짜 결과 반환 |
| **실제 출력 검증** | 생성된 Excel/CSV 파일을 읽어서 검증 | 메모리상 데이터만 검증 |
| **동일 환경 사용** | 사용자와 동일한 설정, 입력, 출력 | QA 전용 별도 설정 사용 |
| **WebSearch 검증 (필수)** | Claude Code WebSearch 도구로 AI 서버 IP를 통해 Google 검색, **필수 QA 항목** | WebSearch 미완료 시 QA 자동 FAIL |

---

## 핵심 변경사항 (v2.1)

1. **GLM API 기반 Google 검증**: Google Search API 대신 GLM API (api.z.ai) 사용
2. **Anthropic 호환 엔드포인트**: `https://api.z.ai/api/anthropic/v1/messages`
3. **Bearer 인증 방식**: `Authorization: Bearer {api_key}` 헤더 사용
4. **간단한 추론 프롬프트**: web_search tool 없이 직접 추론 요청
5. **QA 실행 횟수 1회**: 기본 QA 횟수를 100회에서 1회로 변경
6. **30가지 DDG 품질 검증 요소**: 다각도 분석으로 신뢰성 확보
7. **자동 테스트 단어 생성**: 빈도 기반 영어 단어 5개 자동 생성
8. **실제 파이프라인 강제**: `subprocess.run()`으로 실제 KCPC 실행 후 출력 검증

---

## GLM API 검증 (v2.1)

### 목적
DuckDuckGo 측정값의 신뢰성을 검증하기 위해 GLM API를 사용하여 Google 검색 결과 추정치와 상관관계를 분석한다.

**중요**: GLM API 검증은 **필수 QA 항목**입니다. GLM API 검증이 완료되지 않으면 QA는 자동으로 FAIL로 판정됩니다.

### GLM API 설정

**필수 환경 변수 (.env):**
```env
GLM_API_KEY=your_api_key_here
GLM_BASE_URL=https://api.z.ai/api/anthropic/v1/messages
GLM_MODEL=glm-4.7
```

**성공한 프로젝트 기반:**
```
C:\Users\h0912\claude_project\GLM_WEBSEARCH
```

### QA 통과 기준
| 구분 | 조건 | 결과 |
|------|------|------|
| **DDG 검증** | 모든 단어가 예상 범위 내 | 필수 |
| **GLM API 검증** | 검증이 완료되고 결과 파일 존재 | **필수** |
| **상관관계** | 60% 이상 (high + medium) | 권장 |
| **최종 판정** | DDG + GLM API 모두 통과 | PASS |

### 특징
- **API 키 필요**: GLM API 키가 `.env`에 설정되어야 함
- **IP 주소**: 사용자 컴퓨터가 아닌 **GLM 서버 IP**를 통해 요청
- **간단한 추론**: web_search tool 없이 직접 추론 프롬프트 사용
- **Bearer 인증**: `Authorization: Bearer {api_key}` 헤더 사용

### 실행 방법
```bash
# 1. QA 테스트 실행 (DDG 측정)
python -m kcpc.qa_tester

# 2. GLM API 검증 (자동 실행됨)
# qa_tester.py에서 자동으로 glm_web_search.py 호출

# 또는 독립 실행:
python -m kcpc.glm_web_search

# 3. 결과 확인
# ./output/qa/glm_websearch_results.json
# ./output/qa/glm_websearch_results_report.md
```

### 상관관계 분석 기준
| DDG 측정값 | GLM 추정 | 상관관계 |
|-----------|----------|----------|
| 7-10개 | high (>100K) | high |
| 4-6개 | medium (100-100K) | medium |
| 1-3개 | low (<100) | medium/low |
| 0개 | none (0) | high |

---

## 30가지 DDG 품질 검증 요소

### 1차 그룹: 자체 검증 (핵심)

| # | 요소 | 설명 | 우선순위 |
|---|------|------|----------|
| 1 | **백엔드 교차 검증** | html vs lite 백엔드 결과 비교 | P0 |
| 2 | **재현성 검증** | 3회 반복 측정, 편차 분석 | P0 |
| 3 | **시간대별 일관성** | 오전/오후, 평일/주말 변동 확인 | P1 |
| 4 | **지역별 변동 분석** | region 파라미터 변경 후 비교 | P1 |
| 5 | **키워드 유형별 패턴** | 브랜드명/일반명사/롱테일 차이 | P1 |

### 2차 그룹: 결과 분석

| # | 요소 | 설명 |
|---|------|------|
| 6 | **결과 구조 분석** | title, href, body 필드 활용 |
| 7 | **이상치 탐지** | IQR, Z-score 필터링 |
| 8 | **순위 일관성** | 상위 10개 순서 변화 확인 |
| 9 | **결과 중복 제거** | URL 기반 중복 검출 |
| 10 | **snippet 분석** | body 필드 키워드 빈도 |

### 3차 그룹: 파라미터 최적화

| # | 요소 | 설명 |
|---|------|------|
| 11 | **timelimit 최적화** | d/w/m/y 파라미터 테스트 |
| 12 | **safe_search 효과** | On/Moderate/Off 비교 |
| 13 | **User-Agent 효과** | UA 변경 시 결과 차이 |
| 14 | **max_results 테스트** | 10개 vs 20개 비교 |
| 15 | **A-B 테스트** | 파라미터 조합 실험 |

### 4차 그룹: 통계 검증

| # | 요소 | 설명 |
|---|------|------|
| 16 | **상관계수 분석** | Pearson, Spearman 계산 |
| 17 | **신뢰구간** | 부트스트래핑 구간 추정 |
| 18 | **DDG 일관성 점수(DQCS)** | 100점 만점 신뢰도 산출 |
| 19 | **편향 분석** | 키워드 유형별 편향 확인 |
| 20 | **분산 분석** | 표준편차, 변동계수 계산 |

### 5차 그룹: 수동/반자동 검증

| # | 요소 | 설명 |
|---|------|------|
| 21 | **수동 검증 링크** | DDG 검색 URL 자동 생성 |
| 22 | **표본 추출 검증** | 10개 키워드 무작위 수동 확인 |
| 23 | **교차 엔진 수동 비교** | Google/Bing 수동 검색 후 비교 |
| 24 | **URL 유효성 검증** | HTTP HEAD 요청 확인 |
| 25 | **배치 테스트** | 100/1000개 대량 테스트 |

### 6차 그룹: 안정성/오류 처리

| # | 요소 | 설명 |
|---|------|------|
| 26 | **타임아웃 처리** | 재시도 전략, 지수 백오프 |
| 27 | **오류 분류** | 429/403/네트워크 오류별 처리 |
| 28 | **캐싱 정책 분석** | DDG 서버 캐시 영향 확인 |
| 29 | **결과 최신성** | published_date 확인 |
| 30 | **검색량 추정** | DDG 결과로 검색량 추정 |

---

## 자동 테스트 단어 생성

### 빈도 기반 영어 단어 5개 생성

QA 실행 시 매번 **신규 영어 단어 5개**를 자동 생성합니다.

#### 빈도 분배

| 빈도 그룹 | 점수 범위 | 개수 | 예시 |
|-----------|------------|------|------|
| **고빈도** | 1-3 | 2개 | the, and |
| **중빈도** | 4-7 | 2개 | research, analysis |
| **저빈도** | 8-10 | 1개 | xyzqwerty123-456 |

#### 생성 규칙

1. **고빈도(1-3)**: 영어 가장 빈도 높은 단어
2. **중빈도(4-7)**: 일반적인 기술/비즈니스 용어
3. **저빈도(8-10)**: 무작위 문자열 조합, 희귀 용어

#### 예상 결과 패턴

| 빈도 | 예상 DDG 결과 수 |
|------|------------------|
| 고빈도(1-3) | 8-10 (매우 높음) |
| 중빈도(4-7) | 4-7 (중간) |
| 저빈도(8-10) | 0-3 (매우 낮음) |

---

## WebSearch 딜레이 설정 (Google 차단 방지)

### 딜레이 정책 (google-blocking-rules.md 기반)

WebSearch 도구로 Google 검색 시 **다중 계층 차단 방지**를 적용합니다.

| 설정 | 값 | 설명 |
|------|-----|------|
| **최소 딜레이** | 20초 | 데이터센터 IP 보정 (AI 서버) |
| **최대 딜레이** | 90초 | 충분한 무작위성 |
| **평균 딜레이** | 45초 | 안전 수준 |
| **변동 계수** | 50% | 자연스러운 패턴 (인간 30-50%) |
| **세션당 키워드** | 5개 최대 | 세션 분할 |
| **세션 간 휴식** | 10-30분 | 인간 행동 모사 |

### 예상 실행 시간

- **5개 키워드, 1세션**: 약 3-4분 (평균 45초 × 5)
- **10개 키워드, 2세션**: 약 8-15분 (검색 8분 + 휴식 10분)
- **15개 키워드, 3세션**: 약 15-25분 (검색 11분 + 휴식 20분)

### 딜레이 계산 예시

```
# 기본 45초, ±50% 변동
[1/5] WebSearch('the') → Wait 52s (Base: 45s, Variation: ±22s)
[2/5] WebSearch('research') → Wait 23s (Base: 45s, Variation: ±22s)
[3/5] WebSearch('analysis') → Wait 67s (Base: 45s, Variation: ±22s)
[4/5] WebSearch('python') → Wait 34s (Base: 45s, Variation: ±22s)
[5/5] WebSearch('xyzqwerty123-456') → Wait 48s (Base: 45s, Variation: ±22s)

[BREAK] Wait 18m before next session (if more keywords)
```

### 자연스러운 쿼리 순서

빈도가 섞인 순서로 배치하여 자연스러운 행동 모사:
```
세션 1: high → mid → high → low → mid
세션 2: mid → low → high → mid → low
```

---

## QA 실행 로직 (1회 실행)

### QA 패스 기준

**최종 QA 판정**: DDG 결과와 WebSearch 검증이 모두 완료되어야 PASS

| 구분 | 조건 | 가중치 |
|------|------|--------|
| **DDG 검증** | 모든 단어가 예상 범위 내 | 50% |
| **WebSearch 검증** | 검증 완료 및 결과 파일 존재 | 50% (필수) |
| **상관관계** | high + medium 60% 이상 | 보너스 |

**판정 규칙:**
- **PASS**: DDG 통과 + WebSearch 완료
- **FAIL**: DDG 실패 또는 WebSearch 미완료

테스트 결과가 **예상 패턴과 일치**해야 PASS:

1. **고빈도 단어**: DDG 결과 수 ≥ 7
2. **중빈도 단어**: DDG 결과 수 3~7
3. **저빈도 단어**: DDG 결과 수 ≤ 3

### 실행 설정

- **기본 실행 횟수**: 1회
- **추가 실행 필요 시**: `--max` 옵션으로 지정
- **중단**: `Ctrl+C` 입력 시 중단, 현재까지의 결과 리포트 작성

---

## 필수 검증 항목

### 기본 검증
- `--help` 옵션 동작
- txt/csv/xlsx 입력 실행
- 실제 DDG 요청 로그 확인
- DB 생성, 로그 생성
- 결과 파일 생성
- 컬럼/행 수 검증
- 실패 항목 계약 준수
- Ctrl+C/재개 검토

### WebSearch 검증 (필수)
- **WebSearch 검증 완료**: `websearch_results.json` 파일 존재
- **검증 결과 모두 존재**: 모든 키워드에 대한 Google 추정치
- **상관관계 계산**: DDG vs Google 상관관계 확인
- **최소 상관관계**: high + medium 60% 이상 (권장, 필수 아님)
- **검증 리포트 생성**: `websearch_verification_report.md` 파일 존재

**중요**: WebSearch 검증은 **필수 QA 항목**입니다. WebSearch 검증이 완료되지 않으면:
- QA는 자동으로 FAIL로 판정됩니다
- `qa_report.md`에 "WebSearch 검증 미완료"로 표시됩니다
- WebSearch 지침이 `websearch_instructions.md`에 생성됩니다

### DDG 품질 검증 (30가지)

#### P0 (필수)
1. **백엔드 교차 검증**: html vs lite 일치율 ≥ 80%
2. **재현성 검증**: 3회 반복 편차 ≤ 1

#### P1 (중요)
3. **시간대별 일관성**: 오전/오후 차이 ≤ 2
4. **지역별 변동**: kr-us-jp 차이 분석
5. **키워드 유형별 패턴**: 브랜드명 > 일반명사 > 롱테일 순으로 결과 수 높음

#### P2 (선택)
6-30. 나머지 25가지 요소

---

## QA 리포트

### 리포트 위치

`output/qa/qa_report.md`

### 리포트 내용

```markdown
# QA 리포트

## 실행 정보
- 일시: 2026-04-26 21:00:00
- 재시도 횟수: 3회
- 최종 판정: PASS

## 테스트 단어
| 단어 | 빈도 | 예상 | 실제 | 일치 |
|------|------|------|------|------|
| the | 1 | 8-10 | 9 | ✓ |
| xyzqwerty123 | 10 | 0-3 | 1 | ✓ |

## 30가지 검증 결과
### 백엔드 교차 검증
- html/lite 일치율: 85%

### 재현성 검증
- 3회 반복 편차: 0.8

...

## 무한 반복 이력
| 회차 | 판정 | 실패 사유 |
|------|------|-----------|
| 1 | FAIL | 고빈도 단어 결과 수 부족 |
| 2 | FAIL | 저빈도 단어 결과 수 과다 |
| 3 | PASS | - |

## 최종 판정
**PASS**
```

---

## WebSearch 검증 결과

```markdown
## WebSearch 검증 (AI Server IP)

| Keyword | DDG Count | Google Estimate | Correlation |
|---------|-----------|-----------------|-------------|
| the | 9 | high | high |
| research | 6 | medium | high |
| xyzqwerty123-456 | 1 | low | medium |

### 상관관계 통계
- High Correlation: 2개 (66.7%)
- Medium Correlation: 1개 (33.3%)
- Low Correlation: 0개 (0%)
- No Correlation: 0개 (0%)

### 판정
**PASS** ✅
DDG 측정값이 Google 검색 결과와 66.7% 이상 상관관계를 보임.
```

---

## 실행 명령어

```bash
# 1. QA 실행 (자동 단어 생성, 1회)
python -m kcpc.qa_tester

# 2. WebSearch 검증 준비
python scripts/run_websearch_verification.py

# 3. Claude Code 세션에서 WebSearch 도구로 각 키워드 검색
# (AI 서버 IP를 통해 Google 검색)

# 4. 결과 저장 후 리포트 생성
python -m kcpc.qa_websearch_verifier

# QA 리포트 확인
cat ./output/qa/qa_report.md
cat ./output/qa/websearch_verification_report.md
```

### WebSearch 검증 상세 절차

1. **QA 실행**: `python -m kcpc.qa_tester`
   - 빈도 기반 테스트 단어 10개 자동 생성
   - 실제 DDG 검색으로 측정값 수집
   - 결과 파일: `./output/qa/qa_result_001.xlsx`

2. **WebSearch 준비**: `python scripts/run_websearch_verification.py`
   - WebSearch 검증 태스크 파일 생성
   - 결과 템플릿 파일 생성
   - 태스크 파일: `./output/qa/websearch_task_*.json`

3. **WebSearch 실행** (Claude Code 세션 내)
   ```python
   # 각 키워드에 대해 WebSearch 도구 실행
   WebSearch("python")
   WebSearch("research")
   WebSearch("xyzqwerty123-456")
   ```
   - AI 서버 IP를 통해 Google 검색
   - 결과 규모 추정 (high/medium/low/none)

4. **결과 저장**: `./output/qa/websearch_results.json` 업데이트

5. **리포트 생성**: `python -m kcpc.qa_websearch_verifier`
   - DDG vs WebSearch 상관관계 분석
   - 최종 검증 리포트 생성
