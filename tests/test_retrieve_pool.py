"""scripts/retrieve_pool.py — 가짜 DB·정책 모듈로 topic 별 선택자 적용·게이트 검증 (faiss·GPU 불필요)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import retrieve_pool as rp  # noqa: E402

TOPICS = [{"title": "Topic A", "slug": "a"}, {"title": "Topic B", "slug": "b"}]
POLICY_ROWS = [
    {"topic_id": "a", "topic": "Topic A", "retrieval_cutoff_at": "2023-01-01", "exclude_ids": ["gt-a"], "status": "ok"},
    {"topic_id": "b", "topic": "Topic B (다른 제목)", "retrieval_cutoff_at": "2025-06-01", "exclude_ids": [], "status": "ok"},
]
# id → 공개일. 검색은 항상 같은 순위를 돌려주고, 선택자는 허용 집합으로 자른다.
DATES = {"p1": "2022-05", "p2": "2022-12-31", "p3": "2023-01-01", "p4": "2025-07", "gt-a": "2021"}
RANKED = ["p3", "p1", "gt-a", "p4", "p2"]


class FakePolicy:
    def __init__(self, row):
        self.row = row
        self.cutoff = row["retrieval_cutoff_at"]
        self.exclude_ids = frozenset(row["exclude_ids"])

    def to_dict(self):
        return {"topic_id": self.row["topic_id"], "topic": self.row["topic"],
                "retrieval_cutoff_at": self.cutoff, "exclude_ids": sorted(self.exclude_ids), "status": "ok"}


class FakePolicyMod:
    @staticmethod
    def select_row(rows, topic_id=None):
        for r in rows:
            if r["topic_id"] == topic_id:
                return r
        raise KeyError(topic_id)

    @staticmethod
    def policy_from_row(row):
        return FakePolicy(row)


class FakeDB:
    """set_policy → 허용 집합; get_ids_from_query → 허용 집합 안에서 순위 유지."""

    def __init__(self):
        self.allowed = None
        self.set_calls = []
        self._sidecar_dates = DATES
        self.sidecar_meta = {"created_at": "t", "view": "v", "view_papers_sha256": "s", "records": 5,
                             "by_precision": {"month": 2, "day": 2, "year": 1}}

    def set_policy(self, policy):
        self.set_calls.append(policy.cutoff)
        # 상한 < cutoff 를 흉내: 문자열 앞 7자 비교로 충분한 테스트 데이터
        self.allowed = {i for i, d in DATES.items() if i not in policy.exclude_ids and d[:7] < policy.cutoff[:7]}
        return {"policy": policy.to_dict(), "index_total": 5, "allowed": len(self.allowed),
                "allowed_fingerprint_sha256": "f" * 64, "excluded": {"excluded_id": 1},
                "allowed_date_source": {"sidecar": len(self.allowed)}, "exclude_ids_present_in_index": [],
                "date_precision_default": "year", "sidecar": self.sidecar_meta}

    def is_allowed(self, pid):
        return self.allowed is None or pid in self.allowed

    def get_ids_from_query(self, query, num):
        ids = RANKED if self.allowed is None else [i for i in RANKED if i in self.allowed]
        return ids[:num]


class RetrieveTopicsTest(unittest.TestCase):
    def test_policy_applied_per_topic(self):
        db = FakeDB()
        logs = []
        rows = rp.retrieve_topics(db, TOPICS, 10, exclude=set(), policy_rows=POLICY_ROWS,
                                  policy_mod=FakePolicyMod, log=logs.append)
        self.assertEqual(db.set_calls, ["2023-01-01", "2025-06-01"])
        a, b = rows
        self.assertEqual(a["arxiv_id_ranked"], ["p1", "p2"])                # p3 는 cutoff 당일, gt-a 는 exclude_ids
        self.assertEqual(b["arxiv_id_ranked"], ["p3", "p1", "gt-a", "p2"])  # p4(2025-07) 만 cutoff 이후
        self.assertEqual(a["retrieval_policy"]["topic_id"], "a")
        self.assertEqual(a["retrieval_policy"]["retrieval_cutoff_at"], "2023-01-01")
        self.assertEqual(a["retrieval_policy"]["allowed"], 2)
        self.assertEqual(a["retrieval_policy"]["sidecar"]["records"], 5)
        self.assertEqual(rows[0]["retrieve_num"], 10)
        self.assertTrue(any("≠ topics.jsonl title" in l for l in logs))   # topic 문자열 불일치 경고

    def test_leak_gate_raises(self):
        db = FakeDB()
        with self.assertRaises(RuntimeError):
            rp.retrieve_topics(db, TOPICS[1:], 10, exclude={"gt-a"}, policy_rows=POLICY_ROWS, policy_mod=FakePolicyMod,
                               log=lambda s: None)

    def test_without_policy(self):
        db = FakeDB()
        rows = rp.retrieve_topics(db, TOPICS, 3, log=lambda s: None)
        self.assertEqual(rows[0]["arxiv_id_ranked"], ["p3", "p1", "gt-a"])
        self.assertIsNone(rows[0]["retrieval_policy"])
        self.assertEqual(db.set_calls, [])

    def test_missing_slug(self):
        with self.assertRaises(KeyError):
            rp.retrieve_topics(FakeDB(), [{"title": "X"}], 3, policy_rows=POLICY_ROWS, policy_mod=FakePolicyMod,
                               log=lambda s: None)

    def test_policy_block_shape(self):
        blk = rp.policy_block(FakeDB().set_policy(FakePolicy(POLICY_ROWS[0])))
        for k in ("topic_id", "retrieval_cutoff_at", "exclude_ids", "allowed", "allowed_fingerprint_sha256", "sidecar"):
            self.assertIn(k, blk)


if __name__ == "__main__":
    unittest.main()
