from db.db_manager import DatabaseManager

class SkziRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def get_by_id(self, skzi_id):
        cursor = self.db.execute_query(
            "SELECT * FROM skzi_registry WHERE id = ?", (skzi_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def add_skzi(self, data):
        query = """
        INSERT INTO skzi_registry (
            employee_id,
            arm_id,
            skzi_name_id,
            skzi_number,
            skzi_instance_number,
            skzi_account,
            media_type_id,
            media_number,
            cert_number,
            received_from_id,
            receive_date,
            receive_letter_num,
            install_date,
            expiry_date,
            installer_fio,
            knowledge_check,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data["employee_id"],
            data["arm_id"],
            data.get("skzi_name_id"),
            data.get("skzi_number"),
            data.get("skzi_instance_number"),
            data.get("skzi_account"),
            data.get("media_type_id"),
            data.get("media_number"),
            data.get("cert_number"),
            data.get("received_from_id"),
            data.get("receive_date"),
            data.get("receive_letter_num"),
            data.get("install_date"),
            data.get("expiry_date"),
            data.get("installer_fio"),
            data.get("knowledge_check", "не проводилась"),
            data.get("status", "ACTIVE")
        )
        self.db.execute_query(query, params)
        self.db.commit()

    def update_skzi(self, skzi_id, data):
        query = """
        UPDATE skzi_registry SET
            employee_id = ?,
            arm_id = ?,
            skzi_name_id = ?,
            skzi_number = ?,
            skzi_instance_number = ?,
            skzi_account = ?,
            media_type_id = ?,
            media_number = ?,
            cert_number = ?,
            received_from_id = ?,
            receive_date = ?,
            receive_letter_num = ?,
            install_date = ?,
            expiry_date = ?,
            installer_fio = ?,
            knowledge_check = ?
        WHERE id = ?
        """
        params = (
            data["employee_id"],
            data["arm_id"],
            data.get("skzi_name_id"),
            data.get("skzi_number"),
            data.get("skzi_instance_number"),
            data.get("skzi_account"),
            data.get("media_type_id"),
            data.get("media_number"),
            data.get("cert_number"),
            data.get("received_from_id"),
            data.get("receive_date"),
            data.get("receive_letter_num"),
            data.get("install_date"),
            data.get("expiry_date"),
            data.get("installer_fio"),
            data.get("knowledge_check"),
            skzi_id
        )
        self.db.execute_query(query, params)
        self.db.commit()

    def get_all_active(self):
        query = """
        SELECT
            r.id,
            e.fio,
            at.name as arm_type,
            a.arm_serial,
            sn.name as skzi_name,
            r.skzi_number,
            mt.name as media_type,
            r.media_number,
            a.cabinet_number,
            r.install_date,
            r.expiry_date,
            r.status
        FROM skzi_registry r
        LEFT JOIN employees e ON e.id = r.employee_id
        LEFT JOIN arm a ON a.id = r.arm_id
        LEFT JOIN arm_types at ON a.arm_type_id = at.id
        LEFT JOIN skzi_names sn ON r.skzi_name_id = sn.id
        LEFT JOIN media_types mt ON r.media_type_id = mt.id
        WHERE r.status = 'ACTIVE'
        ORDER BY r.install_date DESC
        """
        cursor = self.db.execute_query(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_all_active_filtered(self, filters):
        base_query = """
        SELECT
            r.id,
            e.fio,
            at.name as arm_type,
            a.arm_serial,
            sn.name as skzi_name,
            r.skzi_number,
            mt.name as media_type,
            r.media_number,
            a.cabinet_number,
            r.install_date,
            r.expiry_date,
            r.status
        FROM skzi_registry r
        LEFT JOIN employees e ON e.id = r.employee_id
        LEFT JOIN arm a ON a.id = r.arm_id
        LEFT JOIN arm_types at ON a.arm_type_id = at.id
        LEFT JOIN skzi_names sn ON r.skzi_name_id = sn.id
        LEFT JOIN media_types mt ON r.media_type_id = mt.id
        WHERE r.status = 'ACTIVE'
        """
        params = []
        if filters.get('fio'):
            base_query += " AND e.fio LIKE ?"
            params.append(f"%{filters['fio']}%")
        if filters.get('skzi_name'):
            base_query += " AND sn.name LIKE ?"
            params.append(f"%{filters['skzi_name']}%")
        if filters.get('arm_type'):
            base_query += " AND at.name LIKE ?"
            params.append(f"%{filters['arm_type']}%")
        if filters.get('cabinet_number'):
            base_query += " AND a.cabinet_number LIKE ?"
            params.append(f"%{filters['cabinet_number']}%")
        if filters.get('install_date_from'):
            base_query += " AND r.install_date >= ?"
            params.append(filters['install_date_from'])
        if filters.get('install_date_to'):
            base_query += " AND r.install_date <= ?"
            params.append(filters['install_date_to'])
        if filters.get('expiry_date_from'):
            base_query += " AND r.expiry_date >= ?"
            params.append(filters['expiry_date_from'])
        if filters.get('expiry_date_to'):
            base_query += " AND r.expiry_date <= ?"
            params.append(filters['expiry_date_to'])
        if filters.get('status') and filters['status'] != 'ACTIVE':
            base_query += " AND r.status = ?"
            params.append(filters['status'])
        base_query += " ORDER BY r.install_date DESC"
        cursor = self.db.execute_query(base_query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_vipnet_data(self):
        query = """
        SELECT
            r.id,
            e.fio,
            d.name AS department,
            a.arm_name,
            a.arm_serial,
            at.name as arm_type,
            a.cabinet_number,
            sn.name as skzi_name,
            r.skzi_account,
            addr.name as install_address
        FROM skzi_registry r
        LEFT JOIN employees e ON e.id = r.employee_id
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN arm a ON a.id = r.arm_id
        LEFT JOIN arm_types at ON a.arm_type_id = at.id
        LEFT JOIN skzi_names sn ON r.skzi_name_id = sn.id
        LEFT JOIN addresses addr ON a.install_address_id = addr.id
        WHERE r.status = 'ACTIVE'
          AND r.skzi_account IS NOT NULL
          AND r.skzi_account != ''
        ORDER BY r.id DESC
        """
        cursor = self.db.execute_query(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_szi_nsd_data(self):
        query = """
        SELECT
            r.id,
            e.fio,
            d.name AS department,
            a.arm_name,
            a.arm_serial,
            a.cabinet_number,
            sz.name as szi_nsd,
            addr.name as install_address
        FROM skzi_registry r
        LEFT JOIN employees e ON e.id = r.employee_id
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN arm a ON a.id = r.arm_id
        LEFT JOIN szi_nsd_names sz ON a.szi_nsd_id = sz.id
        LEFT JOIN addresses addr ON a.install_address_id = addr.id
        WHERE r.status = 'ACTIVE'
          AND a.szi_nsd_id IS NOT NULL
        ORDER BY r.id DESC
        """
        cursor = self.db.execute_query(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_destroyed(self):
        query = """
        SELECT
            r.id,
            e.fio,
            sn.name as skzi_name,
            r.skzi_number,
            r.withdrawal_date,
            r.destruction_act_num,
            r.withdrawer_fio
        FROM skzi_registry r
        LEFT JOIN employees e ON e.id = r.employee_id
        LEFT JOIN skzi_names sn ON r.skzi_name_id = sn.id
        WHERE r.status = 'DESTROYED'
        ORDER BY r.withdrawal_date DESC
        """
        cursor = self.db.execute_query(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def mark_destroyed(self, skzi_id, date, act, withdrawer):
        query = """
        UPDATE skzi_registry
        SET withdrawal_date=?,
            destruction_act_num=?,
            withdrawer_fio=?,
            status='DESTROYED'
        WHERE id=?
        """
        self.db.execute_query(query, (date, act, withdrawer, skzi_id))
        self.db.commit()

    def mass_mark_destroyed(self, skzi_ids, withdrawal_date, act_num, withdrawer_fio):
        placeholders = ','.join(['?' for _ in skzi_ids])
        query = f"""
        UPDATE skzi_registry
        SET withdrawal_date = ?,
            destruction_act_num = ?,
            withdrawer_fio = ?,
            status = 'DESTROYED'
        WHERE id IN ({placeholders})
        """
        params = [withdrawal_date, act_num, withdrawer_fio] + skzi_ids
        self.db.execute_query(query, params)
        self.db.commit()