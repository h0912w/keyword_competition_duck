# Claude Code 프로젝트 통합 설계서  
# KCPC: Keyword Competition Page Counter  
## 키워드 경쟁 페이지 수 측정 시스템

**문서 버전:** v1.0  
**작성 목적:** 다른 AI가 작성한 초안 설계서를 Claude Code가 바로 구현 작업에 참조할 수 있는 프로젝트 설계 지침서로 재구성한다.  
**최종 구현 대상:** 로컬 실행형 Python 배치 프로그램  
**핵심 출력물:** 입력 키워드별 DuckDuckGo 상위 검색 결과 Title 매칭 수를 기록한 Excel/CSV 파일  

---

# 1. 작업 컨텍스트 문서

## 1.1 배경

사용자는 SEO용 웹페이지 제목 또는 키워드 후보를 대량으로 보유하고 있으며, 각 키워드를 제목에 포함하는 경쟁 웹페이지가 얼마나 존재하는지 추정하고자 한다.

정식 Google Search API는 호출량이 제한적이고, 일반 검색 결과 크롤링은 차단 위험이 크다. 따라서 본 프로젝트는 DuckDuckGo 검색 결과를 이용하여, 키워드별 상위 10개 검색 결과 중 실제 `title` 필드에 해당 키워드가 포함된 결과 수를 측정한다.

이 값은 “전체 인터넷 경쟁 페이지 수”가 아니라, **DuckDuckGo 상위 10개 검색 결과 기준의 제목 매칭 측정치**이다.  
따라서 출력 열 이름도 실제 의미를 반영하여 `Top10_Title_Match_Count`를 기본으로 사용한다.

## 1.2 목적

사용자가 `.txt`, `.csv`, `.xlsx` 파일로 세로 나열된 영어 키워드 목록을 입력하면, 각 키워드에 대해 DuckDuckGo 검색을 수행하고, 상위 10개 결과의 제목에 키워드가 포함되는 개수를 측정하여 결과 파일로 내보낸다.

## 1.3 범위

### 포함 범위

- 로컬 PC에서 실행되는 Python CLI 프로그램
- 입력 파일 파싱
- DuckDuckGo 검색 요청
- 검색 결과 title 필드 기반 2차 검증
- 키워드별 측정 결과 SQLite 체크포인트 저장
- 중단 후 재실행 시 이어서 처리
- 결과 Excel/CSV 출력
- 로그 파일 저장
- 실제 네트워크 기반 통합 QA

### 제외 범위

- Google Search API 사용
- 유료 API 사용
- 프록시 우회, 차단 회피 목적의 자동화
- 검색엔진 robots.txt 또는 이용약관 우회
- 저공급/고공급 같은 임의 분류
- 웹 UI 또는 GUI
- 별도 QA 전용 소프트웨어 제작
- Claude Code 실행 중 별도 Anthropic API 호출

## 1.4 입력 정의

| 항목 | 내용 |
|---|---|
| 입력 파일 형식 | `.txt`, `.csv`, `.xlsx` |
| 입력 구조 | 첫 번째 열에 키워드가 세로로 나열됨 |
| 키워드 언어 | 기본적으로 영어 키워드 |
| 허용 데이터 | 공백 포함 문자열 가능 |
| 제외 데이터 | 빈 줄, 공백만 있는 셀, NaN |

## 1.5 출력 정의

| 출력물 | 형식 | 설명 |
|---|---|---|
| 최종 결과 파일 | `.xlsx` 기본, 선택적으로 `.csv` | 키워드와 측정 수치 기록 |
| SQLite DB | `.db` | 체크포인트 및 중간 결과 저장 |
| 로그 파일 | `.log` | 실행 이력, 오류, 재시도 기록 |
| QA 결과 문서 | `.md` 또는 `.xlsx` | QA 에이전트가 실제 파이프라인을 수행한 결과 |

## 1.6 최종 출력 파일 기본 컬럼

| 컬럼명 | 설명 |
|---|---|
| `Keyword` | 입력 키워드 |
| `Top10_Title_Match_Count` | DuckDuckGo 상위 10개 결과 중 title에 키워드가 포함된 결과 수 |
| `Status` | `DONE`, `FAILED`, `SKIPPED` 등 처리 상태 |
| `Error_Message` | 실패 시 오류 메시지 |
| `Updated_At` | 마지막 처리 시각 |

> 원본 초안의 `Competition_Page_Count`는 실제 의미보다 과장될 수 있으므로, 본 설계서에서는 `Top10_Title_Match_Count`를 기본 컬럼명으로 사용한다. 단, 사용자가 원하면 출력 설정에서 별칭으로 `Competition_Page_Count`를 추가할 수 있다.

## 1.7 주요 제약조건

1. DuckDuckGo 검색 결과만 사용한다.
2. 검색 결과 수 전체를 추정하지 않는다.
3. `intitle:"{keyword}"` 쿼리를 사용하되, 검색엔진이 연산자를 무시할 가능성에 대비해 title 필드 2차 검증을 반드시 수행한다.
4. 측정값은 상위 10개 결과 중 title 매칭 개수이다.
5. 실패 시 해당 키워드는 `-1`로 기록하고 전체 파이프라인은 계속 진행한다.
6. 모든 중간 결과는 SQLite에 즉시 저장한다.
7. 로컬 환경에서 독립 실행 가능해야 한다.
8. **QA는 별도 QA 전용 소프트웨어가 아니라, 실제 사용자가 실행하는 동일한 파이프라인을 QA 에이전트가 직접 수행하는 방식으로 진행한다.**
   - **금지 사항**: QA 코드에서 DDG 결과를 시뮬레이션(mock/stub)하는 것은 엄격히 금지된다.
   - **구현 방식**: `subprocess.run()` 등을 통해 실제 `kcpc.main` 모듈을 실행하고, 생성된 Excel/CSV 출력을 읽어서 검증한다.
   - **사유**: QA는 사용자와 동일한 환경에서 동일한 코드를 실행해야만 실제 버그를 발견할 수 있다.
