from db.db_manager import DatabaseManager

class MediaTypeRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self):
        cursor = self.db.execute_query("SELECT id, name FROM media_types ORDER BY name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_by_name(self, name):
        cursor = self.db.execute_query("SELECT id, name FROM media_types WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_id(self, id):
        cursor = self.db.execute_query("SELECT id, name FROM media_types WHERE id = ?", (id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def add(self, name):
        cursor = self.db.execute_query(
            "INSERT INTO media_types (name) VALUES (?)", (name,)
        )
        self.db.commit()
        return cursor.lastrowid