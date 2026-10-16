# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/installer_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('dist/SpiderManWaterBuddy-v1.0.0-Portable.zip', '.')],
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
    name='SpiderManWaterBuddy-v1.0.0-Setup',
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
    icon=['assets/images/app_icon.ico'],
)
