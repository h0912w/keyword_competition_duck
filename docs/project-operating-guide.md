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

## 산출물
| 산출물 | 경로 |
|---|---|
| 결과 Excel | `output/kcpc_result.xlsx` |
| DB | `data/kcpc_database.db` |
| 로그 | `logs/kcpc.log` |
| QA 리포트 | `output/qa/qa_report.md` |
