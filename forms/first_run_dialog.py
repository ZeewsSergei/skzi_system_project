from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from security.auth_service import AuthService

class FirstRunDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth = AuthService()
        self.setWindowTitle("Создание первого администратора")
        self.setFixedSize(400, 250)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("База данных пуста. Создайте учётную запись администратора."))
        layout.addWidget(QLabel("Логин:"))
        self.login_input = QLineEdit()
        layout.addWidget(self.login_input)

        layout.addWidget(QLabel("Пароль:"))
        self.pass_input = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        layout.addWidget(self.pass_input)

        layout.addWidget(QLabel("Подтверждение пароля:"))
        self.confirm_input = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_input)

        btn = QPushButton("Создать")
        btn.clicked.connect(self.create_admin)
        layout.addWidget(btn)

        self.setLayout(layout)

    def create_admin(self):
        login = self.login_input.text().strip()
        password = self.pass_input.text()
        confirm = self.confirm_input.text()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        if password != confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 6 символов")
            return

        # Создаём пользователя с ролью ADMIN
        if self.auth.create_user(login, password, "ADMIN"):
            QMessageBox.information(self, "Успех", f"Администратор {login} создан")
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Пользователь с таким логином уже существует")