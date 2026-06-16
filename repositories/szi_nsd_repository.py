from db.db_manager import DatabaseManager
from core.enums import SkziStatus


class SziNsdRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self):
        """
        Возвращает список всех активных установок СЗИ от НСД
        с объединёнными данными из справочников.
        """
        query = """
        SELECT
            s.id,
            e.fio,
            d.name AS department,
            a.arm_name,
            a.arm_serial,
            at.name AS arm_type,
            a.cabinet_number,
            sz.name AS szi_nsd,
            addr.name AS install_address,
            s.install_date,
            s.installer_fio
        FROM szi_nsd_installations s
        LEFT JOIN employees e ON s.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN arm a ON s.arm_id = a.id
        LEFT JOIN arm_types at ON a.arm_type_id = at.id
        LEFT JOIN szi_nsd_names sz ON s.szi_nsd_id = sz.id
        LEFT JOIN addresses addr ON a.install_address_id = addr.id
        WHERE s.status = 'ACTIVE'
        ORDER BY s.id DESC
        """
        cursor = self.db.execute_query(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, installation_id):
        cursor = self.db.execute_query(
            "SELECT * FROM szi_nsd_installations WHERE id = ?", (installation_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_arm_id(self, arm_id):
        """
        Проверяет, есть ли активная установка СЗИ от НСД на данном АРМ.
        """
        cursor = self.db.execute_query(
            "SELECT id FROM szi_nsd_installations WHERE arm_id = ? AND status = 'ACTIVE'",
            (arm_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def add(self, data):
        """
        Добавляет новую запись в szi_nsd_installations.
        Ожидает словарь с ключами:
        - employee_id
        - arm_id
        - szi_nsd_id
        - install_date
        - installer_fio
        - status (по умолчанию 'ACTIVE')
        """
        query = """
        INSERT INTO szi_nsd_installations (
            employee_id, arm_id, szi_nsd_id, install_date, installer_fio, status
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            data["employee_id"],
            data["arm_id"],
            data.get("szi_nsd_id"),
            data.get("install_date"),
            data.get("installer_fio"),
            data.get("status", SkziStatus.ACTIVE)
        )
        self.db.execute_query(query, params)
        self.db.commit()

    def update(self, installation_id, data):
        """
        Обновляет существующую запись.
        """
        query = """
        UPDATE szi_nsd_installations SET
            employee_id = ?,
            arm_id = ?,
            szi_nsd_id = ?,
            install_date = ?,
            installer_fio = ?
        WHERE id = ?
        """
        params = (
            data["employee_id"],
            data["arm_id"],
            data.get("szi_nsd_id"),
            data.get("install_date"),
            data.get("installer_fio"),
            installation_id
        )
        self.db.execute_query(query, params)
        self.db.commit()

    def mark_destroyed(self, installation_id, withdrawal_date, destruction_act_num, withdrawer_fio):
        """
        Помечает запись как уничтоженную.
        """
        query = """
        UPDATE szi_nsd_installations
        SET status = 'DESTROYED',
            withdrawal_date = ?,
            destruction_act_num = ?,
            withdrawer_fio = ?
        WHERE id = ?
        """
        self.db.execute_query(
            query, (withdrawal_date, destruction_act_num, withdrawer_fio, installation_id)
        )
        self.db.commit()

    def mass_mark_destroyed(self, ids, withdrawal_date, destruction_act_num, withdrawer_fio):
        """
        Массовое уничтожение записей.
        """
        # GUARD: пустой список → IN () — синтаксическая ошибка SQLite
        if not ids:
            return

        # Дополнительная защита: все элементы должны быть целыми числами
        ids = [int(i) for i in ids]

        placeholders = ','.join(['?' for _ in ids])
        query = f"""
        UPDATE szi_nsd_installations
        SET status = 'DESTROYED',
            withdrawal_date = ?,
            destruction_act_num = ?,
            withdrawer_fio = ?
        WHERE id IN ({placeholders})
        """
        params = [withdrawal_date, destruction_act_num, withdrawer_fio] + ids
        self.db.execute_query(query, params)
        self.db.commit()