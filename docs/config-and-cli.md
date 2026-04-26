# 설정 및 CLI

## `.env.example`
```env
# 기본 DDG 요청 설정
DDG_MIN_DELAY=2.0
DDG_MAX_DELAY=3.5
DDG_MAX_RETRIES=3
DDG_TIMEOUT=10
DDG_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
DDG_MAX_RESULTS=10

# 차단 우회 옵션 (사용자가 명시적으로 설정한 경우에만 활성화)
# 프록시 사용
DDG_USE_PROXY=false
DDG_PROXY_LIST=./proxies.txt
# User-Agent 순환
DDG_ROTATE_UA=false
DDG_UA_LIST=./user_agents.txt
# 딜레이 무시 (차단 위험 높음)
DDG_IGNORE_DELAY=false
# SSL 검증 우회
DDG_IGNORE_SSL=false

# QA 전용 Google Search API 설정
# QA 시에만 Google 정식 API를 사용하여 신뢰성 검증
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
QA_USE_GOOGLE_API=true
QA_MAX_GOOGLE_QUERIES=10

# 데이터베이스 및 출력 경로
DB_FILE_PATH=./data/kcpc_database.db
LOG_FILE_PATH=./logs/kcpc.log
OUTPUT_FILE_PATH=./output/kcpc_result.xlsx
OUTPUT_FORMAT=xlsx
```

### DuckDuckGo 요청 정책

#### 기본 정책 (우회 비활성화 시)
- **User-Agent**: 일반 브라우저 User-Agent 사용하여 봇 탐지 방지
- **요청 간격**: `DDG_MIN_DELAY`~`DDG_MAX_DELAY` 초 사이 랜덤 딜레이 강제
- **재시도**: 네트워크 실패 시 지수 백오프(exponential backoff) 적용
- **표준 라이브러리**: `duckduckgo-search` 공식 라이브러리만 사용

#### 우회 옵션 (사용자 명시적 설정 시)
| 옵션 | 환경 변수 | 기본값 | 설명 |
|---|---|---|---|
| **프록시 사용** | `DDG_USE_PROXY` | `false` | `true` 시 `proxies.txt`의 프록시를 순환하며 사용 |
| **프록시 목록** | `DDG_PROXY_LIST` | `./proxies.txt` | 한 줄당 `http://host:port` 또는 `https://host:port` 형식 |
| **UA 순환** | `DDG_ROTATE_UA` | `false` | `true` 시 `user_agents.txt`의 UA를 순환하며 사용 |
| **UA 목록** | `DDG_UA_LIST` | `./user_agents.txt` | 한 줄당 하나의 User-Agent 문자열 |
| **딜레이 무시** | `DDG_IGNORE_DELAY` | `false` | `true` 시 딜레이 없이 연속 요청 (차단 위험 높음) |
| **SSL 무시** | `DDG_IGNORE_SSL` | `false` | `true` 시 SSL 인증서 검증 우회 |

#### 우회 구현 시 주의사항
- 모든 우회 옵션은 **사용자가 `.env`에서 명시적으로 `true`로 설정한 경우에만** 활성화
- 프록시/UA 목록 파일이 없으면 우회 옵션을 무시하고 기본 동작 수행
- `DDG_IGNORE_DELAY=true`는 DuckDuckGo 서버에 과부하를 주어 영구 차단될 수 있음

## CLI
| 옵션 | 필수 | 설명 |
|---|---:|---|
| `--input` | 예 | 입력 파일 경로 |
| `--output` | 아니오 | 출력 파일 경로 |
| `--format` | 아니오 | `xlsx` 또는 `csv` |
| `--reset` | 아니오 | 기존 DB 무시 후 신규 실행 |
