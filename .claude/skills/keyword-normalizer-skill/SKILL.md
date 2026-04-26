# keyword-normalizer-skill

## 역할
키워드 정제와 중복 판정. 원본 키워드를 보존하고 lower().strip() 기반 key/hash를 만든다.

## 공통 규칙
- `CLAUDE.md`의 금지사항과 입출력 계약을 우선한다.
- 출력 계약을 임의 변경하지 않는다.
- 실패 정보는 로그와 DB/QA 리포트에 남긴다.

## 관련 참조
- `CLAUDE.md`
- `docs/input-output-contract.md`
- `docs/workflow-and-failure-policy.md`
- `docs/source-requirements-map.md`
