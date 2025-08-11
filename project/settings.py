from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path
from pydantic import Field
import os
import platform

class Settings(BaseSettings):
    """
    App settings loaded from .env and environment.
    Extra keys are ignored so you can keep provider secrets without breaking validation.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "AI Study Buddy"
    app_env: str = "development"
    app_log_level: str = "INFO"
    enable_dark_mode: bool = False

    # Keyboard shortcuts (defaults)
    shortcut_new_item: str = "N"
    shortcut_delete_item: str = "Delete"
    shortcut_edit_item: str = "E"
    shortcut_quick_add: str = "Ctrl+K"

    # Storage defaults — put DB under user AppData unless SQLITE_PATH is set
    @staticmethod
    def _default_appdata() -> Path:
        sys = platform.system()
        if sys == "Windows":
            base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys == "Darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path.home() / ".local" / "share"
        d = base / "AI-Study-Buddy"
        d.mkdir(parents=True, exist_ok=True)
        return d

    sqlite_path: str = Field(
        default_factory=lambda: str(Settings._default_appdata() / "ai_study_buddy.db")
    )

    # Providers (kept optional; presence flips from sample→live mode)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None

    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_api_scopes: Optional[str] = None
    google_redirect_uri: Optional[str] = None

    openrouter_api_key: Optional[str] = None  # DeepSeek via OpenRouter

    @property
    def sample_mode(self) -> bool:
        """If core providers are missing keys, run in sample/mock mode."""
        # Feel free to tighten this condition if you want partial live features.
        has_supabase = bool(self.supabase_url and self.supabase_anon_key)
        return not has_supabase

def load_settings() -> Settings:
    return Settings()
