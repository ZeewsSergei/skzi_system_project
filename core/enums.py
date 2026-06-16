# core/enums.py
"""
Перечисления для всего приложения.
Использование вместо строковых литералов позволяет:
- поймать опечатку на этапе импорта, а не в runtime
- получить автодополнение в IDE
- иметь единое место для изменения значений

ВАЖНО: значения намеренно совпадают со строками в БД (SQLite).
При передаче в SQL-запрос используйте .value:
    WHERE status = ?  →  params = (SkziStatus.ACTIVE.value,)
    data.get('status', SkziStatus.ACTIVE.value)
"""

from enum import Enum


class SkziStatus(str, Enum):
    """
    Статус записи в реестре СКЗИ / ViPNet / СЗИ от НСД.
    Наследуется от str — можно передавать напрямую туда,
    где ожидается строка (сравнения, словари, SQLite-параметры).
    """
    ACTIVE    = 'ACTIVE'
    DESTROYED = 'DESTROYED'


class UserRole(str, Enum):
    """
    Роли пользователей системы.
    ADMIN    — полный доступ, управление пользователями и справочниками.
    OPERATOR — регистрация и редактирование записей СКЗИ.
    AUDITOR  — только чтение данных и просмотр аудита.
    """
    ADMIN    = 'ADMIN'
    OPERATOR = 'OPERATOR'
    AUDITOR  = 'AUDITOR'


class TrainingResult(str, Enum):
    """Результат проверки знаний сотрудника."""
    PASS = 'удовлетворительно'
    FAIL = 'неудовлетворительно'
    NOT_CONDUCTED = 'не проводилась'