9. AI 판정은 현재 실행 중인 Claude Code 세션이 직접 수행하며, 별도로 `anthropic` 패키지를 호출하거나 API 키를 설정할 필요가 없다.

## 1.8 용어 정의

| 용어 | 정의 |
|---|---|
| KCPC | Keyword Competition Page Counter |
| 키워드 | 사용자가 입력한 SEO 후보 문자열 |
| 측정값 | DuckDuckGo 상위 10개 검색 결과 중 title에 키워드가 포함된 결과 수 |
| 체크포인트 | 중단 후 재개를 위한 SQLite 저장 상태 |
| DONE | 정상 측정 완료 |
| FAILED | 측정 실패, 결과 `-1` 기록 |
| PENDING | 아직 처리 전 |
| RUNNING | 현재 처리 중 |
| QA 에이전트 | 실제 파이프라인을 실행해 구현 결과를 검증하는 Claude Code 서브에이전트 |

---

# 2. 워크플로우 정의

## 2.1 전체 흐름도

```text
[사용자 입력 파일 준비]
        |
        v
[Step 1. 입력 파일 탐지 및 파싱]
        |
        v
[Step 2. 키워드 정제 및 중복 처리]
        |
        v
[Step 3. SQLite 체크포인트 초기화/복구]
        |
        v
[Step 4. 키워드별 DuckDuckGo 검색]
        |
        v
[Step 5. title 필드 2차 검증]
        |
        v
[Step 6. 결과 DB 즉시 저장]
        |
        v
[Step 7. 모든 키워드 완료 여부 판단]
        |
        +---- 미완료 ----> [Step 4 반복]
        |
        v
[Step 8. 최종 Excel/CSV Export]
        |
        v
[Step 9. QA 에이전트 실제 파이프라인 검증]
        |
        v
[Step 10. QA 결과 리포트 생성]
```

## 2.2 상태 전이

```text
[PENDING]
    |
    v
[RUNNING]
    |------------------ 성공 ------------------|
    v                                          v
[DONE]                             competition_count = 0~10
    |
    |------------------ 실패 ------------------|
    v
[FAILED]                           competition_count = -1
```

## 2.3 단계별 상세 정의

### Step 1. 입력 파일 탐지 및 파싱

| 항목 | 내용 |
|---|---|
| 처리 주체 | 스크립트 |
| 관련 스킬 | `file-io-skill` |
| 입력 | 사용자 지정 파일 경로 |
| 출력 | `list[str]` 키워드 목록 |
| 코드 처리 | 확장자 판별, txt/csv/xlsx 파싱, 첫 번째 열 추출 |
| LLM 판단 | 없음 |
| 성공 기준 | 지원 확장자 파일에서 비어 있지 않은 키워드 목록이 생성됨 |
| 검증 방법 | 규칙 기반 검증, 스키마 검증 |
| 실패 시 처리 | 지원하지 않는 확장자 또는 파일 없음 → 즉시 중단하고 사용자에게 오류 출력 |

### Step 2. 키워드 정제 및 중복 처리

| 항목 | 내용 |
|---|---|
| 처리 주체 | 스크립트 |
| 관련 스킬 | `keyword-normalizer-skill` |
| 입력 | 원본 키워드 목록 |
| 출력 | 정제된 키워드 목록 및 원본 인덱스 매핑 |
| 코드 처리 | strip, 빈 값 제거, NaN 제거 |
| LLM 판단 | 중복 처리 정책 검토 시 main-orchestrator가 판단 |
| 성공 기준 | 빈 문자열이 제거되고 원본 인덱스가 보존됨 |
| 검증 방법 | 규칙 기반 검증 |
| 실패 시 처리 | 유효 키워드가 0개이면 즉시 중단 |

### Step 3. SQLite 체크포인트 초기화/복구

| 항목 | 내용 |
|---|---|
| 처리 주체 | 스크립트 |
| 관련 스킬 | `checkpoint-db-skill` |
| 입력 | 정제 키워드 목록 |
| 출력 | `kcpc_database.db`, 처리 시작 인덱스 |
| 코드 처리 | DB 생성, 테이블 생성, 기존 상태 조회 |
| LLM 판단 | 없음 |
| 성공 기준 | DB 파일 생성 또는 기존 DB 정상 로드 |
| 검증 방법 | 스키마 검증 |
| 실패 시 처리 | DB 파일 손상 시 백업 후 신규 DB 생성 여부를 사용자에게 에스컬레이션 |

### Step 4. 키워드별 DuckDuckGo 검색

| 항목 | 내용 |
|---|---|
| 처리 주체 | 스크립트 |
| 관련 스킬 | `ddg-measure-skill` |
| 입력 | 단일 키워드 |
| 출력 | DuckDuckGo 검색 결과 최대 10개 |
| 코드 처리 | `duckduckgo-search` 라이브러리 호출 |
| LLM 판단 | 없음 |
| 성공 기준 | 검색 결과 리스트 또는 빈 리스트 반환 |
| 검증 방법 | 규칙 기반 검증 |
| 실패 시 처리 | 최대 3회 자동 재시도, 실패 시 `FAILED`, `-1` 기록 후 다음 키워드 진행 |

