#!/usr/bin/env python3
"""Stage 3 run manifest — 인수인계 §4 기록 요건.

로그(adapter run_stages.sh 가 tee 한 $DATA/log/<run>.log) + output.jsonl + input manifest + .env 프로파일
+ model config 를 합쳐 run 하나의 manifest JSON 을 만든다.

  run 수준 : 모델·provider·temperature·max_tokens·잘림 재요청 설정, 호출 수·비용, completion_tokens 분포
             (가드 여유 확인), finish_reason 집계, 잘림(버림/유지) 수, 펜스 fallback·illegal bibkey·429·
             모듈 retry·ERROR 수, 시작/종료 시각, git 커밋, 입력 jsonl sha256, view/body_store manifest
  topic 수준: cost_time, block_cycle_count, conv_layer, outline_eval_score, cite_ratio, pool 크기,
             인용된 refs 수, 본문 단어 수, 헤딩 수, (있으면) pool ceiling, Stage 2 통계

주의: parallel_num > 1 이면 호출·비용은 topic 별로 나눌 수 없으므로 run 수준에만 적는다.

사용:
  python scripts/run_manifest.py --log data/kisti-2512/log/smoke.log \
      --output_jsonl data/kisti-2512/output.smoke.jsonl --input_jsonl data/kisti-2512/input.smoke.jsonl \
      [--env_file .env] [--config LLMxMapReduce_V2/config/model_config_llama.json] \
      [--pool_ceiling data/kisti-2512/pool_ceiling.json] [--out data/kisti-2512/manifest/smoke.json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kisti_common import (cited_indices, content_words, count_headings, iter_jsonl,  # noqa: E402
                          parse_env_file, parse_log_records, percentile, sha256_file)

REPO = Path(__file__).resolve().parents[1]
_COST = re.compile(r"OpenRouter cost: \$([0-9.]+)")
_USAGE = re.compile(r"completion usage: prompt_tokens=(\S+) completion_tokens=(\S+) finish_reason=(\S+)")
_TS = "%Y-%m-%d-%H:%M:%S.%f"
PROFILE_KEYS = ("OPENAI_API_BASE", "LLMXMR_PROVIDER", "LLMXMR_TEMPERATURE", "LLMXMR_MAX_TOKENS",
                "LLMXMR_RETRY_TRUNCATED", "LLMXMR_TRACK_COST", "PROMPT_LANGUAGE")


def _int(s):
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


def summarize_log(records, max_tokens=None) -> dict:
    """parse_log_records 결과 → run 수준 집계."""
    s = {"records": len(records), "calls": 0, "total_cost_usd": 0.0, "usage_lines": 0,
         "completion_tokens": {}, "prompt_tokens": {}, "finish_reasons": {},
         "truncated_discarded": 0, "truncated_kept": 0, "fence_fallback": 0, "illegal_bibkeys": 0,
         "rate_limit_429": 0, "internal_server_errors": 0, "module_retries": 0,
         "error_records": 0, "tracebacks": 0, "pipeline_args": None,
         "started": None, "finished": None, "duration_s": None}
    comp, prompt, reasons = [], [], Counter()
    for r in records:
        msg = r["message"]
        if r["level"] == "ERROR":
            s["error_records"] += 1
        if "Traceback (most recent call last)" in msg:
            s["tracebacks"] += 1
        m = _COST.search(msg)
        if m:
            s["calls"] += 1
            s["total_cost_usd"] += float(m.group(1))
        m = _USAGE.search(msg)
        if m:
            s["usage_lines"] += 1
            p, c = _int(m.group(1)), _int(m.group(2))
            if p is not None:
                prompt.append(p)
            if c is not None:
                comp.append(c)
            reasons[m.group(3)] += 1
        if "Truncated response:" in msg and "discarding" in msg:
            s["truncated_discarded"] += 1
        if "Truncated response kept" in msg:
            s["truncated_kept"] += 1
        if "no ```markdown fence found" in msg:
            s["fence_fallback"] += 1
        if "Remove illegal bibkeys" in msg:
            s["illegal_bibkeys"] += 1
        if "Rate limit exceeded" in msg:
            s["rate_limit_429"] += 1
        if "Internal server error" in msg:
            s["internal_server_errors"] += 1
        if msg.startswith("Finished call to") and "this was the" in msg:
            s["module_retries"] += 1
        if s["pipeline_args"] is None and msg.startswith("Start pipeline with args:"):
            s["pipeline_args"] = msg[len("Start pipeline with args:"):].strip()
    s["total_cost_usd"] = round(s["total_cost_usd"], 6)
    s["finish_reasons"] = dict(reasons)

    def dist(vals):
        if not vals:
            return {}
        v = sorted(vals)
        d = {"n": len(v), "min": v[0], "p50": percentile(v, 0.5), "p90": percentile(v, 0.9),
             "p99": percentile(v, 0.99), "max": v[-1], "sum": sum(v)}
        return d
    s["completion_tokens"] = dist(comp)
    s["prompt_tokens"] = dist(prompt)
    if max_tokens and comp:
        s["completion_tokens"]["at_guard"] = sum(1 for c in comp if c >= max_tokens)
        s["completion_tokens"]["guard"] = max_tokens
        s["completion_tokens"]["headroom_ratio"] = round(
            max_tokens / max(c for c in comp if c < max_tokens), 2) if any(c < max_tokens for c in comp) else None
    if records:
        s["started"], s["finished"] = records[0]["ts"], records[-1]["ts"]
        try:
            t0, t1 = datetime.strptime(s["started"], _TS), datetime.strptime(s["finished"], _TS)
            s["duration_s"] = round((t1 - t0).total_seconds(), 1)
        except ValueError:
            pass
    return s


def per_topic_stats(rec) -> dict:
    content = rec.get("content") or ""
    papers = rec.get("papers") or []
    cited = cited_indices(content)
    return {"title": rec.get("title"), "cost_time": rec.get("cost_time"),
            "block_cycle_count": rec.get("block_cycle_count"), "conv_layer": rec.get("conv_layer"),
            "outline_eval_score": rec.get("outline_eval_score"), "cite_ratio": rec.get("cite_ratio"),
            "n_papers": len(papers), "n_refs_cited": len(cited), "n_words": content_words(content),
            "n_headings": count_headings(content), "content_chars": len(content)}


def collect_models(config) -> list[str]:
    found = set()

    def walk(o):
        if isinstance(o, dict):
            if "model" in o and isinstance(o["model"], str):
                found.add(o["model"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(config)
    return sorted(found)


def git_head(path) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", required=True)
    ap.add_argument("--output_jsonl", required=True)
    ap.add_argument("--input_jsonl", required=True)
    ap.add_argument("--env_file", default=str(REPO / ".env"))
    ap.add_argument("--config", default=str(REPO / "LLMxMapReduce_V2/config/model_config_llama.json"))
    ap.add_argument("--pool_ceiling")
    ap.add_argument("--run_name")
    ap.add_argument("--out")
    args = ap.parse_args()

    run_name = args.run_name or Path(args.log).stem
    env = parse_env_file(args.env_file) if Path(args.env_file).exists() else {}
    profile = {k: env.get(k) for k in PROFILE_KEYS}
    max_tokens = _int(profile.get("LLMXMR_MAX_TOKENS"))
    with open(args.log, encoding="utf-8", errors="replace") as f:
        records = parse_log_records(f)
    log_summary = summarize_log(records, max_tokens)
    topics = [per_topic_stats(r) for r in iter_jsonl(args.output_jsonl)]

    input_manifest_path = args.input_jsonl + ".manifest.json"
    input_manifest = json.load(open(input_manifest_path)) if Path(input_manifest_path).exists() else None
    stage2_by_title = {t["title"]: t for t in (input_manifest or {}).get("topics", [])}
    ceil_by_title = {}
    if args.pool_ceiling and Path(args.pool_ceiling).exists():
        ceil_by_title = {t["title"]: t for t in json.load(open(args.pool_ceiling))["topics"]}
    for t in topics:
        t["stage2"] = stage2_by_title.get(t["title"])
        t["pool_ceiling"] = ceil_by_title.get(t["title"])

    config = json.load(open(args.config)) if Path(args.config).exists() else {}
    manifest = {
        "run_name": run_name, "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "models": collect_models(config), "config_file": args.config, "profile": profile,
        "git": {"LLMxMapReduce-v2": git_head(REPO),
                "kisti_data": git_head(os.environ.get("KISTI_DATA_ROOT", "/data2/chanjoong/kisti_data"))},
        "input": {"path": args.input_jsonl, "sha256": sha256_file(args.input_jsonl),
                  "manifest": {k: v for k, v in (input_manifest or {}).items() if k != "topics"}},
        "log": {"path": args.log, **log_summary},
        "topics": topics, "n_topics": len(topics),
    }
    out = args.out or str(REPO / "data" / "manifest" / f"{run_name}.json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    ls = log_summary
    ct = ls["completion_tokens"]
    print(f"run={run_name} topics={len(topics)} calls={ls['calls']} cost=${ls['total_cost_usd']:.4f} "
          f"duration={ls['duration_s']}s")
    print(f"completion_tokens: n={ct.get('n')} p50={ct.get('p50')} p99={ct.get('p99')} max={ct.get('max')} "
          f"at_guard={ct.get('at_guard')} guard={ct.get('guard')} headroom={ct.get('headroom_ratio')}")
    print(f"truncated discarded={ls['truncated_discarded']} kept={ls['truncated_kept']} "
          f"fence_fallback={ls['fence_fallback']} illegal_bibkeys={ls['illegal_bibkeys']} "
          f"429={ls['rate_limit_429']} module_retries={ls['module_retries']} errors={ls['error_records']} "
          f"tracebacks={ls['tracebacks']}")
    for t in topics:
        print(f"  - {t['title'][:60]}: papers={t['n_papers']} cited={t['n_refs_cited']} words={t['n_words']} "
              f"headings={t['n_headings']} block={t['block_cycle_count']} conv={t['conv_layer']} "
              f"outline_eval={t['outline_eval_score']} cite_ratio={t['cite_ratio']} time={t['cost_time']}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
