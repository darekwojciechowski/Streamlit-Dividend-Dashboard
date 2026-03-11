"""
Environment-based settings for the Dividend Dashboard application.

Loaded from environment variables or a .env file at project root.
Override any value by setting the corresponding environment variable.

Usage:
    from config.settings import settings

    processor = DividendDataProcessor(settings.data_file_path)
"""

from pydantic import Field
from pydantic_settings import BaseSettings

from app.config.app_config import DATA_FILE_PATH


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    data_file_path: str = Field(
        default=DATA_FILE_PATH,
        alias="DATA_FILE_PATH",
        description="Path to the TSV dividend data file.",
    )

    environment: str = Field(
        default="local",
        alias="ENVIRONMENT",
        description="Deployment environment: local | staging | production.",
    )

    debug: bool = Field(
        default=False,
        alias="DEBUG",
        description="Enable debug mode (extra logging, stack traces).",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
    }

    @property
    def is_production(self) -> bool:
        """Return True when running in production."""
        return self.environment.lower() == "production"

    @property
    def is_local(self) -> bool:
        """Return True when running locally."""
        return self.environment.lower() == "local"


settings = Settings()
