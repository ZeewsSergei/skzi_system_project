from db.db_manager import DatabaseManager

class TrainingRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self):
        """Возвращает список записей обучения с информацией о сотруднике и отделе."""
        cursor = self.db.execute_query("""
            SELECT t.id, e.fio, t.training_date, t.result, t.position, t.department
            FROM training_logs t
            JOIN employees e ON t.employee_id = e.id
            ORDER BY t.training_date DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def add(self, employee_id, training_date, result, position, department):
        cursor = self.db.execute_query("""
            INSERT INTO training_logs (employee_id, training_date, result, position, department)
            VALUES (?, ?, ?, ?, ?)
        """, (employee_id, training_date, result, position, department))
        self.db.commit()
        return cursor.lastrowid