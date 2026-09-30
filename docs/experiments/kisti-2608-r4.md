# KISTI `kisti-2608-r4` — PoC 1편(llm-agent-optimization) Stage 1·2·3 실행 기록 (2026-09-30)

corpus 쪽이 스냅샷 **`kisti-2608-r4`** 를 채택했다(1,697,512편 = kisti-2608-r2 1,696,254 + GT survey reference 원문 확보분 1,258,
papers.parquet sha `32a77a48`). 선정 25 topic 의 GT 1-hop coverage 51.5% → 81.2%. 정본은
`/data2/chanjoong/kisti_data/docs/asg/AGENT-HANDOFF.md` §0 (2026-09-30 r4 채택 항목). 전체 25편에 앞서 1편으로 입력 교체를 확인했다.

**분모 `n_gt_refs_cutoff` 가 바뀌었다(25 topic 합 2,543 → 4,010, 이 topic 102 → 190).** 이 문서의 recall 을
[kisti-2608.md](kisti-2608.md)(view `kisti-2608`)나 그 이전 실행과 같은 표에 놓지 않는다.

## 1. 무엇을 바꿨나

| 항목 | 변경 |
|---|---|
| 입력 | `KISTI_VIEW=kisti-2608-r4` 만 준다 — `run_stages.sh` 가 DB `../AutoSurvey/database_kisti-kisti-2608-r4`(재빌드 안 함) · 정책 `topic_policy.kisti-2608-r4.jsonl` · 제외 `data/views/kisti-2608-r4/exclude_ids.txt`(43키) · 산출물 `data/kisti-2608-r4/` 를 잡는다 |
| Stage 2 원문 | kisti_data `014b453` 부터 `common/fulltext.FullText` 가 **overlay `bodies.sqlite` → base `body_store`** 순으로 읽는다. r4 추가분의 원문은 overlay 에만 있어, 이전 코드는 이 topic GT ref 190 중 62건을 `--min_chars 2000` 에서 떨어뜨렸다. 이 저장소 코드 수정 없음 |
| 검사 스크립트 | `leak_check.py`·`pool_ceiling.py`·`ref_time_check.py` 에 r4 경로를 명시 인자로 줬다(§5) |
| `scripts/gt_recall.py` (신규) | Stage 3 output 의 본문 인용 ref 로 recall(분모 `n_gt_refs_cutoff`)·precision·refs 수를 계산. GT 는 `pool_ceiling.py` 와 같은 `gap_to_80_refs.jsonl` `tier == in_view`, view id 매칭 |
| PoC topics | `data/kisti-2608-r4/topics.poc.jsonl` — `topics.kisti.jsonl` 에서 `llm-agent-optimization` 한 줄. stage1 의 `--topics` 는 스크립트 값 뒤에 붙어 argparse 에서 이긴다 |

## 2. 공통 설정

| 항목 | 값 |
|---|---|
| corpus / 버전 | view `kisti-2608-r4` (1,697,512편) — **`32a77a48 / 2026-09-30T02:05:49Z`** |
| retrieval 백엔드 | `../AutoSurvey/database_kisti-kisti-2608-r4` (ntotal 1,697,512, nomic) |
| 정책 파일 | `../AutoSurvey/data/topic_policy.kisti-2608-r4.jsonl` (25행 ok, sha256 `f4abd3fe…`) + sidecar `paper_dates.json` (2026-09-30T02:11:54Z, month 462,193 / day 1,230,756 / year 4,563) |
| topic | llm-agent-optimization — *A Survey on the Optimization of Large Language Model-based Agents*, GT DOI `10.1145/3789261`, twin `2503.12434` |
| cutoff / quota | `retrieval_cutoff_at` **2025-03-16** (twin arXiv v1) / `n_gt_refs_cutoff` **190** (`gap_to_80_refs.jsonl` in_view 고유 id 도 190, 불일치 없음) |
| 원문 게이트 | `--min_chars 2000` · `--max_chars 250000` |
| Stage 3 프로파일 | AGENT-HANDOFF §4 — llama-3.3-70b @ OpenRouter `akashml/fp8`, temperature 0.6, max_tokens 8192 가드 + 잘림 재요청, `--block_count 1`, `--parallel_num 4` |
| git | LLMxMapReduce-v2 `5de61ae`, kisti_data `014b453` |

## 3. 실측 (2026-09-30 UTC)

