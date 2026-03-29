from repositories.vipnet_repository import VipNetRepository
from services.arm_service import ArmService
from services.dictionary_service import DictionaryService
from services.audit_service import AuditService
from signals.app_signals import app_signals

class VipNetService:
    def __init__(self):
        self.repo = VipNetRepository()
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
            raise Exception(f"На АРМ с серийным номером {data['arm_serial']} уже зарегистрирован ViPNet Client.")

        skzi_name_id = self.dict_service.get_or_create_skzi_name(data.get('skzi_name'), username) if data.get('skzi_name') else None
        received_from_id = self.dict_service.get_or_create_received_from(data.get('received_from'), username) if data.get('received_from') else None

        # Подготавливаем данные для АРМ (без лишних полей)
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
            'skzi_name_id': skzi_name_id,
            'skzi_account': data.get('skzi_account'),
            'received_from_id': received_from_id,
            'receive_letter_num': data.get('receive_letter_num'),
            'install_date': data.get('install_date'),
            'installer_fio': data.get('installer_fio'),
            'status': 'ACTIVE'
        }
        self.repo.add(installation_data)

        self.audit.log("CREATE", "vipnet_installations", installation_data.get('id'), username,
                       f"ViPNet Client: {data['skzi_account']} для сотрудника ID {data['employee_id']}")
        app_signals.skzi_changed.emit()
        app_signals.employee_changed.emit()

    def update(self, installation_id, data, username):
        old = self.repo.get_by_id(installation_id)
        old_data = dict(old) if old else {}

        # Обработка АРМ
        arm_data = {
            'arm_name': data.get('arm_name', ''),
            'arm_serial': data['arm_serial'],
            'arm_type': data.get('arm_type', ''),
            'cabinet_number': data.get('cabinet_number', ''),
            'install_address': data.get('install_address', '')
        }
        arm_id = self.arm_service.get_or_create_arm(arm_data)

        # Проверка на занятость АРМ (если он изменился)
        if arm_id != old_data.get('arm_id'):
            existing = self.repo.get_by_arm_id(arm_id)
            if existing and existing['id'] != installation_id:
                raise Exception(f"АРМ с серийным номером {data['arm_serial']} уже используется другой установкой ViPNet.")

        skzi_name_id = self.dict_service.get_or_create_skzi_name(data.get('skzi_name'), username) if data.get('skzi_name') else None
        received_from_id = self.dict_service.get_or_create_received_from(data.get('received_from'), username) if data.get('received_from') else None

        installation_data = {
            'employee_id': data['employee_id'],
            'arm_id': arm_id,
            'skzi_name_id': skzi_name_id,
            'skzi_account': data.get('skzi_account'),
            'received_from_id': received_from_id,
            'receive_letter_num': data.get('receive_letter_num'),
            'install_date': data.get('install_date'),
            'installer_fio': data.get('installer_fio')
        }
        self.repo.update(installation_id, installation_data)

        new_data_for_audit = {k: v for k, v in installation_data.items() if v is not None}
        changed = {k: (old_data.get(k), installation_data[k]) for k in installation_data if old_data.get(k) != installation_data[k]}
        self.audit.log("UPDATE", "vipnet_installations", installation_id, username,
                       new_value=str(new_data_for_audit),
                       old_value=str(old_data) if old_data else None,
                       changed_fields=str(changed))
        app_signals.skzi_changed.emit()
        app_signals.employee_changed.emit()

    def mark_destroyed(self, installation_id, date, act, withdrawer, username):
        self.repo.mark_destroyed(installation_id, date, act, withdrawer)
        self.audit.log("DESTROY", "vipnet_installations", installation_id, username,
                       f"Уничтожение ViPNet, акт {act}")
        app_signals.skzi_changed.emit()
        app_signals.employee_changed.emit()

    def mass_mark_destroyed(self, ids, date, act, withdrawer, username):
        self.repo.mass_mark_destroyed(ids, date, act, withdrawer)
        for _id in ids:
            self.audit.log("DESTROY", "vipnet_installations", _id, username,
                           f"Уничтожение ViPNet (массовое), акт {act}")
        app_signals.skzi_changed.emit()
        app_signals.employee_changed.emit()