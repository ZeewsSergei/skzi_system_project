from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from services.skzi_service import SkziService

class DestructionDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.skzi_service = SkziService()
        self.setWindowTitle("Регистрация уничтожения СКЗИ")
        self.setMinimumWidth(400)
        self.init_ui()
        self.load_active_skzi()

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Выберите запись СКЗИ для уничтожения:"))
        self.skzi_combo = QComboBox()
        layout.addWidget(self.skzi_combo)

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
        date = self.date_edit.date().toString("dd.MM.yyyy")
        act = self.act_num.text().strip()
        withdrawer = self.withdrawer.text().strip()
        if not act:
            QMessageBox.warning(self, "Ошибка", "Введите номер акта уничтожения")
            return
        try:
            self.skzi_service.mark_destroyed(skzi_id, date, act, withdrawer, self.user['username'])
            QMessageBox.information(self, "Успех", "Запись об уничтожении добавлена")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))