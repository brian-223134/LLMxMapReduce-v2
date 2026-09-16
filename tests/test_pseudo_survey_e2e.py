"""가짜(pseudo) Survey 로 기록·검사 체인을 끝까지 돌리는 end-to-end 테스트 — API·GPU·DB 없음.

임베드한 예시 corpus(6편, 날짜·원문 포함)·정책(topic 2개)·GT ref 목록으로

  Stage 1  retrieve_pool.retrieve_topics  (가짜 FAISS DB: 선택자 = 허용 집합 안 검색)   → pools.jsonl (+manifest)
  Stage 2  build_corpus_input_kisti.select_papers (가짜 body_store, quota=n_gt_refs_cutoff) → input.jsonl (+manifest)
  Stage 3  파이프라인 대신 **pseudo survey 출력**(본문 [n] 인용·## References·papers[].bibkey)을 만든다 → output.jsonl + 가짜 로그
  검사     leak_check.find_leaks · ref_time_check.check_record · pool_ceiling.compute_ceilings · run_manifest.main()

을 임시 디렉터리에서 실제 파일로 주고받으며, 각 단계 산출물의 정책 블록·판정·manifest 필드를 확인한다.
누수·시간 범위 위반·허위 인용은 output 을 손으로 오염시킨 변형(tampered)으로 검출되는지 본다.
날짜 규칙은 kisti_data/adapter/common/retrieval_policy.py 를 쓴다(없으면 건너뜀).
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import leak_check as lc  # noqa: E402
import pool_ceiling as pc  # noqa: E402
import ref_time_check as rtc  # noqa: E402
import retrieve_pool as rp  # noqa: E402
import run_manifest as rm  # noqa: E402

ADAPTER = Path(os.environ.get("KISTI_DATA_ROOT", "/data2/chanjoong/kisti_data")) / "adapter"
HAVE_ADAPTER = (ADAPTER / "llmxmapreduce" / "build_corpus_input_kisti.py").exists()
if HAVE_ADAPTER:
    sys.path.insert(0, str(ADAPTER / "llmxmapreduce"))
    sys.path.insert(0, str(ADAPTER))
    import build_corpus_input_kisti as stage2  # noqa: E402
    from common import retrieval_policy as policy_lib  # noqa: E402

# ------------------------------------------------------------------ 예시 데이터 (임베드)
TOPICS = [
    {"title": "Pseudo Topic A", "slug": "pseudo-a", "domain": "ai", "n_gt_refs": 3, "n_gt_refs_cutoff": 2,
     "retrieval_cutoff_at": "2023-06-01"},
    {"title": "Pseudo Topic B", "slug": "pseudo-b", "domain": "ai", "n_gt_refs": 2, "n_gt_refs_cutoff": 2,
     "retrieval_cutoff_at": "2025-01-01"},
]
POLICY_ROWS = [
    {"topic_id": "pseudo-a", "topic": "Pseudo Topic A", "retrieval_cutoff_at": "2023-06-01", "gt_first_public_at": "2023-06-01",
     "gt_first_public_source": "arxiv:2306.00001 v1", "exclude_ids": ["10.1145/gt-a", "2306.00001"],
     "corpus_snapshot_id": "pseudo sha256:deadbeef", "status": "ok"},
    {"topic_id": "pseudo-b", "topic": "Pseudo Topic B", "retrieval_cutoff_at": "2025-01-01", "gt_first_public_at": "2025-01-01",
     "gt_first_public_source": "crossref created", "exclude_ids": ["10.1145/gt-b"],
     "corpus_snapshot_id": "pseudo sha256:deadbeef", "status": "ok"},
]
# corpus: id → 공개일(sidecar, 문자열 길이 = 정밀도)
DATES = {"2201.00001": "2022-01", "2212.00002": "2022-12", "10.1145/p3": "2023-05-31", "10.1145/p4": "2023-06-01",
         "2407.00005": "2024-07", "10.1145/p6": "2025", "10.1145/gt-a": "2026-01-08"}
# twin 2306.00001 은 view 가 이미 뺐다(corpus 에 없음). GT 본체 gt-a 는 "view 가 놓친" 경우를 흉내내 남겨 둔다.
META = {  # id → (doi, title, abstract, url)  — Stage 2 가 papers.parquet 에서 읽는 것
    "2201.00001": ("10.48550/arxiv.2201.00001", "Early Method One", "abs 1", "http://arxiv.org/abs/2201.00001"),
    "2212.00002": ("10.48550/arxiv.2212.00002", "Late 2022 Method Two", "abs 2", "http://arxiv.org/abs/2212.00002"),
    "10.1145/p3": ("10.1145/p3", "Journal Paper Three", "abs 3", "https://doi.org/10.1145/p3"),
    "10.1145/p4": ("10.1145/p4", "Cutoff-Day Paper Four", "abs 4", "https://doi.org/10.1145/p4"),
    "2407.00005": ("10.48550/arxiv.2407.00005", "Mid 2024 Method Five", "abs 5", "http://arxiv.org/abs/2407.00005"),
    "10.1145/p6": ("10.1145/p6", "Year-Only 2025 Paper Six", "abs 6", "https://doi.org/10.1145/p6"),
    "10.1145/gt-a": ("10.1145/gt-a", "Pseudo Topic A: A Survey", "GT 본체", "https://doi.org/10.1145/gt-a"),
}
TEXTS = {meta[0]: f"Full text of {meta[1]}. " * 200 for meta in META.values()}          # 각 ≈ 6K자 (min_chars 2000 통과)
TEXTS["10.1145/p3"] = "too short"                                                        # Stage 2 too_short 탈락
RANKED = ["10.1145/gt-a", "10.1145/p4", "10.1145/p3", "2212.00002", "2407.00005", "2201.00001", "10.1145/p6"]
GT_REFS = [   # gap_to_80_refs.jsonl 행 (tier == in_view 가 분모)
    {"slug": "pseudo-a", "tier": "in_view", "view_id": "2201.00001", "kisti_doi": "10.48550/arxiv.2201.00001"},
    {"slug": "pseudo-a", "tier": "in_view", "view_id": "2212.00002", "kisti_doi": "10.48550/arxiv.2212.00002"},
    {"slug": "pseudo-a", "tier": "in_view_blocked", "view_id": "10.1145/p4", "kisti_doi": "10.1145/p4"},   # 분모 밖
    {"slug": "pseudo-a", "tier": "post", "view_id": "2407.00005"},
    {"slug": "pseudo-b", "tier": "in_view", "view_id": "2407.00005"},
    {"slug": "pseudo-b", "tier": "in_view", "view_id": "10.1145/p3"},
]
EXCLUDE_KEYS = ["10.1145/gt-a", "10.48550/arxiv.2306.00001", "10.1145/gt-b"]
VIEW_MANIFEST = {"view_name": "pseudo-view", "created_at": "2026-09-14T13:18:56+00:00",
                 "config": {"cutoff_rule": "없음 (topic 정책)"},
                 "files_sha256": {"papers.parquet": "c1a0c6b3" + "0" * 56}, "source": {"body_store_sha256": "b" * 64}}


class FakePolicyDB:
    """AutoSurvey database 의 정책 부분만 흉내: set_policy → 허용 집합(실제 규칙), 검색은 그 안에서 순위 유지."""

    def __init__(self):
        self.allowed, self.sidecar_meta = None, {"created_at": "2026-09-14T13:26:03+00:00", "view": "pseudo-view",
                                                 "view_papers_sha256": "c1a0c6b3" + "0" * 56, "records": len(DATES),
                                                 "by_precision": {"month": 4, "day": 3, "year": 1}}
        self._sidecar_dates = DATES

    def set_policy(self, policy):
        self.allowed = policy_lib.allowed_ids(DATES, policy.cutoff.isoformat(), policy.exclude_ids)
        summ = policy_lib.allowed_summary(DATES, policy.cutoff.isoformat(), policy.exclude_ids)
        return {"policy": policy.to_dict(), "index_total": len(DATES), "allowed": len(self.allowed),
                "allowed_fingerprint_sha256": _fingerprint(self.allowed),
                "excluded": summ["excluded"], "allowed_date_source": {"sidecar": len(self.allowed)},
                "exclude_ids_present_in_index": sorted(i for i in policy.exclude_ids if i in DATES),
                "date_precision_default": "year", "sidecar": self.sidecar_meta}

    def is_allowed(self, pid):
        return self.allowed is None or pid in self.allowed

    def get_ids_from_query(self, query, num):
        return [i for i in RANKED if self.is_allowed(i)][:num]


def _fingerprint(ids):
    import hashlib
    h = hashlib.sha256()
    for i in sorted(ids):
        h.update(str(i).encode() + b"\n")
    return h.hexdigest()


def _autosurvey_policy_mod():
    """AutoSurvey src.retrieval_policy (policy_from_row/select_row). 없으면 None."""
    p = ROOT.parent / "AutoSurvey"
    if not (p / "src" / "retrieval_policy.py").exists():
        return None
    sys.path.insert(0, str(p))
    from src import retrieval_policy as m  # noqa: E402
    return m


def pseudo_survey(topic_title, papers, cite_plan):
    """Stage 3 출력 한 행을 흉내낸다. cite_plan: 본문에 넣을 [n] 인용 번호 목록(범위 밖 번호 허용)."""
    body = (f"# {topic_title}\n\n## Introduction\n\nThis pseudo survey covers the field {cite_plan[:1]}.\n\n"
            f"## Methods\n\nEarly work {cite_plan[1:3]} and later work {cite_plan[3:]} are compared.\n\n"
            f"## Conclusion\n\nWe summarize {cite_plan[:1]}.\n")
    # 리스트 repr 이 곧 [n, m] 인용 표기
    ref_str = "## References\n" + "\n".join(f"[{i}] {p['title']} {p['url']}" for i, p in enumerate(papers, 1)) + "\n"
    out_papers = [{**p, "bibkey": p["title"].lower().replace(" ", "_")} for p in papers]
    return {"title": topic_title, "cost_time": "0:01:00", "block_cycle_count": 1, "conv_layer": 6,
            "outline_eval_score": 8.0, "cite_ratio": round(len({n for n in cite_plan if 1 <= n <= len(papers)}) / max(1, len(papers)), 3),
            "outline": "# Outline", "content": body + "\n" + ref_str, "ref_str": ref_str, "papers": out_papers}


FAKE_LOG = "\n".join([
    "2026-09-16-10:00:00.000 [INFO] [__main__:77]", "Start pipeline with args: Namespace(block_count=1)",
    "2026-09-16-10:00:01.000 [INFO] [request.openai:70]", "OpenRouter cost: $0.010000 (session total $0.0100 over 1 calls)",
    "2026-09-16-10:00:01.001 [INFO] [request.openai:80]", "completion usage: prompt_tokens=1000 completion_tokens=500 finish_reason=stop",
    "2026-09-16-10:00:02.000 [INFO] [request.openai:70]", "OpenRouter cost: $0.020000 (session total $0.0300 over 2 calls)",
    "2026-09-16-10:00:02.001 [INFO] [request.openai:80]", "completion usage: prompt_tokens=2000 completion_tokens=700 finish_reason=stop",
    "2026-09-16-10:01:00.000 [INFO] [src.pipeline:1]", "save_survey done", ""])


@unittest.skipUnless(HAVE_ADAPTER, "kisti_data adapter not present")
class PseudoSurveyEndToEndTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy_mod = _autosurvey_policy_mod()
        cls.tmp = tempfile.TemporaryDirectory()
        d = cls.d = Path(cls.tmp.name)
        cls.pools = cls._stage1(d)
        cls.inputs, cls.input_manifest = cls._stage2(d, cls.pools)
        cls.outputs = cls._stage3(d, cls.inputs)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ---------------------------------------------------------- 단계
    @classmethod
    def _stage1(cls, d):
        if cls.policy_mod is None:
            raise unittest.SkipTest("AutoSurvey src/retrieval_policy.py 없음")
        rows = rp.retrieve_topics(FakePolicyDB(), TOPICS, retrieve_num=10, exclude={"10.1145/gt-a", "2306.00001"},
                                  policy_rows=POLICY_ROWS, policy_mod=cls.policy_mod, log=lambda s: None)
        with open(d / "pools.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        with open(d / "pools.jsonl.manifest.json", "w") as f:
            json.dump({"topic_policy_file": "embedded", "topic_policy_sha256": "0" * 64,
                       "sidecar": rows[0]["retrieval_policy"]["sidecar"]}, f)
        return rows

    @classmethod
    def _stage2(cls, d, pools):
        inputs, stats = [], []
        for pool, topic, row in zip(pools, TOPICS, POLICY_ROWS):
            ranked = pool["arxiv_id_ranked"]
            blocked = sum(1 for i in ranked if not policy_lib.is_allowed(DATES.get(i), row["retrieval_cutoff_at"]))
            papers, stat = stage2.select_papers(ranked, topic["n_gt_refs_cutoff"], META, TEXTS.get, 2000, 250_000,
                                                exclude={e.lower() for e in row["exclude_ids"]})
            inputs.append({"title": topic["title"], "papers": papers})
            stats.append({"title": topic["title"], "quota": topic["n_gt_refs_cutoff"], "quota_field": "n_gt_refs_cutoff",
                          "resolved": len(papers), **stat,
                          "retrieval_policy": {"topic_id": row["topic_id"], "retrieval_cutoff_at": row["retrieval_cutoff_at"],
                                               "exclude_ids": row["exclude_ids"], "pool_in": len(ranked),
                                               "pool_allowed": len(ranked) - blocked, "blocked_after_cutoff": blocked,
                                               "blocked_no_date": 0,
                                               "allowed_total": pool["retrieval_policy"]["allowed"]}})
        with open(d / "input.jsonl", "w") as f:
            for r in inputs:
                f.write(json.dumps(r) + "\n")
        manifest = {"view": "pseudo-view", "view_manifest": VIEW_MANIFEST, "quota_field": "n_gt_refs_cutoff",
                    "topic_policy_file": "embedded", "paper_dates": {"created_at": "2026-09-14T13:26:03+00:00"},
                    "topics": stats}
        with open(d / "input.jsonl.manifest.json", "w") as f:
            json.dump(manifest, f)
        return inputs, manifest

    @classmethod
    def _stage3(cls, d, inputs):
        outs = [pseudo_survey(inputs[0]["title"], inputs[0]["papers"], [1, 2, 1, 2]),
                pseudo_survey(inputs[1]["title"], inputs[1]["papers"], [1, 2, 9, 1])]   # [9] 는 범위 밖 인용
        with open(d / "output.jsonl", "w") as f:
            for r in outs:
                f.write(json.dumps(r) + "\n")
        (d / "stage3.log").write_text(FAKE_LOG)
        return outs

    # ---------------------------------------------------------- Stage 1
    def test_stage1_pool_is_inside_allowed_set(self):
        a, b = self.pools
        # A: cutoff 2023-06-01 → 2022-01, 2022-12, 2023-05-31 허용; 당일(p4)·2024-07·2025·GT 둘 제외
        self.assertEqual(a["arxiv_id_ranked"], ["10.1145/p3", "2212.00002", "2201.00001"])
        self.assertEqual(a["retrieval_policy"]["allowed"], 3)
        self.assertEqual(a["retrieval_policy"]["retrieval_cutoff_at"], "2023-06-01")
        self.assertEqual(a["retrieval_policy"]["exclude_ids_present_in_index"], ["10.1145/gt-a"])   # view 가 놓친 GT → 선택자가 차단
        self.assertEqual(len(a["retrieval_policy"]["allowed_fingerprint_sha256"]), 64)
        # B: cutoff 2025-01-01 → 2025(연 단위, 상한 12-31) 제외, GT-a 는 B 의 exclude 가 아니지만 2026 이라 날짜로 제외
        self.assertEqual(b["arxiv_id_ranked"], ["10.1145/p4", "10.1145/p3", "2212.00002", "2407.00005", "2201.00001"])
        self.assertNotEqual(a["retrieval_policy"]["allowed_fingerprint_sha256"], b["retrieval_policy"]["allowed_fingerprint_sha256"])

    def test_stage1_leak_gate(self):
        with self.assertRaises(RuntimeError):     # 정책 없이 돌면 view 가 놓친 GT 본체가 검색되고 exclude 게이트가 예외를 낸다
            rp.retrieve_topics(FakePolicyDB(), TOPICS[:1], 10, exclude={"10.1145/gt-a"}, log=lambda s: None)

    # ---------------------------------------------------------- Stage 2
    def test_stage2_quota_and_gates(self):
        a, b = self.inputs
        self.assertEqual([p["arxiv_id"] for p in a["papers"]], ["2212.00002", "2201.00001"])   # p3 는 too_short
        self.assertEqual(self.input_manifest["topics"][0]["too_short"], 1)
        self.assertEqual(self.input_manifest["topics"][0]["retrieval_policy"]["blocked_after_cutoff"], 0)
        self.assertEqual([p["arxiv_id"] for p in b["papers"]], ["10.1145/p4", "2212.00002"])   # B 에서는 p4(2023-06-01) 허용
        self.assertTrue(all(len(p["txt"]) >= 2000 for p in a["papers"] + b["papers"]))

    # ---------------------------------------------------------- 검사: 정상 출력
    def test_leak_check_clean_output(self):
        terms = lc.search_terms(EXCLUDE_KEYS)
        titles = {"gt:pseudo-a": "Pseudo Topic A: A Survey"}
        hits = lc.find_leaks(self.outputs, terms, titles)
        self.assertEqual([h for h in hits if h["kind"] in ("id_hit", "title_hit")], [])

    def test_ref_time_check_clean_output(self):
        a = rtc.check_record(self.outputs[0], POLICY_ROWS[0], DATES, policy_lib.is_allowed)
        self.assertEqual(a["listed"], {"allowed": 2, "time_violation": 0, "excluded_id": 0, "no_date": 0, "not_in_corpus": 0})
        self.assertEqual(a["n_cited"], 2)
        self.assertEqual(a["problems"], [])
        b = rtc.check_record(self.outputs[1], POLICY_ROWS[1], DATES, policy_lib.is_allowed)
        self.assertEqual(b["listed"]["allowed"], 2)
        self.assertEqual(b["cited_out_of_range"], [9])          # 존재하지 않는 [9] 인용 = 허위 인용 신호

    def test_pool_and_input_ceiling(self):
        res = pc.compute_ceilings(TOPICS, self.pools, GT_REFS, self.inputs)
        a, b = res["topics"]
        self.assertEqual((a["n_gt_in_view"], a["pool_hits"], a["input_hits"]), (2, 2, 2))   # in_view_blocked 는 분모 밖
        self.assertEqual(a["pool_ceiling"], 1.0)
        self.assertNotIn("denominator_mismatch", a)
        self.assertEqual((b["n_gt_in_view"], b["pool_hits"], b["input_hits"]), (2, 2, 0))
        self.assertEqual(res["denominator_mismatches"], 0)

    def test_run_manifest_end_to_end(self):
        out = self.d / "manifest.json"
        argv = ["run_manifest.py", "--log", str(self.d / "stage3.log"), "--output_jsonl", str(self.d / "output.jsonl"),
                "--input_jsonl", str(self.d / "input.jsonl"), "--env_file", str(self.d / "no.env"),
                "--config", str(self.d / "no.json"), "--run_name", "pseudo", "--out", str(out)]
        old = sys.argv
        try:
            sys.argv = argv
            with redirect_stdout(io.StringIO()) as buf:
                rm.main()
        finally:
            sys.argv = old
        with open(out) as f:
            m = json.load(f)
        self.assertEqual(m["corpus"]["version"], "c1a0c6b3 / 2026-09-14T13:18:56+00:00")
        self.assertEqual(m["retrieval_policy"]["mode"], "topic_cutoff")
        self.assertEqual(m["retrieval_policy"]["topics_with_policy"], 2)
        self.assertEqual(m["retrieval_policy"]["stage2_blocked_total"], 0)
        self.assertEqual(m["retrieval_policy"]["stage1_leaks"], [])
        t0 = m["topics"][0]
        self.assertEqual(t0["retrieval_policy"]["retrieval_cutoff_at"], "2023-06-01")
        self.assertEqual(t0["retrieval_policy"]["stage1"]["allowed"], 3)
        self.assertEqual(len(t0["retrieval_policy"]["stage1"]["allowed_fingerprint_sha256"]), 64)
        self.assertEqual(t0["retrieval_policy"]["stage2"]["blocked_after_cutoff"], 0)
        self.assertEqual(t0["n_refs_cited"], 2)
        self.assertEqual(m["log"]["calls"], 2)
        self.assertAlmostEqual(m["log"]["total_cost_usd"], 0.03)
        self.assertIn("policy=topic_cutoff", buf.getvalue())

    # ---------------------------------------------------------- 검사: 오염된 출력이 잡히는가
    def test_tampered_output_time_violation_vs_fabrication(self):
        rec = json.loads(json.dumps(self.outputs[0]))
        rec["papers"].append({**dict(zip(("title", "url"), META["2407.00005"][1:4:2])), "arxiv_id": "2407.00005"})   # cutoff 이후 실재 논문
        rec["papers"].append({"title": "Made Up Paper", "url": "http://x/none", "arxiv_id": "fake-id"})           # corpus 밖
        rec["content"] = rec["content"].replace("## Conclusion", "See also [3] and [4].\n\n## Conclusion")
        r = rtc.check_record(rec, POLICY_ROWS[0], DATES, policy_lib.is_allowed)
        kinds = {(p["ref"], p["kind"], p["cited"]) for p in r["problems"]}
        self.assertIn((3, "time_violation", True), kinds)
        self.assertIn((4, "not_in_corpus", True), kinds)
        self.assertEqual(r["cited"]["time_violation"], 1)
        self.assertEqual(r["cited"]["not_in_corpus"], 1)

    def test_tampered_output_gt_leak(self):
        rec = json.loads(json.dumps(self.outputs[0]))
        rec["papers"].append({"title": META["10.1145/gt-a"][1], "url": META["10.1145/gt-a"][3], "arxiv_id": "10.1145/gt-a"})
        hits = lc.find_leaks([rec], lc.search_terms(EXCLUDE_KEYS), {"gt:pseudo-a": "Pseudo Topic A: A Survey"})
        self.assertTrue(any(h["kind"] == "id_hit" and h["term"] == "10.1145/gt-a" for h in hits))
        self.assertTrue(any(h["kind"] == "title_hit" for h in hits))
        r = rtc.check_record(rec, POLICY_ROWS[0], DATES, policy_lib.is_allowed)
        self.assertEqual(r["listed"]["excluded_id"], 1)

    def test_stage1_without_policy_is_flagged_by_stage2_and_manifest(self):
        """정책 없이 뽑은 pool(구 규약) → Stage 2 가 blocked 를 세고, run_manifest 가 stage1_leak 을 표시한다."""
        rows = rp.retrieve_topics(FakePolicyDB(), TOPICS[:1], 10, exclude=set(), log=lambda s: None)
        ranked = rows[0]["arxiv_id_ranked"]
        self.assertIsNone(rows[0]["retrieval_policy"])
        blocked = sum(1 for i in ranked if not policy_lib.is_allowed(DATES.get(i), "2023-06-01"))
        self.assertEqual(blocked, 4)     # gt-a(2026), p4(당일), 2407, p6
        merged = rm.merge_policy(None, {"topic_id": "pseudo-a", "retrieval_cutoff_at": "2023-06-01",
                                        "blocked_after_cutoff": blocked, "blocked_no_date": 0, "allowed_total": 3})
        self.assertIn("stage1_leak", merged)


if __name__ == "__main__":
    unittest.main()
