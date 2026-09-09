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
        self.database_url: str = os.getenv(
            "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/quorum"
        )


settings = Settings()