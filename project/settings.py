from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra="ignore",   # <-- add this line
    )

    app_name: str = "AI Study Buddy"
    app_env: str = "development"
    app_log_level: str = "INFO"
    enable_dark_mode: bool = False

    sqlite_path: str = "./ai_study_buddy.db"

    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None

    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    @property
    def sample_mode(self) -> bool:
        return not (self.supabase_url and self.supabase_anon_key)

def load_settings() -> Settings:
    return Settings()
