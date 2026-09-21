import json

import pytest

from quorum.agents.security_agent import (
    SecurityAgent,
    SecurityAgentError,
    build_security_prompt,
)
from quorum.analysis.context import ContextFile, ContextHunk, ContextLine, PreparedContext
from quorum.analysis.semgrep import SemgrepFinding
from quorum.llm.base import LLMError, LLMProvider


def _finding(**overrides) -> SemgrepFinding:
    entry = {
        "rule_id": "python.lang.security.audit.eval-detected",
        "severity": "medium",
        "file": "src/app.py",
        "line": 8,
        "message": "Detected use of eval()",
        "evidence": "return eval(x)",
        "confidence": 0.4,
    }
    entry.update(overrides)
    return SemgrepFinding(**entry)


def _valid_raw() -> str:
    return json.dumps(
        {
            "findings": [
                {
                    "severity": "high",
                    "title": "Detected eval()",
                    "file": "src/app.py",
                    "line": 8,
                    "evidence": "return eval(x)",
                    "explanation": "code injection risk",
                    "confidence": 0.9,
                }
            ]
        }
    )


class FakeProvider(LLMProvider):
    def __init__(self, result) -> None:
        self.result = result
        self.prompts: list[str] = []

    async def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if callable(self.result):
            return self.result(prompt)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class TestSecurityAgentReview:
    @pytest.mark.asyncio
    async def test_returns_validated_review(self) -> None:
        agent = SecurityAgent(FakeProvider(_valid_raw()))
        review = await agent.review(None, [_finding()], owner="octocat", repo="r", pr_number=1)
        assert len(review.findings) == 1
        assert review.findings[0].severity == "high"
        assert review.findings[0].file == "src/app.py"
        assert review.findings[0].line == 8

    @pytest.mark.asyncio
    async def test_prompt_passed_to_llm(self) -> None:
        provider = FakeProvider(_valid_raw())
        agent = SecurityAgent(provider)
        await agent.review(None, [_finding()], owner="octocat", repo="r", pr_number=7)
        assert len(provider.prompts) == 1
        prompt = provider.prompts[0]
        assert "octocat/r#7" in prompt
        assert "python.lang.security.audit.eval-detected" in prompt

    @pytest.mark.asyncio
    async def test_empty_findings_skips_llm(self) -> None:
        def fail(prompt: str) -> str:
            raise AssertionError("LLM should not be called")

        provider = FakeProvider(fail)
        agent = SecurityAgent(provider)
        review = await agent.review(None, [], owner="octocat", repo="r", pr_number=1)
        assert review.findings == []
        assert provider.prompts == []

    @pytest.mark.asyncio
    async def test_llm_failure_raises_security_agent_error(self) -> None:
        provider = FakeProvider(LLMError("api down"))
        agent = SecurityAgent(provider)
        with pytest.raises(SecurityAgentError, match="LLM call failed"):
            await agent.review(None, [_finding()])

    @pytest.mark.asyncio
    async def test_invalid_output_raises_security_agent_error(self) -> None:
        agent = SecurityAgent(FakeProvider("not json at all"))
        with pytest.raises(SecurityAgentError, match="invalid output"):
            await agent.review(None, [_finding()])

    @pytest.mark.asyncio
    async def test_output_failing_validation_raises(self) -> None:
        agent = SecurityAgent(FakeProvider('{"findings": [{"severity": "critical"}]}'))
        with pytest.raises(SecurityAgentError, match="invalid output"):
            await agent.review(None, [_finding()])


class TestBuildSecurityPromptImport:
    def test_prompt_builder_is_reused(self) -> None:
        assert callable(build_security_prompt)