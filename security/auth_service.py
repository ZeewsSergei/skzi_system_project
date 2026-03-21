import hashlib
import secrets
from db.db_manager import DatabaseManager

class AuthService:
    def __init__(self):
        self.db = DatabaseManager()

    @staticmethod
    def hash_password(password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        return f"{salt}:{key}"

    @staticmethod
    def verify_password(stored, password):
        salt, key = stored.split(':')
        new_key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        return new_key == key

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

    def authenticate(self, username, password):
        cursor = self.db.execute_query(
            "SELECT * FROM users WHERE username = ?", (username,)
        )
        user = cursor.fetchone()
        if user and self.verify_password(user['password_hash'], password):
            return dict(user)
        return None

    def change_password(self, username, new_password):
        password_hash = self.hash_password(new_password)
        self.db.execute_query(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (password_hash, username)
        )
        self.db.commit()