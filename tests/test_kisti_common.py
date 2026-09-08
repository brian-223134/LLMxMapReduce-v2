"""scripts/kisti_common.py — id 규칙 B, 로그 파서, .env 파서, 본문 통계."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import kisti_common as kc  # noqa: E402


class IdRuleTest(unittest.TestCase):
    def test_arxiv_doi_to_base_id(self):
        self.assertEqual(kc.doi_to_id("10.48550/arXiv.2211.01671v2"), "2211.01671")
        self.assertEqual(kc.doi_to_id("10.48550/arxiv.2502.04602"), "2502.04602")

    def test_plain_doi_is_lowercased(self):
        self.assertEqual(kc.doi_to_id("10.1145/3777411"), "10.1145/3777411")
        self.assertEqual(kc.doi_to_id(" 10.1109/COMST.2026.3660854 "), "10.1109/comst.2026.3660854")

    def test_is_arxiv_id(self):
        self.assertTrue(kc.is_arxiv_id("2211.01671"))
        self.assertTrue(kc.is_arxiv_id("2211.01671v3"))
        self.assertTrue(kc.is_arxiv_id("cs.CL/0701001"))
        self.assertFalse(kc.is_arxiv_id("10.1145/3777411"))
        self.assertFalse(kc.is_arxiv_id(""))
        self.assertFalse(kc.is_arxiv_id(None))


class TextHelpersTest(unittest.TestCase):
    def test_norm_title(self):
        self.assertEqual(kc.norm_title("Instruction Tuning for LLMs: A Survey!"), "instruction tuning for llms a survey")

    def test_split_and_cite(self):
        content = "# T\n\n## 1 Intro\nA claim [1,2]. Another [3].\n\n## References\n[1] x\n[2] y\n[3] z [4]\n"
        body, refs = kc.split_references(content)
        self.assertIn("## 1 Intro", body)
        self.assertNotIn("[1] x", body)
        self.assertIn("[1] x", refs)
        self.assertEqual(kc.cited_indices(content), {1, 2, 3})
        self.assertEqual(kc.count_headings(content), 2)
        self.assertEqual(kc.content_words(content), len("# T ## 1 Intro A claim [1,2]. Another [3].".split()))

    def test_percentile(self):
        self.assertIsNone(kc.percentile([], 0.5))
        self.assertEqual(kc.percentile([1, 2, 3, 4, 5], 0.5), 3)
        self.assertEqual(kc.percentile([1, 2, 3, 4, 5], 0.99), 5)
        self.assertEqual(kc.percentile([7], 0.9), 7)


class LogParserTest(unittest.TestCase):
    def test_multiline_records(self):
        lines = [
            "2026-09-03-04:25:12.668 [INFO] [__main__:77]",
            "Start pipeline with args: Namespace(topic=None)",
            "2026-09-03-04:35:38.916 [WARNING] [src.utils.process_str:23]",
            "parse_md_content: no ```markdown fence found, accepting unfenced heading-led content (1972 chars)",
            "2026-09-03-04:36:00.000 [ERROR] [x:1]",
            "line one",
            "line two",
        ]
        recs = kc.parse_log_records(lines)
        self.assertEqual(len(recs), 3)
        self.assertEqual(recs[0]["level"], "INFO")
        self.assertEqual(recs[0]["module"], "__main__:77")
        self.assertTrue(recs[0]["message"].startswith("Start pipeline"))
        self.assertEqual(recs[2]["message"], "line one\nline two")

    def test_lines_before_first_header_are_ignored(self):
        recs = kc.parse_log_records(["garbage", "2026-01-01-00:00:00.000 [INFO] [m:1]", "msg"])
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["message"], "msg")


class EnvParserTest(unittest.TestCase):
    def test_parse_and_redact(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_text(
                "# comment\nexport OPENAI_API_KEY=sk-secret   # key\nexport LLMXMR_PROVIDER=akashml/fp8\n"
                "export LLMXMR_TEMPERATURE=0.6        # 4 agent 공통\nexport LLMXMR_MAX_TOKENS=8192\n"
                "NOT_EXPORTED=1\nexport EMPTY=\n", encoding="utf-8")
            env = kc.parse_env_file(p)
        self.assertEqual(env["OPENAI_API_KEY"], "<redacted>")
        self.assertEqual(env["LLMXMR_PROVIDER"], "akashml/fp8")
        self.assertEqual(env["LLMXMR_TEMPERATURE"], "0.6")
        self.assertEqual(env["LLMXMR_MAX_TOKENS"], "8192")
        self.assertEqual(env["EMPTY"], "")
        self.assertNotIn("NOT_EXPORTED", env)


if __name__ == "__main__":
    unittest.main()
