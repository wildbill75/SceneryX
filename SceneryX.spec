# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\SceneryX\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\SceneryX\\airports.json', '.'), ('D:\\SceneryX\\airport_airlines.json', '.'), ('D:\\SceneryX\\airport_routes.json', '.'), ('D:\\SceneryX\\airport_runways.json', '.'), ('D:\\SceneryX\\installed_airports.json', '.'), ('D:\\SceneryX\\icon.ico', '.'), ('D:\\SceneryX\\web', 'web')],
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
    name='SceneryX',
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
    icon=['D:\\SceneryX\\icon.ico'],
)
