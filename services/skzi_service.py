from repositories.skzi_repository import SkziRepository
from core.enums import SkziStatus
from services.arm_service import ArmService
from services.dictionary_service import DictionaryService
from services.audit_service import AuditService
from signals.app_signals import app_signals
from db.db_manager import DatabaseManager

class SkziService:
    def __init__(self):
        self.db = DatabaseManager()
        self.repo = SkziRepository()
        self.arm_service = ArmService()
        self.dict_service = DictionaryService()
        self.audit = AuditService()

    def register_skzi(self, data, username):
        if not isinstance(data, dict):
            raise TypeError(f"register_skzi ожидает словарь, получен {type(data)}: {data}")

        skzi_name_id = self.dict_service.get_or_create_skzi_name(data.get('skzi_name')) if data.get('skzi_name') else None
        media_type_id = self.dict_service.get_or_create_media_type(data.get('media_type')) if data.get('media_type') else None
        received_from_id = self.dict_service.get_or_create_received_from(data.get('received_from')) if data.get('received_from') else None

        arm_data = {
            'arm_name': data.get('arm_name', ''),
            'arm_serial': data.get('arm_serial', ''),
            'arm_type': data.get('arm_type', ''),
            'os_version': data.get('os_version', ''),
            'antivirus': data.get('antivirus', ''),
            'szi_nsd': data.get('szi_nsd', ''),
            'cabinet_number': data.get('cabinet_number', ''),
            'install_address': data.get('install_address', '')
        }
        arm_id = self.arm_service.get_or_create_arm(arm_data)

        registry_data = {
            'employee_id': data['employee_id'],
            'arm_id': arm_id,
            'skzi_name_id': skzi_name_id,
            'skzi_number': data.get('skzi_number'),
            'skzi_instance_number': data.get('skzi_instance_number'),
            'media_type_id': media_type_id,
            'media_number': data.get('media_number'),
            'cert_number': data.get('cert_number'),
            'received_from_id': received_from_id,
            'receive_date': data.get('receive_date'),
            'receive_letter_num': data.get('receive_letter_num'),
            'install_date': data.get('install_date'),
            'expiry_date': data.get('expiry_date'),
            'installer_fio': data.get('installer_fio'),
            'knowledge_check': data.get('knowledge_check', 'не проводилась'),
            'status': SkziStatus.ACTIVE
        }
        self.repo.add_skzi(registry_data)
        self.audit.log("CREATE", "skzi_registry", registry_data.get('skzi_number'), username,
                       f"СКЗИ: {data['skzi_name']} для сотрудника ID {data['employee_id']}")
        app_signals.skzi_changed.emit()

    def update_skzi(self, skzi_id, data, username):
        if not isinstance(data, dict):
            raise TypeError(f"update_skzi ожидает словарь, получен {type(data)}: {data}")

        old = self.repo.get_by_id(skzi_id)
        old_data = dict(old) if old else {}

        skzi_name_id = self.dict_service.get_or_create_skzi_name(data.get('skzi_name')) if data.get('skzi_name') else None
        media_type_id = self.dict_service.get_or_create_media_type(data.get('media_type')) if data.get('media_type') else None
        received_from_id = self.dict_service.get_or_create_received_from(data.get('received_from')) if data.get('received_from') else None

        arm_data = {
            'arm_name': data.get('arm_name', ''),
            'arm_serial': data.get('arm_serial', ''),
            'arm_type': data.get('arm_type', ''),
            'os_version': data.get('os_version', ''),
            'antivirus': data.get('antivirus', ''),
            'szi_nsd': data.get('szi_nsd', ''),
            'cabinet_number': data.get('cabinet_number', ''),
            'install_address': data.get('install_address', '')
        }
        arm_id = self.arm_service.get_or_create_arm(arm_data)

        registry_data = {
            'employee_id': data['employee_id'],
            'arm_id': arm_id,
            'skzi_name_id': skzi_name_id,
            'skzi_number': data.get('skzi_number'),
            'skzi_instance_number': data.get('skzi_instance_number'),
            'media_type_id': media_type_id,
            'media_number': data.get('media_number'),
            'cert_number': data.get('cert_number'),
            'received_from_id': received_from_id,
            'receive_date': data.get('receive_date'),
            'receive_letter_num': data.get('receive_letter_num'),
            'install_date': data.get('install_date'),
            'expiry_date': data.get('expiry_date'),
            'installer_fio': data.get('installer_fio'),
            'knowledge_check': data.get('knowledge_check')
        }
        self.repo.update_skzi(skzi_id, registry_data)

        new_data_for_audit = {k: v for k, v in registry_data.items() if v is not None}
        changed = {k: (old_data.get(k), registry_data[k]) for k in registry_data if old_data.get(k) != registry_data[k]}
        self.audit.log("UPDATE", "skzi_registry", skzi_id, username,
                       new_value=str(new_data_for_audit),
                       old_value=str(old_data) if old_data else None,
                       changed_fields=str(changed))
        app_signals.skzi_changed.emit()

    def get_skzi_by_id(self, skzi_id):
        return self.repo.get_by_id(skzi_id)

    def get_all_active(self):
        query = """
        SELECT r.id, e.fio, d.name as department, s.name as skzi_name,
               r.skzi_number, a.cabinet_number,
               r.expiry_date, r.knowledge_check, r.status,
               a.arm_serial, at.name as arm_type,
               mt.name as media_type, r.media_number,
               r.install_date
        FROM skzi_registry r
        LEFT JOIN employees e ON r.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN skzi_names s ON r.skzi_name_id = s.id
        LEFT JOIN arm a ON r.arm_id = a.id
        LEFT JOIN arm_types at ON a.arm_type_id = at.id
        LEFT JOIN media_types mt ON r.media_type_id = mt.id
        WHERE r.status = 'ACTIVE'
        """
        cursor = self.db.execute_query(query)
        return [dict(row) for row in cursor.fetchall()]

    def get_destroyed(self):
        query = """
                SELECT r.id, e.fio, d.name as department, s.name as skzi_name,
                       r.skzi_number, r.withdrawal_date, r.destruction_act_num, r.withdrawer_fio
                FROM skzi_registry r
                LEFT JOIN employees e ON r.employee_id = e.id
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN skzi_names s ON r.skzi_name_id = s.id
                WHERE r.status = 'DESTROYED'
                UNION ALL
                SELECT v.id, e.fio, d.name as department, sn.name as skzi_name,
                       v.skzi_account as skzi_number, v.withdrawal_date, v.destruction_act_num, v.withdrawer_fio
                FROM vipnet_installations v
                LEFT JOIN employees e ON v.employee_id = e.id
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN skzi_names sn ON v.skzi_name_id = sn.id
                WHERE v.status = 'DESTROYED'
                ORDER BY withdrawal_date DESC
                """
        cursor = self.db.execute_query(query)
        return [dict(row) for row in cursor.fetchall()]

    def get_vipnet_data(self):
        return self.repo.get_vipnet_data()

    def get_szi_nsd_data(self):
        return self.repo.get_szi_nsd_data()

    def mark_destroyed(self, skzi_id, date, act, withdrawer, username):
        self.repo.mark_destroyed(skzi_id, date, act, withdrawer)
        self.audit.log("DESTROY", "skzi_registry", skzi_id, username,
                       f"Уничтожение, акт {act}")
        app_signals.destruction_changed.emit()
        app_signals.skzi_changed.emit()

    def mass_mark_destroyed(self, skzi_ids, date, act, withdrawer, username):
        # GUARD: нечего уничтожать — выходим без обращения к БД
        if not skzi_ids:
            return
        self.repo.mass_mark_destroyed(skzi_ids, date, act, withdrawer)
        for skzi_id in skzi_ids:
            self.audit.log("DESTROY", "skzi_registry", skzi_id, username,
                           f"Уничтожение (массовое), акт {act}")
        app_signals.destruction_changed.emit()
        app_signals.skzi_changed.emit()