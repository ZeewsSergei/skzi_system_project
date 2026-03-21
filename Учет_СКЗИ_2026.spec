# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('resources', 'resources'), ('forms', 'forms'), ('security', 'security'), ('utils', 'utils'), ('widgets', 'widgets'), ('database', 'database'), ('db', 'db'), ('repositories', 'repositories'), ('services', 'services'), ('signals', 'signals'), ('database_init.py', '.'), ('login_window.py', '.'), ('main_window.py', '.'), ('register_window.py', '.')]
binaries = []
hiddenimports = ['sqlite3', 'secrets', 'pandas', 'numpy', 'openpyxl', 'pytz', 'dateutil', 'repositories.skzi_name_repository', 'repositories.media_type_repository', 'repositories.received_from_repository', 'repositories.arm_type_repository', 'repositories.os_version_repository', 'repositories.antivirus_repository', 'repositories.szi_nsd_name_repository', 'repositories.address_repository']
tmp_ret = collect_all('pandas')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='Учет_СКЗИ_2026',
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
