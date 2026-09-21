import pytest

from quorum.config import Settings
from quorum.llm.base import LLMError, LLMProvider

OLLAMA_ENV_KEYS = (
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "OLLAMA_TIMEOUT_SECONDS",
    "OLLAMA_TEMPERATURE",
)


def _clear_ollama_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in OLLAMA_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


class TestLLMProviderInterface:
    def test_abstract_class_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            LLMProvider()

    @pytest.mark.asyncio
    async def test_concrete_subclass_is_usable(self) -> None:
        class FakeProvider(LLMProvider):
            async def generate(self, prompt: str) -> str:
                return f"hello {prompt}"

        provider = FakeProvider()
        result = await provider.generate("world")
        assert result == "hello world"

    def test_llm_error_is_an_exception(self) -> None:
        assert issubclass(LLMError, Exception)


class TestOllamaSettingsDefaults:
    def test_base_url_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_ollama_env(monkeypatch)
        assert Settings().ollama_base_url == "http://localhost:11434"

    def test_model_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_ollama_env(monkeypatch)
        assert Settings().ollama_model == "qwen2.5-coder:7b"

    def test_timeout_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_ollama_env(monkeypatch)
        assert Settings().ollama_timeout_seconds == 300

    def test_temperature_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_ollama_env(monkeypatch)
        assert Settings().ollama_temperature == 0.0


class TestOllamaSettingsOverride:
    def test_base_url_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
        assert Settings().ollama_base_url == "http://ollama:11434"

    def test_model_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5-coder:14b")
        assert Settings().ollama_model == "qwen2.5-coder:14b"

    def test_timeout_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "120")
        assert Settings().ollama_timeout_seconds == 120

    def test_temperature_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OLLAMA_TEMPERATURE", "0.5")
        assert Settings().ollama_temperature == 0.5