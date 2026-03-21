from db.db_manager import DatabaseManager

class SectorRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self):
        cursor = self.db.execute_query("""
            SELECT s.id, s.name, s.department_id, d.name as department_name
            FROM sectors s
            LEFT JOIN departments d ON s.department_id = d.id
            ORDER BY d.name, s.name
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_by_department(self, department_id):
        cursor = self.db.execute_query(
            "SELECT id, name FROM sectors WHERE department_id = ? ORDER BY name",
            (department_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_by_name(self, name):
        cursor = self.db.execute_query(
            "SELECT * FROM sectors WHERE name = ?", (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_id(self, sector_id):
        cursor = self.db.execute_query(
            "SELECT * FROM sectors WHERE id = ?", (sector_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def add(self, name, department_id):
        cursor = self.db.execute_query(
            "INSERT INTO sectors (name, department_id) VALUES (?, ?)",
            (name, department_id)
        )
        self.db.commit()
        return cursor.lastrowid