| 단계 | 시각 / 소요 | 결과 |
|---|---|---|
| Stage 1 (GPU 6) | 04:18:21–04:20:38 (**2분 17초**) | 허용 **1,541,302 / 1,697,512** (cutoff 이후 day 98,272 · month 57,909 · year 29, 날짜 불명 0, 제외 id 잔존 0). pool **1,200** |
| Stage 2 | 04:29:17–04:29:30 (13초) | quota 190 → **입력 190편**. 탈락: excluded 0 · missing_meta 0 · no_body 0 · too_short 0 · too_long 0 (walked 190). **정책 위반 `blocked_after_cutoff` 0 · `blocked_no_date` 0**. 원문 합 8,355,110자, 최대 220,397자. 원문 출처 base 165 · **overlay 25** |
| Stage 3 | 04:30:05–05:17 저장 (파이프라인 **00:47:39**) | 1/1 저장, 자동 종료 |

### Stage 1·2 — pool·입력의 GT

| 항목 | 값 |
|---|---:|
| GT (view 안, 분모) | 190 |
| pool 1,200 ∩ GT | **66** → pool ceiling **34.7%** |
| — 그중 원문이 overlay 에만 있는 것 | 31 |
| — 그중 원문 < 2,000자 (탈락 후보) | **0** (corpus 쪽 기댓값 0 과 일치) |
| 입력 190 ∩ GT | **31** → input ceiling **16.3%** |

pool 안 GT 66편의 원문을 전부 조회해 길이를 쟀다(입력 quota 밖 35편 포함). overlay 경로가 없었다면 31편이 원문 부족으로 탈락했을 자리다.
Stage 2 manifest `fulltext_source` = `overlay bodies.sqlite (/data2/chanjoong/kisti_data/data/overlay/bodies.sqlite) → body_store.sqlite (science_datalake_260825, sha256 2dd893c3…)`.

### Stage 3 — 결과 (`data/manifest/stage3-2608-r4-poc.json`, `gt_recall.output.json`)

| 항목 | 값 |
|---|---|
| **recall / precision** | **6.3% (12 / 190) / 24.5% (12 / 49)** |
| refs 수 | 본문 인용 **49편** (입력 190편 중, cite_ratio 0.258). 입력 GT 31편 중 12편 인용 |
| 구조 / 분량 | 헤딩 9, 본문 2,762단어(20,447자), outline_eval 8.375, block_cycle_count 1, conv_layer 6 |
| 호출 / 비용 | **887회 / $1.763** (per-call 로그 합, 정본). 키 사용액 차 $2.357($30.340 → $32.697)은 같은 시간 같은 키로 SurveyX·SurveyForge 가 같은 topic PoC 를 돌려 섞인 값 |
| completion_tokens | p50 919 · p99 2,504 · max 3,280 → 가드 8192 대비 여유 2.5배, **가드 도달 0 · 잘림 재요청 0** |
| 재시도·경고 | 429 **536**(상류 `temporarily rate-limited upstream`, 래퍼 재시도 최대 100회로 흡수) · 모듈 retry 27 · 펜스 fallback 7 · illegal bibkey 2 · ERROR 0 · Traceback 0 |

## 4. 검사

| 검사 | 결과 |
|---|---|
| 정책 위반 (Stage 2 사후 검사) | `blocked_after_cutoff` 0 · `blocked_no_date` 0 |
| 시간 범위 (`ref_time_check`) | input·output 모두 time_violation 0 · excluded_id 0 · not_in_corpus 0 · unlisted 0 |
| 누수 (`leak_check`) | input·output hard hits **0**. output title mention 2건 = 생성 survey 자신의 제목(`# 0. A Survey on …`, outline) — topic 문자열이 GT 제목이라 생기는 예상 경고 |
| GT DOI `10.1145/3789261` · twin `2503.12434` | output **0회** · input **0회** · pool 검색 결과(1,200 id) 0회. `pools.jsonl` 의 등장은 행 메타 `retrieval_policy.exclude_ids`·`gt_first_public_source` 뿐 |

## 5. 명령

```bash
K=/data2/chanjoong/kisti_data; S=$K/adapter/llmxmapreduce/run_stages.sh; D=data/kisti-2608-r4; export KISTI_VIEW=kisti-2608-r4
CUDA_VISIBLE_DEVICES=6 $S stage1 --topics $D/topics.poc.jsonl
$S stage2 --only_title "A Survey on the Optimization of Large Language Model-based Agents"
$S stage3
python scripts/pool_ceiling.py --pools $D/pools.jsonl --input $D/input.jsonl --gt_refs $K/candidates/gap_to_80_refs.jsonl --out $D/pool_ceiling.json
python scripts/leak_check.py --output $D/output.jsonl --exclude_keys $K/data/views/kisti-2608-r4/exclude_keys.txt --out $D/leak_check.output.json
python scripts/ref_time_check.py --output $D/output.jsonl --view kisti-2608-r4 \
    --topic_policy ../AutoSurvey/data/topic_policy.kisti-2608-r4.jsonl --out $D/ref_time_check.output.json
python scripts/run_manifest.py --log $D/log/stage3.log --output_jsonl $D/output.jsonl --input_jsonl $D/input.jsonl \
    --pools $D/pools.jsonl --pool_ceiling $D/pool_ceiling.json --run_name stage3-2608-r4-poc --out data/manifest/stage3-2608-r4-poc.json
python scripts/gt_recall.py --output $D/output.jsonl --gt_refs $K/candidates/gap_to_80_refs.jsonl --out $D/gt_recall.output.json
```

