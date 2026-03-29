# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources', 'resources'), ('db', 'db'), ('forms', 'forms'), ('repositories', 'repositories'), ('services', 'services'), ('signals', 'signals'), ('utils', 'utils'), ('widgets', 'widgets'), ('security', 'security'), ('login_window.py', '.'), ('database_init.py', '.'), ('main_window.py', '.')],
    hiddenimports=['login_window', 'database_init', 'main_window', 'db.db_manager', 'db.__init__', 'secrets', 'hashlib', 'ctypes', 'sqlite3', 'pandas', 'openpyxl', 'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtSvg'],
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
    name='Учет СКЗИ',
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
    icon=['resources\\app_icon.ico'],
)
