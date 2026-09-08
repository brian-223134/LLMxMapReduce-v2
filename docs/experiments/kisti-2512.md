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

## 3. view 가 놓친 GT 누수 2건 (`scripts/leak_check.py`)

| view id | 정체 | 어디서 |
|---|---|---|
| `2507.16731` | edge-slm-cloud-llm GT(`10.1145/3838593`)의 **등록 안 된 arXiv 선행판** | edge-slm-cloud-llm·edge-cloud-collaboration 두 pool |
| `10.1109/comst.2025.3648785` | wireless-foundation-models GT(`arXiv:2601.03181`)의 **IEEE COMST 출판본 DOI** | wireless-foundation-models pool |

`data/kisti-2512/exclude_extra.txt` 로 Stage 2 에서 걸러 입력 누수 0(hard hits 0)을 확인했다. 두 논문은 view·export·AutoSurvey
FAISS 인덱스에는 남아 있어 **다른 3 agent 도 노출된다** → view 재생성 시 `exclude_keys` 에 합칠 것. 제목 유사도(자카드 ≥ 0.5) 전수 스캔에서
그 밖의 GT 복제본은 없었다(`2204.06520` 은 제목만 비슷한 2022 방법론 논문).

## 4. Stage 3 — 스모크 (Securing Large Language Models, pool 44편, parallel_num 1)

(실행 중 — 완료 후 `scripts/run_manifest.py` 결과로 채움: 호출·비용·소요, completion_tokens 분포와 8192 가드 여유, 잘림 재요청 수, 펜스 fallback, 구조·단어·인용 수, 누수 검사)

## 5. 재현성 체인

```
view              = kisti-2512 (view_manifest.json sha: input.jsonl.manifest.json → view_manifest.files_sha256)
retrieval 백엔드  = ../AutoSurvey/database_kisti-kisti-2512 (content_sha256 54b4e7b4…, 1,651,701 벡터)
pools             = data/kisti-2512/pools.jsonl (retrieve_num 1200, exclude_ids.txt 게이트)
input             = data/kisti-2512/input.jsonl (+ .manifest.json — min/max_chars, exclude_ids, topic 별 통계)
fulltext          = body_store.sqlite (science_datalake_260825)
프로파일          = .env (temperature 0.6, max_tokens 8192, retry truncated), config/model_config_llama.json
run manifest      = data/manifest/<run>.json (scripts/run_manifest.py)
```

`data/kisti-2512/`는 gitignore 대상(원문 109MB). `exclude_extra.txt`·`pool_ceiling.json`·manifest 류만 추적한다.
