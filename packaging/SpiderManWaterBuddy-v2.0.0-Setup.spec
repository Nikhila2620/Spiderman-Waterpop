# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT_DIR = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT_DIR / 'src' / 'installer_gui.py')],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=[(str(ROOT_DIR / 'dist' / 'SpiderManWaterBuddy-v2.0.0-Portable.zip'), '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SpiderManWaterBuddy-v2.0.0-Setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(ROOT_DIR / 'assets' / 'images' / 'app_icon.ico')],
)
