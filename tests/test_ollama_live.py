import os

import pytest

from quorum.llm.ollama_provider import OllamaProvider

pytestmark = pytest.mark.skipif(
    os.getenv("OLLAMA_LIVE_TESTS") != "1",
    reason="set OLLAMA_LIVE_TESTS=1 and start Ollama to run",
)


class TestOllamaLive:
    @pytest.mark.asyncio
    async def test_generate_reaches_local_ollama(self) -> None:
        provider = OllamaProvider()
        result = await provider.generate("Reply with the single word: ok")
        assert isinstance(result, str)
        assert result.strip()