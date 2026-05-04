# 입력/출력 계약

## 입력
| 항목 | 계약 |
|---|---|
| 확장자 | `.txt`, `.csv`, `.xlsx` |
| 구조 | 첫 번째 열 키워드 세로 나열 |
| 허용 값 | 공백 포함 문자열 |
| 제외 값 | 빈 줄, 공백만 있는 값, NaN |

## 중복 처리
- 원본 키워드는 보존한다.
- 정규화 키는 `lower().strip()`이다.
- 최초 등장 키워드만 측정하고 중복 입력은 기존 결과를 재사용한다.
- 출력에는 모든 유효 입력 키워드가 존재해야 한다.

## Results 컬럼
`Original_Index`, `Keyword`, `Normalized_Key`, `Top10_Title_Match_Count`, `Status`, `Error_Message`, `Updated_At`

## Excel 시트
- `Results`: 키워드별 결과
- `Run_Summary`: 입력 수, 성공/실패/중복 수, 시작/종료/소요 시간
- `Failed_Items`: 실패 항목
- `QA_Summary`: QA 이후 생성 가능

## GLM API 검증 출력
### JSON 결과 파일 (`./output/qa/glm_websearch_results.json`)
```json
{
  "timestamp": "2026-05-04T20:55:34",
  "method": "GLM API Google Search (Inference via Anthropic-compatible endpoint)",
  "model": "glm-4.7",
  "endpoint": "https://api.z.ai/api/anthropic/v1/messages",
  "results": [
    {
      "keyword": "python",
      "ddg_count": 8,
      "google_result_count": 10000000000,
      "google_estimate": "high",
      "correlation": "high",
      "notes": "10000000000"
    }
  ]
}
```

### 검증 리포트 파일 (`./output/qa/glm_verification_report.md`)
- **Summary**: 전체 통계 (High/Medium/Low 비율, 평균 점수)
- **Detailed Results**: 키워드별 상세 비교표
- **Verdict**: EXCELLENT/GOOD/REVIEW REQUIRED

### 상관관계 점수 척도
| 등급 | 점수 | High+Medium 비율 | 설명 |
|------|------|------------------|------|
| EXCELLENT | 2.4-3.0 | ≥ 80% | 매우 높은 상관관계 |
| GOOD | 1.8-2.3 | 60-79% | 높은 상관관계 |
| REVIEW REQUIRED | < 1.8 | < 60% | 상관관계 재검토 필요 |
