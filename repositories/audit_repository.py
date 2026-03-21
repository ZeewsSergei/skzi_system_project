from db.db_manager import DatabaseManager

class AuditRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def add(self, action_type, table_name, record_id, performed_by, new_value):
        self.db.execute_query(
            "INSERT INTO audit_log (action_type, table_name, record_id, performed_by, new_value) VALUES (?, ?, ?, ?, ?)",
            (action_type, table_name, record_id, performed_by, new_value)
        )
        self.db.commit()

    def get_recent(self, limit=100):
        cursor = self.db.execute_query(
            "SELECT action_time, action_type, table_name, performed_by, new_value FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return cursor.fetchall()