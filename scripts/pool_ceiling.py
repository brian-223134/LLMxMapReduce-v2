#!/usr/bin/env python3
"""pool ceiling — LLM×MR 의 recall 상한 (temperature 와 무관, Stage 1·2 에서 결정).

  pool_ceiling  = |Stage 1 pool(1,200) ∩ GT(view 안)| / |GT(view 안)|
  input_ceiling = |Stage 2 입력(quota 편) ∩ GT(view 안)| / |GT(view 안)|   (--input 지정 시)

GT(view 안)은 kisti_data/candidates/gap_to_80_refs.jsonl 의 tier == in_view 행 (인수인계 §5 분모).
매칭 키는 view id (id 규칙 B: arXiv base id 또는 소문자 DOI).

사용:
  python scripts/pool_ceiling.py --pools data/kisti-2512/pools.jsonl \
      --topics $KISTI_DATA_ROOT/data/topics.kisti.jsonl [--input data/kisti-2512/input.jsonl] \
      [--gt_refs $KISTI_DATA_ROOT/candidates/gap_to_80_refs.jsonl] [--out data/kisti-2512/pool_ceiling.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kisti_common import doi_to_id, iter_jsonl  # noqa: E402

KISTI_ROOT = Path(os.environ.get("KISTI_DATA_ROOT", "/data2/chanjoong/kisti_data"))


def gt_ids_by_slug(gt_refs, tier="in_view") -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for r in gt_refs:
        if r.get("tier") != tier:
            continue
        doi = r.get("kisti_doi") or r.get("doi")
        if not doi:
            continue
        out.setdefault(r["slug"], set()).add(doi_to_id(doi))
    return out


def compute_ceilings(topics, pools, gt_refs, inputs=None) -> dict:
    """topics: [{title, slug, n_gt_refs}], pools: [{title, arxiv_id_ranked}],
    gt_refs: gap_to_80_refs 행, inputs: [{title, papers[{arxiv_id}]}] | None."""
    gt = gt_ids_by_slug(gt_refs)
    pool_by_title = {p["title"]: set(p["arxiv_id_ranked"]) for p in pools}
    input_by_title = {i["title"]: {p["arxiv_id"] for p in i["papers"]} for i in (inputs or [])}
    rows = []
    for t in topics:
        title, slug = t["title"], t["slug"]
        gt_ids = gt.get(slug, set())
        pool_ids = pool_by_title.get(title)
        row = {"title": title, "slug": slug, "n_gt_refs": t.get("n_gt_refs"),
               "n_gt_in_view": len(gt_ids), "pool_size": None, "pool_hits": None, "pool_ceiling": None,
               "input_size": None, "input_hits": None, "input_ceiling": None}
        if pool_ids is not None:
            hits = gt_ids & pool_ids
            row.update(pool_size=len(pool_ids), pool_hits=len(hits),
                       pool_ceiling=round(len(hits) / len(gt_ids), 4) if gt_ids else None)
        in_ids = input_by_title.get(title)
        if in_ids is not None:
            hits = gt_ids & in_ids
            row.update(input_size=len(in_ids), input_hits=len(hits),
                       input_ceiling=round(len(hits) / len(gt_ids), 4) if gt_ids else None)
        rows.append(row)

    def mean(key):
        vals = [r[key] for r in rows if r[key] is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    return {"topics": rows, "mean_pool_ceiling": mean("pool_ceiling"),
            "mean_input_ceiling": mean("input_ceiling"), "n_topics": len(rows)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pools", required=True)
    ap.add_argument("--topics", default=str(KISTI_ROOT / "data/topics.kisti.jsonl"))
    ap.add_argument("--input", help="Stage 2 input.jsonl (있으면 input_ceiling 도 계산)")
    ap.add_argument("--gt_refs", default=str(KISTI_ROOT / "candidates/gap_to_80_refs.jsonl"))
    ap.add_argument("--out")
    args = ap.parse_args()

    topics = list(iter_jsonl(args.topics))
    pools = list(iter_jsonl(args.pools))
    gt_refs = list(iter_jsonl(args.gt_refs))
    inputs = list(iter_jsonl(args.input)) if args.input else None
    res = compute_ceilings(topics, pools, gt_refs, inputs)

    print(f"{'slug':34} {'gt_in_view':>10} {'pool_hits':>9} {'pool_ceil':>9} {'in_hits':>7} {'in_ceil':>7}")
    for r in res["topics"]:
        pc = "-" if r["pool_ceiling"] is None else f"{r['pool_ceiling']:.2%}"
        ic = "-" if r["input_ceiling"] is None else f"{r['input_ceiling']:.2%}"
        print(f"{r['slug'][:34]:34} {r['n_gt_in_view']:>10} {str(r['pool_hits']):>9} {pc:>9} "
              f"{str(r['input_hits']):>7} {ic:>7}")
    print(f"mean pool_ceiling={res['mean_pool_ceiling']}  mean input_ceiling={res['mean_input_ceiling']}")
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
