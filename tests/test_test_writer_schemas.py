import json

import pytest

from quorum.agents.test_writer import (
    GeneratedTestParseError,
    InvalidTestSyntaxError,
    parse_and_validate,
    parse_generated_tests,
    validate_test_syntax,
)


def _raw(tests) -> str:
    return json.dumps({"tests": tests})


class TestParseGeneratedTests:
    def test_valid_parse(self) -> None:
        generated = parse_generated_tests(
            _raw(
                [
                    {"name": "test_alpha.py", "code": "def test_alpha():\n    assert True\n"},
                    {"name": "test_beta.py", "code": "def test_beta():\n    assert 1 == 1\n"},
                ]
            )
        )
        assert [t.name for t in generated.tests] == ["test_alpha.py", "test_beta.py"]
        assert generated.tests[0].code.startswith("def test_alpha")

    def test_empty_tests_valid(self) -> None:
        assert parse_generated_tests(_raw([])).tests == []

    def test_missing_tests_key_raises(self) -> None:
        with pytest.raises(GeneratedTestParseError, match="no tests"):
            parse_generated_tests("{}")

    def test_tests_not_a_list_raises(self) -> None:
        with pytest.raises(GeneratedTestParseError, match="not a list"):
            parse_generated_tests('{"tests": "oops"}')

    def test_malformed_json_raises(self) -> None:
        with pytest.raises(GeneratedTestParseError, match="valid JSON"):
            parse_generated_tests("not json")

    def test_non_object_root_raises(self) -> None:
        with pytest.raises(GeneratedTestParseError, match="JSON object"):
            parse_generated_tests("[1, 2]")

    def test_missing_name_raises(self) -> None:
        with pytest.raises(GeneratedTestParseError, match="validation"):
            parse_generated_tests(_raw([{"code": "x"}]))

    def test_missing_code_raises(self) -> None:
        with pytest.raises(GeneratedTestParseError, match="validation"):
            parse_generated_tests(_raw([{"name": "t.py"}]))

    def test_empty_name_raises(self) -> None:
        with pytest.raises(GeneratedTestParseError, match="validation"):
            parse_generated_tests(_raw([{"name": "", "code": "x"}]))

    def test_deterministic(self) -> None:
        raw = _raw([{"name": "t.py", "code": "def t():\n    pass\n"}])
        assert parse_generated_tests(raw) == parse_generated_tests(raw)


class TestValidateTestSyntax:
    def test_valid_code_passes(self) -> None:
        validate_test_syntax("def test_x():\n    assert True\n")

    def test_invalid_code_raises(self) -> None:
        with pytest.raises(InvalidTestSyntaxError, match="not valid Python"):
            validate_test_syntax("def broken(:\n")


class TestParseAndValidate:
    def test_valid_output_passes(self) -> None:
        generated = parse_and_validate(
            _raw([{"name": "t.py", "code": "def t():\n    assert True\n"}])
        )
        assert len(generated.tests) == 1

    def test_invalid_syntax_raises(self) -> None:
        with pytest.raises(InvalidTestSyntaxError, match="not valid Python"):
            parse_and_validate(_raw([{"name": "t.py", "code": "def broken(:"}]))

    def test_bad_json_raises(self) -> None:
        with pytest.raises(GeneratedTestParseError, match="valid JSON"):
            parse_and_validate("nope")