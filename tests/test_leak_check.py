"""scripts/leak_check.py — 합성 레코드로 id/제목 누수 탐지 검증."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import leak_check as lc  # noqa: E402

KEYS = ["10.1145/3777411", "10.48550/arxiv.2211.01671", "10.1109/comst.2026.3660854"]
TITLES = {"gt:instruction-tuning-llms": "Instruction Tuning for Large Language Models: A Survey",
          "twin:2211.01671": "Physically Adversarial Attacks and Defenses in Computer Vision: A Surv"}


class SearchTermsTest(unittest.TestCase):
    def test_terms_include_doi_and_arxiv_base_id(self):
        terms = lc.search_terms(KEYS)
        self.assertEqual(terms["10.1145/3777411"], "10.1145/3777411")
        self.assertEqual(terms["2211.01671"], "10.48550/arxiv.2211.01671")
        self.assertIn("10.48550/arxiv.2211.01671", terms)
        self.assertNotIn("", terms)


class FindLeaksTest(unittest.TestCase):
    def setUp(self):
        self.terms = lc.search_terms(KEYS)

    def test_clean_records_have_no_hits(self):
        recs = [{"title": "T", "papers": [{"arxiv_id": "2301.00001", "url": "http://arxiv.org/abs/2301.00001",
                                           "title": "Some unrelated paper"}],
                 "content": "Body [1].\n\n## References\n[1] Some unrelated paper http://arxiv.org/abs/2301.00001\n"}]
        self.assertEqual(lc.find_leaks(recs, self.terms, TITLES), [])

    def test_twin_id_in_pool_is_id_hit(self):
        recs = [{"title": "T", "papers": [{"arxiv_id": "2211.01671", "url": "http://arxiv.org/abs/2211.01671",
                                           "title": "whatever"}]}]
        hits = lc.find_leaks(recs, self.terms, {})
        self.assertTrue(any(h["kind"] == "id_hit" and h["term"] == "10.48550/arxiv.2211.01671" for h in hits))

    def test_gt_doi_in_refs_is_id_hit(self):
        recs = [{"title": "T", "papers": [], "ref_str": "## References\n[1] X https://doi.org/10.1145/3777411\n"}]
        hits = lc.find_leaks(recs, self.terms, {})
        self.assertEqual([(h["kind"], h["where"]) for h in hits], [("id_hit", "ref_str")])

    def test_gt_title_in_pool_is_title_hit_and_in_body_is_mention(self):
        recs = [{"title": "T",
                 "papers": [{"arxiv_id": "10.1145/x", "url": "https://doi.org/10.1145/x",
                             "title": "Instruction Tuning for Large Language Models: A Survey"}],
                 "content": "As discussed in Instruction Tuning for Large Language Models: A Survey, ..."}]
        hits = lc.find_leaks(recs, self.terms, TITLES)
        kinds = sorted(h["kind"] for h in hits)
        self.assertEqual(kinds, ["title_hit", "title_mention"])

    def test_truncated_twin_title_matches_by_prefix(self):
        recs = [{"title": "T", "papers": [{"arxiv_id": "x", "url": "", "title":
                 "Physically Adversarial Attacks and Defenses in Computer Vision: A Survey"}]}]
        hits = lc.find_leaks(recs, self.terms, TITLES)
        self.assertTrue(any(h["kind"] == "title_hit" and h["term"] == "twin:2211.01671" for h in hits))

    def test_short_terms_do_not_match_inside_text(self):
        # 짧은 DOI 조각이 본문에 우연히 들어가도 9자 미만 검색어는 문자열 검색에 쓰지 않는다
        terms = lc.search_terms(["10.1/ab"])
        recs = [{"title": "T", "papers": [], "content": "see 10.1/ab here"}]
        self.assertEqual(lc.find_leaks(recs, terms, {}), [])


class LoadersTest(unittest.TestCase):
    def test_load_gt_titles_and_twin_titles(self):
        with tempfile.TemporaryDirectory() as d:
            cdir = Path(d) / "ai" / "instruction-tuning-llms"
            cdir.mkdir(parents=True)
            (cdir / "candidate.yaml").write_text(
                'topic: Instruction Tuning for Large Language Models\ndomain: ai\ngt:\n  arxiv_id: null\n'
                '  doi: "10.1145/3777411"\n  title: "Instruction Tuning for Large Language Models: A Survey"\n'
                '  published: "2026-01-08"\nnotes: "x"\n', encoding="utf-8")
            readme = Path(d) / "README.md"
            readme.write_text(
                "## 4. GT 누수\n| key | doi | year | title |\n|---|---|---|---|\n"
                "| gt:ai/x | `10.1/x` | 2026 | GT row |\n"
                "| twin:2211.01671 | `10.48550/arxiv.2211.01671` | 2022 | Physically Adversarial Attacks and Defenses in Computer Vision: A Surv |\n",
                encoding="utf-8")
            topics = [{"title": "Instruction Tuning for Large Language Models", "domain": "ai",
                       "slug": "instruction-tuning-llms"},
                      {"title": "missing", "domain": "ai", "slug": "nope"}]
            gt = lc.load_gt_titles(d, topics)
            tw = lc.load_twin_titles(readme)
        self.assertEqual(gt, {"instruction-tuning-llms": "Instruction Tuning for Large Language Models: A Survey"})
        self.assertEqual(tw, {"2211.01671": "Physically Adversarial Attacks and Defenses in Computer Vision: A Surv"})

    def test_missing_readme_is_empty(self):
        self.assertEqual(lc.load_twin_titles("/nonexistent/README.md"), {})


if __name__ == "__main__":
    unittest.main()
