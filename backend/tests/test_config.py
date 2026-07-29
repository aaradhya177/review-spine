import pytest

from app.config import Settings


def test_local_settings_allow_missing_secrets() -> None:
    settings = Settings(app_env="local")

    settings.require_production_secrets()


def test_production_settings_require_secrets() -> None:
    settings = Settings(app_env="production")

    with pytest.raises(RuntimeError) as exc_info:
        settings.require_production_secrets()

    assert "TIGER_DATABASE_URL" in str(exc_info.value)
    assert "GITHUB_WEBHOOK_SECRET" in str(exc_info.value)


def test_confidence_threshold_is_validated() -> None:
    with pytest.raises(ValueError):
        Settings(auto_post_confidence_threshold=1.2)

