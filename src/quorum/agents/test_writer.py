"""Test Writer Agent: structured output contract and syntax validation.

Phase 12 agent. This module defines the Pydantic schema for the generated
tests the LLM must return and the parser/validator that turns raw LLM text
into a validated :class:`GeneratedTests`. LLM output is untrusted: it is
validated against the schema and every test's code is syntax-checked with the
stdlib ``ast`` module before anything runs in the sandbox. The prompt builder
and the agent itself are added in later chunks of this phase.
"""

import ast
import json

from pydantic import BaseModel, Field, ValidationError

from quorum.analysis.ast_parser import AstFileInfo
from quorum.analysis.context import PreparedContext
from quorum.llm.base import LLMError, LLMProvider


class GeneratedTest(BaseModel):
    """A single generated pytest file."""

    name: str = Field(min_length=1)
    code: str = Field(min_length=1)


class GeneratedTests(BaseModel):
    """The structured output of the Test Writer Agent."""

    tests: list[GeneratedTest]


class GeneratedTestParseError(Exception):
    """Raised when raw agent output cannot be parsed or validated."""


class InvalidTestSyntaxError(Exception):
    """Raised when a generated test's code is not valid Python."""


def parse_generated_tests(raw: str) -> GeneratedTests:
    """Parse and schema-validate raw LLM text into :class:`GeneratedTests`."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise GeneratedTestParseError("test output is not valid JSON") from exc
    if not isinstance(data, dict):
        raise GeneratedTestParseError("test output is not a JSON object")

    tests = data.get("tests")
    if tests is None:
        raise GeneratedTestParseError("test output has no tests list")
    if not isinstance(tests, list):
        raise GeneratedTestParseError("test output tests is not a list")

    try:
        return GeneratedTests(tests=tests)
    except ValidationError as exc:
        raise GeneratedTestParseError("test output failed validation") from exc


def validate_test_syntax(code: str) -> None:
    """Raise :class:`InvalidTestSyntaxError` if ``code`` is not valid Python."""
    try:
        ast.parse(code)
    except SyntaxError as exc:
        raise InvalidTestSyntaxError(
            f"generated test is not valid Python: {exc}"
        ) from exc


def parse_and_validate(raw: str) -> GeneratedTests:
    """Parse raw output and syntax-validate every generated test's code."""
    generated = parse_generated_tests(raw)
    for test in generated.tests:
        validate_test_syntax(test.code)
    return generated


_TEST_WRITER_INSTRUCTIONS = """You are the Quorum Test Writer Agent. Generate pytest tests for the modified Python functions below.

Output ONLY strict JSON with this exact shape:
{"tests": [{"name": "test_<function>.py", "code": "<full pytest code>"}]}

Rules:
- Write one test file per modified function, named test_<function>.py.
- Tests must be valid, self-contained Python; import only the changed modules.
- Use only the standard library and pytest (already installed in the sandbox).
- Cover the function's normal behavior and its argument cases.
- Do not use network, subprocess, or filesystem writes outside /tmp.
- If there are no functions worth testing, return {"tests": []}."""


def build_test_writer_prompt(
    ast_files: list[AstFileInfo],
    prepared_context: PreparedContext | None,
    owner: str = "",
    repo: str = "",
    pr_number: int | None = None,
) -> str:
    """Build a bounded, deterministic test-generation prompt from AST."""
    pr_label = f"{owner}/{repo}#{pr_number}" if pr_number is not None else f"{owner}/{repo}"
    sections = [f"Pull request: {pr_label}", ""]

    sections.append("## Modified functions")
    modified = [
        (info.path, function)
        for info in ast_files
        for function in info.functions
        if function.modified
    ]
    if modified:
        for path, function in modified:
            header = f"### {path} — {function.name}"
            if function.class_name:
                header += f" (method of {function.class_name})"
            sections.append(header)
            if function.decorators:
                sections.append(f"decorators: {', '.join(function.decorators)}")
            sections.append(f"arguments: {', '.join(function.arguments)}")
            sections.append("source:")
            sections.append(function.source)
            sections.append("")
    else:
        sections.append("(none)")
        sections.append("")

    sections.append("## Changed code context (bounded)")
    sections.append(
        prepared_context.render_text() if prepared_context is not None else "(no context)"
    )
    sections.append("")
    sections.append(_TEST_WRITER_INSTRUCTIONS)

    return "\n".join(sections)


class TestWriterError(Exception):
    """Raised when the Test Writer Agent cannot produce valid tests."""

    __test__ = False


class TestWriterAgent:
    """Generates pytest tests using an injected :class:`LLMProvider`."""

    __test__ = False

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def generate_tests(
        self,
        ast_files: list[AstFileInfo],
        prepared_context: PreparedContext | None,
        owner: str = "",
        repo: str = "",
        pr_number: int | None = None,
    ) -> GeneratedTests:
        """Generate and validate tests for the modified functions.

        With no modified functions the LLM is not called and an empty result is
        returned — the agent must not generate tests without a target.
        """
        has_modified = any(
            function.modified
            for info in ast_files
            for function in info.functions
        )
        if not has_modified:
            return GeneratedTests(tests=[])

        prompt = build_test_writer_prompt(
            ast_files, prepared_context, owner, repo, pr_number
        )
        try:
            raw = await self.llm.generate(prompt)
        except LLMError as exc:
            raise TestWriterError(f"test writer LLM call failed: {exc}") from exc

        try:
            return parse_and_validate(raw)
        except (GeneratedTestParseError, InvalidTestSyntaxError) as exc:
            raise TestWriterError(
                f"test writer produced invalid output: {exc}"
            ) from exc