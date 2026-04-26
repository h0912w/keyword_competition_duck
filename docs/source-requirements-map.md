# 원본 설계서 요구사항 커버리지 맵

| 원본 섹션 | 요구사항 | 반영 위치 | 상태 |
|---|---|---|---|
| 1.1~1.2 | DDG Top10 title 매칭 수 측정 목적 | `CLAUDE.md`, 운영 가이드 | 반영 |
| 1.3 | 포함/제외 범위 | `CLAUDE.md` | 반영 |
| 1.4~1.6 | 입력/출력/컬럼 | 입력출력 계약 | 반영 |
| 1.7 | 핵심 제약조건 | `CLAUDE.md`, 실패 정책 | 반영 |
| 1.8 | 용어 | 용어 문서 | 반영 |
| 2 | 워크플로우/상태 전이 | 워크플로우 문서 | 반영 |
| 3 | LLM/스크립트 역할 분리 | `CLAUDE.md`, 역할 분리 문서 | 반영 |
| 4 | 폴더 구조/CLAUDE/에이전트 | 실제 폴더, Agent 문서 | 반영 |
| 5 | Skills 목록 | `.claude/skills/*/SKILL.md` | 반영 |
| 6 | 파일 기반 전달/경로 | 운영 가이드 | 반영 |
| 7 | DB 스키마/중복/상태 | DB 문서 | 반영 |
| 8~9 | 환경/CLI | 설정 및 CLI 문서 | 반영 |
| 10~11 | 구현/검증 지침 | 모듈 계약, 실패 정책 | 반영 |
| 12 | QA 설계 | QA 계획, Agent 문서 | 반영 |
| 13 | 로깅 | 로깅 명세 | 반영 |
| 14 | 산출물 시트 | 입력출력 계약 | 반영 |
| 15~16 | 작업 순서/완료 기준 | 구현 순서, `CLAUDE.md` | 반영 |
| 17~19 | 보완/주의/요약 | 관련 문서 전체 | 반영 |
| **추가** | **DDG 차단 방지 정책** | **워크플로우, 모듈 계약, CLAUDE.md** | **반영** |

점검 결과: `README.md` 없이 `CLAUDE.md + docs + .claude` 구조로 원본 요구사항을 보존했다.

---
## DuckDuckGo 차단 우회 추가 사항 (2026-04-26)

사용자 명시적 설정 시 차단 우회 기능을 제공한다.

### 기본 방지 정책
| 항목 | 내용 | 반영 위치 |
|---|---|---|
| User-Agent 설정 | `.env`에서 설정 가능, 브라우저 모방 | `config-and-cli.md`, `original-design.md` |
| 요청 간격 | `DDG_MIN_DELAY`~`DDG_MAX_DELAY` 랜덤 딜레이 | `workflow-and-failure-policy.md` |
| 지수 백오프 | 429/403 응답 시 재시도 간격 증가 | `workflow-and-failure-policy.md`, `module-contracts.md` |
| 표준 라이브러리 | `duckduckgo-search` 공식 패키지만 사용 | `workflow-and-failure-policy.md` |

### 사용자 옵션 우회 수단
| 우회 수단 | 환경 변수 | 반영 위치 |
|---|---|---|
| 프록시 순환 | `DDG_USE_PROXY`, `DDG_PROXY_LIST` | `config-and-cli.md`, `workflow-and-failure-policy.md`, `module-contracts.md` |
| User-Agent 순환 | `DDG_ROTATE_UA`, `DDG_UA_LIST` | `config-and-cli.md`, `workflow-and-failure-policy.md`, `module-contracts.md` |
| 딜레이 무시 | `DDG_IGNORE_DELAY` | `config-and-cli.md`, `workflow-and-failure-policy.md` |
| SSL 검증 우회 | `DDG_IGNORE_SSL` | `config-and-cli.md`, `workflow-and-failure-policy.md` |

---
## QA 검증 시스템 v2.0 (2026-04-26)

QA 시에 Google API 없이 DDG 자체 검증 30가지 요소를 사용한다.

| 항목 | 내용 | 반영 위치 |
|---|---|
| 30가지 DDG 품질 검증 요소 | 백엔드 교차, 재현성, 시간대별 일관성 등 | `qa-plan.md`, `original-design.md` |
| 자동 테스트 단어 생성 | 빈도 기반 영어 단어 10개 생성 | `qa_tester.py` |
| 무한 반복 QA 로직 | 예상값과 일치할 때까지 재시도 | `qa_tester.py` |
| DDG 백엔드 교차 검증 | html vs lite 백엔드 비교 | `qa_verifier.py` |
| 재현성 검증 | 3회 반복 측정, 편차 분석 | `qa_verifier.py` |
| 통계 검증 | 이상치 탐지, 상관계수, DQCS | `qa_analyzer.py` |
| 환경 변수 | `QA_AUTO_GENERATE_WORDS`, `QA_RETRY_UNTIL_PASS` | `config-and-cli.md`, `.env.example` |
