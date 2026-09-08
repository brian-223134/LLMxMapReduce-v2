"""scripts/run_manifest.py — 합성 로그/출력으로 집계 검증."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import kisti_common as kc  # noqa: E402
import run_manifest as rm  # noqa: E402


def rec(ts, level, module, *msg):
    return [f"2026-09-08-{ts} [{level}] [{module}]", *msg]


LOG = (
    rec("10:00:00.000", "INFO", "__main__:77", "Start pipeline with args: Namespace(topic=None, block_count=1)")
    + rec("10:00:01.000", "INFO", "request.openai:70", "OpenRouter cost: $0.001000 (session total $0.0010 over 1 calls)")
    + rec("10:00:01.001", "INFO", "request.openai:80", "completion usage: prompt_tokens=1000 completion_tokens=500 finish_reason=stop")
    + rec("10:00:02.000", "INFO", "request.openai:70", "OpenRouter cost: $0.004000 (session total $0.0050 over 2 calls)")
    + rec("10:00:02.001", "INFO", "request.openai:80", "completion usage: prompt_tokens=2000 completion_tokens=8192 finish_reason=length")
    + rec("10:00:02.002", "WARNING", "request.openai:90", "Truncated response: finish_reason=length at max_tokens=8192; discarding for re-sampling (session truncated total 1)")
    + rec("10:00:03.000", "WARNING", "src.hidden.basic_modules.digest_module:42", "Finished call to 'x', this was the 1st time calling it.")
    + rec("10:00:04.000", "INFO", "request.openai:70", "OpenRouter cost: $0.002000 (session total $0.0070 over 3 calls)")
    + rec("10:00:04.001", "INFO", "request.openai:80", "completion usage: prompt_tokens=2000 completion_tokens=3000 finish_reason=stop")
    + rec("10:00:05.000", "WARNING", "src.utils.process_str:23", "parse_md_content: no ```markdown fence found, accepting unfenced heading-led content (100 chars)")
    + rec("10:00:06.000", "WARNING", "src.utils.process_str:104", "Remove illegal bibkeys: ['a'], \nall legal bibkeys: [...]")
    + rec("10:00:07.000", "WARNING", "request.openai:82", "Rate limit exceeded in OpenAIRequest.completion: Error code: 429")
    + rec("10:00:08.000", "ERROR", "x:1", "boom", "Traceback (most recent call last):", "  ...")
    + rec("10:01:00.000", "INFO", "src.pipeline:1", "save_survey done")
)


class SummarizeLogTest(unittest.TestCase):
    def test_counts_and_distribution(self):
        s = rm.summarize_log(kc.parse_log_records(LOG), max_tokens=8192)
        self.assertEqual(s["calls"], 3)
        self.assertAlmostEqual(s["total_cost_usd"], 0.007)
        self.assertEqual(s["usage_lines"], 3)
        self.assertEqual(s["finish_reasons"], {"stop": 2, "length": 1})
        ct = s["completion_tokens"]
        self.assertEqual((ct["n"], ct["min"], ct["max"], ct["sum"]), (3, 500, 8192, 11692))
        self.assertEqual(ct["at_guard"], 1)
        self.assertEqual(ct["guard"], 8192)
        self.assertAlmostEqual(ct["headroom_ratio"], round(8192 / 3000, 2))
        self.assertEqual(s["truncated_discarded"], 1)
        self.assertEqual(s["truncated_kept"], 0)
        self.assertEqual(s["module_retries"], 1)
        self.assertEqual(s["fence_fallback"], 1)
        self.assertEqual(s["illegal_bibkeys"], 1)
        self.assertEqual(s["rate_limit_429"], 1)
        self.assertEqual(s["error_records"], 1)
        self.assertEqual(s["tracebacks"], 1)
        self.assertEqual(s["pipeline_args"], "Namespace(topic=None, block_count=1)")
        self.assertEqual(s["duration_s"], 60.0)

    def test_empty_log(self):
        s = rm.summarize_log([], max_tokens=8192)
        self.assertEqual(s["calls"], 0)
        self.assertEqual(s["completion_tokens"], {})
        self.assertIsNone(s["duration_s"])


class PerTopicTest(unittest.TestCase):
    def test_per_topic_stats(self):
        out = {"title": "T", "cost_time": 123.4, "block_cycle_count": 1, "conv_layer": 6,
               "outline_eval_score": 8.9, "cite_ratio": 0.5,
               "papers": [{"title": "a"}, {"title": "b"}, {"title": "c"}, {"title": "d"}],
               "content": "# T\n## 1 A\nclaim [1,2].\n## 2 B\nmore [2]. [4]\n\n## References\n[1] a\n[2] b\n"}
        t = rm.per_topic_stats(out)
        self.assertEqual(t["n_papers"], 4)
        self.assertEqual(t["n_refs_cited"], 3)
        self.assertEqual(t["n_headings"], 3)
        self.assertEqual(t["cite_ratio"], 0.5)
        self.assertGreater(t["n_words"], 0)

    def test_collect_models(self):
        cfg = {"hidden": {"a": {"model": "m1", "infer_type": "OpenAI"}, "b": {"x": {"model": "m2"}}},
               "decode": [{"model": "m1"}]}
        self.assertEqual(rm.collect_models(cfg), ["m1", "m2"])


if __name__ == "__main__":
    unittest.main()
