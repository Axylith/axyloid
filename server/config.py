"""Configuration loaded from environment variables.

In production (Cloud Run), all values come from Secret Manager.
In development, set them via .env or shell export.

Required:
  GITHUB_APP_ID            — numeric app ID, see GitHub App settings
  GITHUB_PRIVATE_KEY_PATH  — path to the .pem private key file
  GITHUB_WEBHOOK_SECRET    — shared secret for HMAC verification

Optional:
  LOG_LEVEL                — DEBUG, INFO (default), WARNING, ERROR
  PORT                     — server port (default 8080; Cloud Run uses this)
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    github_app_id: int
    github_private_key_path: Path
    github_webhook_secret: str

    log_level: str = "INFO"
    port: int = 8080

    # Optional, useful for development:
    debug: bool = False

    @property
    def private_key(self) -> str:
        """Read the PEM file. Validates that it exists at startup."""
        if not self.github_private_key_path.exists():
            raise FileNotFoundError(
                f"GitHub App private key not found: {self.github_private_key_path}"
            )
        return self.github_private_key_path.read_text()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Lazily load and cache settings. Use this everywhere instead of instantiating."""
    return Settings()