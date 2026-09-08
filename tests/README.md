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

원칙: 파이프라인(src/)은 건드리지 않으므로 테스트도 그 바깥(요청 래퍼·입력 빌더·기록 스크립트)만 다룬다.
