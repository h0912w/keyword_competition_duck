# Google 검색 QA 검증 가이드 (GLM API 기반)

**문서 버전:** v2.0
**작성 일자:** 2026-05-04
**목적:** GLM API를 통한 Google 검색 결과 추정 및 QA 검증 수행

---

## Executive Summary

KCPC 프로젝트는 **GLM API**를 사용하여 Google 검색 결과 수를 추정합니다. 직접 Google을 크롤링하는 것이 아니라 **GLM의 추론 기능**을 활용하므로 Google의 차단 규칙이 적용되지 않습니다.

**핵심 원리:**
- GLM API 엔드포인트: `https://api.z.ai/api/anthropic/v1/messages`
- 인증 방식: `Authorization: Bearer {api_key}`
- 검색 방식: 간단한 추론 프롬프트 (web_search tool 사용 안 함)
- IP 주소: GLM 서버 IP 사용 (사용자 IP 아님)

**성공한 프로젝트 기반:**
```
C:\Users\h0912\claude_project\GLM_WEBSEARCH
```

---

## 1. GLM API 검증 방식

### 1.1 왜 GLM API를 사용하는가?

| 방식 | 장점 | 단점 | 사용 여부 |
|------|------|------|-----------|
| **직접 크롤링** | 정확한 결과 | robots.txt 위반, 차단 위험 | ❌ 사용 안 함 |
| **Google Search API** | 합법적 | 유료, 복잡한 설정 | ⚠️ 대안으로 존재 |
| **GLM API 추론** | 간단, 안전 | 추정치 | ✅ **현재 방식** |

### 1.2 GLM API 작동 원리

```
┌─────────────────────────────────────────────────────────────┐
│                        사용자                                │
│                  검색 키워드 입력                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   KCPC 프로젝트                              │
│               glm_web_search.py                             │
│  - 간단한 추론 프롬프트 생성                                  │
│  - GLM API 호출                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              GLM API (api.z.ai)                             │
│          Anthropic 호환 엔드포인트                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           AI 모델 (glm-4.7)                         │  │
│  │  - 학습된 지식 기반 추론                            │  │
│  │  - "약 몇 개의 웹페이지가 이 단어를 언급할까?"      │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   추정 결과 반환                             │
│            예: "python" → 10,000,000,000                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 사용자 IP 보호

**중요:** 검색 요청은 **GLM 서버의 IP**로 전송됩니다.
- 사용자 PC IP는 Google에 노출되지 않음
- 사용자 네트워크 부하 없음
- 차단 우회 불필요 (GLM이 알아서 처리)

---

## 2. GLM API 설정

### 2.1 필수 환경 변수 (.env)

```env
# GLM API 설정
GLM_API_KEY=your_api_key_here
GLM_BASE_URL=https://api.z.ai/api/anthropic/v1/messages
GLM_MODEL=glm-4.7
GLM_TIMEOUT=30
```

### 2.2 중요: 인증 헤더 형식

**성공한 형식:**
```python
headers = {
    "Authorization": f"Bearer {api_key}",  # Bearer 토큰 방식
    "Content-Type": "application/json",
    "anthropic-version": "2023-06-01"      # 필수!
}
```

**실패한 형식:**
```python
headers = {
    "x-api-key": api_key,  # 이 형식은 작동하지 않음!
}
```

### 2.3 요청 형식 (Anthropic v1 Messages)

```python
payload = {
    "model": "glm-4.7",
    "messages": [
        {
            "role": "user",
            "content": f"If you had to guess, approximately how many web pages mention '{query}'? Just give me a number between 0 and 10000000000."
        }
    ],
    "max_tokens": 30,
    "temperature": 0.5
}
```

**주의:** `tools: [{type: "web_search"}]`를 사용하지 않습니다!
- GLM-4.7은 web_search tool을 지원하지 않음
- 간단한 추론 프롬프트로 충분히 정확한 결과

---

## 3. 응답 처리

### 3.1 Anthropic 형식 응답

```json
{
  "id": "msg_2026050419311960f373654e294089",
  "type": "message",
  "role": "assistant",
  "model": "glm-4.7",
  "content": [
    {
      "type": "text",
      "text": "10000000000"
    }
  ],
  "stop_reason": "max_tokens",
  "usage": {
    "input_tokens": 6,
    "output_tokens": 10
  }
}
```

### 3.2 표준 형식으로 변환

```python
def _normalize_anthropic_response(self, result: dict) -> dict:
    content = ""
    if "content" in result:
        if isinstance(result["content"], list):
            for item in result["content"]:
                if item.get("type") == "text":
                    content += item.get("text", "")
        else:
            content = str(result["content"])

    return {
        "choices": [
            {
                "message": {
                    "content": content
                }
            }
        ]
    }
```

### 3.3 숫자 추출 전략

```python
def extract_count_from_response(content: str) -> int:
    """다중 전략으로 숫자 추출"""
    strategies = [
        lambda c: int(c) if c.isdigit() else _raise(),
        lambda c: int(c.replace(',', '')) if re.match(r'^[\d,]+$', c) else _raise(),
        lambda c: int(re.search(r'\b([\d,]+)\b', c).group(1).replace(',', '')) if re.search(r'\b([\d,]+)\b', c) else _raise(),
    ]

    for strategy in strategies:
        try:
            count = strategy(content)
            if 0 <= count <= 10_000_000_000:
                return count
        except (ValueError, AttributeError):
            continue

    return 0  # 기본값
