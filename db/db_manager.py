import sqlite3
import os
from utils.path_helper import get_db_path

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.db_path = get_db_path()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._initialized = True
        self._upgrade_schema()

    def _upgrade_schema(self):
        """Проверяет и обновляет схему базы данных до актуальной версии."""
        cursor = self.conn.cursor()

        # Создаём таблицу sectors, если её нет
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                department_id INTEGER NOT NULL,
                FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
            )
        """)

        # Проверяем наличие колонки sector_id в employees
        cursor.execute("PRAGMA table_info(employees)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'sector_id' not in columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN sector_id INTEGER REFERENCES sectors(id) ON DELETE SET NULL")
        if 'department_id' not in columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL")
        if 'knowledge_check' not in columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN knowledge_check TEXT DEFAULT 'не проводилась'")

        # Обновляем audit_log
        cursor.execute("PRAGMA table_info(audit_log)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'old_value' not in columns:
            cursor.execute("ALTER TABLE audit_log ADD COLUMN old_value TEXT")
        if 'changed_fields' not in columns:
            cursor.execute("ALTER TABLE audit_log ADD COLUMN changed_fields TEXT")

        self.commit()

    def execute_query(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self.conn:
            self.conn.close()