# KCPC 프로젝트 운영 가이드

`README.md` 대체 문서다. KCPC는 입력 키워드별 DuckDuckGo 상위 10개 검색 결과의 title 매칭 수를 측정한다. 이 값은 전체 인터넷 경쟁 페이지 수가 아니다.

## 설치
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
pip install -e .
```

## 기본 실행
```bash
python -m kcpc.main --input ./input/keywords.xlsx
python -m kcpc.main --input ./input/keywords.xlsx --output ./output/result.xlsx
python -m kcpc.main --input ./input/keywords.csv --output ./output/result.csv --format csv
python -m kcpc.main --input ./input/keywords.xlsx --reset
```

## QA를 위한 Google Search API 설정

QA 시 DDG 측정값의 신뢰성을 검증하기 위해 Google Search API를 사용할 수 있습니다. 설정 방법은 **[Google API 설정 가이드](google-api-setup-guide.md)**를 참조하세요.

### 간단 요약
1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. Custom Search API 활성화
3. API 키 생성 (`GOOGLE_API_KEY`)
4. [Programmable Search Engine](https://programmablesearchengine.google.com/)에서 검색 엔진 생성 (`GOOGLE_SEARCH_ENGINE_ID`)
5. `.env` 파일에 설정 추가

## 산출물
| 산출물 | 경로 |
|---|---|
| 결과 Excel | `output/kcpc_result.xlsx` |
| DB | `data/kcpc_database.db` |
| 로그 | `logs/kcpc.log` |
| QA 리포트 | `output/qa/qa_report.md` |
