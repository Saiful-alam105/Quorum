"""OpenAI-backed LLM provider (Phase 9).

Sends a prompt to the OpenAI Chat Completions API and returns the generated
text. The API key is read from configuration only and is never logged or
included in exceptions. Configuration (base URL, model, timeout, temperature)
comes from settings unless overridden in the constructor.
"""

import httpx

from quorum.config import settings
from quorum.llm.base import LLMError, LLMProvider


class OpenAIProvider(LLMProvider):
    """Generates text through the OpenAI API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.model = model if model is not None else settings.openai_model
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else settings.openai_timeout_seconds
        )

    async def generate(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            raise LLMError("prompt must not be empty")
        if not self.api_key:
            raise LLMError("OpenAI API key not configured")
        if not self.model:
            raise LLMError("OpenAI model not configured")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise LLMError(f"OpenAI request failed: {exc}") from exc

        if response.status_code in (401, 403):
            raise LLMError("OpenAI authentication failed (check API key)")
        if response.status_code == 429:
            raise LLMError("OpenAI rate limit exceeded")
        if response.status_code != 200:
            raise LLMError(
                f"OpenAI returned {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMError("OpenAI returned invalid JSON") from exc

        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            raise LLMError("OpenAI returned no choices")
        text = choices[0].get("message", {}).get("content") if isinstance(choices[0], dict) else None
        if not text:
            raise LLMError("OpenAI returned an empty response")
        return text