### Step 5. title 필드 2차 검증

| 항목 | 내용 |
|---|---|
| 처리 주체 | 스크립트 |
| 관련 스킬 | `title-match-validator-skill` |
| 입력 | 검색 결과 리스트, 원본 키워드 |
| 출력 | `Top10_Title_Match_Count` |
| 코드 처리 | 각 결과의 `title` 필드에 원본 키워드가 대소문자 무시로 포함되는지 검사 |
| LLM 판단 | 없음 |
| 성공 기준 | 0~10 사이 정수 산출 |
| 검증 방법 | 규칙 기반 검증 |
| 실패 시 처리 | 결과 구조가 비정상인 경우 해당 키워드 `FAILED`, `-1` 기록 |

### Step 6. 결과 DB 즉시 저장

| 항목 | 내용 |
|---|---|
| 처리 주체 | 스크립트 |
| 관련 스킬 | `checkpoint-db-skill` |
| 입력 | 키워드, 상태, 측정값, 오류 메시지 |
| 출력 | DB 레코드 갱신 |
| 코드 처리 | 1건 처리마다 insert/update 후 commit |
| LLM 판단 | 없음 |
| 성공 기준 | 해당 키워드 결과가 DB에 즉시 반영됨 |
| 검증 방법 | 스키마 검증, 규칙 기반 검증 |
| 실패 시 처리 | DB 쓰기 실패 시 즉시 중단, 로그 기록 |

### Step 7. 전체 완료 여부 판단

| 항목 | 내용 |
|---|---|
| 처리 주체 | 스크립트 |
| 관련 스킬 | `pipeline-runner-skill` |
| 입력 | 현재 인덱스, 전체 키워드 수 |
| 출력 | 반복 계속 또는 종료 |
| 코드 처리 | 인덱스 비교 |
| LLM 판단 | 없음 |
| 성공 기준 | 전체 키워드가 DONE 또는 FAILED 상태로 기록됨 |
| 검증 방법 | 규칙 기반 검증 |
| 실패 시 처리 | 누락 인덱스 발견 시 해당 인덱스부터 재처리 |

### Step 8. 최종 Excel/CSV Export

| 항목 | 내용 |
|---|---|
| 처리 주체 | 스크립트 |
| 관련 스킬 | `export-result-skill` |
| 입력 | DB 전체 결과 |
| 출력 | `output/kcpc_result.xlsx` 또는 `.csv` |
| 코드 처리 | pandas/openpyxl 기반 파일 생성 |
| LLM 판단 | 없음 |
| 성공 기준 | 모든 입력 키워드가 출력 파일에 존재 |
| 검증 방법 | 스키마 검증, 규칙 기반 검증 |
| 실패 시 처리 | 파일 저장 실패 시 경로/권한 오류 출력 후 중단 |

### Step 9. QA 자동 테스트 시스템 (v2.0)

| 항목 | 내용 |
|---|---|
| 처리 주체 | `qa-tester` 모듈, `qa-pipeline-verifier` 서브에이전트 |
| 관련 스킬 | 전체 QA 스킬 |
| 입력 | 자동 생성된 빈도 기반 영어 단어 10개 |
| 출력 | QA 리포트 (`output/qa/qa_report.md`) |
| 코드 처리 | 30가지 DDG 품질 검증, 무한 반복 QA 로직 |

#### 자동 테스트 단어 생성

빈도 기반 영어 단어 10개를 자동 생성합니다:

| 빈도 그룹 | 점수 범위 | 개수 | 예상 DDG 결과 |
|-----------|------------|------|---------------|
| 고빈도 | 1-3 | 3개 | 8-10 (매우 높음) |
| 중빈도 | 4-7 | 4개 | 4-7 (중간) |
| 저빈도 | 8-10 | 3개 | 0-3 (매우 낮음) |

#### 무한 반복 QA 로직

**QA 패스 기준:**
- 고빈도 단어: DDG 결과 수 ≥ 7
- 중빈도 단어: DDG 결과 수 3~7
- 저빈도 단어: DDG 결과 수 ≤ 3

**무한 반복 조건:**
- FAIL 발생 시 자동으로 QA 재실행
- 최대 재시도: 제한 없음 (예상값과 일치할 때까지)
- 강제 중단: 사용자 Ctrl+C 입력

#### 30가지 DDG 품질 검증 요소

**P0 (필수):**
1. 백엔드 교차 검증: html vs lite 일치율 ≥ 80%
2. 재현성 검증: 3회 반복 편차 ≤ 1

**P1 (중요):**
3. 시간대별 일관성: 오전/오후 차이 ≤ 2
4. 지역별 변동: region 파라미터 비교
5. 키워드 유형별 패턴: 브랜드 > 일반 > 롱테일 순

**P2 (선택):**
6-30. 이상치 탐지, 상관계수, 신뢰구간, DQCS, 편향 분석 등

| LLM 판단 | QA 결과 해석, 30가지 검증 항목 판단, 문제 원인 분류 |
| 성공 기준 | 30가지 검증 통과, 예상 패턴과 일치 |
| 검증 방법 | 규칙 기반 검증 + DDG 자체 검증 |
| 실패 시 처리 | QA 자동 재실행, 로그 기록 후 재시도 |

---

# 3. LLM 판단 영역과 코드 처리 영역 구분

## 3.1 원칙

