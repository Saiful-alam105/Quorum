import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")


settings = Settings()