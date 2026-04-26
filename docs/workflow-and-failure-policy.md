# 워크플로우 및 실패 정책

## 흐름
입력 파싱 → 정제/중복 처리 → DB 초기화/복구 → DDG 검색 → title 검증 → DB 저장 → export → QA.

## 상태 전이
`PENDING -> RUNNING -> DONE`, `PENDING -> RUNNING -> FAILED`, `PENDING -> SKIPPED_DUPLICATE`.

## 실패 정책
| 상황 | 처리 |
|---|---|
| 파일 없음/확장자 오류 | 즉시 중단 |
| 유효 키워드 0개 | 즉시 중단 |
| 네트워크 실패 | 최대 3회 재시도 후 해당 키워드 `FAILED`, -1 |
| 결과 구조 비정상 | 해당 키워드 `FAILED`, -1 |
| DB 쓰기 실패 | 즉시 중단 |
| DB 손상 | 백업 후 에스컬레이션 |
| 출력 파일 잠김/권한 오류 | 오류 출력 후 중단 |
| **429 Too Many Requests** | 지수 백오프 후 재시도, 지속 시 해당 키워드 `FAILED` |
| **403 Forbidden** | User-Agent/헤더 검증 후 재시도, 지속 시 해당 키워드 `FAILED` |
| **프록시 연결 실패** | 다음 프록시 시도, 모두 실패 시 기본 연결로 폴백 |

## Ctrl+C
현재 처리 상태가 불완전하게 남지 않도록 하고, 다음 실행에서 `RUNNING` 항목을 재처리한다.

---

## DuckDuckGo 차단 정책

### 기본 동작 (우회 비활성화)
검색엔진의 이용약관을 준수하면서, 정상적인 사용자 행위를 모방하여 차단을 예방한다.

| 수단 | 설명 | 구현 위치 |
|---|---|---|
| **적절한 User-Agent** | 최신 브라우저 User-Agent 사용, 봇 탐지 방지 | `config.py`, `.env` |
| **요청 간격 강제** | `DDG_MIN_DELAY`~`DDG_MAX_DELAY` 초 사이 랜덤 딜레이 | `measurer.py` |
| **지수 백오프** | 429/403 응답 시 대기 시간 증가 | `measurer.py` |
| **표준 라이브러리** | `duckduckgo-search` 공식 패키지만 사용 | `requirements.txt` |
| **동시 요청 금지** | v1.0에서는 순차적 요청만 허용 | `pipeline.py` |

### 사용자 옵션에 따른 우회 수단
사용자가 `.env`에서 명시적으로 설정한 경우, 다음 우회 수단을 사용할 수 있다.

| 우회 수단 | 환경 변수 | 활성화 조건 | 구현 방법 |
|---|---|---|---|
| **프록시 순환** | `DDG_USE_PROXY=true` | 사용자 명시적 설정 | `proxies.txt`에서 프록시를 순환하며 사용 |
| **User-Agent 순환** | `DDG_ROTATE_UA=true` | 사용자 명시적 설정 | `user_agents.txt`에서 UA를 순환하며 사용 |
| **딜레이 무시** | `DDG_IGNORE_DELAY=true` | 사용자 명시적 설정 | 요청 간 딜레이 제거 (차단 위험 높음) |
| **SSL 검증 우회** | `DDG_IGNORE_SSL=true` | 사용자 명시적 설정 | SSL 인증서 검증 건너뛰기 |

### 우회 구현 시 유의사항
1. 모든 우회 옵션은 **사용자가 `.env`에서 명시적으로 `true`로 설정한 경우에만** 활성화
2. 프록시/UA 목록 파일이 없으면 우회를 시도하지 않고 기본 동작 수행
3. 프록시 연결 실패 시 다음 프록시로 시도, 모두 실패하면 직접 연결로 폴백
4. `DDG_IGNORE_DELAY=true`는 DuckDuckGo 서버에 과부하를 주어 영구 차단될 수 있음
5. 우회는 사용자 책임 하에 수행되며, 프로젝트는 기본적으로 이용약관 준수를 권장

### 구현 시 필요한 처리
1. `duckduckgo-search` 라이브러리의 `result` 객체만 사용, 직접 HTML 파싱 금지
2. User-Agent는 `.env`에서 설정 가능하도록 구현
3. 요청 실패 시 재시도 간격은 첫 번째 실패 후 2초, 두 번째 후 4초, 세 번째 후 8초 등 지수 증가
4. 프록시 사용 시 `DDG.results()`의 `proxy` 파라미터 활용
5. SSL 무시 시 `verify=False` 옵션 사용 (requests 라이브러리 기반)

---

## 우회 설정 파일 형식

### proxies.txt
```
http://proxy1.example.com:8080
http://proxy2.example.com:8080
https://secure-proxy.example.com:8443
socks5://socks-proxy.example.com:1080
```

### user_agents.txt
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15
```
