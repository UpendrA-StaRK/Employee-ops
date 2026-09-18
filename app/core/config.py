"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object.

    Values are read from environment variables (case-insensitive).
    A .env file is automatically loaded when present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Employee Operations AI"
    app_version: str = "0.1.0"
    app_env: str = "development"

    # Logging
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+psycopg2://user:password@localhost:5432/employee_ops"


# Module-level singleton - import this everywhere instead of instantiating Settings directly.
settings = Settings()