# Python 모듈 책임 계약

| 파일 | 책임 |
|---|---|
| `main.py` | CLI 엔트리, 인자 파싱, 파이프라인 호출 |
| `config.py` | 환경 변수와 기본 설정, User-Agent 관리, 우회 옵션 로드 |
| `pipeline.py` | 전체 실행 순서와 재개/초기화 흐름 |
| `file_io.py` | txt/csv/xlsx 첫 열 파싱, `proxies.txt`/`user_agents.txt` 로드 |
| `normalizer.py` | strip, NaN 제거, normalized key/hash |
| `measurer.py` | DDG 요청, User-Agent/프록시 설정, 딜레이, 지수 백오프 재시도 |
| `title_validator.py` | title 필드 대소문자 무시 포함 검사 |
| `checkpoint_db.py` | SQLite 스키마, CRUD, 재개 상태 |
| `exporter.py` | xlsx/csv와 시트 생성 |
| `logging_config.py` | 로그 포맷/핸들러 |
| `signal_handler.py` | Ctrl+C 안전 종료 |
| `exceptions.py` | 커스텀 예외 |

모든 함수에 타입 힌트를 작성하고, 예외를 무조건 숨기지 않는다.

### config.py 상세 책임
- `.env` 파일에서 모든 환경 변수를 로드
- 우회 옵션(`DDG_USE_PROXY`, `DDG_ROTATE_UA`, `DDG_IGNORE_DELAY`, `DDG_IGNORE_SSL`)을 파싱
- 각 옵션의 boolean 변환 (`"true"`/`"false"` → `True`/`False`)
- 기본값 제공 (모든 우회 옵션 기본값은 `False`)

### file_io.py 추가 책임
- `proxies.txt` 파일을 읽어 프록시 목록(`list[str]`) 반환
- `user_agents.txt` 파일을 읽어 UA 목록(`list[str]`) 반환
- 파일이 없으면 빈 리스트 반환 (우회 옵션 비활성화)

### measurer.py 상세 책임
- `duckduckgo-search` 라이브러리를 통해 검색 요청 수행
- `.env`에서 설정한 User-Agent를 `DDG.results()`에 전달
- `DDG_ROTATE_UA=true` 시 UA 목록을 순환하며 사용
- `DDG_USE_PROXY=true` 시 프록시 목록을 순환하며 사용, 실패 시 다음 프록시 시도
- 요청 사이 `random.uniform(DDG_MIN_DELAY, DDG_MAX_DELAY)` 딜레이 (단, `DDG_IGNORE_DELAY=true` 시 제외)
- 429/403/timeout 등 네트워크 실패 시 지수 백오프 적용 (2초 → 4초 → 8초)
- 최대 `DDG_MAX_RETRIES`회 재시도 후 실패 시 `None` 반환
- `DDG_IGNORE_SSL=true` 시 SSL 검증 우회 옵션 적용

### 우회 구현 시 함수 구조 예시
```python
def measure_keyword(
    keyword: str,
    config: Config,
    proxies: list[str] | None = None,
    user_agents: list[str] | None = None,
    proxy_index: int = 0,
    ua_index: int = 0
) -> int | None:
    # 우회 옵션에 따른 proxy/ua 선택 로직
    # DDG.results() 호출
    # 지수 백오프 재시도 로직
```
