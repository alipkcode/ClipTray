# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Ali\\Documents\\GitHub\\ClipTray\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Ali\\Documents\\GitHub\\ClipTray\\icon.png', '.'), ('C:\\Users\\Ali\\Documents\\GitHub\\ClipTray\\clips.json', '.')],
    hiddenimports=['uiautomation', 'comtypes', 'comtypes.gen', 'comtypes.gen.UIAutomationClient'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5'],
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
    name='ClipTray',
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
)
