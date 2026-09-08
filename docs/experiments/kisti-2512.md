# KISTI `kisti-2512` 실험 기록 — 2026-09-08

같은 corpus(KISTI view `kisti-2512`)·같은 백본·공통 디코딩 프로파일로 25 topic 산출물을 내는 실행 기록.
설계 근거는 [commoncorpus-setup.md](../commoncorpus-setup.md) §1(retrieval 기반 pool, cutoff), 절차는
`/data2/chanjoong/kisti_data/adapter/llmxmapreduce/run_stages.sh`, 인수인계는 `/data2/chanjoong/kisti_data/docs/asg/AGENT-HANDOFF.md`.

## 1. 공통 설정

| 항목 | 값 |
|---|---|
| corpus | KISTI view `kisti-2512` (1,651,701편, cutoff 2025, GT 25 + twin 15 제외). id 규칙 B = arXiv base id 또는 소문자 DOI |
| 백본 | `meta-llama/llama-3.3-70b-instruct` @ OpenRouter, provider 핀 `akashml/fp8` (fallback 없음) |
| **디코딩 프로파일** | **temperature 0.6**, **max_tokens 8192** 잘림 가드, 걸린 응답(finish_reason=length)은 버리고 재요청 — `.env` `LLMXMR_TEMPERATURE/LLMXMR_MAX_TOKENS`, `request/openai.py` env-gated(`TruncatedResponseError(ValueError)` → 모듈 retry 가 재표본). 파이프라인 src/ 무수정 |
| 파이프라인 인자 | `--block_count 1`(필수), conv_layer 6, kernel 3, result_num 10, top_k 6, self_refine 3, best_of 3, skeleton_group_size 3, digest_group_mode llm |
| topic | `kisti_data/data/topics.kisti.jsonl` 25편, `title` 그대로 입력, `n_gt_refs` = KISTI eligible |
| 원문 게이트 | Stage 2 `--min_chars 2000` · `--max_chars 250000`(llama 131K 컨텍스트 보호) · `--exclude_file data/kisti-2512/exclude_extra.txt` |

corpus 접근은 입력 빌더에만 있다. Stage 1은 AutoSurvey 의 KISTI FAISS 인덱스(topic 제목 1회 임베딩 → abstract top-1,200),
Stage 2는 view parquet + body_store, Stage 3는 input.jsonl 만 읽는다. 논문(§4.2)은 GT 참고문헌 전문을 직접 넣고 검색이 없으므로
우리 Stage 1은 same-corpus 설계에서 추가한 단계다.

## 2. Stage 1·2 실측

| 단계 | 결과 |
|---|---|
| Stage 1 (GPU 4) | 25 topic × 1,200편, exclude 게이트 예외 0. 인덱스 로딩 포함 수 분 |
| Stage 2 | 25 topic 전부 quota 충족, 수 초. too_short 1 · too_long 2 · no_body 0 · missing_meta 0 · **excluded 3**(아래 §3) |
| pool ceiling | 평균 **24.6%** (Stage 1 pool ∩ GT(view 안) / GT(view 안)) |
| input ceiling | 평균 **8.1%** (Stage 2 입력 quota 편 기준). LLM×MR recall 은 이 값을 넘을 수 없다 |

topic 별 (`data/kisti-2512/pool_ceiling.json`, `input.jsonl.manifest.json`):