본 프로젝트는 대부분 결정론적 배치 처리이므로, 실제 실행 중 데이터 측정은 코드가 수행한다.  
LLM은 구현 전 설계 판단, 구현 리뷰, QA 결과 해석, 오류 원인 분류에만 관여한다.

**중요:**  
AI 판정은 현재 실행 중인 Claude Code 세션이 직접 수행하며, 별도로 `anthropic` 패키지를 호출하거나 API 키를 설정할 필요가 없다.

## 3.2 역할 분리 표

| 작업 | 담당 에이전트 | 스크립트 처리 여부 | 설명 |
|---|---|---:|---|
| 요구사항 해석 | `main-orchestrator` | 아니오 | 사용자 요구와 설계서 간 충돌 여부 판단 |
| 폴더 구조 생성 | `main-orchestrator` | 예 | Claude Code가 파일/폴더 생성 |
| 입력 파일 파싱 | 없음 | 예 | Python 코드 |
| 키워드 정제 | 없음 | 예 | Python 코드 |
| DuckDuckGo 검색 요청 | 없음 | 예 | `duckduckgo-search` |
| title 매칭 계산 | 없음 | 예 | 문자열 포함 검사 |
| DB 체크포인트 | 없음 | 예 | SQLite |
| 결과 Export | 없음 | 예 | pandas/openpyxl |
| 오류 원인 분류 | `main-orchestrator`, `qa-pipeline-verifier` | 부분적 | 로그 기반 LLM 판단 |
| QA 수행 | `qa-pipeline-verifier` | 예 | 실제 파이프라인 실행 |
| QA 결과 판단 | `qa-pipeline-verifier` | 아니오 | 누락/오류/품질 문제 판단 |
| 문서 수정 후 검증 | `qa-pipeline-verifier` | 예 | 사용자와 동일한 실행 경로로 검증 |

---

# 4. 구현 스펙

## 4.1 권장 프로젝트 폴더 구조

```text
/project-root
 ├── CLAUDE.md
 ├── README.md
 ├── requirements.txt
 ├── pyproject.toml
 ├── .gitignore
 ├── .env.example
 │
 ├── /.claude
 │   ├── /skills
 │   │   ├── /file-io-skill
 │   │   │   ├── SKILL.md
 │   │   │   ├── /scripts
 │   │   │   └── /references
 │   │   ├── /keyword-normalizer-skill
 │   │   │   ├── SKILL.md
 │   │   │   ├── /scripts
 │   │   │   └── /references
 │   │   ├── /ddg-measure-skill
 │   │   │   ├── SKILL.md
 │   │   │   ├── /scripts
 │   │   │   └── /references
 │   │   ├── /title-match-validator-skill
 │   │   │   ├── SKILL.md
 │   │   │   ├── /scripts
 │   │   │   └── /references
 │   │   ├── /checkpoint-db-skill
 │   │   │   ├── SKILL.md
 │   │   │   ├── /scripts
 │   │   │   └── /references
 │   │   ├── /export-result-skill
 │   │   │   ├── SKILL.md
 │   │   │   ├── /scripts
 │   │   │   └── /references
 │   │   └── /qa-runner-skill
 │   │       ├── SKILL.md
 │   │       ├── /scripts
 │   │       └── /references
 │   │
 │   └── /agents
 │       └── /qa-pipeline-verifier
 │           └── AGENT.md
 │
 ├── /src
 │   └── /kcpc
 │       ├── __init__.py
 │       ├── main.py
 │       ├── config.py
 │       ├── pipeline.py
 │       ├── file_io.py
 │       ├── normalizer.py
 │       ├── measurer.py
 │       ├── title_validator.py
 │       ├── checkpoint_db.py
 │       ├── exporter.py
 │       ├── logging_config.py
 │       ├── signal_handler.py
 │       └── exceptions.py
 │
 ├── /input
 │   └── .gitkeep
 │
 ├── /output
 │   ├── .gitkeep
 │   └── /qa
 │       └── .gitkeep
 │
 ├── /data
 │   └── .gitkeep
 │
 ├── /logs
 │   └── .gitkeep
 │
 ├── /docs
 │   └── design.md
 │
 └── /tests
     ├── test_file_parsing.py
     ├── test_title_validator.py
     └── integration_real_ddg.md
```

## 4.2 CLAUDE.md 핵심 섹션 목록

`CLAUDE.md`에는 상세 구현 코드가 아니라, Claude Code가 작업할 때 따라야 할 핵심 지침만 작성한다.

포함할 섹션:

1. 프로젝트 목적
2. 입력/출력 정의
3. 절대 지켜야 할 제약조건
4. 전체 워크플로우
5. LLM 판단 영역과 코드 처리 영역
6. 폴더 구조 규칙
7. 구현 모듈 목록
8. 스킬 호출 기준
9. QA 에이전트 호출 기준
10. 실패 처리 규칙
11. 금지사항
12. 완료 기준

## 4.3 에이전트 구조

### 기본 구조

본 프로젝트는 단순한 배치 파이프라인이므로 기본적으로 단일 메인 에이전트 구조를 사용한다.

단, 코드 또는 문서 수정 후 검증은 반드시 별도 QA 서브에이전트가 수행한다.

```text
main-orchestrator
    |
    v
qa-pipeline-verifier
```

### 4.3.1 main-orchestrator

| 항목 | 내용 |
|---|---|
| 위치 | `CLAUDE.md` |
| 역할 | 구현 전체 오케스트레이션 |
| 주요 업무 | 폴더 생성, 코드 작성, 스킬 생성, 문서 갱신, QA 요청 |
| 입력 | 사용자 요구사항, 본 설계서 |
| 출력 | 실행 가능한 Python 프로젝트 |
| LLM 판단 | 요구사항 충돌 판단, 오류 수정 우선순위 판단 |

