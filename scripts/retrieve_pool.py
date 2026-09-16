"""Stage 1 of the same-corpus input builder: per-topic retrieval.

For each SurveyEval test topic, retrieve a ranked candidate pool from the
Common Corpus view via AutoSurvey's retrieval stack (nomic-embed-text-v1 +
FAISS), exactly the path the AutoSurvey baseline uses — so every agent in the
same-corpus comparison shares one retrieval backend.

2026-09-14 규약 (kisti_data/docs/asg/AGENT-HANDOFF.md §0): reference cutoff 를 고정하지 않고
topic 마다 GT survey 최초 공개일(retrieval_cutoff_at) 이전 문헌만 검색한다. `--topic_policy` 를 주면
topic 마다 AutoSurvey `database.set_policy(policy_from_row(row))` 로 FAISS IDSelectorBitmap 을 걸어
**검색 자체가 허용 집합 안에서** 돈다 (전체 Top-K 뒤 사후 필터가 아님). topic 행은 topics.jsonl 의
`slug`(= 정책 파일 topic_id) 로 고른다. 정책 없이 돌리면 구 규약(정책 없음)으로 표기된다.

Run with the *autosurvey* conda env (needs faiss + sentence-transformers + GPU
or CPU):

    CUDA_VISIBLE_DEVICES=<idle> /data2/chanjoong/miniforge3/envs/autosurvey/bin/python \
        scripts/retrieve_pool.py \
        --topics /data2/chanjoong/kisti_data/data/topics.kisti.jsonl \
        --db_path ../AutoSurvey/database_kisti-kisti-2608 \
        --exclude_file /data2/chanjoong/kisti_data/data/views/kisti-2608/exclude_ids.txt \
        --topic_policy ../AutoSurvey/data/topic_policy.kisti-2608.jsonl \
        --output data/kisti-2608/pools.jsonl

Output: one JSON line per topic:
    {"title": ..., "arxiv_id_ranked": [...], "retrieve_num": N,
     "retrieval_policy": {topic_id, retrieval_cutoff_at, allowed, allowed_fingerprint_sha256, ...} | None}
plus `<output>.manifest.json` (DB·정책 파일·sidecar·view sha 등 run 수준 출처).
"""

import argparse
import datetime
import hashlib
import json
import os
import sys

AUTOSURVEY_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "AutoSurvey")

# Stage 1 pool 행과 run manifest 에 남기는 정책 필드 (database.set_policy 의 policy_report 에서 고른다)
_REPORT_KEYS = ("index_total", "allowed", "allowed_fingerprint_sha256", "excluded",
                "allowed_date_source", "exclude_ids_present_in_index", "date_precision_default")
_POLICY_KEYS = ("topic_id", "topic", "gt_first_public_at", "gt_first_public_source",
                "retrieval_cutoff_at", "rule", "exclude_ids", "corpus_snapshot_id", "status")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_exclude(path):
    if not path:
        return set()
    with open(path) as f:
        return {l.split("#", 1)[0].strip() for l in f if l.split("#", 1)[0].strip()}


def policy_block(policy_report):
    """database.set_policy 가 돌려준 policy_report → pool 행에 남길 축약 블록."""
    pol = policy_report.get("policy") or {}
    out = {k: pol.get(k) for k in _POLICY_KEYS}
    out.update({k: policy_report.get(k) for k in _REPORT_KEYS})
    side = policy_report.get("sidecar") or {}
    out["sidecar"] = {k: side.get(k) for k in ("created_at", "view", "view_papers_sha256", "records", "by_precision")}
    return out


