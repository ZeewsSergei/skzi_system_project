# login_window.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from security.auth_service import AuthService, BlockedUserError, WarnAttemptsError
from main_window import MainWindow
from forms.change_password_dialog import ChangePasswordDialog

APP_VERSION = "6.0"

# ── Константы размеров ────────────────────────────────────────────────────────
_WIN_W          = 480      # ширина окна
_WIN_H          = 420      # высота окна
_FIELD_H        = 46       # высота полей логин/пароль
_BTN_H          = 50       # высота кнопки «Войти»
_FONT_SIZE      = 14       # шрифт в полях
_LABEL_SIZE     = 13       # шрифт подписей
_PADDING_H      = 44       # горизонтальные отступы контента
_PADDING_V      = 36       # вертикальные отступы контента


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.auth = AuthService()
        self.setWindowTitle(f"Учёт СКЗИ v{APP_VERSION} — Вход")

        # setMinimumSize вместо setFixedSize:
        # при высоком DPI (125 %, 150 %) окно сможет растянуться
        self.setMinimumSize(_WIN_W, _WIN_H)
        self.resize(_WIN_W, _WIN_H)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._init_ui()

    # ──────────────────────────────────────────────────────────────────────────
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(_PADDING_H, _PADDING_V, _PADDING_H, _PADDING_V)

        # ── Заголовок ──────────────────────────────────────────────────────────
        title = QLabel(f"Учёт СКЗИ v{APP_VERSION}")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Введите учётные данные для входа")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(subtitle)

        layout.addSpacing(14)

        # ── Стиль, общий для полей ввода ───────────────────────────────────────
        # Важно: задаём min-height прямо в QSS, чтобы глобальный MODERN_STYLE
        # не перебил высоту, заданную через setMinimumHeight / setFixedHeight.
        field_qss = (
            f"QLineEdit {{"
            f"  font-size: {_FONT_SIZE}px;"
            f"  padding: 0px 12px;"          # вертикальный padding = 0 — высота управляется min-height
            f"  min-height: {_FIELD_H}px;"   # ← ключевая строка: QSS min-height не перебивается
            f"  border: 1px solid #bdc3c7;"
            f"  border-radius: 6px;"
            f"  background: white;"
            f"}}"
            f"QLineEdit:focus {{ border-color: #2ecc71; border-width: 2px; }}"
        )

        # ── Логин ──────────────────────────────────────────────────────────────
        lbl_login = QLabel("Логин:")
        lbl_login.setStyleSheet(
            f"font-size: {_LABEL_SIZE}px; font-weight: bold; color: #2c3e50;"
        )
        layout.addWidget(lbl_login)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")
        self.username_input.setFixedHeight(_FIELD_H)   # жёсткая высота
        self.username_input.setStyleSheet(field_qss)
        layout.addWidget(self.username_input)

        layout.addSpacing(4)

        # ── Пароль ─────────────────────────────────────────────────────────────
        lbl_pwd = QLabel("Пароль:")
        lbl_pwd.setStyleSheet(
            f"font-size: {_LABEL_SIZE}px; font-weight: bold; color: #2c3e50;"
        )
        layout.addWidget(lbl_pwd)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setFixedHeight(_FIELD_H)   # жёсткая высота
        self.password_input.setStyleSheet(field_qss)
        self.password_input.returnPressed.connect(self._handle_login)
        layout.addWidget(self.password_input)

        layout.addSpacing(6)

        # ── Метка ошибки (скрыта по умолчанию) ───────────────────────────────
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(
            "color: #c0392b;"
            "font-size: 11px;"
            "background: #fdecea;"
            "border: 1px solid #f5c6cb;"
            "border-radius: 4px;"
            "padding: 6px 10px;"
        )
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        layout.addSpacing(8)

        # ── Кнопка «Войти» ────────────────────────────────────────────────────
        # Задаём высоту через QSS min-height И setFixedHeight — двойная гарантия
        btn_login = QPushButton("Войти")
        btn_login.setObjectName("loginButton")
        btn_login.setFixedHeight(_BTN_H)          # жёсткая высота кнопки
        btn_login.setStyleSheet(
            f"QPushButton#loginButton {{"
            f"  background-color: #2ecc71;"
            f"  color: white;"
            f"  border: none;"
            f"  min-height: {_BTN_H}px;"          # QSS дублирует setFixedHeight
            f"  font-size: 16px;"
            f"  font-weight: bold;"
            f"  border-radius: 6px;"
            f"}}"
            f"QPushButton#loginButton:hover  {{ background-color: #27ae60; }}"
            f"QPushButton#loginButton:pressed {{ background-color: #1e8449; }}"
        )
        btn_login.clicked.connect(self._handle_login)
        layout.addWidget(btn_login)

    # ──────────────────────────────────────────────────────────────────────────
    def _show_error(self, text: str):
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
            QMessageBox.critical(self, "Доступ закрыт", str(e))
            self.password_input.clear()
            return
        except WarnAttemptsError as e:
            self._show_error(str(e))
            self.password_input.clear()
            return

        if user is None:
            self._show_error("Неверный логин или пароль.")
            self.password_input.clear()
            return

        # ── Успешный вход ─────────────────────────────────────────────────────
        self.password_input.clear()
        self._clear_error()

        if self.auth.must_change_password(username):
            dlg = ChangePasswordDialog(username=username, parent=self, force_change=True)
            dlg.setWindowTitle("Смена пароля обязательна")
            if dlg.exec() != dlg.DialogCode.Accepted:
                QMessageBox.warning(
                    self, "Вход отменён",
                    "Для продолжения работы необходимо сменить пароль."
                )
                return
            cursor = self.auth.db.execute_query(
                "SELECT * FROM users WHERE username = ?", (username,)
            )
            row = cursor.fetchone()
            user = dict(row) if row else user

        if not user:
            self._show_error("Ошибка авторизации. Попробуйте ещё раз.")
            return

        self.main_window = MainWindow(user)
        self.main_window.show()
        self.close()