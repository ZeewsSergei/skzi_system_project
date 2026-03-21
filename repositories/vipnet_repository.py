from db.db_manager import DatabaseManager

class VipNetRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self):
        """
        Возвращает список всех активных установок ViPNet Client
        с объединёнными данными из справочников.
        """
        query = """
        SELECT
            v.id,
            e.fio,
            d.name AS department,
            a.arm_name,
            a.arm_serial,
            at.name AS arm_type,
            a.cabinet_number,
            sn.name AS skzi_name,
            v.skzi_account,
            addr.name AS install_address,
            v.install_date,
            v.received_from_id,
            rf.name AS received_from,
            v.receive_letter_num,
            v.installer_fio
        FROM vipnet_installations v
        LEFT JOIN employees e ON v.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN arm a ON v.arm_id = a.id
        LEFT JOIN arm_types at ON a.arm_type_id = at.id
        LEFT JOIN skzi_names sn ON v.skzi_name_id = sn.id
        LEFT JOIN addresses addr ON a.install_address_id = addr.id
        LEFT JOIN received_from rf ON v.received_from_id = rf.id
        WHERE v.status = 'ACTIVE'
        ORDER BY v.id DESC
        """
        cursor = self.db.execute_query(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, installation_id):
        cursor = self.db.execute_query(
            "SELECT * FROM vipnet_installations WHERE id = ?", (installation_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_arm_id(self, arm_id):
        """
        Проверяет, есть ли активная установка ViPNet на данном АРМ.
        """
        cursor = self.db.execute_query(
            "SELECT id FROM vipnet_installations WHERE arm_id = ? AND status = 'ACTIVE'",
            (arm_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def add(self, data):
        """
        Добавляет новую запись в vipnet_installations.
        Ожидает словарь с ключами:
        - employee_id
        - arm_id
        - skzi_name_id
        - skzi_account
        - received_from_id
        - receive_letter_num
        - install_date
        - installer_fio
        - status (по умолчанию 'ACTIVE')
        """
        query = """
        INSERT INTO vipnet_installations (
            employee_id, arm_id, skzi_name_id, skzi_account,
            received_from_id, receive_letter_num, install_date, installer_fio, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data["employee_id"],
            data["arm_id"],
            data.get("skzi_name_id"),
            data.get("skzi_account"),
            data.get("received_from_id"),
            data.get("receive_letter_num"),
            data.get("install_date"),
            data.get("installer_fio"),
            data.get("status", "ACTIVE")
        )
        self.db.execute_query(query, params)
        self.db.commit()

    def update(self, installation_id, data):
        """
        Обновляет существующую запись.
        """
        query = """
        UPDATE vipnet_installations SET
            employee_id = ?,
            arm_id = ?,
            skzi_name_id = ?,
            skzi_account = ?,
            received_from_id = ?,
            receive_letter_num = ?,
            install_date = ?,
            installer_fio = ?
        WHERE id = ?
        """
        params = (
            data["employee_id"],
            data["arm_id"],
            data.get("skzi_name_id"),
            data.get("skzi_account"),
            data.get("received_from_id"),
            data.get("receive_letter_num"),
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
        UPDATE vipnet_installations
        SET status = 'DESTROYED',
            withdrawal_date = ?,
            destruction_act_num = ?,
            withdrawer_fio = ?
        WHERE id = ?
        """
        self.db.execute_query(query, (withdrawal_date, destruction_act_num, withdrawer_fio, installation_id))
        self.db.commit()

    def mass_mark_destroyed(self, ids, withdrawal_date, destruction_act_num, withdrawer_fio):
        """
        Массовое уничтожение записей.
        """
        placeholders = ','.join(['?' for _ in ids])
        query = f"""
        UPDATE vipnet_installations
        SET status = 'DESTROYED',
            withdrawal_date = ?,
            destruction_act_num = ?,
            withdrawer_fio = ?
        WHERE id IN ({placeholders})
        """
        params = [withdrawal_date, destruction_act_num, withdrawer_fio] + ids
        self.db.execute_query(query, params)
        self.db.commit()