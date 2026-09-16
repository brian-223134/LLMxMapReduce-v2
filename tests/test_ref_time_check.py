"""scripts/ref_time_check.py — 합성 출력/정책/sidecar 로 시간 범위 위반·허위 인용 구분 검증."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ref_time_check as rtc  # noqa: E402

try:
    RP = rtc._policy_lib()
except Exception:   # adapter 가 없는 환경
    RP = None

DATES = {"p1": "2022-05", "p2": "2022-12-31", "p3": "2023-01-01", "p4": "2024", "gt": "2021-03", "nd": ""}
POLICY = {"topic_id": "t", "retrieval_cutoff_at": "2023-01-01", "exclude_ids": ["GT"]}
PAPERS = [{"arxiv_id": i, "title": f"T{i}", "url": f"http://x/{i}"} for i in ("p1", "p2", "p3", "p4", "gt", "nd", "zz")]
CONTENT = "Intro [1] and [3, 5]. More [7] and [9].\n\n## References\n" + "\n".join(
    f"[{n}] T{p['arxiv_id']} http://x/{p['arxiv_id']}" for n, p in enumerate(PAPERS, 1)) + "\n[8] Made Up Paper http://x/none\n"
REC = {"title": "Topic T", "papers": PAPERS, "content": CONTENT, "ref_str": CONTENT.split("\n\n")[-1]}


@unittest.skipIf(RP is None, "kisti_data/adapter 없음")
class RefTimeCheckTest(unittest.TestCase):
    def test_verdicts(self):
        r = rtc.check_record(REC, POLICY, DATES, RP.is_allowed)
        self.assertEqual(r["policy"], "topic_cutoff")
        self.assertEqual(r["listed"], {"allowed": 2, "time_violation": 2, "excluded_id": 1, "no_date": 1, "not_in_corpus": 1})
        # cited: [1]=p1 allowed, [3]=p3 당일→violation, [5]=gt excluded, [7]=zz not_in_corpus, [9] 범위 밖
        self.assertEqual(r["cited"], {"allowed": 1, "time_violation": 1, "excluded_id": 1, "no_date": 0, "not_in_corpus": 1})
        self.assertEqual(r["unlisted_refs"], 1)
        self.assertEqual(r["cited_out_of_range"], [9])
        kinds = {(p["ref"], p["kind"], p["cited"]) for p in r["problems"]}
        self.assertIn((3, "time_violation", True), kinds)
        self.assertIn((4, "time_violation", False), kinds)
        self.assertIn((5, "excluded_id", True), kinds)
        self.assertIn((8, "unlisted_ref", False), kinds)

    def test_no_policy_row(self):
        r = rtc.check_record(REC, None, DATES, RP.is_allowed)
        self.assertEqual(r["policy"], "none")
        self.assertEqual(r["listed"]["time_violation"], 0)
        self.assertEqual(r["listed"]["allowed"], 5)          # 날짜 있는 5편(gt 포함, exclude 없음), no_date 1, not_in_corpus 1
        self.assertEqual(r["listed"]["excluded_id"], 0)

    def test_input_record_counts_all_as_cited(self):
        r = rtc.check_record({"title": "Topic T", "papers": PAPERS[:3]}, POLICY, DATES, RP.is_allowed)
        self.assertEqual(r["n_cited"], 3)
        self.assertEqual(r["cited"]["time_violation"], 1)

    def test_parse_ref_str(self):
        refs = rtc.parse_ref_str("## References\n[1] A title http://a\n[2] No url\n")
        self.assertEqual(refs, [{"n": 1, "title": "A title", "url": "http://a"}, {"n": 2, "title": "No url", "url": None}])


if __name__ == "__main__":
    unittest.main()
