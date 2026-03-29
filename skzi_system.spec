# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Указываем имя приложения
app_name = "Учет СКЗИ"

# Путь к иконке
icon_path = os.path.join('resources', 'app_icon.ico')
if not os.path.exists(icon_path):
    icon_path = None

# Файлы, которые нужно включить в сборку (datas)
datas = []

# Добавляем папку resources, если есть
if os.path.exists('resources'):
    datas.append(('resources', 'resources'))

# Добавляем все .py файлы из корневой папки (чтобы они были доступны)
python_files = []
for f in os.listdir('.'):
    if f.endswith('.py') and f not in ['setup.py', 'pyproject.toml']:
        python_files.append((f, '.'))
datas.extend(python_files)

# Добавляем папки с модулями
for folder in ['db', 'forms', 'repositories', 'services', 'signals', 'utils', 'widgets', 'security']:
    if os.path.exists(folder):
        datas.append((folder, folder))

# Собираем все скрытые импорты
hiddenimports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'pandas',
    'openpyxl',
    'sqlite3',
    'login_window',
    'database_init',
    'main_window',
    'register_window',
    'signals.app_signals',
    'utils.helpers',
    'utils.path_helper',
    'services.dictionary_service',
    'services.audit_service',
    'services.employee_service',
    'services.skzi_service',
    'services.szi_nsd_service',
    'services.vipnet_service',
    'services.arm_service',
    'services.control_service',
    'services.training_service',
    'services.department_service',
    'services.sector_service',
    'repositories.base_repository',
    'repositories.audit_repository',
    'repositories.control_repository',
    'repositories.department_repository',
    'repositories.employee_repository',
    'repositories.sector_repository',
    'repositories.skzi_repository',
    'repositories.skzi_name_repository',
    'repositories.media_type_repository',
    'repositories.received_from_repository',
    'repositories.arm_type_repository',
    'repositories.os_version_repository',
    'repositories.antivirus_repository',
    'repositories.szi_nsd_name_repository',
    'repositories.address_repository',
    'repositories.szi_nsd_repository',
    'repositories.vipnet_repository',
    'repositories.training_repository',
    'forms.backup_dialog',
    'forms.change_password_dialog',
    'forms.control_dialog',
    'forms.department_form',
    'forms.destruction_dialog',
    'forms.employee_form',
    'forms.filter_dialog',
    'forms.mass_destruction_dialog',
    'forms.skzi_form',
    'forms.szi_nsd_form',
    'forms.training_dialog',
    'forms.vipnet_form',
    'widgets.vipnet_tab',
    'widgets.szi_nsd_tab',
    'widgets.destruction_tab',
    'widgets.training_tab',
    'widgets.help_tab',
    'utils.backup',
    'utils.excel_exporter',
    'utils.tray_icon',
    'utils.path_helper',
    'db.db_manager',
    'security.auth_service',
]

# Сборка
a = Analysis(
    ['main.py'],
    pathex=['.'],                    # добавляем текущую папку в путь поиска
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                   # без консольного окна
    icon=icon_path,
)

# Сборка в одну папку
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)