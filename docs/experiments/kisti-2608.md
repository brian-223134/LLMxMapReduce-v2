# KISTI `kisti-2608` + topic 별 cutoff 정책 — Stage 1·2 실행 기록 (2026-09-16)

2026-09-14 규약(교수님 지시): reference cutoff 를 2025-12-31 로 고정하지 않는다. corpus 는 시간 컷 없는 view `kisti-2608`
(1,663,704편)이고, **retrieval 이 topic 마다 GT survey 최초 공개일(`retrieval_cutoff_at`) 이전 문헌만** 허용 집합 안에서 뽑는다.
정본은 `/data2/chanjoong/kisti_data/docs/asg/AGENT-HANDOFF.md` §0 과 AutoSurvey `docs/retrieval-policy.md`. 구 규약 실행 기록은
[kisti-2512.md](kisti-2512.md) — 그 산출물(`data/kisti-2512/`)은 **정책 없음** 으로 표기해 보존한다(`data/kisti-2512/README.md`).

## 1. 무엇을 바꿨나 (이 레포)

| 항목 | 변경 |
|---|---|
| Stage 1 `scripts/retrieve_pool.py` | `--topic_policy PATH` 추가. topic 마다 `topics.kisti.jsonl` 의 `slug`(= 정책 `topic_id`)로 행을 골라 AutoSurvey `database.set_policy(policy_from_row(row))` 를 건 뒤 검색 — FAISS `IDSelectorBitmap` 이라 **검색 자체가 허용 집합 안에서** 돈다(전체 Top-K 뒤 사후 필터 아님). 검색 결과가 허용 집합 밖이면 예외, sidecar 없으면 거부. pool 행에 `retrieval_policy`(topic_id · cutoff · 허용 편수 · 허용 집합 sha256 · 제외 사유 · sidecar meta), `pools.jsonl.manifest.json` 에 DB/정책 파일 sha·view sha. 정책 없이 돌면 `retrieval_policy: null`(구 규약 표기) |
| Stage 2 | corpus 쪽 `build_corpus_input_kisti.py`(2026-09-16, `--topic_policy` 사후 검사·`--quota_field n_gt_refs_cutoff`) 그대로. `run_stages.sh` 가 `KISTI_VIEW=kisti-2608` 이면 DB·정책 파일을 자동으로 넘긴다 |
| `scripts/run_manifest.py` | run 수준 `corpus`(view · papers.parquet sha 앞 8자 · created_at → 버전 열), `retrieval_policy`(mode · 정책 파일 sha · sidecar · Stage 2 위반 합계 · Stage 1 누락 topic), topic 수준 `retrieval_policy`(Stage 1 선택자 결과 + Stage 2 사후 검사 병합; `allowed` 불일치·`stage1_leak` 플래그). `--pools` 인자(기본 input 옆 `pools.jsonl`) |
| `scripts/ref_time_check.py` (신규) | 결과 ref 판정: `allowed` / **`time_violation`(cutoff 이후 실재 논문 = 시간 범위 위반)** / `excluded_id`(GT 누수) / `no_date` / **`not_in_corpus`·`unlisted_ref`(허위·미확인 인용 후보)** 를 cited·listed 로 나눠 기록. 원본 출력은 수정하지 않는다 |
| `scripts/pool_ceiling.py` | GT 키를 `gap_to_80_refs.jsonl` 의 `view_id` 로 매칭(없으면 규칙 B 변환), `n_gt_refs_cutoff`·cutoff 열 추가, `tier == in_view` 편수가 `n_gt_refs_cutoff` 와 다르면 경고 |
| `scripts/leak_check.py` | `--exclude_keys` 기본 경로가 `$KISTI_VIEW`(기본 kisti-2512) 를 따른다 — 새 view 는 명시 |
| tests | `test_retrieve_pool.py` · `test_ref_time_check.py` · `test_run_manifest.py`(정책 블록) · **`test_pseudo_survey_e2e.py`**(가짜 corpus·정책·pseudo Survey 출력으로 Stage 1→2→검사→manifest 체인, 오염 출력 검출) — 65건, API·GPU 없음 |

`KISTI_VIEW` 기본값(kisti-2512)은 바꾸지 않았다. 실행은 `KISTI_VIEW=kisti-2608` 을 명시한다.

## 2. 공통 설정

