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
