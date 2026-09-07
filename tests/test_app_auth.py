import pytest

from quorum.github.app_auth import create_app_jwt


def test_create_app_jwt_missing_app_id(tmp_path: pytest.TempPathFactory) -> None:
    key_file = tmp_path / "test.pem"  # type: ignore
    key_file.write_text("fake-key")  # type: ignore
    with pytest.raises(ValueError, match="must be set"):
        create_app_jwt("", str(key_file))


def test_create_app_jwt_missing_key_path() -> None:
    with pytest.raises(ValueError, match="must be set"):
        create_app_jwt("12345", "")


def test_create_app_jwt_both_missing() -> None:
    with pytest.raises(ValueError, match="must be set"):
        create_app_jwt("", "")