### 4.3.2 qa-pipeline-verifier

| 항목 | 내용 |
|---|---|
| 위치 | `/.claude/agents/qa-pipeline-verifier/AGENT.md` |
| 역할 | 실제 사용자 실행 흐름으로 전체 프로젝트 검증 |
| 입력 | 구현된 프로젝트, 테스트 입력 파일 |
| 출력 | `/output/qa/qa_report.md` |
| 데이터 전달 방식 | 파일 기반 |
| 직접 호출 가능 여부 | 서브에이전트 간 직접 호출 금지, 반드시 main-orchestrator를 통해 호출 |
| 핵심 제약 | QA 전용 별도 소프트웨어 금지. 실제 CLI와 실제 DuckDuckGo 요청을 사용해야 함. |

## 4.4 서브에이전트 사용 기준

본 프로젝트에서는 QA 전용 서브에이전트만 사용한다.

| 서브에이전트 | 사용 이유 | 호출 단계 | 외부 출처 여부 |
|---|---|---|---|
| `qa-pipeline-verifier` | 구현 결과가 실제 사용자 경로로 동작하는지 독립 검증 | 코드 수정 후, 문서 수정 후, 릴리즈 전 | 내부 생성 |

외부에서 가져온 에이전트는 사용하지 않는다.

---

# 5. 스킬/스크립트 파일 목록

## 5.1 스킬 목록

| 스킬명 | 역할 | 트리거 조건 | 주요 산출물 |
|---|---|---|---|
| `file-io-skill` | 입력 파일 로딩 및 출력 파일 저장 보조 | txt/csv/xlsx 처리 필요 시 | 키워드 리스트, 출력 파일 |
| `keyword-normalizer-skill` | 키워드 정제 | 입력 파싱 직후 | 정제 키워드 목록 |
| `ddg-measure-skill` | DuckDuckGo 검색 측정 | 키워드별 측정 단계 | 검색 결과 리스트 |
| `title-match-validator-skill` | title 필드 매칭 수 계산 | 검색 결과 수신 후 | 0~10 정수 |
| `checkpoint-db-skill` | SQLite 체크포인트 관리 | 실행 시작, 키워드 처리 완료 시 | DB 레코드 |
| `export-result-skill` | 최종 결과 파일 생성 | 모든 키워드 처리 후 | `.xlsx`, `.csv` |
| `qa-runner-skill` | QA 실행 절차 보조 | QA 에이전트 검증 시 | QA 입력/결과 파일 |

## 5.2 실제 Python 모듈 목록

| 파일 | 역할 |
|---|---|
| `src/kcpc/main.py` | CLI 엔트리 포인트 |
| `src/kcpc/config.py` | 환경 변수 및 기본 설정 관리 |
| `src/kcpc/pipeline.py` | 전체 파이프라인 제어 |
| `src/kcpc/file_io.py` | 입력 파일 파싱, 출력 파일 저장 |
| `src/kcpc/normalizer.py` | 키워드 정제 |
| `src/kcpc/measurer.py` | DuckDuckGo 검색 호출 |
| `src/kcpc/title_validator.py` | title 매칭 검증 |
| `src/kcpc/checkpoint_db.py` | SQLite DB 생성/조회/갱신 |
| `src/kcpc/exporter.py` | Excel/CSV Export |
| `src/kcpc/logging_config.py` | 로깅 설정 |
| `src/kcpc/signal_handler.py` | Ctrl+C 안전 종료 |
| `src/kcpc/exceptions.py` | 커스텀 예외 |

---

# 6. 데이터 전달 패턴

## 6.1 권장 방식

중간 산출물은 가능한 `/output/` 또는 `/data/`에 저장하고, 에이전트 간에는 파일 경로만 전달한다.

| 데이터 | 전달 방식 | 이유 |
|---|---|---|
| 입력 키워드 파일 | 파일 기반 | 대량 데이터 가능 |
| DB 체크포인트 | 파일 기반 | 재시작 가능 |
| 최종 결과 | 파일 기반 | 사용자 확인 및 후속 처리 용이 |
| QA 리포트 | 파일 기반 | 검토 이력 보존 |
| 짧은 오류 메시지 | 프롬프트 인라인 | 즉시 판단 가능 |

## 6.2 주요 파일 경로

| 파일 | 기본 경로 |
|---|---|
| 입력 폴더 | `/input` |
| DB 파일 | `/data/kcpc_database.db` |
| 로그 파일 | `/logs/kcpc.log` |
| 결과 파일 | `/output/kcpc_result.xlsx` |
| QA 리포트 | `/output/qa/qa_report.md` |

---

# 7. 데이터베이스 설계

## 7.1 테이블: `keyword_measurements`

```sql
CREATE TABLE IF NOT EXISTS keyword_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_index INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    keyword_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    top10_title_match_count INTEGER DEFAULT -1,
    error_message TEXT DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword_hash)
);

CREATE INDEX IF NOT EXISTS idx_status ON keyword_measurements(status);
CREATE INDEX IF NOT EXISTS idx_original_idx ON keyword_measurements(original_index);
CREATE INDEX IF NOT EXISTS idx_keyword_hash ON keyword_measurements(keyword_hash);
```

## 7.2 키워드 중복 처리 정책

초안에서는 `keyword TEXT UNIQUE`를 사용했지만, 대소문자와 공백 차이로 인한 중복 판단이 흔들릴 수 있다.  
따라서 구현 시 다음 기준을 권장한다.

