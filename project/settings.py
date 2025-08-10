from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

    # App settings
    app_name: str = "AI Study Buddy"
    app_env: str = "development"
    app_log_level: str = "INFO"
    enable_dark_mode: bool = False

    # Database
    sqlite_path: str = "./ai_study_buddy.db"

    # Supabase
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None

    # Google OAuth (unused in sample mode)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    @property
    def sample_mode(self) -> bool:
        """
        Indicates whether the app is running without external APIs.
        Sample mode is enabled when required keys are not provided.
        """
        return not (self.supabase_url and self.supabase_anon_key)


def load_settings() -> Settings:
    return Settings()