# security/auth_service.py

import hashlib
import secrets
from db.db_manager import DatabaseManager

# Максимальное число неудачных попыток до блокировки
MAX_FAILED_ATTEMPTS = 5


class AuthService:
    def __init__(self):
        self.db = DatabaseManager()

    # ──────────────────────────────────────────────
    # Работа с паролями
    # ──────────────────────────────────────────────

    @staticmethod
    def hash_password(password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac(
            'sha256', password.encode(), salt.encode(), 100000
        ).hex()
        return f"{salt}:{key}"

    @staticmethod
    def verify_password(stored, password):
        try:
            salt, key = stored.split(':', 1)
        except ValueError:
            return False
        new_key = hashlib.pbkdf2_hmac(
            'sha256', password.encode(), salt.encode(), 100000
        ).hex()
        return new_key == key

    # ──────────────────────────────────────────────
    # Управление пользователями
    # ──────────────────────────────────────────────

    def create_user(self, username, password, role):
        password_hash = self.hash_password(password)
        try:
            self.db.execute_query(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            self.db.commit()
            return True
        except Exception:
            return False

    def change_password(self, username, new_password):
        """Меняет пароль и сбрасывает флаг обязательной смены."""
        password_hash = self.hash_password(new_password)
        self.db.execute_query(
            "UPDATE users SET password_hash = ?, must_change_password = 0 "
            "WHERE username = ?",
            (password_hash, username)
        )
        self.db.commit()

    def must_change_password(self, username):
        cursor = self.db.execute_query(
            "SELECT must_change_password FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        return bool(row and row['must_change_password'])

    # ──────────────────────────────────────────────
    # Аутентификация с защитой от перебора
    # ──────────────────────────────────────────────

    def is_blocked(self, username: str) -> bool:
        """Возвращает True если учётная запись заблокирована."""
        cursor = self.db.execute_query(
            "SELECT is_blocked FROM users WHERE username = ?", (username,)
        )
        row = cursor.fetchone()
        return bool(row and row['is_blocked'])

    def get_failed_attempts(self, username: str) -> int:
        """Возвращает текущее число неудачных попыток."""
        cursor = self.db.execute_query(
            "SELECT failed_attempts FROM users WHERE username = ?", (username,)
        )
        row = cursor.fetchone()
        return int(row['failed_attempts']) if row else 0

    def _increment_failed_attempts(self, username: str):
        """
        Увеличивает счётчик неудачных попыток.
        При достижении MAX_FAILED_ATTEMPTS блокирует учётную запись.
        """
        self.db.execute_query(
            "UPDATE users SET failed_attempts = failed_attempts + 1 "
            "WHERE username = ?",
            (username,)
        )
        self.db.commit()

        attempts = self.get_failed_attempts(username)
        if attempts >= MAX_FAILED_ATTEMPTS:
            self.db.execute_query(
                "UPDATE users SET is_blocked = 1 WHERE username = ?",
                (username,)
            )
            self.db.commit()

    def _reset_failed_attempts(self, username: str):
        """Сбрасывает счётчик после успешного входа."""
        self.db.execute_query(
            "UPDATE users SET failed_attempts = 0 WHERE username = ?",
            (username,)
        )
        self.db.commit()

    def authenticate(self, username: str, password: str):
        """
        Аутентифицирует пользователя.

        Возвращает dict с данными пользователя при успехе.
        Возвращает None при неверном пароле или если пользователь не найден.
        Выбрасывает BlockedUserError если учётная запись заблокирована.
        Выбрасывает BlockedUserError с числом оставшихся попыток
        если пароль неверный и осталось мало попыток.
        """
        cursor = self.db.execute_query(
            "SELECT * FROM users WHERE username = ?", (username,)
        )
        user = cursor.fetchone()

        # Пользователь не найден — не сообщаем об этом явно
        # (нельзя давать подсказку перебором)
        if not user:
            return None

        user = dict(user)

        # Проверяем блокировку ДО проверки пароля
        if user.get('is_blocked'):
            raise BlockedUserError(
                f"Учётная запись «{username}» заблокирована.\n"
                "Обратитесь к администратору для разблокировки."
            )

        # Проверяем пароль
        if self.verify_password(user['password_hash'], password):
            # Успех — сбрасываем счётчик
            self._reset_failed_attempts(username)
            return user
        else:
            # Неудача — увеличиваем счётчик
            self._increment_failed_attempts(username)

            # Перечитываем актуальное состояние
            attempts = self.get_failed_attempts(username)
            remaining = MAX_FAILED_ATTEMPTS - attempts

            if user.get('is_blocked') or attempts >= MAX_FAILED_ATTEMPTS:
                raise BlockedUserError(
                    f"Учётная запись «{username}» заблокирована "
                    f"после {MAX_FAILED_ATTEMPTS} неудачных попыток.\n"
                    "Обратитесь к администратору для разблокировки."
                )

            if remaining <= 2:
                # Предупреждаем когда осталось мало попыток
                raise WarnAttemptsError(
                    f"Неверный пароль. Осталось попыток: {remaining}.\n"
                    f"После {remaining} неудачных попыток "
                    "учётная запись будет заблокирована.",
                    remaining=remaining
                )

            return None

    # ──────────────────────────────────────────────
    # Административные операции
    # ──────────────────────────────────────────────

    def unblock_user(self, username: str):
        """Разблокирует учётную запись и сбрасывает счётчик (только для ADMIN)."""
        self.db.execute_query(
            "UPDATE users SET is_blocked = 0, failed_attempts = 0 "
            "WHERE username = ?",
            (username,)
        )
        self.db.commit()

    def get_all_users(self):
        """Возвращает список всех пользователей (без хешей паролей)."""
        cursor = self.db.execute_query(
            "SELECT id, username, role, must_change_password, "
            "failed_attempts, is_blocked FROM users ORDER BY username"
        )
        return [dict(row) for row in cursor.fetchall()]


# ──────────────────────────────────────────────────────
# Исключения
# ──────────────────────────────────────────────────────

class BlockedUserError(Exception):
    """Учётная запись заблокирована после превышения числа попыток."""
    pass


class WarnAttemptsError(Exception):
    """Предупреждение: осталось мало попыток до блокировки."""
    def __init__(self, message: str, remaining: int):
        super().__init__(message)
        self.remaining = remaining