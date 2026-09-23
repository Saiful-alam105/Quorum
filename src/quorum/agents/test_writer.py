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