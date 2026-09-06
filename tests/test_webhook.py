import hashlib
import hmac

from quorum.github.webhook import verify_signature

SECRET = "test-secret"


def _sign(raw_body: bytes) -> str:
    return "sha256=" + hmac.new(SECRET.encode(), raw_body, hashlib.sha256).hexdigest()


def test_verify_signature_valid() -> None:
    body = b'{"action": "opened"}'
    assert verify_signature(SECRET, body, _sign(body)) is True


def test_verify_signature_invalid() -> None:
    body = b'{"action": "opened"}'
    assert verify_signature(SECRET, body, _sign(b'{"action": "closed"}')) is False


def test_verify_signature_missing() -> None:
    assert verify_signature(SECRET, b"{}", None) is False


def test_verify_signature_malformed() -> None:
    assert verify_signature(SECRET, b"{}", "not-a-signature") is False


def test_verify_signature_empty_secret() -> None:
    assert verify_signature("", b"{}", _sign(b"{}")) is False