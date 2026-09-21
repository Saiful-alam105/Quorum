import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from quorum.llm.base import LLMError
from quorum.llm.ollama_provider import OllamaProvider


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
        with patch("quorum.llm.ollama_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(
                json_data={"response": "def add(a, b):\n    return a + b"}
            )

            provider = OllamaProvider()
            result = await provider.generate("Write a function")

            assert result == "def add(a, b):\n    return a + b"

    @pytest.mark.asyncio
    async def test_sends_correct_payload(self) -> None:
        with patch("quorum.llm.ollama_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(json_data={"response": "ok"})

            provider = OllamaProvider()
            await provider.generate("hello")

            mock_client.post.assert_awaited_once()
            call = mock_client.post.call_args
            assert call.args[0] == "http://localhost:11434/api/generate"
            assert call.kwargs["json"] == {
                "model": "qwen2.5-coder:7b",
                "prompt": "hello",
                "stream": False,
                "options": {"temperature": 0.0},
            }

    @pytest.mark.asyncio
    async def test_custom_provider_parameters(self) -> None:
        with patch("quorum.llm.ollama_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(json_data={"response": "ok"})

            provider = OllamaProvider(
                base_url="http://ollama:11434/",
                model="qwen2.5-coder:14b",
                timeout_seconds=60,
                temperature=0.5,
            )
            await provider.generate("hi")

            call = mock_client.post.call_args
            assert call.args[0] == "http://ollama:11434/api/generate"
            assert call.kwargs["json"]["model"] == "qwen2.5-coder:14b"
            assert call.kwargs["json"]["options"]["temperature"] == 0.5


class TestEmptyPrompt:
    @pytest.mark.asyncio
    async def test_empty_prompt_raises(self) -> None:
        provider = OllamaProvider()
        with pytest.raises(LLMError, match="must not be empty"):
            await provider.generate("")

    @pytest.mark.asyncio
    async def test_whitespace_prompt_raises(self) -> None:
        provider = OllamaProvider()
        with pytest.raises(LLMError, match="must not be empty"):
            await provider.generate("   \n  ")


class TestFailures:
    @pytest.mark.asyncio
    async def test_non_200_raises(self) -> None:
        with patch("quorum.llm.ollama_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(
                status_code=500, text_data="model overloaded"
            )

            provider = OllamaProvider()
            with pytest.raises(LLMError, match="500"):
                await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_connection_error_raises(self) -> None:
        with patch("quorum.llm.ollama_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.ConnectError("refused")

            provider = OllamaProvider()
            with pytest.raises(LLMError, match="ollama request failed"):
                await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_timeout_raises(self) -> None:
        with patch("quorum.llm.ollama_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.ReadTimeout("slow")

            provider = OllamaProvider()
            with pytest.raises(LLMError, match="ollama request failed"):
                await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_missing_response_field_raises(self) -> None:
        with patch("quorum.llm.ollama_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(json_data={})

            provider = OllamaProvider()
            with pytest.raises(LLMError, match="empty response"):
                await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_empty_response_raises(self) -> None:
        with patch("quorum.llm.ollama_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(json_data={"response": ""})

            provider = OllamaProvider()
            with pytest.raises(LLMError, match="empty response"):
                await provider.generate("hi")

    @pytest.mark.asyncio
    async def test_invalid_json_raises(self) -> None:
        with patch("quorum.llm.ollama_provider.httpx.AsyncClient") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_response(invalid_json=True)

            provider = OllamaProvider()
            with pytest.raises(LLMError, match="invalid JSON"):
                await provider.generate("hi")