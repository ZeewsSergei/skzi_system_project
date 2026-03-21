from db.db_manager import DatabaseManager

class ReceivedFromRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self):
        cursor = self.db.execute_query("SELECT id, name FROM received_from ORDER BY name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_by_name(self, name):
        cursor = self.db.execute_query("SELECT id, name FROM received_from WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_id(self, id):
        cursor = self.db.execute_query("SELECT id, name FROM received_from WHERE id = ?", (id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def add(self, name):
        cursor = self.db.execute_query(
            "INSERT INTO received_from (name) VALUES (?)", (name,)
        )
        self.db.commit()
        return cursor.lastrowid