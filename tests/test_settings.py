import importlib
import sys


def test_default_path_created_on_settings_init_without_import_side_effect(tmp_path, monkeypatch):
    """Ensure importing settings doesn't create the data directory, but initializing does."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("SQLITE_PATH", raising=False)

    expected_dir = tmp_path / ".local" / "share" / "AI-Study-Buddy"
    assert not expected_dir.exists()

    # Import module fresh to ensure import doesn't trigger directory creation
    sys.modules.pop("project.settings", None)
    settings_module = importlib.import_module("project.settings")

    assert not expected_dir.exists(), "Importing settings should not create the directory"

    s = settings_module.Settings()
    assert expected_dir.exists(), "Instantiating Settings should create the directory"
    assert s.sqlite_path == str(expected_dir / "ai_study_buddy.db")
