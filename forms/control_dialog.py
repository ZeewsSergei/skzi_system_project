from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from services.control_service import ControlService
from services.skzi_service import SkziService


class ControlDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.notes = None
        self.inspector = None
        self.conditions_check = None
        self.date_edit = None
        self.skzi_combo = None
        self.user = user
        self.control_service = ControlService()
        self.skzi_service = SkziService()
        self.setWindowTitle("Регистрация контроля СКЗИ")
        self.setMinimumWidth(450)
        self.init_ui()
        self.load_active_skzi()

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Выберите запись СКЗИ:"))
        self.skzi_combo = QComboBox()
        layout.addWidget(self.skzi_combo)

        layout.addWidget(QLabel("Дата проверки:"))
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addWidget(self.date_edit)

        layout.addWidget(QLabel("Условия соблюдены:"))
        self.conditions_check = QCheckBox("Да, условия соблюдены")
        self.conditions_check.setChecked(True)
        layout.addWidget(self.conditions_check)

        layout.addWidget(QLabel("Проверяющий (ФИО):"))
        self.inspector = QLineEdit()
        self.inspector.setText(self.user['username'])
        layout.addWidget(self.inspector)

        layout.addWidget(QLabel("Примечание:"))
        self.notes = QLineEdit()
        layout.addWidget(self.notes)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def load_active_skzi(self):
        active = self.skzi_service.get_all_active()
        self.skzi_combo.clear()
        for r in active:
            text = f"{r['fio']} – {r['skzi_name']} (№ {r['skzi_number']})"
            self.skzi_combo.addItem(text, r['id'])

    def save(self):
        if self.skzi_combo.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Нет активных записей СКЗИ")
            return
        skzi_id = self.skzi_combo.currentData()

        # ИСПРАВЛЕНО: формат yyyy-MM-dd (ISO) вместо dd-MM-yyyy
        check_date = self.date_edit.date().toString("yyyy-MM-dd")

        conditions = "Условия соблюдены" if self.conditions_check.isChecked() \
            else "Условия не соблюдены"
        inspector = self.inspector.text().strip()
        notes = self.notes.text().strip()

        if not inspector:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО проверяющего")
            return

        try:
            self.control_service.register_control(
                skzi_id, check_date, conditions, inspector,
                notes, self.user['username']
            )
            QMessageBox.information(self, "Успех", "Результат контроля сохранён")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))