| 항목 | 처리 |
|---|---|
| 원본 키워드 | `keyword` 컬럼에 보존 |
| 비교용 키워드 | `strip()` 후 원본 유지 |
| 중복 판정 | `lower().strip()` 기반 hash |
| 중복 입력 발견 시 | 최초 등장 인덱스만 측정하고, 출력에는 동일 결과를 재사용 |

## 7.3 상태 값

| 상태 | 의미 |
|---|---|
| `PENDING` | 처리 전 |
| `RUNNING` | 현재 처리 중 |
| `DONE` | 정상 완료 |
| `FAILED` | 오류로 실패 |
| `SKIPPED_DUPLICATE` | 중복 키워드로 측정 생략, 기존 결과 재사용 |

---

# 8. 환경 설정

## 8.1 `.env.example`

```env
DDG_MIN_DELAY=2.0
DDG_MAX_DELAY=3.5
DDG_MAX_RETRIES=3
DDG_TIMEOUT=10
DDG_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36

DB_FILE_PATH=./data/kcpc_database.db
LOG_FILE_PATH=./logs/kcpc.log
OUTPUT_FILE_PATH=./output/kcpc_result.xlsx

OUTPUT_FORMAT=xlsx
DDG_MAX_RESULTS=10
```

## 8.2 `requirements.txt`

```text
duckduckgo-search>=6.0.0
pandas>=2.0.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
```

## 8.3 Python 버전

Python 3.10 이상을 기본으로 한다.

---

# 9. CLI 실행 스펙

## 9.1 기본 실행

```bash
python -m kcpc.main --input ./input/keywords.xlsx
```

## 9.2 출력 경로 지정

```bash
python -m kcpc.main --input ./input/keywords.xlsx --output ./output/result.xlsx
```

## 9.3 CSV 출력

```bash
python -m kcpc.main --input ./input/keywords.csv --output ./output/result.csv --format csv
```

## 9.4 재개 실행

재개는 사용자가 별도 옵션을 주지 않아도 DB가 있으면 자동 수행한다.

```bash
python -m kcpc.main --input ./input/keywords.xlsx
```

## 9.5 신규 실행

기존 DB를 무시하고 새로 실행하고 싶을 때만 옵션을 사용한다.

```bash
python -m kcpc.main --input ./input/keywords.xlsx --reset
```

---

# 10. 구현 지침

## 10.1 필수 구현 원칙

1. 모듈을 분리한다.
2. 모든 함수에 타입 힌트를 작성한다.
3. 모든 키워드는 처리 직후 DB에 commit한다.
4. DuckDuckGo 요청 사이에는 반드시 `time.sleep()` 기반 딜레이를 적용한다.
5. 비동기 처리, 멀티스레딩, 동시 요청은 v1.0에서 사용하지 않는다.
6. 진행률은 `tqdm` 없이 콘솔 한 줄 갱신 방식으로 표시한다.
7. Mock 기반 테스트를 사용하지 않는다.
8. 단, 순수 함수인 title 매칭 검증, 파일 파싱 로직은 로컬 데이터 기반 규칙 테스트가 가능하다.
9. 네트워크 관련 QA는 실제 DuckDuckGo 요청으로만 수행한다.
10. 검색엔진 차단을 우회하기 위한 프록시 자동화는 구현하지 않는다.
11. 적절한 User-Agent를 설정하고 요청 간격을 준수하여 차단을 방지한다.
12. 429/403 응답 시 지수 백오프를 적용하여 재시도한다.

## 10.2 금지사항 (최소화)

| 금지 항목 | 이유 |
|---|---|
| Google 검색 크롤링 | 차단 및 정책 위험 |
| 유료 API 사용 | 무료 DDG 사용 원칙 |
| 검색 결과 전체 수 추정 | 상위 10개만 측정 |
| Mock으로 DDG 응답 대체 | 실제 동작 검증 불가 |
| `anthropic` API 호출 | Claude Code 세션 내부 판단으로 충분 |
| 결과값 임의 분류 | 사용자가 원한 것은 원본 수치 기록 |

### 허용되는 우회 수단 (사용자 명시적 설정 시)
다음 우회 수단은 사용자가 `.env`에서 명시적으로 설정한 경우에만 허용된다.

| 우회 수단 | 환경 변수 | 설명 |
|---|---|---|
| 프록시 순환 | `DDG_USE_PROXY=true` | `proxies.txt`의 프록시를 순환하며 사용 |
| User-Agent 순환 | `DDG_ROTATE_UA=true` | `user_agents.txt`의 UA를 순환하며 사용 |
| 딜레이 무시 | `DDG_IGNORE_DELAY=true` | 요청 간 딜레이 제거 (차단 위험 높음) |
| SSL 검증 우회 | `DDG_IGNORE_SSL=true` | SSL 인증서 검증 건너뛰기 |

> **주의**: 모든 우회 수단은 사용자의 명시적 설정이 있을 때만 활성화되며, 기본 동작은 DuckDuckGo 이용약관을 준수한다.

---

# 11. 검증 패턴

## 11.1 단계별 검증 요약

