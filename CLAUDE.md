# CLAUDE.md — KCPC 운영 기준

## 최우선 규칙
- 원본 설계서 요구사항을 누락하지 않는다. 세부 요구사항은 `docs/source-requirements-map.md`와 각 참조문서에 보존한다.
- `README.md`는 생성하지 않는다. 사용법/설치/구조 설명은 `docs/project-operating-guide.md`에 둔다.
- 코드 또는 문서 수정 후 반드시 `qa-pipeline-verifier`를 호출하고 `/output/qa/qa_report.md`를 생성한다.
- QA 전용 별도 소프트웨어 금지. QA는 사용자와 동일한 CLI와 실제 DuckDuckGo 요청으로 수행한다.
- AI 판단은 현재 Claude Code 세션이 직접 수행한다. `anthropic` 패키지/API 키를 추가하지 않는다.

---

## 참조문서 빠른찾기

| 문서 | 경로 | 주요 내용 | 언제 참조할 것인가 |
|---|---|---|---|
| **원본 설계서** | `docs/original-design.md` | 전체 프로젝트 설계, 워크플로우, DB 스키마, 환경설정 | 프로젝트 전체 이해, 구현 시 참조 |
| **요구사항 맵** | `docs/source-requirements-map.md` | 원본 설계서 요구사항 커버리지 | 누락 검토, 변경 영향 확인 |
| **모듈 계약** | `docs/module-contracts.md` | 각 Python 모듈의 책임과 함수 명세 | 코드 구현/수정 시 |
| **워크플로우** | `docs/workflow-and-failure-policy.md` | 실행 흐름, 상태 전이, 실패 정책, **DDG 차단 우회** | 오류 처리, 재시도 로직 구현 시 |
| **입출력 계약** | `docs/input-output-contract.md` | 입력 파일 형식, 출력 컬럼 명세 | 파일 I/O 구현 시 |
| **설정 및 CLI** | `docs/config-and-cli.md` | `.env` 변수, CLI 옵션, **DDG_USER_AGENT 설정** | 설정 추가/변경 시 |
| **DB 스키마** | `docs/database-schema.md` | 테이블 구조, 인덱스, 상태 값 | DB 구현/변경 시 |
| **로깅 명세** | `docs/logging-spec.md` | 로그 경로, 포맷, 레벨, 필수 로그 | 로그 구현 시 |
| **운영 가이드** | `docs/project-operating-guide.md` | 설치, 실행 명령어, 산출물 경로 | 사용법 확인 시 |
| **구현 순서** | `docs/implementation-sequence.md` | 개발 단계별 작업 순서 | 프로젝트 구현 시 |
| **QA 계획** | `docs/qa-plan.md` | QA 절차, 테스트 데이터, 검증 항목 | QA 수행 시 |
| **용어 사전** | `docs/glossary.md` | 프로젝트 관련 용어 정의 | 용어 혼동 시 |
| **LLM/스크립트 경계** | `docs/llm-vs-script-boundary.md` | AI 판단 영역과 코드 처리 영역 구분 | 작업 분배 시 |
| **파일 목록** | `docs/file-list.md` | 프로젝트 전체 파일 목록 | 파일 위치 확인 시 |

---

## 프로젝트 정의
KCPC는 `.txt`, `.csv`, `.xlsx` 첫 번째 열의 영어 키워드 목록을 입력받아, 각 키워드에 대해 DuckDuckGo 상위 10개 검색 결과의 `title`에 원본 키워드가 포함되는 개수를 측정하고 Excel/CSV로 출력하는 로컬 Python 배치 프로그램이다.

---

## 절대 입출력 계약
- **입력**: 첫 번째 열에 키워드가 세로로 나열된 `.txt`, `.csv`, `.xlsx`
- **제외**: 빈 줄, 공백만 있는 셀, NaN
- **기본 출력**: `/output/kcpc_result.xlsx`
- **DB**: `/data/kcpc_database.db`
- **로그**: `/logs/kcpc.log`
- **QA**: `/output/qa/qa_report.md`
- **Results 기본 컬럼**: `Original_Index`, `Keyword`, `Normalized_Key`, `Top10_Title_Match_Count`, `Status`, `Error_Message`, `Updated_At`
- **측정값**: 0~10 정수이며 실패 시 -1
- `Competition_Page_Count`는 기본 컬럼명이 아니다. 사용자가 원할 때만 별칭 컬럼으로 추가한다.

---

## 차단 우회 정책 (사용자 옵션)

### 기본 정책 (v1.0)
- **기본값**: DuckDuckGo 이용약관을 준수하여 정상적인 요청만 수행
- **User-Agent**: `.env`에서 설정한 브라우저 User-Agent 사용
- **요청 간격**: `DDG_MIN_DELAY`~`DDG_MAX_DELAY` 초 랜덤 딜레이 강제
- **재시도**: 429/403 응답 시 지수 백오프 적용

### 사용자 옵션에 따른 우회 수단
사용자가 `.env` 또는 CLI 옵션으로 명시적으로 설정한 경우, 다음 우회 수단을 사용할 수 있다.

