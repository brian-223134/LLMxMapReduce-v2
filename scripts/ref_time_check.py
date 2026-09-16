#!/usr/bin/env python3
"""결과 ref 의 시간 범위 검증 — 2026-09-14 규약 (AGENT-HANDOFF.md §5).

생성 결과(Stage 3 output.jsonl)나 입력(Stage 2 input.jsonl)의 참고문헌을 topic 정책(retrieval_cutoff_at ·
exclude_ids)과 sidecar(paper_dates.json) 로 판정한다. **원본 출력은 손대지 않고** 판정 로그만 남긴다.

판정 (ref 하나 = papers[i], ref 번호 i+1; ref_str 의 `[n] 제목 url` 과 대조)
  allowed          sidecar 공개일 상한 < cutoff ∧ id ∉ exclude_ids
  time_violation   corpus 에 실재하는 논문이지만 공개일 상한 ≥ cutoff  → "시간 범위 위반" (허위 인용과 구분)
  excluded_id      정책 exclude_ids(GT 본체·선행판·사본)                → GT 누수 (leak_check.py 와 이중 확인)
  no_date          corpus 에 있으나 날짜 없음(정책상 검색 불가였어야 함)
  not_in_corpus    sidecar 에 없는 id — 입력 pool 밖 참고문헌 = 허위/미확인 인용 후보
  unlisted_ref     ref_str 에는 있는데 papers[] 에 없는 번호 — 파이프라인이 만들지 않는 항목이므로 허위 인용 후보
본문에 `[n]` 으로 실제 인용된 것(cited)과 목록에만 있는 것(listed)을 나눠 센다.

정책 행이 없는 topic(예: 스모크 'Securing Large Language Models')은 policy=none 으로 기록만 한다.
날짜 규칙은 kisti_data/adapter/common/retrieval_policy.py(4 agent 공통) 를 그대로 쓴다.

사용:
  python scripts/ref_time_check.py --output data/kisti-2608/output.jsonl \\
      [--input data/kisti-2608/input.jsonl] [--topics $KISTI_DATA_ROOT/data/topics.kisti.jsonl] \\
      [--topic_policy ../AutoSurvey/data/topic_policy.kisti-2608.jsonl] [--view kisti-2608] \\
      [--out data/kisti-2608/ref_time_check.output.json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kisti_common import cited_indices, iter_jsonl, split_references  # noqa: E402

KISTI_ROOT = Path(os.environ.get("KISTI_DATA_ROOT", "/data2/chanjoong/kisti_data"))
KISTI_VIEW = os.environ.get("KISTI_VIEW", "kisti-2512")
AUTOSURVEY_ROOT = Path(__file__).resolve().parents[2] / "AutoSurvey"
_REF_LINE = re.compile(r"^\[(\d+)\]\s+(.*?)(?:\s+(https?://\S+))?\s*$", re.M)
VERDICTS = ("allowed", "time_violation", "excluded_id", "no_date", "not_in_corpus")


def _policy_lib():
    sys.path.insert(0, str(KISTI_ROOT / "adapter"))
    from common import retrieval_policy as rp  # noqa: E402
    return rp


def parse_ref_str(ref_str) -> list[dict]:
    """`## References` 블록의 `[n] 제목 url` 행 → [{n, title, url}]."""
    out = []
    for m in _REF_LINE.finditer(ref_str or ""):
        out.append({"n": int(m.group(1)), "title": m.group(2).strip(), "url": m.group(3)})
    return out


def judge_paper(pid, dates, cutoff, exclude_ids, is_allowed) -> tuple[str, str | None]:
    """→ (verdict, date)."""
    pid = str(pid or "").strip()
    if pid.lower() in exclude_ids:
        return "excluded_id", dates.get(pid)
    if pid not in dates:
        return "not_in_corpus", None
    d = dates.get(pid)
    if not d:
        return "no_date", None
    if cutoff is None:
        return "allowed", d
    return ("allowed" if is_allowed(d, cutoff) else "time_violation"), d


def check_record(rec, policy_row, dates, is_allowed) -> dict:
    """output/input jsonl 한 행 → topic 판정."""
    papers = rec.get("papers") or []
    content = rec.get("content") or ""
    ref_str = rec.get("ref_str") or ""
    if not ref_str and content:
        _, ref_str = split_references(content)
    cited = cited_indices(content) if content else set(range(1, len(papers) + 1))
    cutoff = (policy_row or {}).get("retrieval_cutoff_at")
    excl = {e.lower() for e in ((policy_row or {}).get("exclude_ids") or [])}
    listed, cited_c, problems = Counter(), Counter(), []
    for i, p in enumerate(papers, 1):
        verdict, d = judge_paper(p.get("arxiv_id"), dates, cutoff, excl, is_allowed)
        listed[verdict] += 1
        is_cited = i in cited
        if is_cited:
            cited_c[verdict] += 1
        if verdict != "allowed":
            problems.append({"ref": i, "id": p.get("arxiv_id"), "date": d, "kind": verdict, "cited": is_cited,
                             "title": (p.get("title") or "")[:120]})
    refs = parse_ref_str(ref_str)
    unlisted = [r for r in refs if r["n"] < 1 or r["n"] > len(papers)]
    url_mismatch = [r["n"] for r in refs if 1 <= r["n"] <= len(papers) and r["url"]
                    and papers[r["n"] - 1].get("url") and r["url"] != papers[r["n"] - 1]["url"]]
    for r in unlisted:
        problems.append({"ref": r["n"], "id": None, "date": None, "kind": "unlisted_ref", "cited": r["n"] in cited,
                         "title": r["title"][:120]})
    cited_missing = sorted(n for n in cited if n < 1 or n > len(papers))
    return {"title": rec.get("title"), "topic_id": (policy_row or {}).get("topic_id"),
            "retrieval_cutoff_at": cutoff, "policy": "topic_cutoff" if cutoff else "none",
            "n_papers": len(papers), "n_ref_lines": len(refs), "n_cited": len(cited),
            "listed": {k: listed.get(k, 0) for k in VERDICTS},
            "cited": {k: cited_c.get(k, 0) for k in VERDICTS},
            "unlisted_refs": len(unlisted), "ref_url_mismatch": url_mismatch, "cited_out_of_range": cited_missing,
            "problems": problems}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", help="Stage 3 output.jsonl")
    ap.add_argument("--input", help="Stage 2 input.jsonl (papers 만 검사, 전부 cited 로 간주)")
    ap.add_argument("--topics", default=str(KISTI_ROOT / "data/topics.kisti.jsonl"))
    ap.add_argument("--view", default=KISTI_VIEW, help="sidecar 를 찾을 view (기본 $KISTI_VIEW)")
    ap.add_argument("--paper_dates", help="sidecar paper_dates.json (기본 data/views/<view>/paper_dates.json)")
    ap.add_argument("--topic_policy", help="정책 JSONL (기본 AutoSurvey/data/topic_policy.<view>.jsonl). 'none' 이면 정책 없이 기록만")
    ap.add_argument("--out")
    args = ap.parse_args()
    if not (args.output or args.input):
        ap.error("--output 또는 --input 중 하나는 필요")

    rp = _policy_lib()
    slug_by_title = {t["title"]: t.get("slug") for t in iter_jsonl(args.topics)}
    policy_rows, policy_path = {}, None
    if (args.topic_policy or "").lower() != "none":
        policy_path = Path(args.topic_policy) if args.topic_policy else AUTOSURVEY_ROOT / "data" / f"topic_policy.{args.view}.jsonl"
        if not policy_path.exists():
            raise SystemExit(f"정책 파일 없음: {policy_path} (--topic_policy PATH 또는 'none')")
        policy_rows = rp.load_topic_policy(policy_path)
    dates_path = Path(args.paper_dates) if args.paper_dates else KISTI_ROOT / "data/views" / args.view / "paper_dates.json"
    dates, dates_meta = rp.load_paper_dates(dates_path)
    if not dates:
        raise SystemExit(f"sidecar 없음: {dates_path}")

    report = {"view": args.view, "paper_dates": str(dates_path),
              "sidecar": {k: dates_meta.get(k) for k in ("created_at", "view_papers_sha256", "records", "by_precision")},
              "topic_policy_file": str(policy_path) if policy_path else None,
              "rule": "upper_bound(sidecar 공개일) < retrieval_cutoff_at ∧ id ∉ exclude_ids; 결과 원본은 수정하지 않음",
              "files": {}}
    total = Counter()
    for label, path in (("input", args.input), ("output", args.output)):
        if not path:
            continue
        rows = []
        for rec in iter_jsonl(path):
            slug = slug_by_title.get(rec.get("title"))
            row = policy_rows.get(slug) if slug else None
            if slug and policy_rows and row is None:
                raise KeyError(f"topic {rec.get('title')!r} (slug={slug}) 의 정책 행이 {policy_path} 에 없음")
            r = check_record(rec, row, dates, rp.is_allowed)
            rows.append(r)
            for k in VERDICTS:
                total[f"{label}.cited.{k}"] += r["cited"][k]
                total[f"{label}.listed.{k}"] += r["listed"][k]
            total[f"{label}.unlisted_refs"] += r["unlisted_refs"]
            flag = "" if not r["problems"] else f"  ⚠ {len(r['problems'])} problems"
            print(f"[{label}] {r['title'][:55]:55} policy={r['policy']:12} cutoff={str(r['retrieval_cutoff_at']):10} "
                  f"papers={r['n_papers']:4} cited={r['n_cited']:4} viol(cited/listed)="
                  f"{r['cited']['time_violation']}/{r['listed']['time_violation']} "
                  f"excl={r['listed']['excluded_id']} not_in_corpus={r['listed']['not_in_corpus']} "
                  f"unlisted={r['unlisted_refs']}{flag}")
        report["files"][label] = {"path": path, "records": len(rows), "topics": rows}
    report["totals"] = dict(total)
    n_viol = sum(v for k, v in total.items() if k.endswith(".listed.time_violation"))
    n_excl = sum(v for k, v in total.items() if k.endswith(".listed.excluded_id"))
    n_fab = sum(v for k, v in total.items() if k.endswith(".listed.not_in_corpus") or k.endswith(".unlisted_refs"))
    print(f"time-range violations={n_viol}  excluded-id hits={n_excl}  fabricated/unverifiable={n_fab}")
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"-> {args.out}")
    sys.exit(1 if n_excl else 0)


if __name__ == "__main__":
    main()
