"""LLM provider selection (Phase 9).

Agents depend on the :class:`LLMProvider` abstraction, never on a concrete
provider. This factory returns the configured provider so provider selection
lives in one place instead of inside agents.
"""

from quorum.config import settings
from quorum.llm.base import LLMError, LLMProvider
from quorum.llm.ollama_provider import OllamaProvider
from quorum.llm.openai_provider import OpenAIProvider

_ROLE_MODEL_ATTRS = {
    "security": "openai_security_model",
    "test": "openai_test_model",
    "chat": "openai_chat_model",
}


def openai_model_for_role(cfg, role: str) -> str:
    """Resolve the OpenAI model for a role, falling back to the generic model."""
    attr = _ROLE_MODEL_ATTRS.get(role)
    value = getattr(cfg, attr, "") if attr else ""
    return value or cfg.openai_model


def create_llm_provider(cfg=None, role: str | None = None) -> LLMProvider:
    """Return the configured LLM provider (openai or ollama)."""
    cfg = cfg or settings
    name = (cfg.llm_provider or "ollama").strip().lower()
    if name == "openai":
        model = openai_model_for_role(cfg, role) if role else cfg.openai_model
        return OpenAIProvider(model=model)
    if name == "ollama":
        return OllamaProvider()
    raise LLMError(f"unknown LLM provider configured: {name}")