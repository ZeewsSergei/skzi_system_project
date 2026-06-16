from repositories.skzi_name_repository import SkziNameRepository
from repositories.media_type_repository import MediaTypeRepository
from repositories.received_from_repository import ReceivedFromRepository
from repositories.arm_type_repository import ArmTypeRepository
from repositories.os_version_repository import OsVersionRepository
from repositories.antivirus_repository import AntivirusRepository
from repositories.szi_nsd_name_repository import SziNsdNameRepository
from repositories.address_repository import AddressRepository
from services.audit_service import AuditService

class DictionaryService:
    def __init__(self):
        self.skzi_name_repo = SkziNameRepository()
        self.media_type_repo = MediaTypeRepository()
        self.received_from_repo = ReceivedFromRepository()
        self.arm_type_repo = ArmTypeRepository()
        self.os_version_repo = OsVersionRepository()
        self.antivirus_repo = AntivirusRepository()
        self.szi_nsd_name_repo = SziNsdNameRepository()
        self.address_repo = AddressRepository()
        self.audit = AuditService()

    # SkziName
    def get_skzi_names(self):
        return self.skzi_name_repo.get_all()

    def get_or_create_skzi_name(self, name, username="system"):
        print(f"DictionaryService.get_or_create_skzi_name: name='{name}'")
        if not name:
            return None
        existing = self.skzi_name_repo.get_by_name(name)
        if existing:
            # Убедимся, что existing - словарь
            if isinstance(existing, dict) and 'id' in existing:
                return existing['id']
            else:
                # Если по какой-то причине existing не словарь, логируем и возвращаем его как ID (если это число)
                print(f"Warning: existing имеет неожиданный тип {type(existing)}. Возвращаем как есть.")
                return existing if isinstance(existing, (int, str)) else None
        else:
            new_id = self.skzi_name_repo.add(name)
            self.audit.log("CREATE", "skzi_names", new_id, username, f"Наименование СКЗИ: {name}")
            return new_id

    # MediaType
    def get_media_types(self):
        return self.media_type_repo.get_all()

    def get_or_create_media_type(self, name, username="system"):
        print(f"DictionaryService.get_or_create_media_type: name='{name}'")
        if not name:
            return None
        existing = self.media_type_repo.get_by_name(name)
        if existing:
            if isinstance(existing, dict) and 'id' in existing:
                return existing['id']
            else:
                print(f"Warning: existing имеет неожиданный тип {type(existing)}. Возвращаем как есть.")
                return existing if isinstance(existing, (int, str)) else None
        else:
            new_id = self.media_type_repo.add(name)
            self.audit.log("CREATE", "media_types", new_id, username, f"Тип носителя: {name}")
            return new_id

    # ReceivedFrom
    def get_received_from(self):
        return self.received_from_repo.get_all()

    def get_or_create_received_from(self, name, username="system"):
        print(f"DictionaryService.get_or_create_received_from: name='{name}'")
        if not name:
            return None
        existing = self.received_from_repo.get_by_name(name)
        if existing:
            if isinstance(existing, dict) and 'id' in existing:
                return existing['id']
            else:
                print(f"Warning: existing имеет неожиданный тип {type(existing)}. Возвращаем как есть.")
                return existing if isinstance(existing, (int, str)) else None
        else:
            new_id = self.received_from_repo.add(name)
            self.audit.log("CREATE", "received_from", new_id, username, f"От кого получен: {name}")
            return new_id

    # ArmType
    def get_arm_types(self):
        return self.arm_type_repo.get_all()

    def get_or_create_arm_type(self, name, username="system"):
        print(f"DictionaryService.get_or_create_arm_type: name='{name}'")
        if not name:
            return None
        existing = self.arm_type_repo.get_by_name(name)
        if existing:
            if isinstance(existing, dict) and 'id' in existing:
                return existing['id']
            else:
                print(f"Warning: existing имеет неожиданный тип {type(existing)}. Возвращаем как есть.")
                return existing if isinstance(existing, (int, str)) else None
        else:
            new_id = self.arm_type_repo.add(name)
            self.audit.log("CREATE", "arm_types", new_id, username, f"Тип АРМ: {name}")
            return new_id

    # OsVersion
    def get_os_versions(self):
        return self.os_version_repo.get_all()

    def get_or_create_os_version(self, name, username="system"):
        print(f"DictionaryService.get_or_create_os_version: name='{name}'")
        if not name:
            return None
        existing = self.os_version_repo.get_by_name(name)
        if existing:
            if isinstance(existing, dict) and 'id' in existing:
                return existing['id']
            else:
                print(f"Warning: existing имеет неожиданный тип {type(existing)}. Возвращаем как есть.")
                return existing if isinstance(existing, (int, str)) else None
        else:
            new_id = self.os_version_repo.add(name)
            self.audit.log("CREATE", "os_versions", new_id, username, f"ОС: {name}")
            return new_id

    # Antivirus
    def get_antiviruses(self):
        return self.antivirus_repo.get_all()

    def get_or_create_antivirus(self, name, username="system"):
        print(f"DictionaryService.get_or_create_antivirus: name='{name}'")
        if not name:
            return None
        existing = self.antivirus_repo.get_by_name(name)
        if existing:
            if isinstance(existing, dict) and 'id' in existing:
                return existing['id']
            else:
                print(f"Warning: existing имеет неожиданный тип {type(existing)}. Возвращаем как есть.")
                return existing if isinstance(existing, (int, str)) else None
        else:
            new_id = self.antivirus_repo.add(name)
            self.audit.log("CREATE", "antiviruses", new_id, username, f"Антивирус: {name}")
            return new_id

    # SziNsdName
    def get_szi_nsd_names(self):
        return self.szi_nsd_name_repo.get_all()

    def get_or_create_szi_nsd_name(self, name, username="system"):
        print(f"DictionaryService.get_or_create_szi_nsd_name: name='{name}'")
        if not name:
            return None
        existing = self.szi_nsd_name_repo.get_by_name(name)
        if existing:
            if isinstance(existing, dict) and 'id' in existing:
                return existing['id']
            else:
                print(f"Warning: existing имеет неожиданный тип {type(existing)}. Возвращаем как есть.")
                return existing if isinstance(existing, (int, str)) else None
        else:
            new_id = self.szi_nsd_name_repo.add(name)
            self.audit.log("CREATE", "szi_nsd_names", new_id, username, f"СЗИ от НСД: {name}")
            return new_id

    # Address
    def get_addresses(self):
        return self.address_repo.get_all()

    def get_or_create_address(self, name, username="system"):
        print(f"DictionaryService.get_or_create_address: name='{name}'")
        if not name:
            return None
        existing = self.address_repo.get_by_name(name)
        if existing:
            if isinstance(existing, dict) and 'id' in existing:
                return existing['id']
            else:
                print(f"Warning: existing имеет неожиданный тип {type(existing)}. Возвращаем как есть.")
                return existing if isinstance(existing, (int, str)) else None
        else:
            new_id = self.address_repo.add(name)
            self.audit.log("CREATE", "addresses", new_id, username, f"Адрес: {name}")
            return new_id