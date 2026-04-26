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
