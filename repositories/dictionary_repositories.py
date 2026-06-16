# repositories/dictionary_repositories.py
"""
УСТАРЕВШИЙ МОДУЛЬ.
Оставлен для совместимости со сборкой PyInstaller.

Реальные репозитории справочников находятся в отдельных файлах:
    repositories/skzi_name_repository.py
    repositories/media_type_repository.py
    repositories/arm_type_repository.py
    repositories/address_repository.py
    repositories/os_version_repository.py
    repositories/szi_nsd_name_repository.py
    repositories/antivirus_repository.py
    repositories/received_from_repository.py

Этот файл является реэкспортом из перечисленных модулей,
чтобы старый код `from repositories.dictionary_repositories import X`
продолжал работать без изменений.

ВНИМАНИЕ: BaseRepository.get_by_name() возвращает только id (int),
тогда как отдельные репозитории возвращают dict {'id': ..., 'name': ...}.
DictionaryService использует отдельные репозитории — не используйте
этот файл в новом коде.
"""

import warnings

warnings.warn(
    "dictionary_repositories устарел. "
    "Импортируйте классы из отдельных файлов репозиториев.",
    DeprecationWarning,
    stacklevel=2,
)

# Реэкспортируем из реальных репозиториев
from repositories.skzi_name_repository import SkziNameRepository
from repositories.media_type_repository import MediaTypeRepository
from repositories.arm_type_repository import ArmTypeRepository
from repositories.address_repository import AddressRepository
from repositories.os_version_repository import OsVersionRepository
from repositories.szi_nsd_name_repository import SziNsdNameRepository
from repositories.antivirus_repository import AntivirusRepository
from repositories.received_from_repository import ReceivedFromRepository

__all__ = [
    'SkziNameRepository',
    'MediaTypeRepository',
    'ArmTypeRepository',
    'AddressRepository',
    'OsVersionRepository',
    'SziNsdNameRepository',
    'AntivirusRepository',
    'ReceivedFromRepository',
]