| 단계 | 성공 기준 | 검증 방법 | 실패 처리 |
|---|---|---|---|
| 입력 파일 파싱 | 키워드 1개 이상 추출 | 규칙 기반 | 즉시 중단 |
| 키워드 정제 | 빈 값 제거, 인덱스 보존 | 규칙 기반 | 유효 키워드 0개면 중단 |
| DB 초기화 | 테이블/인덱스 존재 | 스키마 검증 | 손상 시 에스컬레이션 |
| DDG 검색 | 결과 리스트 또는 빈 리스트 반환 | 규칙 기반 | 최대 3회 재시도 |
| title 검증 | 0~10 정수 반환 | 규칙 기반 | 실패 시 `-1` |
| DB 저장 | 1건마다 commit | 스키마 검증 | 즉시 중단 |
| Export | 전체 키워드 행 존재 | 규칙 기반 | 저장 경로 오류 출력 |
| QA | 실제 파이프라인 통과 | LLM 자기 검증 + 사람 검토 | 수정 후 재검증 |

## 11.2 실패 처리 기준

| 방식 | 사용 시점 |
|---|---|
| 자동 재시도 | 네트워크 타임아웃, 일시적 연결 실패 |
| 에스컬레이션 | DB 손상, 입력 구조 모호, 출력 파일 잠김 |
| 스킵 + 로그 | 단일 키워드 측정 실패, 중복 키워드 |

---

# 12. QA 설계

## 12.1 QA 원칙

QA 전용 별도 소프트웨어를 만들지 않는다.  
`qa-pipeline-verifier`는 사용자가 실제로 실행하는 명령과 같은 방식으로 프로젝트를 실행한다.

## 12.2 QA 에이전트의 필수 수행 항목

1. 테스트 입력 파일 생성
   - `test_keywords.txt`
   - `test_keywords.csv`
   - `test_keywords.xlsx`
2. 실제 CLI 실행
3. 실제 DuckDuckGo 요청 확인
4. DB 파일 생성 여부 확인
5. 로그 파일 생성 여부 확인
6. 결과 Excel/CSV 생성 여부 확인
7. 출력 행 수와 입력 키워드 수 비교
8. 결과 컬럼 검증
9. Ctrl+C 안전 종료 수동 또는 반자동 검증
10. QA 리포트 작성

## 12.3 QA 테스트 데이터 예시

```text
seo
keyword research
ultra rare xyzqwerty123seo
best project management software
ai writing tool
```

QA에서는 많은 키워드를 사용하지 않는다.  
테스트 시간이 과도하게 길어지는 것을 막기 위해 5개 내외의 키워드만 사용한다.

## 12.4 QA 리포트 형식

`/output/qa/qa_report.md`

포함 내용:

1. 실행 일시
2. 실행 명령어
3. 입력 파일 목록
4. 출력 파일 목록
5. DB 검증 결과
6. 로그 검증 결과
7. 결과 파일 컬럼 검증
8. 결과 행 수 검증
9. 실제 DuckDuckGo 측정 성공 여부
10. 발견된 문제
11. 수정 필요 항목
12. 최종 판정: `PASS` 또는 `FAIL`

## 12.5 코드 또는 문서 수정 후 QA 규칙

코드나 문서를 수정한 경우 `qa-pipeline-verifier`를 반드시 호출한다.

QA 에이전트는 다음을 수행해야 한다.

```text
[수정 사항 확인]
      |
      v
[테스트 입력 생성]
      |
      v
[사용자와 동일한 CLI 실행]
      |
      v
[출력 파일 확인]
      |
      v
[DB/로그 확인]
      |
      v
[QA 리포트 작성]
      |
      v
[PASS/FAIL 판정]
```

---

# 13. 로깅 설계

## 13.1 로그 경로

```text
/logs/kcpc.log
```

## 13.2 로그 포맷

```text
[%(asctime)s] [%(levelname)-8s] - %(message)s
```

## 13.3 로그 레벨

| 레벨 | 용도 |
|---|---|
| DEBUG | 키워드별 상세 처리 |
| INFO | 실행 시작/완료, 진행률 |
| WARNING | 재시도 가능한 문제 |
| ERROR | 단일 키워드 실패 또는 파일 저장 실패 |
| CRITICAL | 파이프라인 중단 오류 |

## 13.4 필수 로그

```text
[INFO] KCPC 파이프라인 시작
[INFO] 입력 파일 로드 완료: 총 N개 키워드
[INFO] 체크포인트 확인: 인덱스 N부터 재개
[DEBUG] 측정 시작: keyword
[WARNING] DDG 요청 실패, 재시도 1/3
[INFO] 측정 완료: keyword -> 3
[ERROR] 측정 실패: keyword -> error message
[INFO] 결과 파일 저장 완료
[INFO] QA 실행 완료
```

---

# 14. 산출물 파일 형식

## 14.1 최종 Excel 파일

기본 경로:

```text
/output/kcpc_result.xlsx
```

기본 시트:

| 시트명 | 설명 |
|---|---|
| `Results` | 키워드별 측정 결과 |
| `Run_Summary` | 실행 요약 |
| `Failed_Items` | 실패 키워드 목록 |
| `QA_Summary` | QA 결과 요약. QA 이후 생성 가능 |

## 14.2 Results 시트

| 컬럼 | 설명 |
|---|---|
| `Original_Index` | 원본 입력 순서 |
| `Keyword` | 원본 키워드 |
| `Normalized_Key` | 중복 판정용 정규화 키 |
| `Top10_Title_Match_Count` | 상위 10개 결과 중 title 매칭 수 |
| `Status` | 처리 상태 |
| `Error_Message` | 오류 메시지 |
| `Updated_At` | 갱신 시각 |

## 14.3 Run_Summary 시트

