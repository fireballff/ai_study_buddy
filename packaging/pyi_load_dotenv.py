# packaging/pyi_load_dotenv.py
import os, sys, pathlib
try:
    from dotenv import load_dotenv
except Exception:
    # If python-dotenv isn't installed, just skip quietly
    load_dotenv = None

def _load_env_from_exe_dir():
    try:
        if getattr(sys, "frozen", False):
            base = pathlib.Path(sys.executable).parent
        else:
            # when running from source, assume repo root ≈ this file's parent two levels up
            base = pathlib.Path(__file__).resolve().parents[1]
        env_path = base / ".env"
        if load_dotenv and env_path.exists():
            load_dotenv(env_path)
    except Exception:
        # don't crash the app if env loading fails
        pass

_load_env_from_exe_dir()
