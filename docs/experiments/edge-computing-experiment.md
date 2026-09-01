# Edge Computing 실험 기록 (2026-08-31)

같은 corpus(same-corpus) 재현 체인 검증을 위해 **Edge Computing** 토픽으로 수행한
스모크(pool 20편) 및 본편급(pool 187편) 실측 기록. 세미나 발표용 메트릭 정리.

관련 문서: [commoncorpus-setup.md](commoncorpus-setup.md) (절차·설계 근거), `HANDOFF.md` (현황 요약)

## 1. 공통 설정

| 항목 | 값 |
|---|---|
| 백본 모델 | `meta-llama/llama-3.3-70b-instruct` (OpenRouter, akashml/fp8 핀, temp 0) |
| 모델 설정 | `LLMxMapReduce_V2/config/model_config_llama.json` |
| Corpus view | `surveyeval-2512` (947,444편, cutoff 2025-12-31, GT 서베이 20편 arXiv ID 제외) |
| Pool 구성 | retrieval 기반 (FAISS 인덱스 947,444편, 빌드 84분 1회성 → retrieval 1,200편, GT 누출 0) |
| 파이프라인 옵션 | `conv_layer=6, conv_kernel_width=3, top_k=6, self_refine_count=3, self_refine_best_of=3, skeleton_group_size=3` |

## 2. 실행별 메트릭 요약

| 메트릭 | 스모크 (pool 20편) | 본편급 (pool 187편) |
|---|---|---|
| 실행 일시 | 2026-08-31 08:33 | 2026-08-31 10:10 |
| pool 모드 | `gt_count` | `fixed` (187편) |
| full text 수집 | 20/20편, 실패 0, **약 4분** (241s) | 187/187편 (fetch 실패 5·짧음 2 제외, 194편 순회), **약 27분** (1,620s) |
| **생성 시간** | **28분 7초** (parallel_num 1) | **57분 7초** (parallel_num 4) |
| LLM 호출 수 | 289회 | 864회 |
| **비용 (OpenRouter)** | **$0.472** | **$1.803** (키 사용액 차 $1.796와 교차 일치) |
| 호출당 평균 비용 | $0.00163 | $0.00209 |
| API 에러 | 0 | 0 |
| 펜스 fallback 발동 | 4회 | 11회 |
| **본문 단어 수** (참고문헌 제외) | **1,405** | **3,431** |
| 본문 문자 수 | 10,008자 | 24,815자 |
| 섹션 구조 | 헤딩 7개 | 헤딩 14개 (대섹션 6개 + 서브섹션) |
| 참고문헌 수 | 20 | 187 |
| cite_ratio | 1.0 | 0.332 |
| outline_eval | — | 8.9 |
| **PDF 페이지** | (미컴파일) | **17페이지** (258KB) |

- 비용 출처: 파이프라인 per-call 로그의 세션 누계(`request.openai` 로거).
  본편급은 실행 전후 `scripts/check_credits.py` 스냅샷(`output_cost_log.txt`)의 키 사용액 차와 교차 검증됨.
- 생성 시간은 파이프라인 시작 로그 → `save_survey` 완료 로그 기준 (full text 수집 시간 별도).

## 3. 비용 모델 (실측 2점 fit)

- **편당 비용 ≈ $0.31 + $0.008 × pool 크기** — pool 크기에 거의 선형 (hidden/digest 단계가 비용의 ~98%)
- 본편 20편(gt_count pool, 평균 수백 편) 추정: **약 $36**
- 시간도 encode 단계(Digest, SkeletonRefine)가 지배적 — 본편급 기준 SkeletonRefine 단독 약 33분

## 4. 이슈 및 해결

- **run1 실패 (08:00)**: llama가 마크다운 코드펜스 없이 응답 → `parse_md_content`에서 `AttributeError` → tenacity RetryError로 중단.
  → 펜스 누락 시 fallback 파싱 추가(`e998e64`)로 해결. 이후 run2·본편급에서 fallback이 각 4회/11회 발동하며 정상 처리.

## 5. 관찰 / 세미나 논점

- **분량**: llama 산출물 3,431단어는 GT 서베이(8K~30K단어) 대비 짧음. 분량 통제 프롬프트는 미수정 상태 — 개선 여지.
- **cite_ratio**: pool 20편일 때 1.0 → 187편일 때 0.332. pool이 커지면 인용 커버리지가 떨어짐.
- **비용 선형성**: pool 크기가 비용의 지배 변수 (스모크 $0.47 → 187편 $1.80). 본편 20편 실행 전 키 상한 조정 필요 (잔여 $10.3 < 추정 $36).
- **병렬화**: parallel_num 1→4로 pool 9.4배를 시간 2배 수준으로 처리.

## 6. 산출물 위치

| 파일 | 설명 |
|---|---|
| `LLMxMapReduce_V2/output/smoke.edge_computing.llama33-70b.jsonl` | 스모크 결과 (0.98MB) |
| `LLMxMapReduce_V2/output/edge_computing.full.llama33-70b.jsonl` | 본편급 결과 (10.2MB) |
| `LLMxMapReduce_V2/output/md/Edge Computing.md` | 스모크 마크다운 |
| `LLMxMapReduce_V2/output/md/Edge Computing (full 187).md` | 본편급 마크다운 |
| `LLMxMapReduce_V2/output/tex/Edge_Computing.pdf` | 본편급 컴파일 PDF (17p) |
| `LLMxMapReduce_V2/output/log/smoke_edge_computing_run2.log` | 스모크 실행 로그 |
| `LLMxMapReduce_V2/output/log/edge_computing_full.log` | 본편급 실행 로그 |
| `data/smoke/edge_computing.*.jsonl(+manifest)` | 입력 pool·manifest |
| `output_cost_log.txt` | 본편급 전후 크레딧 스냅샷 |
