import hashlib
import hmac
import os
import sys
from pathlib import Path

os.environ["GITHUB_WEBHOOK_SECRET"] = "test-secret"
os.environ["DATABASE_URL"] = "sqlite://"

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

TEST_WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]


def sign_body(raw_body: bytes) -> str:
    return "sha256=" + hmac.new(TEST_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()