| 설정 | 환경 변수 | 설명 |
|---|---|---|
| **프록시 사용** | `DDG_USE_PROXY=true`<br>`DDG_PROXY_LIST=http://...` | HTTP(S) 프록시를 통해 요청 라우팅 |
| **User-Agent 순환** | `DDG_ROTATE_UA=true` | 여러 브라우저 User-Agent를 순환하며 사용 |
| **요청 간격 무시** | `DDG_IGNORE_DELAY=true` | 딜레이 없이 연속 요청 (차단 위험 높음) |
| **TLS 검증 우회** | `DDG_IGNORE_SSL=true` | SSL 인증서 검증 우회 (자가서명된 프록시용) |

### 우회 구현 시 주의사항
- 우회 수단은 **사용자가 명시적으로 설정한 경우에만** 활성화된다
- 기본 동작은 DuckDuckGo 이용약관을 준수한다
- 프록시 목록 파일은 `proxies.txt`에 한 줄당 하나의 `http://host:port` 형식으로 작성
- User-Agent 목록은 `user_agents.txt`에 한 줄당 하나의 UA 문자열로 작성

---

## 금지사항 (최소화)
- **Google Search API/Google 검색 크롤링**: 차단 및 정책 위험
- **유료 API 사용**: 무료 DDG 사용 원칙
- **검색 결과 전체 수 추정**: 상위 10개만 측정
- **저공급/고공급 등 임의 분류**: 원본 수치 기록
- **웹 UI/GUI**: v1.0에서는 CLI만 지원
- **DDG QA Mock 대체**: 실제 요청으로 QA
- **비동기/멀티스레드/동시 요청**: v1.0에서 금지
- **출력 헤더명/시트명/경로 임의 변경**: 계약 준수

---

## LLM 판단 영역과 스크립트 처리 영역
- **스크립트**: 입력 파싱, 키워드 정제, 중복 판정, DDG 요청, title 매칭 계산, SQLite 체크포인트, export, 로그, Ctrl+C 안전 종료
- **LLM**: 요구사항 충돌 판단, 구현/문서 수정 우선순위, QA 결과 해석, 오류 원인 분류, 누락 검토
- **실제 측정값 산출은 코드가 수행한다.** LLM은 검색 결과 수를 추정하거나 보정하지 않는다.
- 상세는 `docs/llm-vs-script-boundary.md`를 따른다.

---

## 고정 워크플로우
1. 입력 파일 탐지 및 파싱
2. 키워드 정제 및 중복 처리
3. SQLite 체크포인트 초기화/복구
4. 키워드별 DuckDuckGo 검색 (일반 검색 후 title 2차 검증)
5. 반환 결과 `title` 필드 대소문자 무시 포함 검사
6. 키워드 1건마다 DB 즉시 commit
7. 미완료 항목 반복 처리
8. Excel/CSV export
9. `qa-pipeline-verifier` 실제 파이프라인 검증
10. QA 리포트 작성 및 PASS/FAIL 판정

---

## 구현 규칙
- Python 3.10 이상, 패키지 경로는 `src/kcpc/`
- 모든 함수에 타입 힌트를 작성한다.
- 모듈 책임은 `docs/module-contracts.md`와 일치시킨다.
- 진행률은 `tqdm` 없이 콘솔 한 줄 갱신 방식으로 표시한다.
- DuckDuckGo만 사용하고 일반 검색을 수행한 후 title 2차 검증으로 매칭 수를 측정한다.
- 요청 사이에는 `DDG_MIN_DELAY`~`DDG_MAX_DELAY` 딜레이를 강제한다 (단, `DDG_IGNORE_DELAY=true` 시 제외).
- 네트워크 실패는 최대 `DDG_MAX_RETRIES`회 재시도 후 해당 키워드만 `FAILED`, `-1`로 기록한다.

---

## DB/체크포인트 규칙
- 테이블명은 `keyword_measurements`
- 중복 판정은 `lower().strip()` 기반 hash
- 원본 키워드는 보존한다.
- 상태 값은 `PENDING`, `RUNNING`, `DONE`, `FAILED`, `SKIPPED_DUPLICATE`만 사용한다.
- DB 손상 시 임의 삭제하지 말고 백업 후 사용자 에스컬레이션 대상으로 기록한다.

---

## QA 완료 기준
- `.txt`, `.csv`, `.xlsx` 첫 번째 열에서 키워드를 추출한다.
- 유효 키워드가 결과에 누락 없이 존재한다.
- 각 키워드는 DDG 검색과 title 2차 검증을 거친다.
- 결과값은 0~10 또는 실패 시 -1이다.
- SQLite DB와 로그 파일이 생성된다.
- 중단 후 재실행 시 이어서 진행한다.
- 최종 Excel/CSV가 지정 경로에 생성된다.
- QA 리포트 최종 판정이 PASS다.
- `docs/source-requirements-map.md` 기준 원본 설계서 대비 누락 0% 검토가 완료됐다.
