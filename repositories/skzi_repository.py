from db.db_manager import DatabaseManager
from core.enums import SkziStatus


class SkziRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def get_by_id(self, skzi_id):
        cursor = self.db.execute_query(
            "SELECT * FROM skzi_registry WHERE id = ?", (skzi_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_active(self):
        cursor = self.db.execute_query("""
            SELECT r.*, e.fio, sn.name as skzi_name, mt.name as media_type,
                   a.cabinet_number, a.arm_serial, at.name as arm_type
            FROM skzi_registry r
            JOIN employees e ON r.employee_id = e.id
            JOIN arm a ON r.arm_id = a.id
            LEFT JOIN skzi_names sn ON r.skzi_name_id = sn.id
            LEFT JOIN media_types mt ON r.media_type_id = mt.id
            LEFT JOIN arm_types at ON a.arm_type_id = at.id
            WHERE r.status = 'ACTIVE'
            ORDER BY r.id DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_all_active_filtered(self, filters):
        query = """
            SELECT r.*, e.fio, sn.name as skzi_name, mt.name as media_type,
                   a.cabinet_number, a.arm_serial, at.name as arm_type,
                   d.name as department_name
            FROM skzi_registry r
            JOIN employees e ON r.employee_id = e.id
            JOIN arm a ON r.arm_id = a.id
            LEFT JOIN departments d ON e.department_id = d.id
            LEFT JOIN skzi_names sn ON r.skzi_name_id = sn.id
            LEFT JOIN media_types mt ON r.media_type_id = mt.id
            LEFT JOIN arm_types at ON a.arm_type_id = at.id
            WHERE r.status = ?
        """
        params = [filters.get('status', 'ACTIVE')]

        if 'department_id' in filters and filters['department_id'] is not None:
            query += " AND e.department_id = ?"
            params.append(filters['department_id'])

        if 'fio' in filters and filters['fio']:
            query += " AND LOWER(e.fio) LIKE LOWER(?)"
            params.append(f"%{filters['fio']}%")

        if 'skzi_name_id' in filters and filters['skzi_name_id'] is not None:
            query += " AND r.skzi_name_id = ?"
            params.append(filters['skzi_name_id'])

        if 'arm_type_id' in filters and filters['arm_type_id'] is not None:
            query += " AND a.arm_type_id = ?"
            params.append(filters['arm_type_id'])

        if 'cabinet_number' in filters and filters['cabinet_number']:
            query += " AND LOWER(a.cabinet_number) LIKE LOWER(?)"
            params.append(f"%{filters['cabinet_number']}%")

        if 'install_date_from' in filters and filters['install_date_from']:
            query += " AND r.install_date >= ?"
            params.append(filters['install_date_from'])
        if 'install_date_to' in filters and filters['install_date_to']:
            query += " AND r.install_date <= ?"
            params.append(filters['install_date_to'])

        if 'expiry_date_from' in filters and filters['expiry_date_from']:
            query += " AND r.expiry_date >= ?"
            params.append(filters['expiry_date_from'])
        if 'expiry_date_to' in filters and filters['expiry_date_to']:
            query += " AND r.expiry_date <= ?"
            params.append(filters['expiry_date_to'])

        query += " ORDER BY r.id DESC"

        cursor = self.db.execute_query(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_destroyed(self):
        cursor = self.db.execute_query("""
            SELECT r.*, e.fio, sn.name as skzi_name
            FROM skzi_registry r
            JOIN employees e ON r.employee_id = e.id
            LEFT JOIN skzi_names sn ON r.skzi_name_id = sn.id
            WHERE r.status = 'DESTROYED'
            ORDER BY r.withdrawal_date DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def add_skzi(self, data):
        query = """
        INSERT INTO skzi_registry (
            employee_id, arm_id, skzi_name_id, skzi_number, skzi_instance_number,
            media_type_id, media_number, cert_number, received_from_id,
            receive_date, receive_letter_num, install_date, expiry_date,
            installer_fio, knowledge_check, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data['employee_id'],
            data['arm_id'],
            data.get('skzi_name_id'),
            data.get('skzi_number'),
            data.get('skzi_instance_number'),
            data.get('media_type_id'),
            data.get('media_number'),
            data.get('cert_number'),
            data.get('received_from_id'),
            data.get('receive_date'),
            data.get('receive_letter_num'),
            data.get('install_date'),
            data.get('expiry_date'),
            data.get('installer_fio'),
            data.get('knowledge_check', 'не проводилась'),
            data.get('status', SkziStatus.ACTIVE)
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
            data['employee_id'],
            data['arm_id'],
            data.get('skzi_name_id'),
            data.get('skzi_number'),
            data.get('skzi_instance_number'),
            data.get('media_type_id'),
            data.get('media_number'),
            data.get('cert_number'),
            data.get('received_from_id'),
            data.get('receive_date'),
            data.get('receive_letter_num'),
            data.get('install_date'),
            data.get('expiry_date'),
            data.get('installer_fio'),
            data.get('knowledge_check'),
            skzi_id
        )
        self.db.execute_query(query, params)
        self.db.commit()

    def mark_destroyed(self, skzi_id, withdrawal_date, destruction_act_num, withdrawer_fio):
        query = """
        UPDATE skzi_registry
        SET status = 'DESTROYED',
            withdrawal_date = ?,
            destruction_act_num = ?,
            withdrawer_fio = ?
        WHERE id = ?
        """
        self.db.execute_query(
            query, (withdrawal_date, destruction_act_num, withdrawer_fio, skzi_id)
        )
        self.db.commit()

    def mass_mark_destroyed(self, ids, withdrawal_date, destruction_act_num, withdrawer_fio):
        # GUARD: пустой список → IN () — синтаксическая ошибка SQLite
        if not ids:
            return

        # Дополнительная защита: все элементы должны быть целыми числами
        ids = [int(i) for i in ids]

        placeholders = ','.join(['?' for _ in ids])
        query = f"""
        UPDATE skzi_registry
        SET status = 'DESTROYED',
            withdrawal_date = ?,
            destruction_act_num = ?,
            withdrawer_fio = ?
        WHERE id IN ({placeholders})
        """
        params = [withdrawal_date, destruction_act_num, withdrawer_fio] + ids
        self.db.execute_query(query, params)
        self.db.commit()

    def get_vipnet_data(self):
        cursor = self.db.execute_query("""
            SELECT v.*, e.fio, sn.name as skzi_name
            FROM vipnet_installations v
            JOIN employees e ON v.employee_id = e.id
            LEFT JOIN skzi_names sn ON v.skzi_name_id = sn.id
            WHERE v.status = 'ACTIVE'
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_szi_nsd_data(self):
        cursor = self.db.execute_query("""
            SELECT s.*, e.fio, sz.name as szi_nsd
            FROM szi_nsd_installations s
            JOIN employees e ON s.employee_id = e.id
            LEFT JOIN szi_nsd_names sz ON s.szi_nsd_id = sz.id
            WHERE s.status = 'ACTIVE'
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]