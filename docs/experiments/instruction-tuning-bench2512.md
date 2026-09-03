# Instruction Tuning (bench-2512) 실험 기록 — 2026-09-03

벤치마크 인스턴스 `bench-2512`의 첫 토픽으로 same-corpus 입력 체인을 실행한 기록.
Stage 1·2는 완료했고 **Stage 3는 재실행 대기 상태**다 (§3).

관련 문서: [commoncorpus-setup.md](../commoncorpus-setup.md) (절차)
· `../asg-common-corpus/docs/llmxmapreduce-v2-usage.md` (코퍼스 쪽 절차서)
· `../asg-common-corpus/candidates/GT-SURVEYS.md` (topic 정본)

## 1. 대상 토픽

| 항목 | 값 |
|---|---|
| Topic (agent 입력) | `Instruction Tuning for Large Language Models` |
| GT survey | Instruction Tuning for Large Language Models: A Survey (ACM CSUR, 2026-01-08) |
| GT DOI | [10.1145/3777411](https://doi.org/10.1145/3777411) |
| domain / slug | ai / `instruction-tuning-llms` |
| cov (recall ceiling) | 89% |
| **elig (= `n_gt_refs`, pool 정원)** | **153** |
| preprint 쌍둥이 | 2308.10792 (view에서 제외됨) |

`n_gt_refs`는 `candidates/SELECTION.md`의 **elig** 열에서 온다 (cov가 아니다).
`--pool_mode gt_count`가 이 값을 필수로 읽으므로 누락 시 KeyError로 죽는다.

## 2. Stage 1·2 실측 (완료)

| 단계 | 결과 |
|---|---|
| view | `bench-2512` (947,451편, cutoff 2025-12-31) |
| retrieval DB | `../AutoSurvey/database_commoncorpus-bench-2512` (947,451 벡터, dim 768) |
| Stage 1 retrieval | 1,200편 후보, **약 1분** (대부분 TinyDB·FAISS 로딩) |
| GT/twin 누출 | **0** (`gt_exclude.txt` 15 id 이중 게이트 통과) |
| Stage 2 full text | **153/154편 확보**, **11.7분** (`--fetch_delay 4`) |
| 확보 실패 | 1건 — `2308.14306` HTTP 404 (정당한 실패) |
| `too_short` 탈락 | 0건 |
| 전문 분량 | 합계 5,820,499자 (편당 min 11,072 / 중앙 33,763 / max 258,977) |
| 입력 JSONL | `data/inputs/bench-2512.instruction-tuning.input.jsonl` (6.1MB) |

처리율 약 8.4편/분. `walked=154`로 정원 153을 채웠다 — retrieval 상위권의 전문 해결률이
매우 높다는 뜻이다 (edge computing 본편급은 187편에 194편 순회).

### 2.1 arXiv 429와 캐시 오염 (이번 실행에서 발생)

Stage 2 첫 시도에서 arXiv 429가 쏟아졌고, `FullTextResolver`가 이 **일시적** 실패를
`failure.json`으로 **영구 동결**했다. 동결된 논문은 이후 모든 실행·모든 agent의 공유
캐시에서 빠지므로 pool 구성이 실행 시점의 네트워크 상태에 좌우된다.

- 오염 **290건** 발견·제거 (429 × 34 → 중단 실패로 살아남은 구버전 프로세스가 추가 251건).
- 제거 후 정당한 동결은 3건뿐: 404 × 1, `parsed text too short` × 2.
- 대응은 `asg-common-corpus` 쪽에서 이뤄졌다 (본 저장소 변경 아님):
  실패 경로 스로틀 유지 · 429/타임아웃 지수 백오프 재시도 · 일시적 실패 미동결 ·
  e-print를 버전 없이 받아 `content-disposition`에서 버전 회수(논문당 요청 2회 → **1회**,
  429를 자주 내는 `export.arxiv.org` API 미사용).
- 그 결과 처리율이 약 1편/분 → **8.4편/분**으로 올랐고 재시도 후 429는 0건이었다.

⚠️ **재현성 주의**: 위 Stage 2 실측치는 수정된 resolver 기준이다. 재현 시
`asg-common-corpus`의 fulltext provider/resolver 커밋을 함께 고정할 것.

## 3. Stage 3 — run1 폐기, 재실행 필요

`--block_count`를 넘기지 않아 **SkeletonRefineModule(convolution)이 한 번도 실행되지 않은 채**
서베이가 저장됐다. `src/args.py`의 기본값이 0이고, 0이면 그 단계가 통째로 건너뛰어진다.
에러도 경고도 남지 않는다.

| 지표 | edge full 187 (정상 기준) | **run1 (폐기)** |
|---|---|---|
| `--block_count` | 1 | **0 (미지정)** |
| conv_layer (기록값) | 6 | **0** |
| block_cycle_count | 1 | **0** |
| outline_eval_score | 8.915 | **null** |
| 본문 단어수 | 3,283 | 1,862 |
| cite_ratio | 0.332 | 0.346 |
| 참고문헌 수 | 187 | 153 |
| 소요 / 비용 | 57분 / $1.80 | 12.5분 / $0.453 (190 calls) |

`--conv_layer 6` 자체는 CLI 기본값으로 정상 전달됐으나, block이 0이라 그 단계가 돌지 않아
기록값이 0으로 남았다. 산출물은 삭제하지 않고
`LLMxMapReduce_V2/output/discarded.no-block-count.jsonl`로 보관했다.

**재실행 커맨드** (`--block_count 1`만 추가):

```bash
cd LLMxMapReduce_V2
set -a && . ../.env && set +a
PYTHONPATH=$(pwd) /data2/chanjoong/miniforge3/envs/llmxmr/bin/python ./src/start_pipeline.py \
    --input_file ../data/inputs/bench-2512.instruction-tuning.input.jsonl \
    --output_file ./output/bench-2512.instruction-tuning.llama33-70b.jsonl \
    --config_file ./config/model_config_llama.json \
    --data_num 1 --parallel_num 4 --block_count 1
```

run1의 로그 관찰: WARNING 12건(429 upstream 1 · 펜스 누락 fallback 1 · illegal bibkey 제거 1 등),
ERROR·Traceback 0건. 펜스 fallback 패치(`e998e64`)는 정상 동작했다.

예상 비용은 편당 $0.31 + $0.008 × pool 크기 모델로 **약 $1.5**
([edge-computing-experiment.md](edge-computing-experiment.md) §3의 2점 fit).

## 4. 백본·통제 변수

| 항목 | 값 |
|---|---|
| 백본 | `meta-llama/llama-3.3-70b-instruct` (OpenRouter, `akashml/fp8` 핀, temp 0) |
| 모델 설정 | `LLMxMapReduce_V2/config/model_config_llama.json` |
| 파이프라인 인자 | `skeleton_group_size=3, conv_layer=6, conv_kernel_width=3, conv_result_num=10, top_k=6, self_refine_count=3, self_refine_best_of=3, digest_group_mode=llm` |
| **`block_count=1`** | run1에서 누락 → §3 |

## 5. 재현성 체인

```
view              = bench-2512 (947,451편)
base_corpus_sha256= 6bb204d15111f2edd944ac47112a0a46f9b9bf252d5e20d3a719a3c439d4285e
dataset_revision  = cd87dd095f86aa7306aef70024e250f4839b1f71
pools             = data/pools/bench-2512.instruction-tuning.pools.jsonl (retrieve_num 1200)
input             = data/inputs/bench-2512.instruction-tuning.input.jsonl
                    (+ .manifest.json — pool_mode gt_count, fetch_delay 4.0, min_chars 2000)
retrieval 백엔드  = ../AutoSurvey/database_commoncorpus-bench-2512
                    content_sha256 7393bef6b788dcac8b27a0249b7a7eb2756c55a4fb77586cda663362c4638d90
fulltext cache    = ../asg-common-corpus/data/fulltext_cache/arxiv/<id>/metadata.json (version+sha256)
```

`data/pools/`·`data/inputs/`는 gitignore 대상이라 저장소에 없다. topic 정의만
`data/bench-2512/topics.instruction-tuning.jsonl`로 추적한다.

## 6. 부수 확인 — retrieval 인덱스는 정상

`AutoSurvey/scripts/check_db.py --verify-embeddings`가 이 DB를 "문제 있음"으로 판정하지만
**인덱스 결함이 아니다.** nomic-bert의 위치 캐시가 stateful이라, 947K편 빌드 시점의 모델
상태와 갓 로딩한 모델로 1건 인코딩한 결과가 달라 abs에서 cos≈0.985가 나온다 (임계 0.999).

| 검증 | 결과 |
|---|---|
| 순서·매핑 | argmax 자기일치 12/12, 자기 cos 0.985 vs 비대각 최대 0.71 |
| 인코더 결정성 | GPU/CPU/TF32 전부 동일 (1.000000) |
| 텍스트·프리픽스·배치 구성 | 전부 원인 아님 |
| 긴 시퀀스로 캐시 warm 후 | 0.984 → **0.995** (원인 확정) |
| title 인덱스 | 정확히 1.000000 (짧아서 영향 없음) |

→ 이 경고만으로 재빌드하지 말 것. 재빌드해도 같은 수치가 나온다.
retrieval 품질도 정상이었다 (pool 상위 15편 전부 instruction-tuning 주제).
