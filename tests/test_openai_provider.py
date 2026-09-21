import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from quorum.llm.base import LLMError
from quorum.llm.openai_provider import OpenAIProvider


def _make_response(
    status_code: int = 200, json_data=None, text_data: str = "", invalid_json: bool = False
):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = text_data
    if invalid_json:
        mock_response.json.side_effect = ValueError("no json")
    else:
        mock_response.json.return_value = json_data
    return mock_response


class TestGenerate:
    @pytest.mark.asyncio
    async def test_returns_response_text(self) -> None:
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(
                json_data={
                    "choices": [
                        {"message": {"role": "assistant", "content": "def add(a, b): return a + b"}}
                    ]
                }
            )

            provider = OpenAIProvider(api_key="secret", model="gpt-test")
            result = await provider.generate("Write a function")

            assert result == "def add(a, b): return a + b"

    @pytest.mark.asyncio
    async def test_sends_correct_request(self) -> None:
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(
                json_data={"choices": [{"message": {"content": "ok"}}]}
            )

            provider = OpenAIProvider(
                api_key="secret-key",
                base_url="https://api.openai.com/v1/",
                model="gpt-test",
                timeout_seconds=60,
            )
            await provider.generate("hello")

            mock_client.post.assert_awaited_once()
            call = mock_client.post.call_args
            assert call.args[0] == "https://api.openai.com/v1/chat/completions"
            assert call.kwargs["headers"]["Authorization"] == "Bearer secret-key"
            assert call.kwargs["json"] == {
                "model": "gpt-test",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": False,
            }

    @pytest.mark.asyncio
    async def test_model_defaults_from_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from quorum.config import settings

        monkeypatch.setattr(settings, "openai_model", "gpt-configured")
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(
                json_data={"choices": [{"message": {"content": "ok"}}]}
            )

            provider = OpenAIProvider(api_key="secret")
            await provider.generate("hi")

            call = mock_client.post.call_args
            assert call.kwargs["json"]["model"] == "gpt-configured"


class TestEmptyPrompt:
    @pytest.mark.asyncio
    async def test_empty_prompt_raises(self) -> None:
        provider = OpenAIProvider(api_key="secret", model="gpt-test")
        with pytest.raises(LLMError, match="must not be empty"):
            await provider.generate("")

    @pytest.mark.asyncio
    async def test_whitespace_prompt_raises(self) -> None:
        provider = OpenAIProvider(api_key="secret", model="gpt-test")
        with pytest.raises(LLMError, match="must not be empty"):
            await provider.generate("   \n ")


class TestConfiguration:
    @pytest.mark.asyncio
    async def test_missing_api_key_raises(self) -> None:
        provider = OpenAIProvider(api_key="", model="gpt-test")
        with pytest.raises(LLMError, match="API key not configured"):
            await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_missing_model_raises(self) -> None:
        provider = OpenAIProvider(api_key="secret", model="")
        with pytest.raises(LLMError, match="model not configured"):
            await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_api_key_never_in_error_message(self) -> None:
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(
                status_code=500, text_data="secret-key leaked?"
            )
            provider = OpenAIProvider(api_key="super-secret-value", model="gpt-test")
            with pytest.raises(LLMError) as exc_info:
                await provider.generate("hi")
            assert "super-secret-value" not in str(exc_info.value)


class TestFailures:
    @pytest.mark.asyncio
    async def test_authentication_error_raises(self) -> None:
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(status_code=401, text_data="bad key")

            provider = OpenAIProvider(api_key="wrong", model="gpt-test")
            with pytest.raises(LLMError, match="authentication failed"):
                await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_rate_limit_error_raises(self) -> None:
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(status_code=429, text_data="rate limited")

            provider = OpenAIProvider(api_key="secret", model="gpt-test")
            with pytest.raises(LLMError, match="rate limit"):
                await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_other_http_error_raises(self) -> None:
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(
                status_code=400, text_data="model does not exist"
            )

            provider = OpenAIProvider(api_key="secret", model="gpt-test")
            with pytest.raises(LLMError, match="400"):
                await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_connection_error_raises(self) -> None:
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.ConnectError("refused")

            provider = OpenAIProvider(api_key="secret", model="gpt-test")
            with pytest.raises(LLMError, match="OpenAI request failed"):
                await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_timeout_raises(self) -> None:
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.ReadTimeout("slow")

            provider = OpenAIProvider(api_key="secret", model="gpt-test")
            with pytest.raises(LLMError, match="OpenAI request failed"):
                await provider.generate("hi")


class TestResponseParsing:
    @pytest.mark.asyncio
    async def test_invalid_json_raises(self) -> None:
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(invalid_json=True)

            provider = OpenAIProvider(api_key="secret", model="gpt-test")
            with pytest.raises(LLMError, match="invalid JSON"):
                await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_no_choices_raises(self) -> None:
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(json_data={})

            provider = OpenAIProvider(api_key="secret", model="gpt-test")
            with pytest.raises(LLMError, match="no choices"):
                await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_empty_content_raises(self) -> None:
        with patch("quorum.llm.openai_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(
                json_data={"choices": [{"message": {"content": ""}}]}
            )

            provider = OpenAIProvider(api_key="secret", model="gpt-test")
            with pytest.raises(LLMError, match="empty response"):
                await provider.generate("hi")