# repositories/control_repository.py

from db.db_manager import DatabaseManager


class ControlRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self):
        """Получить список всех проверок с данными СКЗИ и сотрудника."""
        cursor = self.db.execute_query("""
            SELECT
                c.id,
                COALESCE(sn.name, '') AS skzi_name,
                e.fio,
                c.check_date,
                c.conditions_met,
                c.inspector,
                c.notes
            FROM control_checks c
            LEFT JOIN skzi_registry s ON s.id = c.skzi_registry_id
            LEFT JOIN skzi_names sn ON s.skzi_name_id = sn.id
            LEFT JOIN employees e ON e.id = s.employee_id
            ORDER BY c.check_date DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def add(self, skzi_id, check_date, conditions_met, inspector, notes=""):
        """Добавить запись контрольной проверки."""
        cursor = self.db.execute_query("""
            INSERT INTO control_checks (
                skzi_registry_id,
                check_date,
                conditions_met,
                inspector,
                notes
            )
            VALUES (?, ?, ?, ?, ?)
        """, (skzi_id, check_date, conditions_met, inspector, notes))
        self.db.commit()
        return cursor.lastrowid

    def delete(self, control_id):
        """Удалить запись контрольной проверки."""
        self.db.execute_query(
            "DELETE FROM control_checks WHERE id = ?",
            (control_id,)
        )
        self.db.commit()