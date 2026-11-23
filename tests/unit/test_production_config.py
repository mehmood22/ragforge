import pytest
from pydantic import ValidationError

from ragforge.core.config import Settings


def test_production_requires_groq_key() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            environment="production",
            database_url=("postgresql+asyncpg://user:pass@localhost/test"),
            jwt_secret="a" * 64,
            groq_api_key=None,
        )


def test_production_rejects_test_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            environment="production",
            database_url=("postgresql+asyncpg://user:pass@localhost/test"),
            jwt_secret=("ragforge-test-only-secret-not-for-production"),
            groq_api_key="test-placeholder",
        )


def test_production_accepts_valid_configuration() -> None:
    settings = Settings(
        _env_file=None,
        environment="production",
        database_url=("postgresql+asyncpg://user:pass@localhost/test"),
        jwt_secret="a" * 64,
        groq_api_key="test-placeholder",
        debug=False,
    )

    assert settings.environment == "production"
    assert settings.debug is False