| 항목 | 값 |
|---|---|
| corpus / 버전 | view `kisti-2608` (1,663,704편, 시간 컷 없음) — **`c1a0c6b3 / 2026-09-14T13:18:56Z`** (papers.parquet sha 앞 8자 / created_at) |
| retrieval 백엔드 | `../AutoSurvey/database_kisti-kisti-2608` (v2 인덱스 + 12,217편 append, 2026-09-14 13:48 UTC, ntotal 1,663,704 = sidecar 레코드 수) |
| 정책 파일 | `../AutoSurvey/data/topic_policy.kisti-2608.jsonl` (25행 status ok, sha256 `ee010f27…`) |
| 문헌 날짜 | sidecar `paper_dates.json` (2026-09-14T13:26:03Z, month 460,772 / day 1,198,375 / year 4,557) |
| 판정 | `upper_bound(공개일) < retrieval_cutoff_at` (당일·날짜 불명 제외) ∧ id ∉ `exclude_ids` |
| quota | `n_gt_refs_cutoff` (topic 별 cutoff 분모; 합 2,559, 구 `n_gt_refs` 합 2,767) |
| 원문 게이트 | `--min_chars 2000` · `--max_chars 250000`, 제외 파일 `data/views/kisti-2608/exclude_ids.txt`(40키) |
| 프로파일 (Stage 3, 미실행) | temperature 0.6 · max_tokens 8192 가드 · 잘림 재요청, `--block_count 1`, `--parallel_num 4` |

## 3. Stage 1·2 실측 (2026-09-16 03:18–03:40 UTC)

| 단계 | 결과 |
|---|---|
| Stage 1 (GPU 3) | 25 topic × 1,200편. 정책 경고 0, 누수 게이트 예외 0, **인덱스에 남은 제외 id 0**, 허용 편수가 AutoSurvey `policy_report.py` 표와 topic 마다 일치(예: instruction-tuning 1,304,896 / 1,663,704). 로딩 ≈ 10분 + topic 당 수 초 |
| Stage 2 | 25 topic 전부 quota 충족(2,559/2,559). **`blocked_after_cutoff` = 0, `blocked_no_date` = 0 (25/25)** → Stage 1 선택자가 제대로 걸렸다. too_short 3 · too_long 3 · excluded 0 · no_body 0. 입력 99.9MB, 원문 합 94.8M자 |
| 누수 검사 | `leak_check.py --input`: hard hits 0, title mention 0 (`leak_check.input.json`) |
| 시간 범위 | `ref_time_check.py --input`: time_violation 0 · excluded_id 0 · not_in_corpus 0 (`ref_time_check.input.json`) |
| ceiling | 평균 **pool 26.3%** (구 24.6%) / **input 8.5%** (구 8.1%) — 분모가 cutoff 분모로 바뀌어 직접 비교는 아님 |

topic 별 (`pool_ceiling.json`, `input.jsonl.manifest.json`, `pools.jsonl`). 괄호는 구 규약(kisti-2512 v2, 정책 없음, 분모 `n_gt_refs`) 값:

