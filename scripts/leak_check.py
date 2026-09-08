#!/usr/bin/env python3
"""GT 누수 검사 — 인수인계 §4: GT DOI·twin arXiv id·twin 제목이 입력 pool·본문·refs 에 0회여야 한다.

검사 대상
  --input  : Stage 2 input.jsonl  (papers[].arxiv_id / url / title)
  --output : Stage 3 output.jsonl (content, ref_str, outline, papers[])
검사 키
  --exclude_keys : view 의 exclude_keys.txt (DOI 형식 38개 = GT 본체 25 + twin 15). 각 키에서
                   DOI 문자열과 (arXiv 면) base id 를 검색어로 만든다.
  --candidates_dir : candidates/<domain>/<slug>/candidate.yaml 의 gt.title (GT 제목)
  --twin_readme    : candidates/README.md §4 표의 `| twin:<id> | ... | <제목> |` 행 (twin 제목, 70자 절단)
판정
  id_hit    : 키가 papers id/url 에 있거나 본문·refs 문자열에 나타남           → 실패(exit 1)
  title_hit : GT/twin 제목(정규화)이 papers[].title 과 일치                     → 실패(exit 1)
  title_mention : 본문·refs 문자열 안에 제목이 등장 (인용 없이 언급될 수 있음)   → 경고만
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kisti_common import doi_to_id, is_arxiv_id, iter_jsonl, norm_title  # noqa: E402

KISTI_ROOT = Path(os.environ.get("KISTI_DATA_ROOT", "/data2/chanjoong/kisti_data"))
_TWIN_ROW = re.compile(r"^\|\s*twin:(\S+)\s*\|[^|]*\|[^|]*\|\s*(.*?)\s*\|\s*$")


def search_terms(exclude_keys) -> dict[str, str]:
    """{검색어(소문자): 출처 키}. DOI 자체와, arXiv 면 base id 도 넣는다."""
    terms = {}
    for k in exclude_keys:
        k = k.strip().lower()
        if not k:
            continue
        terms[k] = k
        pid = doi_to_id(k)
        if is_arxiv_id(pid):
            terms[pid] = k
    return terms


def load_gt_titles(candidates_dir, topics) -> dict[str, str]:
    """{slug: GT 제목} — candidate.yaml 의 gt: 블록 안 title (PyYAML 없이 줄 파싱)."""
    out = {}
    for t in topics:
        p = Path(candidates_dir) / t["domain"] / t["slug"] / "candidate.yaml"
        if not p.exists():
            continue
        in_gt = False
        for line in p.read_text(encoding="utf-8").splitlines():
            if re.match(r"^gt:\s*$", line):
                in_gt = True
                continue
            if in_gt and not line.startswith(" "):
                in_gt = False
            m = re.match(r"^\s+title:\s*(.*)$", line) if in_gt else None
            if m:
                out[t["slug"]] = m.group(1).strip().strip('"').strip("'")
                break
    return out


def load_twin_titles(readme_path) -> dict[str, str]:
    """{twin arXiv id: 제목(표에서 절단된 그대로)}."""
    out = {}
    if not readme_path or not Path(readme_path).exists():
        return out
    for line in Path(readme_path).read_text(encoding="utf-8").splitlines():
        m = _TWIN_ROW.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def find_leaks(records, terms, titles) -> list[dict]:
    """records: input/output jsonl 행. terms: {검색어: 키}. titles: {라벨: 제목}.
    반환: [{title(topic), kind, term, where}]."""
    hits = []
    norm_titles = {label: norm_title(t) for label, t in titles.items() if t}
    for rec in records:
        topic = rec.get("title", "")
        papers = rec.get("papers") or []
        # 1) papers id / url
        for p in papers:
            pid = str(p.get("arxiv_id") or "").lower()
            url = str(p.get("url") or "").lower()
            for term, key in terms.items():
                if pid == term or (term in url and len(term) >= 9):
                    hits.append({"title": topic, "kind": "id_hit", "term": key, "where": f"papers[{pid}]"})
            nt = norm_title(p.get("title") or "")
            for label, t in norm_titles.items():
                if nt and (nt == t or (len(t) >= 40 and nt.startswith(t))):
                    hits.append({"title": topic, "kind": "title_hit", "term": label, "where": f"papers[{pid}]"})
        # 2) 문자열 필드
        for field in ("content", "ref_str", "outline"):
            text = rec.get(field)
            if not text:
                continue
            low = text.lower()
            for term, key in terms.items():
                if len(term) >= 9 and term in low:
                    hits.append({"title": topic, "kind": "id_hit", "term": key, "where": field})
            nl = norm_title(text)
            for label, t in norm_titles.items():
                if len(t) >= 25 and t in nl:
                    hits.append({"title": topic, "kind": "title_mention", "term": label, "where": field})
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input")
    ap.add_argument("--output")
    ap.add_argument("--topics", default=str(KISTI_ROOT / "data/topics.kisti.jsonl"))
    ap.add_argument("--exclude_keys", default=str(KISTI_ROOT / "data/views/kisti-2512/exclude_keys.txt"))
    ap.add_argument("--candidates_dir", default=str(KISTI_ROOT / "candidates"))
    ap.add_argument("--twin_readme", default=str(KISTI_ROOT / "candidates/README.md"))
    ap.add_argument("--out")
    args = ap.parse_args()
    if not (args.input or args.output):
        ap.error("--input 또는 --output 중 하나는 필요")

    topics = list(iter_jsonl(args.topics))
    keys = [l.strip() for l in Path(args.exclude_keys).read_text().splitlines() if l.strip()]
    terms = search_terms(keys)
    titles = {f"gt:{s}": t for s, t in load_gt_titles(args.candidates_dir, topics).items()}
    titles.update({f"twin:{i}": t for i, t in load_twin_titles(args.twin_readme).items()})

    report = {"exclude_keys": len(keys), "search_terms": len(terms), "titles": len(titles), "files": {}}
    all_hits = []
    for label, path in (("input", args.input), ("output", args.output)):
        if not path:
            continue
        recs = list(iter_jsonl(path))
        hits = find_leaks(recs, terms, titles)
        report["files"][label] = {"path": path, "records": len(recs), "hits": hits}
        all_hits += hits
        print(f"[{label}] {len(recs)} records, {len(hits)} hits")
        for h in hits:
            print(f"   {h['kind']:14} {h['term']:40} {h['where']:24} {h['title'][:50]}")
    hard = [h for h in all_hits if h["kind"] in ("id_hit", "title_hit")]
    report["hard_hits"] = len(hard)
    report["mentions"] = len(all_hits) - len(hard)
    print(f"hard hits={len(hard)} (id/title in pool·refs)  title mentions={report['mentions']} (경고)")
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"-> {args.out}")
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
