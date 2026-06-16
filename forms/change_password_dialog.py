from PyQt6.QtWidgets import *
from security.auth_service import AuthService, BlockedUserError, WarnAttemptsError

class ChangePasswordDialog(QDialog):
    def __init__(self, username=None, parent=None, force_change=False):
        super().__init__(parent)
        self.force_change = force_change
        self.confirm_input = None
        self.new_pass_input = None
        self.old_pass_input = None
        self.username_input = None
        self.username = username
        self.auth = AuthService()
        self.init_ui()
        if force_change:
            self.setWindowTitle("Обязательная смена пароля")
            # Можно добавить поясняющий текст

    def init_ui(self):
        self.setWindowTitle("Смена пароля")
        self.setFixedSize(350, 250)
        layout = QVBoxLayout()

        if not self.username:
            layout.addWidget(QLabel("Логин:"))
            self.username_input = QLineEdit()
            layout.addWidget(self.username_input)
        else:
            self.username_input = None
            layout.addWidget(QLabel(f"Смена пароля для: {self.username}"))

        layout.addWidget(QLabel("Текущий пароль:"))
        self.old_pass_input = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        layout.addWidget(self.old_pass_input)

        layout.addWidget(QLabel("Новый пароль:"))
        self.new_pass_input = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        layout.addWidget(self.new_pass_input)

        layout.addWidget(QLabel("Подтверждение нового пароля:"))
        self.confirm_input = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_input)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сменить пароль")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.handle_change)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def handle_change(self):
        if self.username_input:
            username = self.username_input.text().strip()
            if not username:
                QMessageBox.warning(self, "Ошибка", "Введите логин")
                return
        else:
            username = self.username

        old_pass = self.old_pass_input.text()
        new_pass = self.new_pass_input.text()
        confirm = self.confirm_input.text()

        if not old_pass or not new_pass or not confirm:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        if new_pass != confirm:
            QMessageBox.warning(self, "Ошибка", "Новый пароль и подтверждение не совпадают")
            return
        if len(new_pass) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 6 символов")
            return

        try:
            user = self.auth.authenticate(username, old_pass)
        except BlockedUserError as e:
            QMessageBox.critical(self, "Доступ закрыт", str(e))
            return
        except WarnAttemptsError as e:
            QMessageBox.warning(self, "Предупреждение", str(e))
            return
        if not user:
            QMessageBox.critical(self, "Ошибка", "Неверный текущий пароль или логин")
            return

        try:
            self.auth.change_password(username, new_pass)
            QMessageBox.information(self, "Успех", "Пароль успешно изменён")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сменить пароль: {e}")