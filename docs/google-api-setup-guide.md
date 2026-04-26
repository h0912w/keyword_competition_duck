# Google Search API 설정 가이드

KCPC QA 검증을 위해 Google Custom Search API를 설정하는 방법입니다.

---

## 전제 조건

- Google 계정
- 신용카드 (API 사용 요금 청구용, 무료 할당량 내에서는 비용 없음)

---

## Step 1: Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 상단에서 프로젝트 선택 → **"새 프로젝트"** 클릭
3. 프로젝트 이름 입력 (예: `KCPC-QA`)
4. **"만들기"** 클릭

---

## Step 2: Custom Search API 활성화

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 선택
2. **"API 및 서비스"** → **"라이브러리"** 클릭
3. **"Custom Search API"** 검색
4. **"Custom Search API"** 클릭 후 **"사용 설정"** 클릭

---

## Step 3: API 키 생성

1. **"API 및 서비스"** → **"사용자 인증 정보"** 클릭
2. 상단에서 **"사용자 인증 정보 만들기"** 클릭
3. **"API 키"** 선택 후 **"다음"** 클릭
4. 생성된 API 키 복사 (`.env`의 `GOOGLE_API_KEY`에 입력)

### API 키 제한 설정 (선택 사항 but 권장)
1. 생성된 API 키 클릭
2. **"애플리케이션 제한사항"**에서 **"IP 주소"** 선택
3. 로컬 테스트용으로는 비워두거나 개인 IP 입력

---

## Step 4: Programmable Search Engine (CSE) 생성

1. [Google Programmable Search Engine](https://programmablesearchengine.google.com/) 접속
2. **"추가"** → **"프로그래밍 가능 검색 엔진"** 클릭
3. **"시작하기"** 클릭
4. 검색 엔진 설정:
   - **"검색 엔진 이름"** 입력 (예: `KCPC QA`)
   - **"검색할 사이트"** 입력 (예: `www.example.com`)
   - **"만들기"** 클릭

---

## Step 5: 검색 엔진 ID (CX) 확인 및 설정

1. 생성된 검색 엔진 클릭
2. **"설정"** 탭 클릭
3. **"검색 엔진 ID"** 복사 (`.env`의 `GOOGLE_SEARCH_ENGINE_ID`에 입력)

### 중요: 전체 웹 검색 설정

기본적으로 CSE는 특정 사이트만 검색합니다. 전체 웹 검색을 위해서는:

1. 검색 엔진의 **"설정"** → **"웹"** 탭으로 이동
2. **"전체 웹을 검색하도록 설정"** 활성화
3. **"저장"** 클릭

---

## Step 6: `.env` 파일 설정

프로젝트 루트의 `.env` 파일에 다음 내용 추가:

```env
# QA 전용 Google Search API 설정
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GOOGLE_SEARCH_ENGINE_ID=012345678901234567890:abcdefg
QA_USE_GOOGLE_API=true
QA_MAX_GOOGLE_QUERIES=10
```

---

## Step 7: 무료 할당량 확인

Google Custom Search API 무료 할당량:
- **일일 100회** 쿼리 (무료)
- 초과 시 1000회당 $5 청구

QA 시 `QA_MAX_GOOGLE_QUERIES=10`으로 제한하여 무료 할당량 내에서 사용하십시오.

---

## Step 8: 테스트

```bash
# QA 실행으로 Google API 검증 테스트
python -m kcpc.main --input ./input/test_keywords.txt

# QA 리포트 확인
cat ./output/qa/qa_report.md
```

---

## 문제 해결

### "QUOTA_EXCEEDED" 오류
- 무료 할당량(일일 100회) 초과
- 다음 날 다시 시도 또는 유료 요금제로 업그레이드

### "API key not valid" 오류
- API 키가 올바르지 않음
- Google Cloud Console에서 API 키 재확인

### "Invalid cx" 오류
- 검색 엔진 ID(CX)가 올바르지 않음
- Programmable Search Engine에서 CX ID 재확인

### "Forbidden" 오류
- API 사용 제한 설정 확인
- IP 제한이 설정된 경우 현재 IP가 허용 목록에 있는지 확인

---

## 참고 링크

- [Google Cloud Console](https://console.cloud.google.com/)
- [Custom Search API](https://developers.google.com/custom-search/v1/overview)
- [Programmable Search Engine](https://programmablesearchengine.google.com/)
- [API 키 관리](https://console.cloud.google.com/apis/credentials)
