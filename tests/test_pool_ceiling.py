"""scripts/pool_ceiling.py — 합성 pool/topic/GT 로 ceiling 계산 검증."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pool_ceiling as pc  # noqa: E402

TOPICS = [{"title": "Topic A", "slug": "a", "n_gt_refs": 3},
          {"title": "Topic B", "slug": "b", "n_gt_refs": 2},
          {"title": "Topic C (no pool)", "slug": "c", "n_gt_refs": 1}]
GT_REFS = [
    {"slug": "a", "tier": "in_view", "kisti_doi": "10.48550/arxiv.2301.00001v2"},   # → 2301.00001
    {"slug": "a", "tier": "in_view", "kisti_doi": "10.1145/ABC.123"},               # → 10.1145/abc.123
    {"slug": "a", "tier": "in_view", "kisti_doi": "10.48550/arxiv.2301.00003"},
    {"slug": "a", "tier": "t1_arxiv", "doi": "10.48550/arXiv.2301.00009"},          # view 밖 → 분모 제외
    {"slug": "b", "tier": "in_view", "kisti_doi": "10.48550/arxiv.2302.00001"},
    {"slug": "b", "tier": "in_view", "doi": "10.48550/arXiv.2302.00002"},           # kisti_doi 없으면 doi
    {"slug": "c", "tier": "in_view", "kisti_doi": "10.48550/arxiv.2303.00001"},
]
POOLS = [{"title": "Topic A", "arxiv_id_ranked": ["2301.00001", "10.1145/abc.123", "9999.99999", "2301.00009"]},
         {"title": "Topic B", "arxiv_id_ranked": ["2302.00002", "x"]}]
INPUTS = [{"title": "Topic A", "papers": [{"arxiv_id": "2301.00001"}, {"arxiv_id": "9999.99999"}]},
          {"title": "Topic B", "papers": [{"arxiv_id": "x"}]}]


class PoolCeilingTest(unittest.TestCase):
    def test_gt_ids_by_slug_applies_rule_b_and_tier(self):
        gt = pc.gt_ids_by_slug(GT_REFS)
        self.assertEqual(gt["a"], {"2301.00001", "10.1145/abc.123", "2301.00003"})
        self.assertEqual(gt["b"], {"2302.00001", "2302.00002"})

    def test_pool_and_input_ceilings(self):
        res = pc.compute_ceilings(TOPICS, POOLS, GT_REFS, INPUTS)
        by = {r["slug"]: r for r in res["topics"]}
        a, b, c = by["a"], by["b"], by["c"]
        self.assertEqual((a["n_gt_in_view"], a["pool_size"], a["pool_hits"]), (3, 4, 2))
        self.assertAlmostEqual(a["pool_ceiling"], 2 / 3, places=3)
        self.assertEqual((a["input_size"], a["input_hits"]), (2, 1))
        self.assertAlmostEqual(a["input_ceiling"], 1 / 3, places=3)
        self.assertEqual((b["pool_hits"], b["pool_ceiling"]), (1, 0.5))
        self.assertEqual((b["input_hits"], b["input_ceiling"]), (0, 0.0))
        self.assertIsNone(c["pool_ceiling"])   # pool 없음
        self.assertIsNone(c["input_ceiling"])
        self.assertAlmostEqual(res["mean_pool_ceiling"], (2 / 3 + 0.5) / 2, places=3)
        self.assertEqual(res["n_topics"], 3)

    def test_without_inputs(self):
        res = pc.compute_ceilings(TOPICS, POOLS, GT_REFS)
        self.assertTrue(all(r["input_ceiling"] is None for r in res["topics"]))
        self.assertIsNone(res["mean_input_ceiling"])


if __name__ == "__main__":
    unittest.main()
