import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
        self.github_app_id: str = os.getenv("GITHUB_APP_ID", "")
        self.github_app_private_key_path: str = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH", "")
        self.github_client_id: str = os.getenv("GITHUB_CLIENT_ID", "")
        self.github_client_secret: str = os.getenv("GITHUB_CLIENT_SECRET", "")
        self.github_app_slug: str = os.getenv("GITHUB_APP_SLUG", "")
        self.github_redirect_uri: str = os.getenv(
            "GITHUB_REDIRECT_URI", "http://localhost:8000/auth/callback"
        )
        self.frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.database_url: str = os.getenv(
            "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/quorum"
        )
        self.context_budget_estimated_tokens: int = int(
            os.getenv("CONTEXT_BUDGET_ESTIMATED_TOKENS", "8000")
        )
        self.context_chars_per_token: int = int(
            os.getenv("CONTEXT_CHARS_PER_TOKEN", "4")
        )
        self.context_min_context_lines: int = int(
            os.getenv("CONTEXT_MIN_CONTEXT_LINES", "2")
        )


settings = Settings()