import json

import pytest

from quorum.agents.test_writer import TestWriterAgent, TestWriterError
from quorum.analysis.ast_parser import AstFileInfo, FunctionInfo
from quorum.llm.base import LLMError, LLMProvider


def _ast_with_modified() -> list[AstFileInfo]:
    return [
        AstFileInfo(
            path="app.py",
            functions=[
                FunctionInfo(
                    name="alpha",
                    kind="function",
                    arguments=["x"],
                    source="def alpha(x):\n    return x + 1",
                    modified=True,
                )
            ],
        )
    ]


def _valid_raw() -> str:
    return json.dumps(
        {"tests": [{"name": "test_alpha.py", "code": "def test_alpha():\n    assert True\n"}]}
    )


class FakeProvider(LLMProvider):
    def __init__(self, result) -> None:
        self.result = result
        self.prompts: list[str] = []

    async def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class TestTestWriterAgent:
    @pytest.mark.asyncio
    async def test_returns_validated_tests(self) -> None:
        agent = TestWriterAgent(FakeProvider(_valid_raw()))
        generated = await agent.generate_tests(_ast_with_modified(), None, owner="o", repo="r", pr_number=1)
        assert len(generated.tests) == 1
        assert generated.tests[0].name == "test_alpha.py"

    @pytest.mark.asyncio
    async def test_prompt_passed_to_llm(self) -> None:
        provider = FakeProvider(_valid_raw())
        agent = TestWriterAgent(provider)
        await agent.generate_tests(_ast_with_modified(), None, owner="octocat", repo="r", pr_number=7)
        assert len(provider.prompts) == 1
        assert "octocat/r#7" in provider.prompts[0]
        assert "alpha" in provider.prompts[0]

    @pytest.mark.asyncio
    async def test_no_modified_functions_skips_llm(self) -> None:
        def fail(prompt: str) -> str:
            raise AssertionError("LLM should not be called")

        agent = TestWriterAgent(FakeProvider(fail))
        ast = [AstFileInfo(path="app.py", functions=[FunctionInfo(name="x", kind="function", arguments=[], source="", modified=False)])]
        generated = await agent.generate_tests(ast, None)
        assert generated.tests == []
        assert agent.llm.prompts == []

    @pytest.mark.asyncio
    async def test_llm_failure_raises(self) -> None:
        agent = TestWriterAgent(FakeProvider(LLMError("api down")))
        with pytest.raises(TestWriterError, match="LLM call failed"):
            await agent.generate_tests(_ast_with_modified(), None)

    @pytest.mark.asyncio
    async def test_invalid_json_raises(self) -> None:
        agent = TestWriterAgent(FakeProvider("not json"))
        with pytest.raises(TestWriterError, match="invalid output"):
            await agent.generate_tests(_ast_with_modified(), None)

    @pytest.mark.asyncio
    async def test_invalid_syntax_raises(self) -> None:
        bad = json.dumps({"tests": [{"name": "t.py", "code": "def broken(:"}]})
        agent = TestWriterAgent(FakeProvider(bad))
        with pytest.raises(TestWriterError, match="invalid output"):
            await agent.generate_tests(_ast_with_modified(), None)