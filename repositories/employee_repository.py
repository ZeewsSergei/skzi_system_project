from db.db_manager import DatabaseManager

class EmployeeRepository:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self):
        cursor = self.db.execute_query("""
            SELECT e.id, e.fio, e.position, e.sector_id, e.department_id,
                   s.name as sector_name, d.name as department_name,
                   e.knowledge_check
            FROM employees e
            LEFT JOIN sectors s ON e.sector_id = s.id
            LEFT JOIN departments d ON e.department_id = d.id
            ORDER BY e.fio
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, emp_id):
        cursor = self.db.execute_query(
            "SELECT * FROM employees WHERE id = ?", (emp_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_fio(self, fio):
        cursor = self.db.execute_query(
            "SELECT id FROM employees WHERE fio = ?", (fio,)
        )
        return cursor.fetchone()

    def add(self, fio, position, sector_id, department_id, knowledge_check):
        cursor = self.db.execute_query("""
            INSERT INTO employees (fio, position, sector_id, department_id, knowledge_check)
            VALUES (?, ?, ?, ?, ?)
        """, (fio, position, sector_id, department_id, knowledge_check))
        self.db.commit()
        return cursor.lastrowid

    def update(self, emp_id, fio, position, sector_id, department_id, knowledge_check):
        self.db.execute_query("""
            UPDATE employees
            SET fio = ?, position = ?, sector_id = ?, department_id = ?, knowledge_check = ?
            WHERE id = ?
        """, (fio, position, sector_id, department_id, knowledge_check, emp_id))
        self.db.commit()