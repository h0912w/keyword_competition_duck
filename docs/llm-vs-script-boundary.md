# LLM 판단 영역과 스크립트 처리 영역

| 작업 | 담당 | 스크립트 | LLM |
|---|---|---:|---:|
| 요구사항 해석 | main-orchestrator | 아니오 | 예 |
| 폴더/파일 생성 | main-orchestrator | 예 | 예 |
| 입력 파일 파싱 | Python | 예 | 아니오 |
| 키워드 정제/중복 | Python | 예 | 아니오 |
| DuckDuckGo 검색 | Python | 예 | 아니오 |
| title 매칭 계산 | Python | 예 | 아니오 |
| SQLite 체크포인트 | Python | 예 | 아니오 |
| 결과 Export | Python | 예 | 아니오 |
| 오류 원인 분류 | main/QA | 부분 | 예 |
| QA 수행 | qa-pipeline-verifier | 예 | 예 |
| QA 결과 판단 | qa-pipeline-verifier | 아니오 | 예 |

별도 `anthropic` API 호출은 금지한다. 측정값은 LLM이 추정하지 않는다.

## QA 원칙 (실제 파이프라인 사용)

QA는 별도 QA 전용 소프트웨어가 아니라, 실제 사용자가 실행하는 동일한 파이프라인을 사용해야 한다.

| 원칙 | 설명 | 스크립트 구현 방식 |
|---|---|---|
| **실제 파이프라인 실행** | QA에서도 실제 `kcpc.main` 모듈 실행 | `subprocess.run([sys.executable, "-m", "kcpc.main", ...])` |
| **실제 DDG 요청** | Mock/Stub 사용 금지 | `duckduckgo_search` 라이브러리로 실제 검색 |
| **실제 출력 검증** | 생성된 Excel/CSV 파일을 읽어서 검증 | `pd.read_excel()`로 결과 파일 로드 후 검증 |
| **동일 환경 사용** | 사용자와 동일한 설정, 입력, 출력 경로 사용 | QA에서도 동일한 `.env` 설정, 동일한 입력/출력 경로 사용 |

### 금지 사항 (예시)

| 금지 사항 | 위반 예시 | 올바른 구현 |
|---|---|---|
| **DDG 결과 시뮬레이션** | `actual = random.randint(7, 10)` | 실제 `kcpc.main` 실행 후 `pd.read_excel()`로 결과 확인 |
| **Mock 함수 사용** | `def mock_ddg_search(): return fake_results` | 실제 `DDGS().text()` 호출 |
| **메모리상 데이터만 검증** | DB에 저장된 데이터만 확인 | 생성된 Excel/CSV 파일을 실제로 읽어서 검증 |
