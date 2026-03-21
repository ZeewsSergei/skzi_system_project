from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate

class FilterDialog(QDialog):
    def __init__(self, parent=None, initial_filters=None):
        super().__init__(parent)
        self.setWindowTitle("Расширенный фильтр")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Сотрудник (часть ФИО):"))
        self.fio = QLineEdit()
        layout.addWidget(self.fio)

        layout.addWidget(QLabel("Наименование СКЗИ:"))
        self.skzi_name = QLineEdit()
        layout.addWidget(self.skzi_name)

        layout.addWidget(QLabel("Тип АРМ:"))
        self.arm_type = QLineEdit()
        layout.addWidget(self.arm_type)

        layout.addWidget(QLabel("Кабинет:"))
        self.cabinet = QLineEdit()
        layout.addWidget(self.cabinet)

        # Поля дат
        layout.addWidget(QLabel("Дата установки от:"))
        self.install_date_from = QDateEdit(calendarPopup=True)
        self.install_date_from.setDate(QDate.currentDate().addYears(-1))
        self.install_date_from.setSpecialValueText("Не выбрано")
        layout.addWidget(self.install_date_from)

        layout.addWidget(QLabel("Дата установки до:"))
        self.install_date_to = QDateEdit(calendarPopup=True)
        self.install_date_to.setDate(QDate.currentDate())
        self.install_date_to.setSpecialValueText("Не выбрано")
        layout.addWidget(self.install_date_to)

        layout.addWidget(QLabel("Срок от:"))
        self.expiry_date_from = QDateEdit(calendarPopup=True)
        self.expiry_date_from.setDate(QDate.currentDate())
        self.expiry_date_from.setSpecialValueText("Не выбрано")
        layout.addWidget(self.expiry_date_from)

        layout.addWidget(QLabel("Срок до:"))
        self.expiry_date_to = QDateEdit(calendarPopup=True)
        self.expiry_date_to.setDate(QDate.currentDate())
        self.expiry_date_to.setSpecialValueText("Не выбрано")
        layout.addWidget(self.expiry_date_to)

        layout.addWidget(QLabel("Статус:"))
        self.status = QComboBox()
        self.status.addItems(["ACTIVE", "DESTROYED"])
        self.status.setCurrentText("ACTIVE")
        layout.addWidget(self.status)

        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("Применить")
        apply_btn.clicked.connect(self.accept)
        clear_btn = QPushButton("Сбросить")
        clear_btn.clicked.connect(self.clear_filters)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if initial_filters:
            self.set_filters(initial_filters)

    def set_filters(self, filters):
        if 'fio' in filters:
            self.fio.setText(filters['fio'])
        if 'skzi_name' in filters:
            self.skzi_name.setText(filters['skzi_name'])
        if 'arm_type' in filters:
            self.arm_type.setText(filters['arm_type'])
        if 'cabinet_number' in filters:
            self.cabinet.setText(filters['cabinet_number'])
        if 'install_date_from' in filters:
            self.install_date_from.setDate(QDate.fromString(filters['install_date_from'], "dd.MM.yyyy"))
        if 'install_date_to' in filters:
            self.install_date_to.setDate(QDate.fromString(filters['install_date_to'], "dd.MM.yyyy"))
        if 'expiry_date_from' in filters:
            self.expiry_date_from.setDate(QDate.fromString(filters['expiry_date_from'], "dd.MM.yyyy"))
        if 'expiry_date_to' in filters:
            self.expiry_date_to.setDate(QDate.fromString(filters['expiry_date_to'], "dd.MM.yyyy"))
        if 'status' in filters:
            index = self.status.findText(filters['status'])
            if index >= 0:
                self.status.setCurrentIndex(index)

    def clear_filters(self):
        self.fio.clear()
        self.skzi_name.clear()
        self.arm_type.clear()
        self.cabinet.clear()
        self.install_date_from.setDate(QDate.currentDate().addYears(-1))
        self.install_date_to.setDate(QDate.currentDate())
        self.expiry_date_from.setDate(QDate.currentDate())
        self.expiry_date_to.setDate(QDate.currentDate())
        self.status.setCurrentText("ACTIVE")

    def get_filters(self):
        filters = {}
        if self.fio.text():
            filters['fio'] = self.fio.text()
        if self.skzi_name.text():
            filters['skzi_name'] = self.skzi_name.text()
        if self.arm_type.text():
            filters['arm_type'] = self.arm_type.text()
        if self.cabinet.text():
            filters['cabinet_number'] = self.cabinet.text()

        if self.install_date_from.date().year() > 1900:
            filters['install_date_from'] = self.install_date_from.date().toString("dd.MM.yyyy")
        if self.install_date_to.date().year() < 2100:
            filters['install_date_to'] = self.install_date_to.date().toString("dd.MM.yyyy")
        if self.expiry_date_from.date().year() > 1900:
            filters['expiry_date_from'] = self.expiry_date_from.date().toString("dd.MM.yyyy")
        if self.expiry_date_to.date().year() < 2100:
            filters['expiry_date_to'] = self.expiry_date_to.date().toString("dd.MM.yyyy")

        filters['status'] = self.status.currentText()
        return filters