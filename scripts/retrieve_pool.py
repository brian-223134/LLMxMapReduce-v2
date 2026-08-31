"""Stage 1 of the same-corpus input builder: per-topic retrieval.

For each SurveyEval test topic, retrieve a ranked candidate pool from the
Common Corpus view via AutoSurvey's retrieval stack (nomic-embed-text-v1 +
FAISS), exactly the path the AutoSurvey baseline uses — so every agent in the
same-corpus comparison shares one retrieval backend.

Run with the *autosurvey* conda env (needs faiss + sentence-transformers + GPU
or CPU):

    CUDA_VISIBLE_DEVICES=<idle> /data2/chanjoong/miniforge3/envs/autosurvey/bin/python \
        scripts/retrieve_pool.py \
        --topics data/surveyeval/test_topics.jsonl \
        --db_path ../AutoSurvey/database_commoncorpus-surveyeval-2512 \
        --exclude_file data/surveyeval/gt_arxiv_ids.txt \
        --output data/pools/surveyeval-2512.pools.jsonl

Output: one JSON line per topic:
    {"title": ..., "arxiv_id_ranked": [...], "retrieve_num": N}
"""

import argparse
import json
import os
import sys

AUTOSURVEY_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "AutoSurvey")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topics", required=True, help="jsonl with {'title': ...} per line")
    parser.add_argument("--db_path", required=True, help="AutoSurvey-format DB dir (with FAISS index)")
    parser.add_argument("--embedding_model", default="nomic-ai/nomic-embed-text-v1",
                        help="must match the model the index was built with")
    parser.add_argument("--retrieve_num", type=int, default=1200,
                        help="candidates per topic (paper: 1,200, as in AutoSurvey)")
    parser.add_argument("--exclude_file", default=None,
                        help="GT arXiv base ids; already excluded in the view — this is a defensive double gate")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    sys.path.insert(0, os.path.abspath(AUTOSURVEY_ROOT))
    from src.database import database  # noqa: E402

    exclude = set()
    if args.exclude_file:
        with open(args.exclude_file) as f:
            exclude = {l.strip() for l in f if l.strip()}

    db = database(db_path=args.db_path, embedding_model=args.embedding_model)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    n_written = 0
    with open(args.topics) as fin, open(args.output, "w") as fout:
        for line in fin:
            if not line.strip():
                continue
            topic = json.loads(line)
            title = topic["title"]
            ids = db.get_ids_from_query(title, num=args.retrieve_num)
            leaked = [i for i in ids if i in exclude]
            if leaked:
                raise RuntimeError(
                    f"GT survey id(s) {leaked} returned for topic {title!r} — "
                    f"the index was built from the wrong view."
                )
            fout.write(json.dumps({
                "title": title,
                "arxiv_id_ranked": list(ids),
                "retrieve_num": args.retrieve_num,
            }) + "\n")
            n_written += 1
            print(f"[{n_written}] {len(ids):5d} candidates  {title[:70]}")

    print(f"done: {n_written} topics -> {args.output}")


if __name__ == "__main__":
    main()