| 항목 | 설명 |
|---|---|
| `Total_Input_Rows` | 입력 전체 행 수 |
| `Total_Valid_Keywords` | 유효 키워드 수 |
| `Done_Count` | 성공 수 |
| `Failed_Count` | 실패 수 |
| `Duplicate_Count` | 중복 수 |
| `Started_At` | 시작 시각 |
| `Finished_At` | 종료 시각 |
| `Elapsed_Seconds` | 총 소요 시간 |

---

# 15. Claude Code 작업 순서

Claude Code는 다음 순서로 구현한다.

## 15.1 1차 구현

1. 프로젝트 폴더 구조 생성
2. `CLAUDE.md` 생성
3. `.claude/skills` 생성
4. `.claude/agents/qa-pipeline-verifier/AGENT.md` 생성
5. Python 패키지 구조 생성
6. 설정 파일 생성
7. 입력 파싱 구현
8. DB 체크포인트 구현
9. DuckDuckGo 측정 구현
10. Export 구현
11. 로깅 구현
12. CLI 구현

## 15.2 1차 자체 검증

1. `python -m kcpc.main --help`
2. txt 입력 파일 실행
3. csv 입력 파일 실행
4. xlsx 입력 파일 실행
5. 결과 파일 열 검증
6. DB 레코드 수 검증
7. 로그 파일 확인

## 15.3 QA 에이전트 검증

1. `qa-pipeline-verifier` 호출
2. QA용 입력 파일 생성
3. 실제 CLI 실행
4. 실제 DDG 요청 확인
5. 결과 파일 검증
6. QA 리포트 작성
7. FAIL이면 main-orchestrator가 수정
8. 수정 후 QA 재실행

---

# 16. 완료 기준

본 프로젝트는 다음 조건을 모두 만족해야 완료로 본다.

1. `/input`에 `.txt`, `.csv`, `.xlsx` 파일을 넣고 실행할 수 있다.
2. 첫 번째 열의 키워드를 정상 추출한다.
3. 각 키워드에 대해 DuckDuckGo 검색을 수행한다.
4. `intitle:"keyword"` 쿼리를 사용한다.
5. 반환 결과의 title 필드를 2차 검증한다.
6. 결과값은 0~10 또는 실패 시 -1이다.
7. 키워드 1건마다 SQLite DB에 commit한다.
8. 중단 후 재실행 시 이어서 진행한다.
9. 최종 Excel 파일이 생성된다.
10. 출력 파일에는 모든 유효 키워드가 누락 없이 포함된다.
11. 로그 파일이 생성된다.
12. 코드 또는 문서 수정 후 QA 에이전트가 실제 파이프라인을 수행했다.
13. QA 리포트가 `/output/qa/qa_report.md`에 생성된다.
14. QA 최종 판정이 `PASS`이다.

---

# 17. 설계상 보완 사항

원본 초안 대비 본 설계서에서 보완한 사항은 다음과 같다.

| 원본 초안 항목 | 보완 내용 |
|---|---|
| `Competition_Page_Count` | 실제 의미에 맞게 `Top10_Title_Match_Count`로 변경 |
| `keyword TEXT UNIQUE` | 중복 판정 안정성을 위해 `keyword_hash` 추가 |
| 출력 컬럼 2개만 사용 | 실무 검증을 위해 상태/오류/시간 컬럼 추가 |
| QA 테스트 | 실제 파이프라인 기반 QA 에이전트 구조로 확장 |
| Claude 지시 | CLAUDE.md, SKILL.md, AGENT.md 구조로 재배치 |
| 향후 프록시 확장 | 정책 위반 가능성이 있어 v1.0 설계 범위에서 제외 |

---

# 18. 구현 시 주의사항

1. DuckDuckGo 검색 결과는 시점과 네트워크 상태에 따라 달라질 수 있다.
2. 이 시스템의 결과는 절대적인 웹페이지 수가 아니다.
3. `intitle:` 연산자가 항상 완벽히 적용된다고 가정하면 안 된다.
4. 반드시 title 필드의 실제 문자열을 재검증해야 한다.
5. 대량 실행 시 검색엔진 부하를 줄이기 위해 딜레이를 강제한다.
6. 실패한 키워드는 나중에 별도 재처리할 수 있도록 `Failed_Items` 시트에 기록한다.
7. QA에서는 많은 키워드를 사용하지 말고 5개 내외로 제한한다.
8. QA는 Mock 없이 실제 네트워크 요청으로 수행한다.
9. 단, title 검증 같은 순수 함수는 로컬 고정 데이터로 규칙 테스트할 수 있다.
10. 사용자가 결과를 후속 SEO 판단에 사용할 수 있도록 수치를 임의로 분류하지 않는다.

---

# 19. 최종 요약

KCPC 프로젝트는 입력 키워드 목록을 받아 DuckDuckGo 상위 10개 검색 결과의 제목 매칭 수를 측정하고, 그 결과를 Excel/CSV로 출력하는 로컬 Python 배치 시스템이다.

본 설계서의 핵심은 다음과 같다.

- 검색 결과 전체 수가 아니라 상위 10개 title 매칭 수를 측정한다.
- 측정 결과를 임의 분류하지 않고 원본 수치 그대로 기록한다.
- 모든 결과는 SQLite에 즉시 저장하여 중단 후 재개가 가능하다.
- Claude Code는 구현 오케스트레이션을 담당하고, 실제 측정은 Python 스크립트가 담당한다.
- 코드 또는 문서 수정 후에는 QA 에이전트가 사용자와 동일한 파이프라인을 직접 실행해 검증한다.
- 별도 Anthropic API 호출은 필요하지 않다.

---
**문서 종료**
