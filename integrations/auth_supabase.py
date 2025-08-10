from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Session:
    user_id: str
    email: str
    provider: str = "google"


class SupabaseAuth:
    """
    Stubbed Supabase authentication. In sample mode, returns a mock session.
    Later milestones could integrate actual Supabase client.
    """

    def __init__(self, url: Optional[str], anon_key: Optional[str], sample_mode: bool):
        self.url = url
        self.anon_key = anon_key
        self.sample_mode = sample_mode

    def sign_in_with_google(self) -> Session:
        # Return a mock session when running in sample mode or missing keys
        if self.sample_mode or not (self.url and self.anon_key):
            return Session(user_id="sample-user-123", email="sample@local.dev")
        # Real sign-in would involve launching a browser and retrieving OAuth tokens.
        # For testing (CI), we can read from an environment variable as fallback.
        import os
        email = os.getenv("TEST_EMAIL", "user@example.com")
        return Session(user_id="real-user-001", email=email)

    def sign_out(self) -> None:
        return None