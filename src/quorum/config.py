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
        self.semgrep_ruleset: str = os.getenv("SEMGREP_RULESET", "p/security-audit")
        self.semgrep_timeout_seconds: int = int(
            os.getenv("SEMGREP_TIMEOUT_SECONDS", "120")
        )
        self.sandbox_image: str = os.getenv("SANDBOX_IMAGE", "quorum-sandbox:latest")
        self.sandbox_timeout_seconds: int = int(
            os.getenv("SANDBOX_TIMEOUT_SECONDS", "60")
        )
        self.sandbox_memory_limit: str = os.getenv("SANDBOX_MEMORY_LIMIT", "256m")
        self.sandbox_pids_limit: int = int(os.getenv("SANDBOX_PIDS_LIMIT", "256"))
        self.sandbox_tmpfs_size: str = os.getenv("SANDBOX_TMPFS_SIZE", "64m")
        self.sandbox_workdir: str = os.getenv("SANDBOX_WORKDIR", "/workspace")
        self.ollama_base_url: str = os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self.ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
        self.ollama_timeout_seconds: int = int(
            os.getenv("OLLAMA_TIMEOUT_SECONDS", "300")
        )
        self.ollama_temperature: float = float(
            os.getenv("OLLAMA_TEMPERATURE", "0.0")
        )
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url: str = os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")
        self.openai_security_model: str = os.getenv(
            "OPENAI_SECURITY_MODEL", "gpt-5.6-terra"
        )
        self.openai_test_model: str = os.getenv(
            "OPENAI_TEST_MODEL", "gpt-5.6-terra"
        )
        self.openai_chat_model: str = os.getenv(
            "OPENAI_CHAT_MODEL", "gpt-5.6-luna"
        )
        self.openai_timeout_seconds: int = int(
            os.getenv("OPENAI_TIMEOUT_SECONDS", "300")
        )


settings = Settings()