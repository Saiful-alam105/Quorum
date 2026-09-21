"""Ollama-backed LLM provider (Phase 9).

Sends a prompt to the Ollama HTTP API (``POST /api/generate``) and returns the
generated text. Configuration (base URL, model, timeout, temperature) comes
from settings unless overridden in the constructor.
"""

import httpx

from quorum.config import settings
from quorum.llm.base import LLMError, LLMProvider


class OllamaProvider(LLMProvider):
    """Generates text through a local Ollama server."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
        temperature: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout_seconds = timeout_seconds or settings.ollama_timeout_seconds
        self.temperature = (
            settings.ollama_temperature if temperature is None else temperature
        )

    async def generate(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            raise LLMError("prompt must not be empty")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise LLMError(f"ollama request failed: {exc}") from exc

        if response.status_code != 200:
            raise LLMError(
                f"ollama returned {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMError("ollama returned invalid JSON") from exc

        text = data.get("response")
        if not text:
            raise LLMError("ollama returned an empty response")
        return text