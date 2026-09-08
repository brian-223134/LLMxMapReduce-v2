"""adapter/llmxmapreduce/build_corpus_input_kisti.py 의 select_papers — FullText 를 mock 해서 게이트 검증.

adapter 가 없는 머신에서는 건너뛴다 (KISTI_DATA_ROOT, 기본 /data2/chanjoong/kisti_data).
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ADAPTER = Path(os.environ.get("KISTI_DATA_ROOT", "/data2/chanjoong/kisti_data")) / "adapter"
HAVE_ADAPTER = (ADAPTER / "llmxmapreduce" / "build_corpus_input_kisti.py").exists()
if HAVE_ADAPTER:
    sys.path.insert(0, str(ADAPTER / "llmxmapreduce"))
    import build_corpus_input_kisti as b  # noqa: E402

META = {
    "2301.00001": ("10.48550/arxiv.2301.00001", "P1", "abs1", "http://arxiv.org/abs/2301.00001"),
    "10.1145/a": ("10.1145/a", "P2", None, "https://doi.org/10.1145/a"),
    "short": ("doi:short", "P3", "abs3", "u3"),
    "long": ("doi:long", "P4", "abs4", "u4"),
    "nobody": ("doi:nobody", "P5", "abs5", "u5"),
    "2301.00006": ("10.48550/arxiv.2301.00006", "P6", "abs6", "u6"),
}
TEXTS = {"10.48550/arxiv.2301.00001": "x" * 5000, "10.1145/a": "y" * 3000, "doi:short": "z" * 100,
         "doi:long": "w" * 300_000, "doi:nobody": None, "10.48550/arxiv.2301.00006": "v" * 4000}
RANKED = ["2301.00001", "missing-meta", "10.1145/a", "short", "long", "nobody", "2301.00006", "never-walked"]


@unittest.skipUnless(HAVE_ADAPTER, "kisti_data adapter not present")
class SelectPapersTest(unittest.TestCase):
    def test_gates_and_quota(self):
        papers, stat = b.select_papers(RANKED, quota=3, meta=META, get_text=TEXTS.get,
                                       min_chars=2000, max_chars=250_000)
        self.assertEqual([p["arxiv_id"] for p in papers], ["2301.00001", "10.1145/a", "2301.00006"])
        self.assertEqual(stat["missing_meta"], 1)
        self.assertEqual(stat["too_short"], 1)
        self.assertEqual(stat["too_long"], 1)
        self.assertEqual(stat["no_body"], 1)
        self.assertEqual(stat["walked"], 7)          # quota 를 채우면 멈춘다 (never-walked 는 안 봄)
        self.assertEqual(stat["max_len"], 5000)
        self.assertEqual(stat["total_chars"], 12000)
        self.assertEqual(papers[1]["abstract"], "")   # None → ""
        self.assertEqual(papers[0]["url"], "http://arxiv.org/abs/2301.00001")
        self.assertEqual(set(papers[0]), {"title", "abstract", "url", "txt", "arxiv_id"})

    def test_max_chars_zero_disables_cap(self):
        papers, stat = b.select_papers(RANKED, quota=10, meta=META, get_text=TEXTS.get,
                                       min_chars=2000, max_chars=0)
        self.assertIn("long", [p["arxiv_id"] for p in papers])
        self.assertEqual(stat["too_long"], 0)
        self.assertEqual(stat["walked"], len(RANKED))  # quota 미달이면 끝까지 순회

    def test_exclude_ids_are_skipped_and_counted(self):
        papers, stat = b.select_papers(RANKED, quota=2, meta=META, get_text=TEXTS.get,
                                       exclude={"2301.00001"})
        self.assertEqual([p["arxiv_id"] for p in papers], ["10.1145/a", "2301.00006"])
        self.assertEqual(stat["excluded"], 1)

    def test_load_exclude_ids_parses_comments_and_case(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("# view 가 놓친 GT\n2507.16731   # twin\n\n10.1109/COMST.2025.3648785\n")
            name = f.name
        self.assertEqual(b.load_exclude_ids(name), {"2507.16731", "10.1109/comst.2025.3648785"})
        self.assertEqual(b.load_exclude_ids(None), set())

    def test_defaults(self):
        self.assertEqual(b.DEFAULT_MIN_CHARS, 2000)
        self.assertEqual(b.DEFAULT_MAX_CHARS, 250_000)


if __name__ == "__main__":
    unittest.main()
