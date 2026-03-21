from PyQt6.QtWidgets import *
from services.department_service import DepartmentService
from signals.app_signals import app_signals

class DepartmentForm(QDialog):
    def __init__(self, parent=None, username="admin"):
        super().__init__(parent)
        self.username = username
        self.service = DepartmentService()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Добавление отдела")
        self.setFixedSize(400, 150)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Название подразделения:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.save_department)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.close)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_department(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название отдела")
            return

        try:
            self.service.add_department(name, self.username)
            # Явно отправляем сигнал об изменении отделов
            app_signals.department_changed.emit()
            QMessageBox.information(self, "Успех", "Отдел добавлен")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))