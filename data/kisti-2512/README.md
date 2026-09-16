# data/kisti-2512 — 구 규약 산출물 (정책 없음, 보존)

view `kisti-2512` v2(1,651,487편, `591b4325 / 2026-09-08T07:01:07Z`; v1 산출물은 `*.v1.*`) 기준 Stage 1·2 산출물과
스모크(`output.smoke.*`, Securing Large Language Models, 44편). **2026-09-14 규약(topic 별 GT 최초 공개일 cutoff) 이전 실행이며
retrieval 정책이 없다** — 결과표에는 `policy=none, view 컷 2025-12-31` 로 표기하고, 새 규약 결과(`data/kisti-2608/`)와 같은 표에 두지 않는다.

- 규약상 못 쓰는 이유(2026-09-16 실측, `ref_time_check.v2-nopolicy.json`): `input.jsonl` 25 topic 입력 2,767편 중 **876편이
  topic cutoff 이후**(instruction-tuning 109편 중 94, model-merging 157 중 118 …). pool 단계에서는 instruction-tuning 1,200편 중 999편.
  Stage 2 가 사후 필터로 걸러도 "허용 집합 안에서 검색" 규약을 만족하지 못하므로 Stage 1 부터 `kisti-2608` 로 재실행했다.
- 삭제하지 않는다. 파일별 정체는 `docs/experiments/kisti-2512.md` §5 재현성 체인.
