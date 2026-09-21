import pytest

from quorum.config import settings
from quorum.llm.base import LLMError
from quorum.llm.factory import create_llm_provider, openai_model_for_role
from quorum.llm.ollama_provider import OllamaProvider
from quorum.llm.openai_provider import OpenAIProvider


class TestCreateLLMProvider:
    def test_openai_selection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "llm_provider", "openai")
        provider = create_llm_provider()
        assert isinstance(provider, OpenAIProvider)

    def test_ollama_selection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "llm_provider", "ollama")
        provider = create_llm_provider()
        assert isinstance(provider, OllamaProvider)

    def test_default_provider_is_openai(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "llm_provider", "openai")
        provider = create_llm_provider()
        assert isinstance(provider, OpenAIProvider)

    def test_unknown_provider_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "llm_provider", "gemini")
        with pytest.raises(LLMError, match="unknown LLM provider"):
            create_llm_provider()

    def test_openai_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "llm_provider", "OPENAI")
        assert isinstance(create_llm_provider(), OpenAIProvider)


class TestRoleModels:
    def test_security_model_falls_back_to_generic(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "openai_model", "generic-model")
        monkeypatch.setattr(settings, "openai_security_model", "")
        assert openai_model_for_role(settings, "security") == "generic-model"

    def test_security_model_overrides_generic(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "openai_model", "generic-model")
        monkeypatch.setattr(settings, "openai_security_model", "security-model")
        assert openai_model_for_role(settings, "security") == "security-model"

    def test_unknown_role_uses_generic(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "openai_model", "generic-model")
        assert openai_model_for_role(settings, "unknown") == "generic-model"

    def test_factory_uses_role_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "llm_provider", "openai")
        monkeypatch.setattr(settings, "openai_model", "generic-model")
        monkeypatch.setattr(settings, "openai_security_model", "security-model")
        provider = create_llm_provider(role="security")
        assert isinstance(provider, OpenAIProvider)
        assert provider.model == "security-model"