def retrieve_topics(db, topics, retrieve_num, exclude=frozenset(), policy_rows=None, policy_mod=None,
                    topic_id_field="slug", log=print):
    """topic 마다 (정책이 있으면 선택자를 건 뒤) 검색한다. 반환: pool 행 목록.

    db          : AutoSurvey src.database.database (get_ids_from_query / set_policy / is_allowed)
    policy_rows : load_policy_rows() 결과. None 이면 정책 없음(구 규약)
    policy_mod  : select_row / policy_from_row 를 가진 모듈 (AutoSurvey src.retrieval_policy)
    """
    rows = []
    for n, topic in enumerate(topics, 1):
        title = topic["title"]
        block = None
        if policy_rows is not None:
            slug = topic.get(topic_id_field)
            if not slug:
                raise KeyError(f"topic {title!r} 에 {topic_id_field!r} 가 없어 정책 행을 고를 수 없다")
            row = policy_mod.select_row(policy_rows, topic_id=slug)
            if (row.get("topic") or "").strip() and row["topic"].strip() != title.strip():
                log(f"[policy] ⚠ topic_id={slug}: 정책 행 topic {row['topic']!r} ≠ topics.jsonl title {title!r}")
            policy = policy_mod.policy_from_row(row)
            report = db.set_policy(policy)
            block = policy_block(report)
        ids = list(db.get_ids_from_query(title, num=retrieve_num))
        leaked = [i for i in ids if i in exclude]
        if leaked:
            raise RuntimeError(
                f"GT survey id(s) {leaked} returned for topic {title!r} — "
                f"the index was built from the wrong view."
            )
        if block is not None:
            not_allowed = [i for i in ids if not db.is_allowed(i)]
            if not_allowed:
                raise RuntimeError(f"정책 선택자가 걸렸는데 허용 집합 밖 id 가 검색됨: {not_allowed[:5]} ({title!r})")
            if len(ids) < retrieve_num:
                log(f"[policy] ⚠ {block['topic_id']}: 허용 집합 안에서 {len(ids)} < {retrieve_num} 편만 검색됨")
        rows.append({"title": title, "arxiv_id_ranked": ids, "retrieve_num": retrieve_num,
                     "retrieval_policy": block})
        tag = f"cutoff<{block['retrieval_cutoff_at']} allowed={block['allowed']:,}" if block else "policy=none"
        log(f"[{n}] {len(ids):5d} candidates  {tag}  {title[:60]}")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--topics", required=True, help="jsonl with {'title': ..., 'slug': ...} per line")
    parser.add_argument("--db_path", required=True, help="AutoSurvey-format DB dir (with FAISS index)")
    parser.add_argument("--embedding_model", default="nomic-ai/nomic-embed-text-v1",
                        help="must match the model the index was built with")
    parser.add_argument("--retrieve_num", type=int, default=1200,
                        help="candidates per topic (paper: 1,200, as in AutoSurvey)")
    parser.add_argument("--exclude_file", default=None,
                        help="GT arXiv base ids; already excluded in the view — this is a defensive double gate")
    parser.add_argument("--topic_policy", default=None,
                        help="topic 정책 JSONL (AutoSurvey/data/topic_policy.<view>.jsonl). topic 마다 set_policy 후 검색. "
                             "없으면 정책 없이(구 규약) 돌고 pool 행의 retrieval_policy 가 null 이 된다")
    parser.add_argument("--topic_id_field", default="slug", help="topics.jsonl 에서 정책 topic_id 로 쓸 필드")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    sys.path.insert(0, os.path.abspath(AUTOSURVEY_ROOT))
    from src.database import database  # noqa: E402

    policy_rows, policy_mod = None, None
    if args.topic_policy:
        from src import retrieval_policy as policy_mod  # noqa: E402
        policy_rows = policy_mod.load_policy_rows(args.topic_policy)
        print(f"[policy] {args.topic_policy} ({len(policy_rows)} rows)", flush=True)
    else:
        print("[policy] ⚠ --topic_policy 없음 — 정책 없이 검색 (2026-09-14 규약 위반, 구 규약 재현용)", flush=True)

    exclude = load_exclude(args.exclude_file)
    with open(args.topics) as f:
        topics = [json.loads(l) for l in f if l.strip()]

    db = database(db_path=args.db_path, embedding_model=args.embedding_model)
    if policy_rows is not None and db._sidecar_dates is None:
        raise SystemExit(f"정책이 있는데 sidecar 가 없다: {args.db_path}/paper_dates.json — DOI 레코드가 연 단위로 판정되어 허용 집합이 달라진다")

    rows = retrieve_topics(db, topics, args.retrieve_num, exclude, policy_rows, policy_mod, args.topic_id_field,
                           log=lambda s: print(s, flush=True))

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as fout:
        for r in rows:
            fout.write(json.dumps(r) + "\n")

    export_manifest = None
    p = os.path.join(args.db_path, "corpus_export_manifest.json")
    if os.path.exists(p):
        with open(p) as f:
            export_manifest = json.load(f)
    manifest = {
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "db_path": os.path.abspath(args.db_path), "embedding_model": args.embedding_model,
        "retrieve_num": args.retrieve_num, "index_total": int(db.abs_loaded_index.ntotal),
        "corpus_export_manifest": {k: export_manifest.get(k) for k in ("format", "created_at", "records", "view", "content_sha256")}
        if export_manifest else None,
        "sidecar": db.sidecar_meta,
        "topics_file": os.path.abspath(args.topics), "topics_sha256": _sha256(args.topics),
        "exclude_file": os.path.abspath(args.exclude_file) if args.exclude_file else None,
        "topic_policy_file": os.path.abspath(args.topic_policy) if args.topic_policy else None,
        "topic_policy_sha256": _sha256(args.topic_policy) if args.topic_policy else None,
        "topic_id_field": args.topic_id_field,
        "rule": "검색은 허용 집합(upper_bound(공개일) < retrieval_cutoff_at ∧ id ∉ exclude_ids) 안에서 FAISS IDSelectorBitmap 으로 수행"
                if args.topic_policy else "정책 없음 (구 규약, 2025-12-31 view 컷만)",
        "n_topics": len(rows),
    }
    with open(args.output + ".manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"done: {len(rows)} topics -> {args.output} (+manifest)")


if __name__ == "__main__":
    main()
