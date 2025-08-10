from __future__ import annotations
from integrations.auth_supabase import SupabaseAuth


def test_sample_mode_returns_mock_session():
    auth = SupabaseAuth(url=None, anon_key=None, sample_mode=True)
    session = auth.sign_in_with_google()
    assert session.user_id == "sample-user-123"
    assert session.email.endswith("@local.dev")