| slug | n_gt_refs | GT in view | pool hits | pool ceil | input hits | input ceil | resolved/quota | short/long/excl | max chars |
|---|---|---|---|---|---|---|---|---|---|
| instruction-tuning-llms | 109 | 110 | 17 | 15.4% | 2 | 1.8% | 109/109 | 0/0/0 | 165,414 |
| llm-function-calling | 77 | 74 | 14 | 18.9% | 7 | 9.5% | 77/77 | 0/0/0 | 92,026 |
| model-merging | 157 | 165 | 47 | 28.5% | 28 | 17.0% | 157/157 | 0/0/0 | 98,504 |
| diffusion-model-alignment | 127 | 139 | 23 | 16.6% | 11 | 7.9% | 127/127 | 0/0/0 | 187,217 |
| llm-agent-optimization | 112 | 112 | 24 | 21.4% | 7 | 6.2% | 112/112 | 0/0/0 | 115,735 |
| retrieval-explainability | 129 | 127 | 11 | 8.7% | 3 | 2.4% | 129/129 | 0/1/0 | 177,040 |
| trustworthy-rag | 87 | 86 | 17 | 19.8% | 3 | 3.5% | 87/87 | 0/0/0 | 85,822 |
| large-models-timeseries | 210 | 213 | 19 | 8.9% | 3 | 1.4% | 210/210 | 1/0/0 | 190,993 |
| deep-graph-clustering | 108 | 108 | 47 | 43.5% | 23 | 21.3% | 108/108 | 0/0/0 | 87,218 |
| negative-sampling-recsys | 135 | 138 | 42 | 30.4% | 20 | 14.5% | 135/135 | 0/0/0 | 146,366 |
| mllm-adversarial-attacks | 60 | 52 | 18 | 34.6% | 4 | 7.7% | 60/60 | 0/0/0 | 101,998 |
| llm-training-data-detection | 57 | 56 | 14 | 25.0% | 4 | 7.1% | 57/57 | 0/0/0 | 85,889 |
| physical-adversarial-attacks | 150 | 149 | 67 | 45.0% | 26 | 17.4% | 150/150 | 0/1/0 | 201,461 |
| harmful-finetuning | 107 | 120 | 61 | 50.8% | 28 | 23.3% | 107/107 | 0/0/0 | 101,998 |
| llm-watermarking | 44 | 42 | 8 | 19.1% | 0 | 0.0% | 44/44 | 0/0/0 | 86,018 |
| moe-inference-optimization | 116 | 113 | 42 | 37.2% | 13 | 11.5% | 116/116 | 0/0/0 | 123,821 |
| kv-cache-serving | 61 | 60 | 19 | 31.7% | 1 | 1.7% | 61/61 | 0/0/0 | 149,339 |
| edge-slm-cloud-llm | 138 | 136 | 28 | 20.6% | 15 | 11.0% | 138/138 | 0/0/1 | 158,063 |
| llm-edge-inference | 94 | 85 | 13 | 15.3% | 5 | 5.9% | 94/94 | 0/0/0 | 88,764 |
| llm-distributed-training | 170 | 174 | 49 | 28.2% | 14 | 8.1% | 170/170 | 0/0/0 | 119,148 |
| edge-cloud-collaboration | 175 | 167 | 60 | 35.9% | 15 | 9.0% | 175/175 | 0/0/1 | 159,142 |
| wireless-foundation-models | 116 | 119 | 10 | 8.4% | 3 | 2.5% | 116/116 | 0/0/1 | 104,984 |
| ai-wireless-reasoning | 75 | 72 | 8 | 11.1% | 2 | 2.8% | 75/75 | 0/0/0 | 173,823 |
| agentic-satellite-networks | 67 | 66 | 10 | 15.2% | 3 | 4.5% | 67/67 | 0/0/0 | 85,679 |
| ai-video-streaming | 83 | 79 | 20 | 25.3% | 3 | 3.8% | 83/83 | 0/0/0 | 117,400 |

pool ceiling 이 낮은 이유는 검색 쿼리가 topic 제목 한 문장뿐이기 때문이다(AutoSurvey 는 LLM 이 만든 여러 쿼리로 검색).
input ceiling 은 quota(=n_gt_refs)만큼만 자르므로 더 낮다. 결과표에는 topic ceiling(view 안 GT 비율)과 함께 둘 다 병기한다.

### 2.1 view v2 전환 (2026-09-08 08:08 UTC) — Stage 1·2 재실행

KISTI 쪽이 view를 **v2(1,651,487편)** 로 교체했다: v1에서 GT 본체 사본 2편(§3)과 **cutoff 이후인 arXiv 2601.\* 212편**(KISTI year=2025 오기재)을 뺀 것.
경로·명령·`.env`는 그대로이고 AutoSurvey DB는 재빌드가 아니라 v1 인덱스에서 214 벡터만 제거한 것이다. 이 레포에서 검증한 내용:

