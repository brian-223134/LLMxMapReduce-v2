import os
from openai import OpenAI, InternalServerError, RateLimitError, APIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    before_sleep_log,
    retry_if_exception_type
)
import logging
logger = logging.getLogger(__name__)


class OpenAIRequest:
    # session-wide credit accounting, shared across all models/instances
    _total_cost = 0.0
    _cost_call_count = 0

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
        if os.environ.get("LLMXMR_TRACK_COST", "1") not in ("0", "false", ""):
            extra_body["usage"] = {"include": True}
        self.extra_body = extra_body or None
        # LLMXMR_TEMPERATURE: uniform temperature for every call (the caller
        # never passes one). Empty/unset = provider default.
        temperature = os.environ.get("LLMXMR_TEMPERATURE")
        self.temperature = float(temperature) if temperature not in (None, "") else None

    def _track_cost(self, usage):
        cost = getattr(usage, "cost", None)
        if cost is None and getattr(usage, "model_extra", None):
            cost = usage.model_extra.get("cost")
        if cost is None:
            return
        cls = OpenAIRequest
        cls._total_cost += float(cost)
        cls._cost_call_count += 1
        logger.info(
            f"OpenRouter cost: ${float(cost):.6f} "
            f"(session total ${cls._total_cost:.4f} over {cls._cost_call_count} calls)"
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
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, **kwargs
            )
            # Ensure the response contains valid choices data
            if not response.choices or len(response.choices) == 0:
                error_msg = "OpenAI API returned empty choices in response"
                logger.debug(error_msg)
                raise ValueError(error_msg)
            answer = response.choices[0].message.content
            token_usage = response.usage
            if token_usage is not None:
                self._track_cost(token_usage)

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
