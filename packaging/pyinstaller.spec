# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None
APP_NAME = "AI-Study-Buddy"

# Resolve paths relative to the spec file
BASE_DIR = Path(os.getcwd()) / "packaging"          # .../ai_study_buddy/packaging
REPO_ROOT = BASE_DIR.parent                         # .../ai_study_buddy
ENTRY = REPO_ROOT / "scripts" / "dev_run.py"

qt_datas = collect_data_files("PyQt6")
extra_datas = [
    (str(REPO_ROOT / ".env"), "."),
    (str(REPO_ROOT / "README.md"), "."),
    (str(REPO_ROOT / "migrations"), "migrations"),
]

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
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window
    icon=str(REPO_ROOT / "packaging" / "app.ico"),
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
