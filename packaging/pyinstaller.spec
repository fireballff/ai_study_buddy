# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None
APP_NAME = "AI-Study-Buddy"

REPO_ROOT = Path(os.getcwd())
ENTRY = REPO_ROOT / "scripts" / "dev_run.py"
ICON = REPO_ROOT / "packaging" / "app.ico"

# Qt data (plugins etc.)
qt_datas = collect_data_files("PyQt6")

# Runtime assets shipped with the app
extra_datas = [
    (str(REPO_ROOT / "alembic.ini"), "."),
    (str(REPO_ROOT / "migrations"), "migrations"),
    (str(REPO_ROOT / "README.md"), "."),
    
]

# Include .env if present at build time (optional; you can also drop it in later)
dotenv = REPO_ROOT / ".env"
if dotenv.exists():
    extra_datas.append((str(dotenv), "."))

# Copy all .qss under ui/, preserving folder structure
ui_dir = REPO_ROOT / "ui"
if ui_dir.exists():
    for p in ui_dir.rglob("*.qss"):
        rel_dest = str(p.parent.relative_to(REPO_ROOT))  # e.g. "ui/calendar"
        extra_datas.append((str(p), rel_dest))

# Hidden imports (kept lean to avoid Qt3D/WebEngine noise)
hidden = []
hidden += [
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.QtNetwork",
    "PyQt6.QtPrintSupport",
]
hidden += collect_submodules("sqlalchemy.dialects")
hidden += collect_submodules("dateutil")
hidden += collect_submodules("tzlocal")
hidden += [m for m in collect_submodules("alembic") if not m.startswith("alembic.testing")]
hidden += collect_submodules("googleapiclient")
hidden += collect_submodules("google.oauth2")
hidden += collect_submodules("google_auth_oauthlib")
hidden += collect_submodules("httplib2")
for pkg in ("ui", "agents", "integrations", "project"):
    hidden += collect_submodules(pkg)

# Exclude noisy/unused Qt modules
excludes = [
    "PyQt6.Qt3DCore", "PyQt6.Qt3DRender", "PyQt6.Qt3DExtras", "PyQt6.Qt3DAnimation",
    "PyQt6.QtPdf", "PyQt6.QtPdfWidgets", "PyQt6.QtNfc",
    "PyQt6.QtQuick", "PyQt6.QtQuick3D", "PyQt6.QtQuickWidgets", "PyQt6.QtQml",
    "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineQuick", "PyQt6.QtWebView",
    "PyQt6.QtHelp", "PyQt6.QtDesigner", "PyQt6.QtRemoteObjects",
    "PyQt6.QtSpatialAudio", "PyQt6.QtSensors", "PyQt6.QtSerialPort",
    "PyQt6.lupdate", "PyQt6.uic.pyuic",
    "alembic.testing", "alembic.testing.suite", "alembic.testing.plugin",
    "pytest", "py", "pluggy",
]

# Limit Qt plugins (smaller, quieter build)
hooksconfig = {
    "qt_plugins": ["platforms", "styles", "imageformats", "iconengines", "networkinformation", "tls"],
}

# Runtime hook to auto-load .env from exe folder at startup
runtime_hooks = [str(REPO_ROOT / "packaging" / "pyi_load_dotenv.py")]

a = Analysis(
    [str(ENTRY)],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=qt_datas + extra_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig=hooksconfig,
    runtime_hooks=runtime_hooks,
    excludes=excludes,
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
    upx=False,   # set True only if UPX is installed
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)
