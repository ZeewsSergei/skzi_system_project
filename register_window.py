from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox
from security.auth_service import AuthService

class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.role = None
        self.confirm = None
        self.password = None
        self.username = None
        self.auth = AuthService()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Регистрация пользователя")
        self.setFixedSize(300, 300)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Логин:"))
        self.username = QLineEdit()
        layout.addWidget(self.username)

        layout.addWidget(QLabel("Пароль:"))
        self.password = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        layout.addWidget(self.password)

        layout.addWidget(QLabel("Подтверждение:"))
        self.confirm = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm)

        layout.addWidget(QLabel("Роль:"))
        self.role = QComboBox()
        self.role.addItems(["OPERATOR", "AUDITOR", "ADMIN"])
        layout.addWidget(self.role)

        btn = QPushButton("Зарегистрировать")
        btn.clicked.connect(self.handle_register)
        layout.addWidget(btn)

        self.setLayout(layout)

    def handle_register(self):
        user = self.username.text().strip()
        pwd = self.password.text()
        conf = self.confirm.text()
        role = self.role.currentText()
        if not user or not pwd:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        if pwd != conf:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
        if len(pwd) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 6 символов")
            return
        if self.auth.create_user(user, pwd, role):
            QMessageBox.information(self, "Успех", f"Пользователь {user} создан")
            self.close()
        else:
            QMessageBox.critical(self, "Ошибка", "Пользователь с таким именем уже существует")