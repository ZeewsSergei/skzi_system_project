from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from services.szi_nsd_service import SziNsdService
from signals.app_signals import app_signals


class DestructionNsdDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.withdrawer = None
        self.act_num = None
        self.date_edit = None
        self.record_combo = None
        self.user = user
        self.service = SziNsdService()
        self.setWindowTitle("Регистрация уничтожения СЗИ от НСД")
        self.setMinimumWidth(500)
        self.init_ui()
        self.load_active_installations()

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Выберите запись:"))
        self.record_combo = QComboBox()
        layout.addWidget(self.record_combo)

        layout.addWidget(QLabel("Дата уничтожения:"))
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addWidget(self.date_edit)

        layout.addWidget(QLabel("№ акта уничтожения:"))
        self.act_num = QLineEdit()
        layout.addWidget(self.act_num)

        layout.addWidget(QLabel("ФИО изъявшего:"))
        self.withdrawer = QLineEdit()
        self.withdrawer.setText(self.user['username'])
        layout.addWidget(self.withdrawer)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def load_active_installations(self):
        active = self.service.get_all_active()
        self.record_combo.clear()
        for r in active:
            text = f"{r['fio']} – {r['szi_nsd']} (АРМ: {r['arm_serial']})"
            self.record_combo.addItem(text, r['id'])

    def save(self):
        if self.record_combo.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Нет активных записей СЗИ от НСД")
            return
        record_id = self.record_combo.currentData()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        act = self.act_num.text().strip()
        withdrawer = self.withdrawer.text().strip()
        if not act:
            QMessageBox.warning(self, "Ошибка", "Введите номер акта уничтожения")
            return
        try:
            self.service.mark_destroyed(record_id, date, act, withdrawer, self.user['username'])
            QMessageBox.information(self, "Успех", "Запись об уничтожении добавлена")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))