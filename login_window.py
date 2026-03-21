from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from security.auth_service import AuthService
from main_window import MainWindow
from forms.change_password_dialog import ChangePasswordDialog

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.change_btn = None
        self.login_btn = None
        self.pass_input = None
        self.user_input = None
        self.auth = AuthService()
        self.main_win = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Авторизация - Учет СКЗИ")
        self.setFixedSize(350, 250)
        layout = QVBoxLayout()
        layout.setSpacing(15)

        header = QLabel("Вход в систему")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        self.user_input = QLineEdit(placeholderText="Логин")
        self.user_input.returnPressed.connect(self.handle_login)
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit(placeholderText="Пароль", echoMode=QLineEdit.EchoMode.Password)
        self.pass_input.returnPressed.connect(self.handle_login)
        layout.addWidget(self.pass_input)

        self.login_btn = QPushButton("Войти")
        self.login_btn.setObjectName("primaryButton")
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        self.change_btn = QPushButton("Сменить пароль")
        self.change_btn.setStyleSheet("color: #7f8c8d; border: none; background: none; text-decoration: underline;")
        self.change_btn.clicked.connect(self.open_change_password)
        layout.addWidget(self.change_btn)

        self.setLayout(layout)

    def handle_login(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
        user = self.auth.authenticate(username, password)
        if user:
            self.main_win = MainWindow(user)
            self.main_win.show()
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль")

    def open_change_password(self):
        dlg = ChangePasswordDialog(parent=self)
        dlg.exec()