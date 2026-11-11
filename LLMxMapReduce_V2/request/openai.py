import os
from openai import OpenAI, InternalServerError, RateLimitError, APIError, BadRequestError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    before_sleep_log,
    retry_if_exception_type
)
import logging
logger = logging.getLogger(__name__)


def _env_flag(name, default="1"):
    # empty == unset: fall back to the default ("0"/"false" turns it off)
    value = os.environ.get(name)
    if value in (None, ""):
        value = default
    return value not in ("0", "false")


class TruncatedResponseError(ValueError):
    """The completion hit LLMXMR_MAX_TOKENS (finish_reason == "length").

    Subclasses ValueError on purpose: every module-level tenacity retry in
    src/ (digest, orchestra, neurons, ...) already retries on ValueError, so a
    truncated sample is discarded and re-requested without touching the
    pipeline code. The wrapper's own retry (429/5xx) does not catch it.
    """


class DataInspectionFailedError(RuntimeError):
    """Alibaba DashScope rejected the call with 400 `data_inspection_failed`
    (content moderation on the input or the output).

    Deliberately NOT a ValueError and NOT an openai.APIError: neither the
    wrapper retry (429/5xx/APIError) nor the module-level retries (ValueError,
    ...) catch it, so the same prompt is not re-sent 100x and no module shrinks
    or rewrites the input to get past the filter. The call fails, the log gets
    one `data_inspection_failed` ERROR line, and the run must be reported as is.
    """


def _is_data_inspection_failed(exc):
    code = getattr(exc, "code", None)
    body = getattr(exc, "body", None)
    if code is None and isinstance(body, dict):
        code = body.get("code") or (body.get("error") or {}).get("code")
    return code == "data_inspection_failed" or "data_inspection_failed" in str(exc)


def _env_price(name):
    value = os.environ.get(name)
    return float(value) if value not in (None, "") else None


