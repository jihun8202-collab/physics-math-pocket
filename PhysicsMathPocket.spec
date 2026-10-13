# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "data"), "data"),
        (str(ROOT / "assets" / "physics_pocket.png"), "assets"),
        (str(ROOT / "assets" / "physics_pocket.ico"), "assets"),
        (str(ROOT / "SOURCES.md"), "."),
        (str(ROOT / "DESIGN_NOTES.md"), "."),
        (str(ROOT / "LICENSE.md"), "."),
        (str(ROOT / "README_KO.md"), "."),
        (str(ROOT / "START_HERE.txt"), "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PhysicsMathPocket",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "physics_pocket.ico"),
    version=str(ROOT / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PhysicsMathPocket",
)
