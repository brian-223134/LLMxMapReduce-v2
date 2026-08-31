"""Stage 2 of the same-corpus input builder: materialize full text and emit
the LLMxMapReduce-V2 input JSONL.

Takes the ranked candidate pools from scripts/retrieve_pool.py, resolves full
text for the top papers through the Common Corpus FullTextResolver (arXiv
e-print -> latex parser, cache-frozen), and writes one survey per line in the
format EncodePipeline/Survey expects:

    {"title": <topic>, "papers": [{"title", "abstract", "url", "txt", "arxiv_id"}]}

Run with the *asg-corpus* conda env (has the common_corpus package):

    /data2/chanjoong/miniforge3/envs/asg-corpus/bin/python scripts/build_corpus_input.py \
        --pools data/pools/surveyeval-2512.pools.jsonl \
        --topics data/surveyeval/test_topics.jsonl \
        --view surveyeval-2512 \
        --output data/inputs/surveyeval-2512.input.jsonl

Pool size per survey defaults to that survey's GT reference count
(--pool_mode gt_count), keeping input scale comparable to the paper's setting
where each survey gets its own reference list. First-time full-text fetches
hit arXiv with a politeness delay, so a full 20-topic build takes hours; the
cache makes reruns free.
"""

import argparse
import json
import os
import sys
import time

CORPUS_ROOT_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "..", "asg-common-corpus")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pools", required=True, help="output of retrieve_pool.py")
    parser.add_argument("--topics", required=True, help="test_topics.jsonl with n_gt_refs per title")
    parser.add_argument("--corpus_root", default=CORPUS_ROOT_DEFAULT)
    parser.add_argument("--view", required=True, help="view name, recorded in the run manifest")
    parser.add_argument("--pool_mode", choices=["gt_count", "fixed"], default="gt_count")
    parser.add_argument("--pool_size", type=int, default=100, help="papers per survey when --pool_mode fixed")
    parser.add_argument("--min_chars", type=int, default=2000,
                        help="skip resolved texts shorter than this (parser floor is 500)")
    parser.add_argument("--limit_topics", type=int, default=None, help="smoke: only first N topics")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    corpus_root = os.path.abspath(args.corpus_root)
    sys.path.insert(0, os.path.join(corpus_root, "src"))
    from common_corpus.fulltext.resolver import FullTextResolver  # noqa: E402
    import duckdb  # noqa: E402

    corpus_dir = os.path.join(corpus_root, "data", "corpus", "v0.1-poc")
    papers_parquet = os.path.join(corpus_dir, "papers.parquet")
    view_manifest_path = os.path.join(corpus_root, "data", "views", args.view, "view_manifest.json")
    with open(view_manifest_path) as f:
        view_manifest = json.load(f)

    n_refs_by_title = {}
    with open(args.topics) as f:
        for line in f:
            if line.strip():
                t = json.loads(line)
                n_refs_by_title[t["title"]] = t.get("n_gt_refs")

    resolver = FullTextResolver(corpus_dir=corpus_dir)
    con = duckdb.connect()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    stats = []
    with open(args.pools) as fin, open(args.output, "w") as fout:
        for topic_i, line in enumerate(fin):
            if not line.strip():
                continue
            if args.limit_topics is not None and topic_i >= args.limit_topics:
                break
            pool = json.loads(line)
            title = pool["title"]
            ranked = pool["arxiv_id_ranked"]

            if args.pool_mode == "gt_count":
                quota = n_refs_by_title.get(title)
                if quota is None:
                    raise KeyError(f"topic {title!r} not in {args.topics}")
            else:
                quota = args.pool_size

            meta = {r[0]: (r[1], r[2]) for r in con.execute(
                f"SELECT arxiv_id, title, abstract FROM '{papers_parquet}' WHERE arxiv_id IN "
                f"({','.join('?' * len(ranked))})", ranked).fetchall()}

            papers, failed, too_short, walked = [], 0, 0, 0
            t0 = time.time()
            for arxiv_id in ranked:
                if len(papers) >= quota:
                    break
                walked += 1
                if arxiv_id not in meta:
                    continue
                try:
                    doc = resolver.resolve(arxiv_id=arxiv_id)
                except Exception:
                    failed += 1
                    continue
                if len(doc.text) < args.min_chars:
                    too_short += 1
                    continue
                p_title, p_abstract = meta[arxiv_id]
                papers.append({
                    "title": p_title,
                    "abstract": p_abstract or "",
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "txt": doc.text,
                    "arxiv_id": arxiv_id,
                })
            fout.write(json.dumps({"title": title, "papers": papers}) + "\n")
            stat = {"title": title, "quota": quota, "resolved": len(papers),
                    "fetch_failed": failed, "too_short": too_short,
                    "walked": walked,
                    "seconds": round(time.time() - t0, 1)}
            stats.append(stat)
            print(json.dumps(stat))

    manifest = {
        "view": args.view,
        "view_manifest": view_manifest,
        "pools_file": os.path.abspath(args.pools),
        "pool_mode": args.pool_mode,
        "min_chars": args.min_chars,
        "topics": stats,
    }
    with open(args.output + ".manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"done: {len(stats)} topics -> {args.output} (+manifest)")


if __name__ == "__main__":
    main()
