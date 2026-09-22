import os

import pytest

from quorum.agents.security_agent import SecurityAgent, SecurityAgentReview
from quorum.analysis.semgrep import SemgrepFinding
from quorum.config import settings
from quorum.llm.factory import create_llm_provider

pytestmark = pytest.mark.skipif(
    os.getenv("OPENAI_LIVE_TESTS") != "1",
    reason="set OPENAI_LIVE_TESTS=1 and configure OPENAI_API_KEY to run",
)


class TestSecurityAgentLive:
    @pytest.mark.asyncio
    async def test_review_reaches_api(self) -> None:
        if not settings.openai_api_key:
            pytest.skip("OPENAI_API_KEY not configured")
        provider = create_llm_provider(role="security")
        agent = SecurityAgent(provider)
        findings = [
            SemgrepFinding(
                rule_id="python.lang.security.audit.eval-detected",
                severity="medium",
                file="app.py",
                line=3,
                message="Detected use of eval()",
                evidence="return eval(x)",
                confidence=0.4,
            )
        ]
        review = await agent.review(None, findings)
        assert isinstance(review, SecurityAgentReview)