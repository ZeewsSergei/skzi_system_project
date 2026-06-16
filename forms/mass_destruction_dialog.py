from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate

class MassDestructionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Массовое уничтожение СКЗИ")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Дата уничтожения:"))
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addWidget(self.date_edit)

        layout.addWidget(QLabel("№ акта уничтожения:"))
        self.act_num = QLineEdit()
        layout.addWidget(self.act_num)

        layout.addWidget(QLabel("ФИО изъявшего:"))
        self.withdrawer = QLineEdit()
        layout.addWidget(self.withdrawer)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Уничтожить")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'act': self.act_num.text().strip(),
            'withdrawer': self.withdrawer.text().strip()
        }