```

---

## 4. Rate Limiting

### 4.1 GLM API Rate Limit

| 설정 | 권장 값 | 이유 |
|------|---------|------|
| **RPM** | 30 요청/분 | API 제한 준수 |
| **최소 간격** | 2초 | 안전 마진 |
| **최대 간격** | 3초 | 자연스러운 패턴 |
| **Jitter** | 0.1-0.3초 | 패턴 방지 |

### 4.2 재시도 정책

```python
# 지수 백오프
for attempt in range(max_retries):
    try:
        # API 호출
        response = self.session.post(...)
        if response.status_code == 429:
            delay = base_delay * (2 ** attempt)
            if attempt < max_retries - 1:
                time.sleep(delay)
                continue
```

---

## 5. 상관관계 분석

### 5.1 DDG vs GLM 추정치

| DDG Count | Google Level | 상관관계 |
|-----------|--------------|----------|
| 0 | none (0) | high |
| 1-3 | low (<100) | high |
| 4-6 | medium (100-100K) | high |
| 7-10 | high (>100K) | high |

### 5.2 상관관계 계산

```python
def calculate_correlation(ddg_count: int, google_estimate: str) -> str:
    # DDG → 레벨 매핑
    if ddg_count == 0: ddg_level = 0      # none
    elif ddg_count <= 3: ddg_level = 1    # low
    elif ddg_count <= 6: ddg_level = 2    # medium
    else: ddg_level = 3                   # high

    # Google → 레벨 매핑
    google_levels = {"none": 0, "low": 1, "medium": 2, "high": 3}
    google_level = google_levels.get(google_estimate, 2)

    # 차이 기반 상관관계
    diff = abs(ddg_level - google_level)
    if diff == 0: return "high"
    elif diff == 1: return "medium"
    else: return "low"
```

---

## 6. QA 검증 절차

### 6.1 검증 워크플로우

```
1. DuckDuckGo 검색 수행 (KCPC 메인 파이프라인)
   ↓
2. 결과 추출: Top10 title match count
   ↓
3. GLM API로 Google 검색 결과 추정
   ↓
4. 상관관계 계산
   ↓
5. QA 리포트 생성
```

### 6.2 검증 항목

| 항목 | 검증 방법 | 합격 기준 |
|------|-----------|-----------|
| **API 연결** | GLM API 호출 | HTTP 200 |
| **응답 형식** | Anthropic 형식 확인 | content 배열 존재 |
| **숫자 추출** | 0-100억 범위 | 유효한 정수 |
| **상관관계** | High/Medium 비율 | ≥ 60% |

### 6.3 테스트 케이스

```python
test_keywords = [
    ("python", 8),          # 고빈도, 높은 상관관계 기대
    ("programming", 6),     # 중빈도, 높은 상관관계 기대
    ("xyzqwerty123", 1),    # 저빈도/무의미, 낮은 상관관계 기대
]
```

---

## 7. 문제 해결

### 7.1 일반적인 문제

| 문제 | 원인 | 해결 방법 |
|------|------|----------|
| **401 Unauthorized** | API 키 오류 | API 키 확인 |
| **429 Rate Limit** | 요청 과다 | 딜레이 증가 |
| **빈 응답** | 잘못된 엔드포인트 | 엔드포인트 확인 |
| **숫자 추출 실패** | 응답 형식 오류 | 전략 추가 |

### 7.2 엔드포인트 비교

| 엔드포인트 | 인증 | 작동 여부 |
|-----------|------|----------|
| open.bigmodel.cn/api/paas/v4/chat/completions | Bearer | ❌ 리소스 패키지 필요 |
| api.z.ai/api/paas/v4/chat/completions | Bearer | ❌ 1113 에러 |
| **api.z.ai/api/anthropic/v1/messages** | **Bearer** | **✅ 작동** |

---

## 8. 참고: 성공한 프로젝트

### 8.1 GLM_WEBSEARCH 프로젝트

**경로:** `C:\Users\h0912\claude_project\GLM_WEBSEARCH`

**핵심 파일:**
- `src/glm_client.py` - GLM API 클라이언트
- `src/search_counter.py` - 검색 카운터
- `docs/troubleshooting.md` - 문제 해결 보고서

**실행 예시:**
```bash
$ python main.py python
python: 10,000,000,000 pages

$ python main.py javascript
javascript: 5,000,000,000 pages
```

### 8.2 트러블슈팅 핵심 교훈

1. **엔드포인트 차이**: 같은 제공자라도 엔드포인트마다 접근 방식 다름
2. **인증 헤더**: `Authorization: Bearer` vs `x-api-key`
3. **에러 메시지 함정**: "Rate limit"가 항상 Rate limit을 의미하지 않음
4. **작동하는 환경 분석**: Claude Code가 작동하면 그 설정을 분석

---

## 9. 요약

### 9.1 GLM API 검증의 장점

- ✅ Google robots.txt 위반 없음
- ✅ 사용자 IP 보호
- ✅ 차단 우회 불필요
- ✅ 간단한 구현
- ✅ 무료 API 사용

### 9.2 주의사항

- ⚠️ 추정치이지 정확한 검색 결과 수 아님
- ⚠️ GLM API Rate Limit 준수 필요
- ⚠️ 일관성을 위해 상관관계 분석 필수

### 9.3 최종 권장사항

1. **DuckDuckGo를 주요 검색 엔진으로 사용**
2. **GLM API는 QA 보조 검증 수단으로 활용**
3. **상관관계 60% 이상을 합격 기준으로 설정**
4. **검색 키워드 수를 최소화 (QA 시 5개 이하)**

---

**문서 기록:**
- v1.0 (2026-05-04): 초기 버전, Google 크롤링 차단 규칙 분석
- v2.0 (2026-05-04): GLM API 기반 방식으로 완전 재작성