class OpenAIRequest:
    # session-wide credit accounting, shared across all models/instances
    _total_cost = 0.0
    _cost_call_count = 0
    # session-wide token accounting (backends that do not return a cost, e.g. DashScope)
    _prompt_tokens_total = 0
    _completion_tokens_total = 0
    _usage_call_count = 0
    _estimated_cost = 0.0
    # session-wide output-guard accounting (LLMXMR_MAX_TOKENS)
    _truncated_count = 0
    # session-wide 400 data_inspection_failed count (DashScope moderation)
    _inspection_failed_count = 0

    def __init__(self, model):
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_API_BASE"),
        )
        self.model = model
        extra_body = {}
        # LLMXMR_PROVIDER: OpenRouter provider pin (endpoint tag). Without a
        # pin OpenRouter routes the same model to providers with different
        # quantizations mid-run. Empty/unset = original behaviour.
        provider = os.environ.get("LLMXMR_PROVIDER")
        if provider:
            extra_body["provider"] = {"order": [provider], "allow_fallbacks": False}
        # LLMXMR_TRACK_COST (default on): ask OpenRouter to return the credit
        # cost of each call in usage.cost. Set to 0 to disable (e.g. non-OpenRouter
        # backends that reject unknown fields).
        if _env_flag("LLMXMR_TRACK_COST"):
            extra_body["usage"] = {"include": True}
        self.extra_body = extra_body or None
        # LLMXMR_TEMPERATURE: uniform temperature for every call (the caller
        # never passes one). Empty/unset = provider default.
        temperature = os.environ.get("LLMXMR_TEMPERATURE")
        self.temperature = float(temperature) if temperature not in (None, "") else None
        # LLMXMR_MAX_TOKENS: output guard against runaway samples (llama on
        # akashml may otherwise loop up to its 128K completion limit). It is a
        # truncation guard, not a length control: pick it well above the
        # longest legitimate output. Empty/unset = original behaviour.
        max_tokens = os.environ.get("LLMXMR_MAX_TOKENS")
        self.max_tokens = int(max_tokens) if max_tokens not in (None, "") else None
        # LLMXMR_RETRY_TRUNCATED (default on, only meaningful with the guard):
        # a response that hit the guard cannot be a valid sample, so discard it
        # and let the caller's retry draw a new one. Set to 0 to keep it.
        self.retry_truncated = self.max_tokens is not None and _env_flag("LLMXMR_RETRY_TRUNCATED")
        # LLMXMR_PRICE_IN / LLMXMR_PRICE_OUT: USD per 1M prompt / completion
        # tokens. Only used when the backend returns no cost (DashScope): each
        # call then logs a token-based estimate. Empty/unset = no estimate.
        self.price_in = _env_price("LLMXMR_PRICE_IN")
        self.price_out = _env_price("LLMXMR_PRICE_OUT")

    def _track_cost(self, usage):
        """Returns True when the backend reported a cost (OpenRouter usage.cost)."""
        cost = getattr(usage, "cost", None)
        if cost is None and getattr(usage, "model_extra", None):
            cost = usage.model_extra.get("cost")
        if cost is None:
            return False
        cls = OpenAIRequest
        cls._total_cost += float(cost)
        cls._cost_call_count += 1
        logger.info(
            f"OpenRouter cost: ${float(cost):.6f} "
            f"(session total ${cls._total_cost:.4f} over {cls._cost_call_count} calls)"
        )
        return True

    def _log_usage(self, usage, finish_reason, estimate_cost=False):
        # One line per call so a run log can be turned into a
        # completion_tokens distribution (guard headroom check).
        prompt = getattr(usage, "prompt_tokens", None)
        completion = getattr(usage, "completion_tokens", None)
        details = getattr(usage, "prompt_tokens_details", None)
        cached = getattr(details, "cached_tokens", None) if details is not None else None
        cls = OpenAIRequest
        cls._usage_call_count += 1
        cls._prompt_tokens_total += prompt or 0
        cls._completion_tokens_total += completion or 0
        logger.info(
            "completion usage: "
            f"prompt_tokens={prompt} "
            f"completion_tokens={completion} "
            f"finish_reason={finish_reason}"
            + (f" cached_tokens={cached}" if cached is not None else "")
            + f" (session tokens in={cls._prompt_tokens_total} out={cls._completion_tokens_total}"
            f" over {cls._usage_call_count} calls)"
        )
        if estimate_cost and self.price_in is not None and self.price_out is not None:
            cost = ((prompt or 0) * self.price_in + (completion or 0) * self.price_out) / 1e6
            cls._estimated_cost += cost
            logger.info(
                f"Estimated cost: ${cost:.6f} "
                f"(session total ${cls._estimated_cost:.4f}; ${self.price_in}/${self.price_out} per 1M in/out)"
            )

    @retry(
        wait=wait_random_exponential(multiplier=2, max=60),
        stop=stop_after_attempt(100),
        retry=retry_if_exception_type((RateLimitError, InternalServerError, APIError)) # retry only on these errors
        )
    def completion(self, messages, **kwargs):
        try:
            if self.extra_body is not None:
                kwargs.setdefault("extra_body", self.extra_body)
            if self.temperature is not None:
                kwargs.setdefault("temperature", self.temperature)
            if self.max_tokens is not None:
                kwargs.setdefault("max_tokens", self.max_tokens)
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, **kwargs
            )
            # Ensure the response contains valid choices data
            if not response.choices or len(response.choices) == 0:
                error_msg = "OpenAI API returned empty choices in response"
                logger.debug(error_msg)
                raise ValueError(error_msg)
            choice = response.choices[0]
            answer = choice.message.content
            finish_reason = getattr(choice, "finish_reason", None)
            token_usage = response.usage
            if token_usage is not None:
                reported = self._track_cost(token_usage)
                self._log_usage(token_usage, finish_reason, estimate_cost=not reported)
            if finish_reason == "length" and self.max_tokens is not None:
                cls = OpenAIRequest
                cls._truncated_count += 1
                if self.retry_truncated:
                    logger.warning(
                        f"Truncated response: finish_reason=length at max_tokens={self.max_tokens}; "
                        f"discarding for re-sampling (session truncated total {cls._truncated_count})"
                    )
                    raise TruncatedResponseError(
                        f"completion truncated at max_tokens={self.max_tokens}"
                    )
                logger.warning(
                    f"Truncated response kept (LLMXMR_RETRY_TRUNCATED=0), "
                    f"session truncated total {cls._truncated_count}"
                )

        except TruncatedResponseError:
            raise  # already logged; do not dump the prompt below
        except BadRequestError as e:
            if not _is_data_inspection_failed(e):
                logger.error(f"Unexpected error in OpenAIRequest.completion: {e}. messages: \n{messages}")
                raise
            cls = OpenAIRequest
            cls._inspection_failed_count += 1
            if isinstance(messages, str):
                texts = [messages]
            else:
                texts = [str(m.get("content", "")) if isinstance(m, dict) else str(m) for m in messages or []]
            head = " ".join((texts[-1] if texts else "")[:300].split())
            logger.error(
                f"data_inspection_failed (400) model={self.model}: {e}. Input left unchanged, not retried "
                f"(session total {cls._inspection_failed_count}). "
                f"prompt_chars={sum(len(t) for t in texts)} head={head!r}"
            )
            raise DataInspectionFailedError(str(e)) from e
        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded in OpenAIRequest.completion: {e}")
            raise 
        except InternalServerError as e:
            logger.warning(f"Internal server error in OpenAIRequest.completion: {e}")
            # logger.warning(f"Prompt: {messages}")
            raise 
        except Exception as e:
            logger.error(f"Unexpected error in OpenAIRequest.completion: {e}. messages: \n{messages}")
            raise 
                
        return answer, token_usage