| slug | cutoff | 허용 편수 | quota (구 n_gt_refs) | GT in view | pool hits | pool ceil (구) | input hits | input ceil (구) | resolved | short/long | max chars |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| instruction-tuning-llms | 2023-08-21 | 1,304,896 | 95 (109) | 95 | 31 | 32.6% (15.4%) | 10 | 10.5% (1.8%) | 95/95 | 0/0 | 81,444 |
| llm-function-calling | 2026-01-14 | 1,654,546 | 74 (77) | 74 | 14 | 18.9% (18.9%) | 7 | 9.5% (9.5%) | 74/74 | 0/0 | 92,026 |
| model-merging | 2024-08-14 | 1,460,094 | 139 (157) | 139 | 34 | 24.5% (28.5%) | 21 | 15.1% (17.0%) | 139/139 | 0/0 | 66,784 |
| diffusion-model-alignment | 2026-02-10 | 1,663,703 | 139 (128) | 139 | 23 | 16.6% (16.6%) | 11 | 7.9% (7.9%) | 139/139 | 0/0 | 187,217 |
| llm-agent-optimization | 2025-03-16 | 1,540,142 | 102 (112) | 102 | 28 | 27.5% (21.4%) | 8 | 7.8% (6.2%) | 102/102 | 0/0 | 149,339 |
| retrieval-explainability | 2022-12-14 | 1,202,448 | 113 (129) | 113 | 15 | 13.3% (8.7%) | 4 | 3.5% (2.4%) | 113/113 | 0/1 | 87,480 |
| trustworthy-rag | 2025-02-08 | 1,528,223 | 78 (87) | 78 | 13 | 16.7% (19.8%) | 3 | 3.9% (3.5%) | 78/78 | 0/0 | 81,169 |
| large-models-timeseries | 2023-10-16 | 1,326,717 | 183 (210) | 183 | 13 | 7.1% (8.9%) | 2 | 1.1% (1.4%) | 183/183 | 1/1 | 191,065 |
| deep-graph-clustering | 2022-11-23 | 1,191,055 | 83 (108) | 83 | 37 | 44.6% (43.5%) | 14 | 16.9% (21.3%) | 83/83 | 0/0 | 80,100 |
| negative-sampling-recsys | 2026-01-28 | 1,657,045 | 138 (135) | 138 | 42 | 30.4% (30.4%) | 20 | 14.5% (14.5%) | 138/138 | 0/0 | 146,366 |
| mllm-adversarial-attacks | 2026-03-30 | 1,663,703 | 52 (60) | 52 | 18 | 34.6% (34.6%) | 4 | 7.7% (7.7%) | 52/52 | 0/0 | 101,998 |
| llm-training-data-detection | 2026-01-07 | 1,653,071 | 56 (57) | 56 | 14 | 25.0% (25.0%) | 4 | 7.1% (7.1%) | 56/56 | 0/0 | 85,889 |
| physical-adversarial-attacks | 2022-11-03 | 1,186,466 | 128 (150) | 128 | 65 | 50.8% (45.0%) | 26 | 20.3% (17.4%) | 128/128 | 0/1 | 114,778 |
| harmful-finetuning | 2024-09-26 | 1,472,911 | 84 (107) | 84 | 40 | 47.6% (50.8%) | 15 | 17.9% (23.3%) | 84/84 | 0/0 | 85,895 |
| llm-watermarking | 2025-12-05 | 1,641,322 | 44 (44) | 42 ⚠ | 8 | 19.1% (19.1%) | 0 | 0.0% (0.0%) | 44/44 | 0/0 | 86,018 |
| moe-inference-optimization | 2024-12-18 | 1,503,417 | 111 (116) | 111 | 44 | 39.6% (37.2%) | 18 | 16.2% (11.5%) | 111/111 | 0/0 | 123,821 |
| kv-cache-serving | 2026-07-01 | 1,663,704 | 61 (61) | 61 | 19 | 31.1% (31.7%) | 1 | 1.6% (1.7%) | 61/61 | 0/0 | 145,986 |
| edge-slm-cloud-llm | 2025-07-22 | 1,591,193 | 134 (139) | 134 | 31 | 23.1% (20.6%) | 15 | 11.2% (11.0%) | 134/134 | 0/0 | 158,063 |
| llm-edge-inference | 2026-04-24 | 1,663,704 | 85 (94) | 85 | 13 | 15.3% (15.3%) | 5 | 5.9% (5.9%) | 85/85 | 0/0 | 67,843 |
| llm-distributed-training | 2024-07-29 | 1,451,432 | 165 (170) | 165 | 64 | 38.8% (28.2%) | 18 | 10.9% (8.1%) | 165/165 | 1/0 | 184,629 |
| edge-cloud-collaboration | 2025-05-03 | 1,561,520 | 167 (175) | 167 | 62 | 37.1% (35.9%) | 16 | 9.6% (9.0%) | 167/167 | 0/0 | 159,142 |
| wireless-foundation-models | 2025-12-26 | 1,643,688 | 119 (116) | 119 | 10 | 8.4% (8.4%) | 3 | 2.5% (2.5%) | 119/119 | 0/0 | 104,984 |
| ai-wireless-reasoning | 2026-04-23 | 1,663,704 | 72 (75) | 72 | 8 | 11.1% (11.1%) | 2 | 2.8% (2.8%) | 72/72 | 0/0 | 173,823 |
| agentic-satellite-networks | 2026-02-03 | 1,663,703 | 66 (68) | 66 | 9 | 13.6% (15.2%) | 3 | 4.5% (4.5%) | 66/66 | 0/0 | 85,679 |
| ai-video-streaming | 2024-06-04 | 1,431,447 | 71 (83) | 71 | 21 | 29.6% (25.3%) | 2 | 2.8% (3.8%) | 71/71 | 0/0 | 78,501 |

관찰:

- 2026년 cutoff 9 topic(허용 99~100%)은 pool·input 이 구 규약과 같다 — 2026년 문헌이 view 에 들어왔어도 검색 상위에 들지 않았다.
- 선행판 때문에 cutoff 가 앞당겨진 topic 은 pool 이 GT 시점 문헌으로 바뀌어 pool ceiling 이 오르는 쪽(instruction-tuning 15→33%, llm-distributed 28→39%)과
  내리는 쪽(harmful-finetuning 51→48%, model-merging 29→25%)이 섞였다. 분모(`n_gt_refs_cutoff`)도 함께 줄었으므로 recall 상한으로만 읽는다.
- **⚠ llm-watermarking 분모**: `topics.kisti.jsonl` 의 `n_gt_refs_cutoff` 는 44 인데 `gap_to_80_refs.jsonl` 의 `tier == in_view` 행 44건 중 view id 가
  중복인 쌍이 둘(`10.1145/3637528.3671573` ×2, `2310.08920` ×2) 있어 **서로 다른 논문은 42편**이다. `pool_ceiling.py` 는 id 집합으로 세므로 42 를
  분모로 쓴다. corpus 쪽(`candidates/gap_to_80.py`)에 전달할 것 — ref 행 수와 논문 수 중 무엇을 분모로 할지 결정 필요.
- 구 kisti-2512 입력을 새 정책으로 판정하면(`data/kisti-2512/ref_time_check.v2-nopolicy.json`) 2,767편 중 **876편이 cutoff 이후**다
  (instruction-tuning 109 중 94, model-merging 157 중 118). Stage 1 부터 재실행한 근거.

## 4. Stage 3 — 미실행

키 잔여가 **$0.63**(한도 $30 중 $29.37 사용, 2026-09-16 03:16 UTC `check_credits.py`)라 본편(25편 ≈ $30, 4~6h)을 돌리지 못했다. 키 한도 상향 후:

```bash
S=/data2/chanjoong/kisti_data/adapter/llmxmapreduce/run_stages.sh; K=/data2/chanjoong/kisti_data
KISTI_VIEW=kisti-2608 $S stage3                    # data/kisti-2608/input.jsonl → output.jsonl, 저장 완료 시 자동 종료
python scripts/run_manifest.py --log data/kisti-2608/log/stage3.log --output_jsonl data/kisti-2608/output.jsonl \
    --input_jsonl data/kisti-2608/input.jsonl --pool_ceiling data/kisti-2608/pool_ceiling.json --run_name stage3-2608
python scripts/leak_check.py --output data/kisti-2608/output.jsonl --exclude_keys $K/data/views/kisti-2608/exclude_keys.txt
python scripts/ref_time_check.py --output data/kisti-2608/output.jsonl --view kisti-2608 --out data/kisti-2608/ref_time_check.output.json
```

결과 ref 검증 규약: `ref_time_check.py` 가 cutoff 이후 실재 논문 인용을 **시간 범위 위반**(`time_violation`)으로, 입력 pool 밖 ref 를
허위·미확인 인용(`not_in_corpus`·`unlisted_ref`)으로 나눠 기록한다. 파이프라인은 입력 papers 만 인용하므로 정책이 걸린 입력에서는 둘 다 0 이어야
하고, 0 이 아니면 그 자체가 파이프라인의 인용 경로 문제다. 원본 output.jsonl 은 손대지 않는다.

## 5. 재현성 체인

```
view              = kisti-2608 (papers.parquet sha c1a0c6b3…, created 2026-09-14T13:18:56Z, 시간 컷 없음)
정책              = ../AutoSurvey/data/topic_policy.kisti-2608.jsonl (sha256 ee010f27…; 25행 ok) + sidecar paper_dates.json (2026-09-14T13:26:03Z)
retrieval 백엔드  = ../AutoSurvey/database_kisti-kisti-2608 (1,663,704 벡터; append_manifest.json 2026-09-14T13:48:28Z)
pools             = data/kisti-2608/pools.jsonl (+.manifest.json; 행마다 retrieval_policy: cutoff·allowed·allowed_fingerprint_sha256)
input             = data/kisti-2608/input.jsonl (+.manifest.json; topic 마다 retrieval_policy.blocked_* = 0, quota_field n_gt_refs_cutoff)
검사              = data/kisti-2608/{pool_ceiling,leak_check.input,ref_time_check.input}.json
구 규약 산출물    = data/kisti-2512/ (정책 없음, 보존; README.md)
```

`data/kisti-2608/*.jsonl` 은 gitignore(원문 100MB). manifest·검사 json 만 추적한다.
