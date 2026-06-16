# login_window.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from security.auth_service import AuthService, BlockedUserError, WarnAttemptsError
from main_window import MainWindow
from forms.change_password_dialog import ChangePasswordDialog


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.auth = AuthService()
        self.setWindowTitle("Учёт СКЗИ — Вход")
        self.setFixedSize(360, 260)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 30, 40, 30)

        # Заголовок
        title = QLabel("Учёт СКЗИ v6.0")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Введите учётные данные для входа")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Поле логина
        layout.addWidget(QLabel("Логин:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")
        layout.addWidget(self.username_input)

        # Поле пароля
        layout.addWidget(QLabel("Пароль:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Пароль")
        # Enter в поле пароля → попытка входа
        self.password_input.returnPressed.connect(self._handle_login)
        layout.addWidget(self.password_input)

        # Метка ошибки (скрыта по умолчанию)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #c0392b; font-size: 11px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        # Кнопка входа
        btn_login = QPushButton("Войти")
        btn_login.setObjectName("primaryButton")
        btn_login.clicked.connect(self._handle_login)
        layout.addWidget(btn_login)

    def _show_error(self, text: str):
        """Показывает встроенную метку ошибки."""
        self.error_label.setText(text)
        self.error_label.setVisible(True)

    def _clear_error(self):
        self.error_label.setVisible(False)
        self.error_label.setText("")

    def _handle_login(self):
        self._clear_error()

        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_error("Заполните все поля.")
            return

        try:
            user = self.auth.authenticate(username, password)
        except BlockedUserError as e:
            # Учётная запись заблокирована — показываем диалог
            QMessageBox.critical(self, "Доступ закрыт", str(e))
            self.password_input.clear()
            return
        except WarnAttemptsError as e:
            # Неверный пароль, но ещё есть попытки — предупреждаем
            self._show_error(str(e))
            self.password_input.clear()
            return

        if user is None:
            # Неверный пароль (без предупреждения — далеко до блокировки)
            self._show_error("Неверный логин или пароль.")
            self.password_input.clear()
            return

        # ── Успешный вход ──
        self.password_input.clear()
        self._clear_error()

        # Проверяем обязательную смену пароля
        if self.auth.must_change_password(username):
            dlg = ChangePasswordDialog(
                username=username,
                parent=self,
                force_change=True
            )
            dlg.setWindowTitle("Смена пароля обязательна")
            if dlg.exec() != dlg.DialogCode.Accepted:
                # Пользователь закрыл диалог — не пускаем в систему
                QMessageBox.warning(
                    self, "Вход отменён",
                    "Для продолжения работы необходимо сменить пароль."
                )
                return
            # Перечитываем пользователя после смены пароля
            user = self.auth.authenticate(username, dlg.new_password_value
                                          if hasattr(dlg, 'new_password_value')
                                          else password)
            if not user:
                # На случай если смена прошла, но re-auth не удался
                cursor = self.auth.db.execute_query(
                    "SELECT * FROM users WHERE username = ?", (username,)
                )
                row = cursor.fetchone()
                user = dict(row) if row else None

        if not user:
            self._show_error("Ошибка авторизации. Попробуйте ещё раз.")
            return

        # Открываем главное окно
        self.main_window = MainWindow(user)
        self.main_window.show()
        self.close()