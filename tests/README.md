# tests/

네트워크·GPU·API 키 없이 도는 유닛/mock 테스트. `unittest` 표준 라이브러리만 쓴다 (pytest 가 있으면 그대로 돌아간다).

```bash
cd /data2/chanjoong/survey-agent/LLMxMapReduce-v2
PYTHONPATH=LLMxMapReduce_V2 /data2/chanjoong/miniforge3/envs/llmxmr/bin/python -m unittest discover -s tests -v
```

| 파일 | 대상 | 비고 |
|---|---|---|
| `test_openai_request.py` | `LLMxMapReduce_V2/request/openai.py` — env 프로파일(temperature·provider), 출력 가드(max_tokens, finish_reason=length 버림/유지), 비용·usage 로그 | OpenAI 클라이언트 mock. `openai`·`tenacity` 가 있는 env(llmxmr) 필요, 없으면 skip |
| `test_kisti_common.py` | `scripts/kisti_common.py` — id 규칙 B, 로그/.env 파서, 본문 통계 | |
| `test_pool_ceiling.py` | `scripts/pool_ceiling.py` — pool/input ceiling 계산 | |
| `test_leak_check.py` | `scripts/leak_check.py` — GT DOI·twin id·제목 누수 탐지, candidate.yaml/README 로더 | |
| `test_run_manifest.py` | `scripts/run_manifest.py` — 로그 집계(호출·비용·completion_tokens 분포·잘림·fallback), topic 통계 | |
| `test_build_corpus_input_kisti.py` | `kisti_data/adapter/llmxmapreduce/build_corpus_input_kisti.py` — `select_papers` 게이트(min/max_chars, no_body, quota) | FullText mock. adapter 가 없으면 skip |
| `test_retrieve_pool.py` | `scripts/retrieve_pool.py` — topic 마다 `set_policy` 호출·허용 집합 안 검색·누수 게이트·정책 블록 | 가짜 DB·정책 모듈. faiss 불필요 |
| `test_ref_time_check.py` | `scripts/ref_time_check.py` — 시간 범위 위반 / 제외 id / corpus 밖(허위 후보) / 목록 밖 ref 판정, cited·listed 구분 | 날짜 규칙은 `kisti_data/adapter/common/retrieval_policy.py`, 없으면 skip |
| `test_pseudo_survey_e2e.py` | **가짜 Survey end-to-end**: 임베드한 예시 corpus·정책·GT ref 로 Stage 1(가짜 DB) → Stage 2(`select_papers`, 가짜 원문) → pseudo 출력(본문 `[n]` 인용·References·가짜 로그) → `leak_check`·`ref_time_check`·`pool_ceiling`·`run_manifest.main()` 을 임시 디렉터리 파일로 연결. 오염된 출력(cutoff 이후 논문·허위 ref·GT 본체)이 잡히는지 포함 | adapter + `../AutoSurvey/src/retrieval_policy.py` 필요, 없으면 skip |

원칙: 파이프라인(src/)은 건드리지 않으므로 테스트도 그 바깥(요청 래퍼·입력 빌더·기록 스크립트)만 다룬다.