| 검증 | 결과 |
|---|---|
| view v2 | papers.parquet sha `591b4325`, 2601.\* id **0건**, `exclude_ids.txt` 40키 |
| AutoSurvey v2 인덱스 | abs·title 모두 ntotal 1,651,487 = id 맵 크기, 표본 200개 벡터가 v1과 **바이트 동일**, 제거 214 = 2601.\* 212 + 누수 2 |
| v1 산출물 오염 | 옛 pools에 2601.\* id 47건(중복 포함), 옛 input에 4편 → `*.v1.*` 로 보존 후 재실행 |
| GT 분모 | `gap_to_80_refs.jsonl`(in_view 2,764)은 미갱신이나 제거 214편 중 GT ref 0건 → 분모 유효 |
| Stage 1 (v2) | 25 topic × 1,200편, 2601.\* 0, 누수 id 0 |
| Stage 2 (v2) | quota 전부 충족, excluded 0(이중 게이트 `exclude_extra.txt` 는 이제 무해), too_short 1 · too_long 2, 2601.\* 0, hard hits 0 |
| ceiling | 평균 pool 24.6% / input 8.1% (v1과 같음) |

topic 별로 달라진 것 (`topics.kisti.jsonl` 의 n_gt_refs +1 세 topic 과 2601.\* 제거 영향):

| slug | quota | pool hits | input hits |
|---|---|---|---|
| diffusion-model-alignment | 127 → 128 | 23 → 23 | 11 → 11 |
| edge-slm-cloud-llm | 138 → 139 | 28 → 28 | 15 → 15 |
| agentic-satellite-networks | 67 → 68 | 10 → 10 | 3 → 3 |

§2 의 topic 표는 v1 기준 수치이며 위 차이 외에는 동일하다. **§4 스모크는 v1 실행분**(입력 manifest sha `c7b8d4e7`)이고 재현하지 않는다. 본편은 v2 입력으로 돌린다.

## 3. view 가 놓친 GT 누수 2건 (`scripts/leak_check.py`)

| view id | 정체 | 어디서 |
|---|---|---|
| `2507.16731` | edge-slm-cloud-llm GT(`10.1145/3838593`)의 **등록 안 된 arXiv 선행판** | edge-slm-cloud-llm·edge-cloud-collaboration 두 pool |
| `10.1109/comst.2025.3648785` | wireless-foundation-models GT(`arXiv:2601.03181`)의 **IEEE COMST 출판본 DOI** | wireless-foundation-models pool |

`data/kisti-2512/exclude_extra.txt` 로 Stage 2 에서 걸러 입력 누수 0(hard hits 0)을 확인했다. 두 논문은 view·export·AutoSurvey
FAISS 인덱스에는 남아 있어 **다른 3 agent 도 노출된다** → view 재생성 시 `exclude_keys` 에 합칠 것. 제목 유사도(자카드 ≥ 0.5) 전수 스캔에서
그 밖의 GT 복제본은 없었다(`2204.06520` 은 제목만 비슷한 2022 방법론 논문).

## 4. Stage 3 — 스모크 (Securing Large Language Models, pool 44편, parallel_num 1)

새 프로파일(temperature 0.6, max_tokens 8192, 잘림 재요청)의 첫 실행. `data/manifest/smoke.json`, 산출물 `data/kisti-2512/output.smoke.md`.

| 항목 | 값 |
|---|---|
| 소요 / 호출 / 비용 | **00:47:45** (파이프라인 기준) / **367회** / **$0.727** (per-call 로그 합) |
| completion_tokens | n=367, p50 864, p90 3735, p99 4350, **max 5613** → 가드 8192 대비 여유 **1.46배**, 가드 도달 0건 |
| finish_reason | {'stop': 367} |
| 잘림 재요청 | **0** (temp 0.6 에서 이 파이프라인은 367회 중 루프 0. AutoSurvey 의 "초안 30% 루프"는 여기로 옮겨오지 않음) |
| 재시도·경고 | 모듈 retry 2 · 펜스 fallback 8 · illegal bibkey 제거 2 · 429 10(래퍼 재시도로 흡수) · ERROR 0 · Traceback 0 |
| 구조 / 분량 | 헤딩 9개(대섹션 3 + 서브 5), 본문 **2,945단어**(21,083자) |
| 인용 | pool 44편 중 **35편 인용** (cite_ratio 0.795) — 논문의 Ref. Recall 에 해당하는 pool 활용률 |
| 내부 점수 | outline_eval 8.7, block_cycle_count 1, conv_layer 6 (SkeletonRefine 정상 수행) |
| 누수 검사 | 본문·refs·papers 에 GT DOI·twin id·제목 **0회** (`leak_check.output.smoke.json`) |
| 원문 형식 | s2orc/pmc plain text 를 digest 프롬프트가 그대로 소화 (파싱 실패 0) |

관찰과 주의:

- **가드 여유가 AutoSurvey 보다 빡빡하다.** 최대 출력 6건이 전부 convolution(skeleton 수정/refine, 전체 outline + digest 분석을 다시 씀) 호출로 4.2~5.6K 토큰이다. 저장된 outline 은 44편 pool 에서 15.2K자, edge 187편(temp 0)에서 14.1K자로 pool 크기에 비례하지 않으므로 큰 topic 에서도 8192 안쪽일 가능성이 높지만, 본편에서 `at_guard>0` 이 convolution 에서 나오면 그것은 루프가 아니라 정상 출력 절단이다 → 그때는 LLM×MR 만 `LLMXMR_MAX_TOKENS` 를 12288 로 올리고 프로파일 편차로 기록한다.
- **파이프라인은 저장 후 종료하지 않는다** (`start_pipeline.py` 의 `while True: gevent.sleep(5)`, 원본 설계). 스모크는 저장 확인 후 수동 kill 했고, `run_stages.sh stage3` 에 OUTPUT 줄 수 == N 이면 자동 종료하는 루프를 넣었다(`AUTO_STOP=0` 으로 끌 수 있음).
- **키가 공유되고 있다.** 스모크 전후 키 사용액 차 $1.50 vs per-call 합 $0.727 — 같은 시간에 다른 프로세스가 같은 키를 썼다. 비용 기록은 per-call 로그 합(manifest)을 정본으로 한다.
- 시간의 대부분은 SkeletonRefine(convolution 6층 × 10 + best-of-3 refine 3회) 이라 pool 44편에서도 48분이다. 25편 본편은 `--parallel_num 4` 로 4~6시간, 비용은 편당 ≈ $0.31 + $0.008×pool(평균 109) ≈ $1.2 → **약 $30**. 키 잔여 $3.75 라 **본편 전에 키 한도 상향이 필요**하다.
- 이전 temp 0 실측(edge 187편 3,431단어, cite_ratio 0.332)과 비교하면 44편 pool 에서 2,945단어·cite_ratio 0.795 — 분량은 pool 보다 topic·skeleton 에, 인용률은 pool 크기에 좌우된다는 기존 관찰과 일치.

## 4.1 본편 실행 방법 (25 topic)

```bash
S=/data2/chanjoong/kisti_data/adapter/llmxmapreduce/run_stages.sh
$S stage3                              # data/kisti-2512/input.jsonl → output.jsonl, 로그 data/kisti-2512/log/stage3.log, 자동 종료
python scripts/run_manifest.py --log data/kisti-2512/log/stage3.log --output_jsonl data/kisti-2512/output.jsonl \
    --input_jsonl data/kisti-2512/input.jsonl --pool_ceiling data/kisti-2512/pool_ceiling.json --run_name stage3
python scripts/leak_check.py --output data/kisti-2512/output.jsonl
```
parallel_num 4 에서는 호출·비용을 topic 별로 나눌 수 없으므로 manifest 의 run 수준 값만 쓴다. 중간에 죽으면 output.jsonl 에 저장된 topic 을 input 에서 빼고 `INPUT=… OUTPUT=…` 로 이어 돌린다(파이프라인은 append).

## 5. 재현성 체인

```
view              = kisti-2512 **v2** (papers.parquet sha 591b4325; v1 c7b8d4e7 은 data/views/kisti-2512-v1/)
retrieval 백엔드  = ../AutoSurvey/database_kisti-kisti-2512 v2 (1,651,487 벡터, view_diff_manifest.json created_at 2026-09-08T07:17Z; v1 은 database_kisti-kisti-2512-v1/)
pools             = data/kisti-2512/pools.jsonl (v2; retrieve_num 1200, exclude_ids.txt 40키 게이트) — v1 은 pools.v1.jsonl
input             = data/kisti-2512/input.jsonl (v2, + .manifest.json — min/max_chars, exclude_ids, topic 별 통계) — v1 은 input.v1.jsonl
fulltext          = body_store.sqlite (science_datalake_260825)
프로파일          = .env (temperature 0.6, max_tokens 8192, retry truncated), config/model_config_llama.json
run manifest      = data/manifest/<run>.json (scripts/run_manifest.py) — smoke: data/manifest/smoke.json
스모크 산출물     = data/kisti-2512/output.smoke.md (+ leak_check.output.smoke.json)
```

`data/kisti-2512/`는 gitignore 대상(원문 109MB). `exclude_extra.txt`·`pool_ceiling.json`·manifest 류만 추적한다.
