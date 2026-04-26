# 구현 순서

1. 폴더 구조 확인
2. `CLAUDE.md`와 `docs/` 확인
3. `.claude/skills`, `.claude/agents` 확인
4. Python 패키지 구조 생성/갱신
5. 설정 파일 생성/갱신 (`.env`에 `DDG_USER_AGENT` 및 우회 옵션 포함)
6. 입력 파싱, DB, DDG 측정(User-Agent/프록시 설정 포함), title 검증, export, 로깅, CLI 구현
7. `python -m kcpc.main --help`
8. txt/csv/xlsx 입력 실행
9. 결과 파일, DB 레코드, 로그 검증
10. QA 에이전트 검증 및 PASS/FAIL 리포트 작성

### DDG 요청 구현 시 주의사항
- `measurer.py`에서 `DDG_USER_AGENT` 환경 변수를 읽어 `DDG.results()`에 전달
- 요청 간격은 `random.uniform(DDG_MIN_DELAY, DDG_MAX_DELAY)`으로 랜덤화 (단, `DDG_IGNORE_DELAY=true` 시 제외)
- 429/403 응답 시 `time.sleep(2 ** retry_count)` 지수 백오프 적용
- 직접 HTML 파싱 없이 `duckduckgo-search` 반환 값만 사용

### 우회 옵션 구현 시 추가사항
| 모듈 | 추가 구현 사항 |
|---|---|
| `config.py` | 우회 옵션(`DDG_USE_PROXY`, `DDG_ROTATE_UA`, `DDG_IGNORE_DELAY`, `DDG_IGNORE_SSL`) 파싱 |
| `file_io.py` | `proxies.txt`, `user_agents.txt` 파일 로드 함수 추가 |
| `measurer.py` | 프록시/UA 순환 로직, SSL 무시 옵션 처리 |

### 우회 구현 우선순서
1. 기본 동작 (우회 비활성화) 먼저 완성
2. `DDG_USE_PROXY` 구현 (프록시 순환, 실패 시 폴백)
3. `DDG_ROTATE_UA` 구현 (UA 순환)
4. `DDG_IGNORE_DELAY` 구현 (딜레이 제거)
5. `DDG_IGNORE_SSL` 구현 (SSL 검증 우회)
