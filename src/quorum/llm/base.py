"""LLM layer: provider interface (Phase 9).

Keeps the model behind an interface so later phases (Security Agent, Test
Writer) can generate text without depending on Ollama or the chosen model.
"""

from abc import ABC, abstractmethod


class LLMError(Exception):
    """Raised when an LLM provider cannot generate a response."""


class LLMProvider(ABC):
    """Interface every LLM-backed provider must implement."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt."""