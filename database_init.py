import sqlite3
import os
import hashlib
import secrets
from utils.path_helper import get_db_path

def hash_password(password):
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    return f"{salt}:{key}"

def create_database():
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Справочные таблицы
    cursor.executescript("""
        -- 1. Справочник наименований СКЗИ
        CREATE TABLE IF NOT EXISTS skzi_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        -- 2. Справочник типов носителей
        CREATE TABLE IF NOT EXISTS media_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        -- 3. Справочник "От кого получен"
        CREATE TABLE IF NOT EXISTS received_from (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        -- 4. Справочник типов АРМ
        CREATE TABLE IF NOT EXISTS arm_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        -- 5. Справочник версий ОС
        CREATE TABLE IF NOT EXISTS os_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        -- 6. Справочник антивирусов
        CREATE TABLE IF NOT EXISTS antiviruses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        -- 7. Справочник наименований СЗИ от НСД
        CREATE TABLE IF NOT EXISTS szi_nsd_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        -- 8. Справочник адресов установки
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        -- Таблица отделов
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        -- Таблица секторов (привязаны к отделу)
        CREATE TABLE IF NOT EXISTS sectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            department_id INTEGER NOT NULL,
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
        );

        -- Таблица сотрудников
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT NOT NULL UNIQUE,
            position TEXT NOT NULL,
            sector_id INTEGER,
            department_id INTEGER,
            knowledge_check TEXT DEFAULT 'не проводилась',
            FOREIGN KEY (sector_id) REFERENCES sectors(id) ON DELETE SET NULL,
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
        );

        -- Таблица АРМ (без специфичных полей, только общие)
        CREATE TABLE IF NOT EXISTS arm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arm_name TEXT,
            arm_serial TEXT UNIQUE,
            arm_type_id INTEGER,
            cabinet_number TEXT,
            install_address_id INTEGER,
            FOREIGN KEY (arm_type_id) REFERENCES arm_types(id) ON DELETE SET NULL,
            FOREIGN KEY (install_address_id) REFERENCES addresses(id) ON DELETE SET NULL
        );

        -- Основная таблица реестра СКЗИ (общая)
        CREATE TABLE IF NOT EXISTS skzi_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            arm_id INTEGER NOT NULL,
            skzi_name_id INTEGER,
            skzi_number TEXT UNIQUE,
            skzi_instance_number TEXT,
            media_type_id INTEGER,
            media_number TEXT,
            cert_number TEXT UNIQUE,
            received_from_id INTEGER,
            receive_date DATE,
            receive_letter_num TEXT,
            install_date DATE,
            expiry_date DATE,
            withdrawal_date DATE,
            installer_fio TEXT,
            withdrawer_fio TEXT,
            destruction_act_num TEXT,
            knowledge_check TEXT DEFAULT 'не проводилась',
            status TEXT DEFAULT 'ACTIVE',
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (arm_id) REFERENCES arm(id),
            FOREIGN KEY (skzi_name_id) REFERENCES skzi_names(id) ON DELETE SET NULL,
            FOREIGN KEY (media_type_id) REFERENCES media_types(id) ON DELETE SET NULL,
            FOREIGN KEY (received_from_id) REFERENCES received_from(id) ON DELETE SET NULL
        );

        -- Таблица для ViPNet Client (отдельная)
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
            UNIQUE(arm_id, status)  -- на одном АРМ может быть только одна активная запись ViPNet
        );

        -- Таблица для СЗИ от НСД (отдельная)
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
            UNIQUE(arm_id, status)  -- на одном АРМ может быть только одна активная запись СЗИ от НСД
        );

        -- Таблица пользователей
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'OPERATOR'
        );

        -- Таблица обучения
        CREATE TABLE IF NOT EXISTS training_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            training_date DATE NOT NULL,
            result TEXT NOT NULL,
            position TEXT,
            department TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );

        -- Таблица аудита
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            action_type TEXT,
            table_name TEXT,
            record_id INTEGER,
            performed_by TEXT,
            new_value TEXT,
            old_value TEXT,
            changed_fields TEXT
        );

        -- Таблица контрольных проверок (не используется, но оставим)
        CREATE TABLE IF NOT EXISTS control_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skzi_registry_id INTEGER NOT NULL,
            check_date DATE NOT NULL,
            conditions_met TEXT NOT NULL,
            inspector TEXT,
            notes TEXT,
            FOREIGN KEY (skzi_registry_id) REFERENCES skzi_registry(id)
        );
    """)

    # Начальные данные для справочников
    cursor.executescript("""
        INSERT OR IGNORE INTO departments (name) VALUES ('Бухгалтерия'), ('IT-отдел'), ('Юридический отдел');
        INSERT OR IGNORE INTO sectors (name, department_id) VALUES 
            ('Сектор разработки', (SELECT id FROM departments WHERE name='IT-отдел')),
            ('Сектор сопровождения', (SELECT id FROM departments WHERE name='IT-отдел')),
            ('Сектор расчётов', (SELECT id FROM departments WHERE name='Бухгалтерия'));

        INSERT OR IGNORE INTO skzi_names (name) VALUES ('КриптоПро CSP 5.0 R3'), ('ViPNet Client 4');
        INSERT OR IGNORE INTO media_types (name) VALUES ('Рутокен'), ('eToken'), ('Esmart'), ('JaCarta');
        INSERT OR IGNORE INTO received_from (name) VALUES ('УФК'), ('СПб ИАЦ');
        INSERT OR IGNORE INTO arm_types (name) VALUES ('Системный блок'), ('Ноутбук'), ('Планшет'), ('Тонкий клиент'), ('Сервер');
        INSERT OR IGNORE INTO os_versions (name) VALUES ('Windows 10'), ('Альт Linux'), ('Astra Linux');
        INSERT OR IGNORE INTO antiviruses (name) VALUES ('Kaspersky Endpoint Security'), ('Dr.Web');
        INSERT OR IGNORE INTO szi_nsd_names (name) VALUES ('Dallas Lock'), ('Secret Net');
        INSERT OR IGNORE INTO addresses (name) VALUES 
            ('Невский пр., д. 176, литера А'),
            ('Невский пр., д. 174, литера А'),
            ('Невский пр., д. 174, литера Б');
    """)

    # Пользователь admin
    admin_hash = hash_password("admin123")
    cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                   ("admin", admin_hash, "ADMIN"))

    conn.commit()
    conn.close()
    print(f"База данных успешно инициализирована по пути: {db_path}")

if __name__ == "__main__":
    create_database()