(검사는 asg-corpus env, `leak_check`·`ref_time_check` 는 input 에도 같은 인자로 `--input` 을 준다.)

## 6. 관찰과 다음

- **overlay 원문 경로가 실제로 쓰였다.** 입력 190편 중 25편, pool 안 GT 66편 중 31편의 원문이 overlay 에서 왔고 탈락은 0 — 014b453 이전 코드였다면 이 자리는 원문 부족으로 떨어지고 quota 는 뒤 순위 비-GT 로 채워졌을 것이다.
- **input ceiling 이 recall 을 묶는다.** 입력은 pool 상위 190편(`gt_count` quota)이라 pool 의 GT 66편 중 31편만 들어갔고, 그중 12편을 인용했다(입력 GT 인용률 39%, 전체 인용률 26%). recall 6.3% 는 input ceiling 16.3% 안쪽이다.
- **25편 본편 예상**: 편당 ≈ 48분 · $1.76 (quota 190 기준, quota 가 topic 마다 97~281 로 달라 편차 있음). 25편 합 대략 $40 안팎인데 **키 잔여 $7.30**(한도 $40, 05:19 UTC)이라 본편 전에 한도 상향이 필요하다. 같은 키를 다른 agent 가 동시에 쓰면 akashml 429 가 크게 늘어난다(이번 536회).
- **분모 불일치 7 topic (corpus 쪽 전달)**: `pool_ceiling.py` 경고 — topics `n_gt_refs_cutoff` 와 `gap_to_80_refs.jsonl` in_view 고유 id 수가 다르다(model-merging 211/210, large-models-timeseries 281/280, llm-watermarking 80/78, moe-inference-optimization 174/172, edge-slm-cloud-llm 231/229, edge-cloud-collaboration 240/239, wireless-foundation-models 238/236). 원인은 kisti-2608 때 llm-watermarking 에서 본 것과 같은 ref 행 중복(같은 view id 가 in_view 두 행, 예: model-merging `2310.04799`, moe-inference `2310.18339`·`2308.14352`)이다 — 확인함. 분모를 ref 행 수로 할지 논문 수로 할지 corpus 쪽 결정 필요. PoC topic 은 190/190 으로 해당 없음.
- `candidates/gap_to_80_refs_r4_alias.jsonl` 에는 이 topic in_view 가 1건(`2309.07864`) 더 있지만 채택 분모(topics 190)는 기본 `gap_to_80_refs.jsonl` 기준이라 그것을 썼다.

## 7. 재현성 체인

```
view              = kisti-2608-r4 (papers.parquet sha 32a77a48…, created 2026-09-30T02:05:49Z)
정책              = ../AutoSurvey/data/topic_policy.kisti-2608-r4.jsonl (sha256 f4abd3fe…) + sidecar paper_dates.json (2026-09-30T02:11:54Z)
retrieval 백엔드  = ../AutoSurvey/database_kisti-kisti-2608-r4 (1,697,512 벡터; append, 재빌드 없음)
원문              = kisti_data/data/overlay/bodies.sqlite → science_datalake_260825 body_store (kisti_data 014b453)
topics            = data/kisti-2608-r4/topics.poc.jsonl (1행)
pools / input     = data/kisti-2608-r4/{pools,input}.jsonl (+.manifest.json)
output            = data/kisti-2608-r4/output.jsonl, manifest data/manifest/stage3-2608-r4-poc.json
survey 본문       = data/kisti-2608-r4/output.poc.md (output 의 content + ref_str; References 는 입력 190편 전체, 본문 인용은 49편)
                    PDF data/kisti-2608-r4/tex/A_Survey_on_the_Optimization_of_Large_Language_Model-based_Agents.pdf (17쪽, scripts/jsonl_to_tex.py --compile)
검사              = data/kisti-2608-r4/{pool_ceiling,leak_check.*,ref_time_check.*,gt_recall.output}.json
```

`data/kisti-2608-r4/*.jsonl` 은 gitignore(원문 포함). `topics.poc.jsonl`·`output.poc.md`·`tex/*.pdf`·manifest·검사 json 만 추적한다.
