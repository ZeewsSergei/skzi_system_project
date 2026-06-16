# db/db_manager.py

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

    def _safe_add_column(self, table, column, col_type):
        """Безопасно добавляет колонку, игнорируя ошибку duplicate column."""
        try:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            print(f"Добавлен столбец {column} в таблицу {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
            # Столбец уже существует, игнорируем
            print(f"Столбец {column} уже существует в таблице {table}, пропускаем")

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

        # Добавляем недостающие колонки в employees
        self._safe_add_column('employees', 'sector_id', 'INTEGER REFERENCES sectors(id) ON DELETE SET NULL')
        self._safe_add_column('employees', 'department_id', 'INTEGER REFERENCES departments(id) ON DELETE SET NULL')
        self._safe_add_column('employees', 'knowledge_check', "TEXT DEFAULT 'не проводилась'")

        # Добавляем недостающие колонки в skzi_registry
        self._safe_add_column('skzi_registry', 'skzi_account', 'TEXT')
        self._safe_add_column('skzi_registry', 'skzi_name_id', 'INTEGER')
        self._safe_add_column('skzi_registry', 'skzi_number', 'TEXT')
        self._safe_add_column('skzi_registry', 'skzi_instance_number', 'TEXT')
        self._safe_add_column('skzi_registry', 'media_type_id', 'INTEGER')
        self._safe_add_column('skzi_registry', 'media_number', 'TEXT')
        self._safe_add_column('skzi_registry', 'cert_number', 'TEXT')
        self._safe_add_column('skzi_registry', 'received_from_id', 'INTEGER')
        self._safe_add_column('skzi_registry', 'receive_date', 'DATE')
        self._safe_add_column('skzi_registry', 'receive_letter_num', 'TEXT')
        self._safe_add_column('skzi_registry', 'install_date', 'DATE')
        self._safe_add_column('skzi_registry', 'expiry_date', 'DATE')
        self._safe_add_column('skzi_registry', 'withdrawal_date', 'DATE')
        self._safe_add_column('skzi_registry', 'installer_fio', 'TEXT')
        self._safe_add_column('skzi_registry', 'withdrawer_fio', 'TEXT')
        self._safe_add_column('skzi_registry', 'destruction_act_num', 'TEXT')
        self._safe_add_column('skzi_registry', 'knowledge_check', "TEXT DEFAULT 'не проводилась'")
        self._safe_add_column('skzi_registry', 'status', "TEXT DEFAULT 'ACTIVE'")

        # Добавляем недостающие колонки в arm
        self._safe_add_column('arm', 'os_version_id', 'INTEGER REFERENCES os_versions(id) ON DELETE SET NULL')
        self._safe_add_column('arm', 'antivirus_id', 'INTEGER REFERENCES antiviruses(id) ON DELETE SET NULL')
        self._safe_add_column('arm', 'szi_nsd_id', 'INTEGER REFERENCES szi_nsd_names(id) ON DELETE SET NULL')

        # Добавляем недостающие колонки в audit_log
        self._safe_add_column('audit_log', 'old_value', 'TEXT')
        self._safe_add_column('audit_log', 'changed_fields', 'TEXT')

        self._safe_add_column('users', 'must_change_password', 'INTEGER DEFAULT 0')
        # Поля для блокировки учётной записи (шаг 11)
        self._safe_add_column('users', 'failed_attempts', 'INTEGER DEFAULT 0')
        self._safe_add_column('users', 'is_blocked', 'INTEGER DEFAULT 0')

        # Создаём таблицы ViPNet и СЗИ от НСД, если их нет (для обратной совместимости)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vipnet_installations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                arm_id INTEGER NOT NULL,
                skzi_name_id INTEGER,
                skzi_account TEXT NOT NULL,
                received_from_id INTEGER,
                receive_letter_num TEXT,
                install_date DATE,
                installer_fio TEXT,
                status TEXT DEFAULT 'ACTIVE',
                withdrawal_date DATE,
                destruction_act_num TEXT,
                withdrawer_fio TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (arm_id) REFERENCES arm(id),
                FOREIGN KEY (skzi_name_id) REFERENCES skzi_names(id) ON DELETE SET NULL,
                FOREIGN KEY (received_from_id) REFERENCES received_from(id) ON DELETE SET NULL,
                UNIQUE(arm_id, status)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS szi_nsd_installations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                arm_id INTEGER NOT NULL,
                szi_nsd_id INTEGER NOT NULL,
                install_date DATE,
                installer_fio TEXT,
                status TEXT DEFAULT 'ACTIVE',
                withdrawal_date DATE,
                destruction_act_num TEXT,
                withdrawer_fio TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (arm_id) REFERENCES arm(id),
                FOREIGN KEY (szi_nsd_id) REFERENCES szi_nsd_names(id) ON DELETE SET NULL,
                UNIQUE(arm_id, status)
            )
        """)

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