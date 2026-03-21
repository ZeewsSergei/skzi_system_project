# repositories/control_repository.py

import sqlite3
from utils.path_helper import get_db_path


def get_connection():
    conn = sqlite3.connect(get_db_path())
    return conn


def get_all_controls():
    """
    Получить список всех проверок
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id,
            s.skzi_name,
            e.fio,
            c.check_date,
            c.conditions_met,
            c.inspector
        FROM control_checks c
        LEFT JOIN skzi_registry s ON s.id = c.skzi_registry_id
        LEFT JOIN employees e ON e.id = s.employee_id
        ORDER BY c.check_date DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def add_control(skzi_id, date, result, inspector):
    """
    Добавить запись проверки
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO control_checks (
            skzi_registry_id,
            check_date,
            conditions_met,
            inspector
        )
        VALUES (?, ?, ?, ?)
    """, (skzi_id, date, result, inspector))

    conn.commit()
    conn.close()


def delete_control(control_id):
    """
    Удалить запись проверки
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM control_checks WHERE id=?",
        (control_id,)
    )

    conn.commit()
    conn.close()