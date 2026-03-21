from db.db_manager import DatabaseManager

class AuditService:
    def __init__(self):
        self.db = DatabaseManager()

    def log(self, action_type, table_name, record_id, user, new_value, old_value=None, changed_fields=None):
        """
        Записывает действие в аудит.
        :param action_type: тип действия (CREATE, UPDATE, DELETE, DESTROY и т.д.)
        :param table_name: имя таблицы
        :param record_id: идентификатор записи
        :param user: пользователь
        :param new_value: новое значение (или описание)
        :param old_value: старое значение (опционально)
        :param changed_fields: список изменённых полей (опционально)
        """
        query = """
        INSERT INTO audit_log (action_type, table_name, record_id, performed_by, new_value, old_value, changed_fields)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(query, (action_type, table_name, record_id, user, str(new_value), str(old_value) if old_value else None, str(changed_fields) if changed_fields else None))
        self.db.commit()

    def get_recent(self, limit=100):
        cursor = self.db.execute_query(
            "SELECT action_time, action_type, table_name, performed_by, new_value, old_value, changed_fields FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return cursor.fetchall()