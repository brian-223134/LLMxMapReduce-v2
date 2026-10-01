#!/usr/bin/env python3
"""GT recall·precision — 인수인계 §5 채점 (Stage 3 output.jsonl).

  recall    = |본문 인용 ref ∩ GT(view 안)| / n_gt_refs_cutoff
  precision = |본문 인용 ref ∩ GT(view 안)| / |본문 인용 ref|
  refs 수   = 본문에 [n] 으로 인용된 서로 다른 논문 수 (공변량으로 병기)
  recall_with_post (보조 지표, 2026-09-30) = |인용 ∩ (GT(view 안) ∪ post)| / (n_gt_refs_cutoff + n_gt_refs_post)
             post = GT 공개일 이후에 나왔지만 GT 가 인용했고 view 에 있는 ref (검색 정책이 막아 정상이면 hit 0)

GT(view 안)은 pool_ceiling.py 와 같은 kisti_data/candidates/gap_to_80_refs.jsonl 의 tier == in_view 행(view_id 로 매칭),
분모는 topics.jsonl 의 n_gt_refs_cutoff. papers[] 에만 있고 본문에 인용되지 않은 편은 gt_hits_listed 로 따로 적는다.
분모가 view·정책마다 다르므로 view 가 다른 실행의 recall 을 같은 표에 놓지 말 것.

사용:
  python scripts/gt_recall.py --output data/kisti-2608-r4/output.jsonl \
      [--topics $KISTI_DATA_ROOT/data/topics.kisti.jsonl] \
      [--gt_refs $KISTI_DATA_ROOT/candidates/gap_to_80_refs.jsonl] [--out data/kisti-2608-r4/gt_recall.output.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kisti_common import cited_indices, iter_jsonl  # noqa: E402

KISTI_ROOT = Path(os.environ.get("KISTI_DATA_ROOT", "/data2/chanjoong/kisti_data"))


def score_record(rec, gt: set[str], denom: int, post: set[str] | None = None) -> dict:
    papers = rec.get("papers") or []
    content = rec.get("content") or ""
    cited = {str(papers[i - 1].get("arxiv_id")).lower()
             for i in cited_indices(content) if 1 <= i <= len(papers)}
    listed = {str(p.get("arxiv_id")).lower() for p in papers}
    hit = cited & gt
    post = post or set()
    hit_post = cited & post
    return {"n_papers": len(papers), "n_refs_cited": len(cited),
            "gt_hits_post": len(hit_post), "n_post": len(post),
            "recall_with_post": round((len(hit) + len(hit_post)) / (denom + len(post)), 4) if (denom or post) else None,
            "gt_hits_cited": len(hit), "gt_hits_listed": len(listed & gt),
            "recall": round(len(hit) / denom, 4) if denom else None,
            "precision": round(len(hit) / len(cited), 4) if cited else None,
            "gt_hits_cited_ids": sorted(hit)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", required=True, help="Stage 3 output.jsonl")
    ap.add_argument("--topics", default=str(KISTI_ROOT / "data/topics.kisti.jsonl"))
    ap.add_argument("--gt_refs", default=str(KISTI_ROOT / "candidates/gap_to_80_refs.jsonl"))
    ap.add_argument("--out")
    args = ap.parse_args()

    topics = {t["title"]: t for t in iter_jsonl(args.topics)}
    gt, post = defaultdict(set), defaultdict(set)
    for r in iter_jsonl(args.gt_refs):
        if r.get("tier") == "in_view" and r.get("view_id"):
            gt[r["slug"]].add(r["view_id"].lower())
        elif r.get("tier") == "post" and r.get("view_id"):
            post[r["slug"]].add(r["view_id"].lower())

    rows = []
    for rec in iter_jsonl(args.output):
        t = topics.get(rec.get("title"))
        if t is None:
            print(f"[skip] topics 에 없는 title: {rec.get('title')!r}", file=sys.stderr)
            continue
        denom = t.get("n_gt_refs_cutoff")
        row = {"title": t["title"], "slug": t["slug"], "denominator": denom,
               "denominator_field": "n_gt_refs_cutoff", "n_gt_refs_cutoff_view": t.get("n_gt_refs_cutoff_view"),
               "gt_unique_in_view": len(gt[t["slug"]]), "n_gt_refs_post": t.get("n_gt_refs_post"),
               **score_record(rec, gt[t["slug"]], denom, post[t["slug"]])}
        if row["gt_unique_in_view"] != denom:
            print(f"⚠ {t['slug']}: n_gt_refs_cutoff={denom} ≠ gt_refs in_view={row['gt_unique_in_view']}", file=sys.stderr)
        rows.append(row)
        print(f"{t['slug']:<30} recall={row['recall']} precision={row['precision']} "
              f"refs={row['n_refs_cited']} hits={row['gt_hits_cited']}/{denom} (listed {row['gt_hits_listed']}) "
              f"recall_with_post={row['recall_with_post']}")
    if args.out:
        Path(args.out).write_text(json.dumps({"topics": rows, "topics_file": args.topics, "gt_refs_file": args.gt_refs},
                                             ensure_ascii=False, indent=2) + "\n")
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
