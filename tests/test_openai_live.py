import os

import pytest

from quorum.config import settings
from quorum.llm.openai_provider import OpenAIProvider

pytestmark = pytest.mark.skipif(
    os.getenv("OPENAI_LIVE_TESTS") != "1",
    reason="set OPENAI_LIVE_TESTS=1 and configure OPENAI_API_KEY/OPENAI_MODEL to run",
)


class TestOpenAILive:
    @pytest.mark.asyncio
    async def test_generate_reaches_api(self) -> None:
        if not settings.openai_api_key or not settings.openai_model:
            pytest.skip("OPENAI_API_KEY / OPENAI_MODEL not configured")
        provider = OpenAIProvider()
        result = await provider.generate("Reply with the single word: ok")
        assert isinstance(result, str)
        assert result.strip()