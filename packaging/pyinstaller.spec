# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None
APP_NAME = "AI-Study-Buddy"

# Build relative to repo root (run pyinstaller from repo root)
REPO_ROOT = Path(os.getcwd())
ENTRY = REPO_ROOT / "scripts" / "dev_run.py"
ICON = REPO_ROOT / "packaging" / "app.ico"

# Pull Qt data (simple, reliable; you can slim later)
qt_datas = collect_data_files("PyQt6")

# Ship extras with the app
extra_datas = [
    (str(REPO_ROOT / ".env.sample"), "."),
    (str(REPO_ROOT / "README.md"), "."),
    (str(REPO_ROOT / "migrations"), "migrations"),
]
# Optionally include real .env if present (be mindful of secrets)
if (REPO_ROOT / ".env").exists():
    extra_datas.append((str(REPO_ROOT / ".env"), "."))

a = Analysis(
    [str(ENTRY)],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=qt_datas + extra_datas,
    hiddenimports=collect_submodules("PyQt6"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    name=APP_NAME,
    icon=str(ICON),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # hide console window
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name=APP_NAME,
)
