"""request/openai.py 의 env-gated 프로파일·출력 가드 — OpenAI 클라이언트를 mock 해서 네트워크 없이 검증.

실행 (llmxmr env, openai·tenacity 필요):
  PYTHONPATH=LLMxMapReduce_V2 python -m unittest tests.test_openai_request -v
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "LLMxMapReduce_V2"))

try:
    import request.openai as ro  # noqa: E402
    HAVE_DEPS = True
except ImportError:  # openai / tenacity 가 없는 env
    HAVE_DEPS = False

BASE_ENV = {"OPENAI_API_KEY": "sk-test", "OPENAI_API_BASE": "http://localhost/v1",
            "LLMXMR_PROVIDER": "", "LLMXMR_TEMPERATURE": "", "LLMXMR_MAX_TOKENS": "",
            "LLMXMR_RETRY_TRUNCATED": "", "LLMXMR_TRACK_COST": ""}
PROFILE_ENV = {**BASE_ENV, "LLMXMR_PROVIDER": "akashml/fp8", "LLMXMR_TEMPERATURE": "0.6",
               "LLMXMR_MAX_TOKENS": "8192", "LLMXMR_TRACK_COST": "1"}


def fake_response(content="# ok", finish_reason="stop", prompt=100, completion=10, cost=0.001):
    usage = SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion, cost=cost, model_extra=None)
    choice = SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice], usage=usage)


def make_request(env, responses):
    """env 로 OpenAIRequest 를 만들고 create() 가 responses 를 순서대로 돌려주게 한다."""
    with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(ro, "OpenAI") as client_cls:
        req = ro.OpenAIRequest(model="test-model")
    create = req.client.chat.completions.create
    create.side_effect = list(responses)
    return req, create


@unittest.skipUnless(HAVE_DEPS, "openai/tenacity not installed in this env")
class OpenAIRequestProfileTest(unittest.TestCase):
    def setUp(self):
        ro.OpenAIRequest._total_cost = 0.0
        ro.OpenAIRequest._cost_call_count = 0
        ro.OpenAIRequest._truncated_count = 0

    def test_unset_env_keeps_original_kwargs(self):
        req, create = make_request(BASE_ENV, [fake_response()])
        answer, usage = req.completion([{"role": "user", "content": "hi"}])
        self.assertEqual(answer, "# ok")
        kwargs = create.call_args.kwargs
        self.assertNotIn("temperature", kwargs)
        self.assertNotIn("max_tokens", kwargs)
        # provider 미설정 + TRACK_COST 빈 값(=기본 on) → usage accounting 만 남는다
        self.assertEqual(kwargs["extra_body"], {"usage": {"include": True}})
        self.assertIsNone(req.max_tokens)
        self.assertFalse(req.retry_truncated)

    def test_track_cost_off_drops_extra_body(self):
        req, create = make_request({**BASE_ENV, "LLMXMR_TRACK_COST": "0"}, [fake_response()])
        req.completion("hi")
        self.assertNotIn("extra_body", create.call_args.kwargs)

    def test_retry_truncated_empty_means_default_on(self):
        req, _ = make_request({**PROFILE_ENV, "LLMXMR_RETRY_TRUNCATED": ""}, [fake_response()])
        self.assertTrue(req.retry_truncated)

    def test_profile_env_is_passed_to_create(self):
        req, create = make_request(PROFILE_ENV, [fake_response()])
        req.completion("hi")
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["temperature"], 0.6)
        self.assertEqual(kwargs["max_tokens"], 8192)
        self.assertEqual(kwargs["extra_body"]["provider"], {"order": ["akashml/fp8"], "allow_fallbacks": False})
        self.assertEqual(kwargs["extra_body"]["usage"], {"include": True})
        self.assertEqual(kwargs["model"], "test-model")

    def test_caller_kwargs_win_over_env(self):
        # 평가 코드(APIModel)는 temperature 를 명시 전달한다 → env 값이 덮어쓰면 안 된다
        req, create = make_request(PROFILE_ENV, [fake_response()])
        req.completion("hi", temperature=0)
        self.assertEqual(create.call_args.kwargs["temperature"], 0)

    def test_truncated_is_discarded_and_raised_once(self):
        req, create = make_request(PROFILE_ENV, [fake_response(finish_reason="length", completion=8192)])
        with self.assertRaises(ro.TruncatedResponseError) as cm:
            req.completion("hi")
        self.assertIsInstance(cm.exception, ValueError)  # 모듈 retry 가 잡는 타입
        self.assertEqual(create.call_count, 1)  # 래퍼 자체 retry(429/5xx)는 재시도하지 않음
        self.assertEqual(ro.OpenAIRequest._truncated_count, 1)

    def test_truncated_is_kept_when_retry_disabled(self):
        env = {**PROFILE_ENV, "LLMXMR_RETRY_TRUNCATED": "0"}
        req, _ = make_request(env, [fake_response(content="partial", finish_reason="length")])
        answer, _ = req.completion("hi")
        self.assertEqual(answer, "partial")
        self.assertEqual(ro.OpenAIRequest._truncated_count, 1)

    def test_length_without_guard_is_original_behaviour(self):
        env = {**PROFILE_ENV, "LLMXMR_MAX_TOKENS": ""}
        req, create = make_request(env, [fake_response(content="partial", finish_reason="length")])
        answer, _ = req.completion("hi")
        self.assertEqual(answer, "partial")
        self.assertNotIn("max_tokens", create.call_args.kwargs)
        self.assertEqual(ro.OpenAIRequest._truncated_count, 0)

    def test_stop_does_not_count_as_truncated(self):
        req, _ = make_request(PROFILE_ENV, [fake_response(finish_reason="stop", completion=4000)])
        answer, usage = req.completion("hi")
        self.assertEqual(usage.completion_tokens, 4000)
        self.assertEqual(ro.OpenAIRequest._truncated_count, 0)

    def test_cost_accumulates_across_instances(self):
        req1, _ = make_request(PROFILE_ENV, [fake_response(cost=0.002)])
        req2, _ = make_request(PROFILE_ENV, [fake_response(cost=0.003)])
        req1.completion("a")
        req2.completion("b")
        self.assertAlmostEqual(ro.OpenAIRequest._total_cost, 0.005)
        self.assertEqual(ro.OpenAIRequest._cost_call_count, 2)

    def test_usage_line_is_logged_for_distribution(self):
        req, _ = make_request(PROFILE_ENV, [fake_response(prompt=1234, completion=567)])
        with self.assertLogs(ro.logger, level="INFO") as cm:
            req.completion("hi")
        joined = "\n".join(cm.output)
        self.assertIn("completion usage: prompt_tokens=1234 completion_tokens=567 finish_reason=stop", joined)

    def test_empty_choices_raises_value_error(self):
        req, _ = make_request(PROFILE_ENV, [SimpleNamespace(choices=[], usage=None)])
        with self.assertRaises(ValueError):
            req.completion("hi")


if __name__ == "__main__":
    unittest.main()
