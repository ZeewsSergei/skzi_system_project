from repositories.szi_nsd_repository import SziNsdRepository
from services.arm_service import ArmService
from services.dictionary_service import DictionaryService
from services.audit_service import AuditService
from signals.app_signals import app_signals

class SziNsdService:
    def __init__(self):
        self.repo = SziNsdRepository()
        self.arm_service = ArmService()
        self.dict_service = DictionaryService()
        self.audit = AuditService()

    def get_all_active(self):
        return self.repo.get_all()

    def get_by_id(self, installation_id):
        return self.repo.get_by_id(installation_id)

    def register(self, data, username):
        existing = self.repo.get_by_arm_id(data['arm_id']) if data.get('arm_id') else None
        if existing:
            raise Exception(f"На АРМ с серийным номером {data['arm_serial']} уже зарегистрировано СЗИ от НСД.")

        szi_nsd_id = self.dict_service.get_or_create_szi_nsd_name(data.get('szi_nsd'), username) if data.get('szi_nsd') else None

        arm_data = {
            'arm_name': data.get('arm_name', ''),
            'arm_serial': data['arm_serial'],
            'arm_type': data.get('arm_type', ''),
            'cabinet_number': data.get('cabinet_number', ''),
            'install_address': data.get('install_address', '')
        }
        arm_id = self.arm_service.get_or_create_arm(arm_data)

        installation_data = {
            'employee_id': data['employee_id'],
            'arm_id': arm_id,
            'szi_nsd_id': szi_nsd_id,
            'install_date': data.get('install_date'),
            'installer_fio': data.get('installer_fio'),
            'status': 'ACTIVE'
        }
        self.repo.add(installation_data)

        self.audit.log("CREATE", "szi_nsd_installations", installation_data.get('id'), username,
                       f"СЗИ от НСД: {data.get('szi_nsd')} для сотрудника ID {data['employee_id']}")
        app_signals.skzi_changed.emit()
        app_signals.employee_changed.emit()

    def update(self, installation_id, data, username):
        old = self.repo.get_by_id(installation_id)
        old_data = dict(old) if old else {}

        arm_data = {
            'arm_name': data.get('arm_name', ''),
            'arm_serial': data['arm_serial'],
            'arm_type': data.get('arm_type', ''),
            'cabinet_number': data.get('cabinet_number', ''),
            'install_address': data.get('install_address', '')
        }
        arm_id = self.arm_service.get_or_create_arm(arm_data)

        if arm_id != old_data.get('arm_id'):
            existing = self.repo.get_by_arm_id(arm_id)
            if existing and existing['id'] != installation_id:
                raise Exception(f"АРМ с серийным номером {data['arm_serial']} уже используется другой установкой СЗИ от НСД.")

        szi_nsd_id = self.dict_service.get_or_create_szi_nsd_name(data.get('szi_nsd'), username) if data.get('szi_nsd') else None

        installation_data = {
            'employee_id': data['employee_id'],
            'arm_id': arm_id,
            'szi_nsd_id': szi_nsd_id,
            'install_date': data.get('install_date'),
            'installer_fio': data.get('installer_fio')
        }
        self.repo.update(installation_id, installation_data)

        new_data_for_audit = {k: v for k, v in installation_data.items() if v is not None}
        changed = {k: (old_data.get(k), installation_data[k]) for k in installation_data if old_data.get(k) != installation_data[k]}
        self.audit.log("UPDATE", "szi_nsd_installations", installation_id, username,
                       new_value=str(new_data_for_audit),
                       old_value=str(old_data) if old_data else None,
                       changed_fields=str(changed))
        app_signals.skzi_changed.emit()
        app_signals.employee_changed.emit()

    def mark_destroyed(self, installation_id, date, act, withdrawer, username):
        self.repo.mark_destroyed(installation_id, date, act, withdrawer)
        self.audit.log("DESTROY", "szi_nsd_installations", installation_id, username,
                       f"Уничтожение СЗИ от НСД, акт {act}")
        app_signals.skzi_changed.emit()
        app_signals.employee_changed.emit()

    def mass_mark_destroyed(self, ids, date, act, withdrawer, username):
        self.repo.mass_mark_destroyed(ids, date, act, withdrawer)
        for _id in ids:
            self.audit.log("DESTROY", "szi_nsd_installations", _id, username,
                           f"Уничтожение СЗИ от НСД (массовое), акт {act}")
        app_signals.skzi_changed.emit()
        app_signals.employee_changed.emit()