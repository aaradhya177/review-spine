from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Review Spine"
    app_env: Literal["local", "test", "staging", "production"] = "local"
    log_level: str = "INFO"
    backend_cors_origins: list[AnyHttpUrl] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    tiger_database_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str | None = None
    default_review_model: str | None = None
    default_embedding_model: str = "text-embedding-3-large"

    github_app_id: str | None = None
    github_webhook_secret: str | None = None
    github_private_key_path: str | None = None

    auto_post_confidence_threshold: float = Field(default=0.82, ge=0.0, le=1.0)
    daily_llm_budget_usd: float = Field(default=25.0, ge=0.0)

    def require_production_secrets(self) -> None:
        """Fail clearly when production starts without required secrets."""

        if self.app_env != "production":
            return

        missing = [
            name
            for name, value in {
                "TIGER_DATABASE_URL": self.tiger_database_url,
                "OPENAI_API_KEY": self.openai_api_key,
                "DEFAULT_REVIEW_MODEL": self.default_review_model,
                "GITHUB_APP_ID": self.github_app_id,
                "GITHUB_WEBHOOK_SECRET": self.github_webhook_secret,
                "GITHUB_PRIVATE_KEY_PATH": self.github_private_key_path,
            }.items()
            if not value
        ]
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Missing required production settings: {joined}")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.require_production_secrets()
    return settings

