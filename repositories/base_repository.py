from db.db_manager import DatabaseManager

class BaseRepository:
    def __init__(self, table_name):
        self.db = DatabaseManager()
        self.table_name = table_name

    def get_all(self):
        cursor = self.db.execute_query(f"SELECT id, name FROM {self.table_name} ORDER BY name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_by_name(self, name):
        cursor = self.db.execute_query(f"SELECT id FROM {self.table_name} WHERE name = ?", (name,))
        row = cursor.fetchone()
        return row['id'] if row else None

    def add(self, name):
        cursor = self.db.execute_query(f"INSERT INTO {self.table_name} (name) VALUES (?)", (name,))
        self.db.commit()
        return cursor.lastrowid