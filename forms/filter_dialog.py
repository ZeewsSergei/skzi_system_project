from PyQt6.QtWidgets import *
from core.enums import SkziStatus
from PyQt6.QtCore import QDate
from services.dictionary_service import DictionaryService
from services.department_service import DepartmentService

class FilterDialog(QDialog):
    def __init__(self, parent=None, initial_filters=None):
        super().__init__(parent)

        # Инициализация сервисов
        self.dict_service = DictionaryService()
        self.dept_service = DepartmentService()

        self.setWindowTitle("Расширенный фильтр")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # --- Отдел (выпадающий список) ---
        layout.addWidget(QLabel("Отдел:"))
        self.department_combo = QComboBox()
        self.department_combo.addItem("Не выбрано", None)
        depts = self.dept_service.get_all_departments()
        for d in depts:
            self.department_combo.addItem(d['name'], d['id'])
        layout.addWidget(self.department_combo)

        # --- Сотрудник (часть ФИО) ---
        layout.addWidget(QLabel("Сотрудник (часть ФИО):"))
        self.fio = QLineEdit()
        layout.addWidget(self.fio)

        # --- Наименование СКЗИ (выпадающий список) ---
        layout.addWidget(QLabel("Наименование СКЗИ:"))
        self.skzi_name_combo = QComboBox()
        self.skzi_name_combo.addItem("Не выбрано", None)
        skzi_names = self.dict_service.get_skzi_names()
        for item in skzi_names:
            self.skzi_name_combo.addItem(item['name'], item['id'])
        layout.addWidget(self.skzi_name_combo)

        # --- Тип АРМ (выпадающий список) ---
        layout.addWidget(QLabel("Тип АРМ:"))
        self.arm_type_combo = QComboBox()
        self.arm_type_combo.addItem("Не выбрано", None)
        arm_types = self.dict_service.get_arm_types()
        for item in arm_types:
            self.arm_type_combo.addItem(item['name'], item['id'])
        layout.addWidget(self.arm_type_combo)

        # --- Кабинет ---
        layout.addWidget(QLabel("Кабинет:"))
        self.cabinet = QLineEdit()
        layout.addWidget(self.cabinet)

        # --- Даты установки ---
        layout.addWidget(QLabel("Дата установки от:"))
        self.install_date_from = QDateEdit(calendarPopup=True)
        self.install_date_from.setSpecialValueText("Не выбрано")
        self.install_date_from.clear()
        layout.addWidget(self.install_date_from)

        layout.addWidget(QLabel("Дата установки до:"))
        self.install_date_to = QDateEdit(calendarPopup=True)
        self.install_date_to.setSpecialValueText("Не выбрано")
        self.install_date_to.clear()
        layout.addWidget(self.install_date_to)

        # --- Даты срока ---
        layout.addWidget(QLabel("Срок от:"))
        self.expiry_date_from = QDateEdit(calendarPopup=True)
        self.expiry_date_from.setSpecialValueText("Не выбрано")
        self.expiry_date_from.clear()
        layout.addWidget(self.expiry_date_from)

        layout.addWidget(QLabel("Срок до:"))
        self.expiry_date_to = QDateEdit(calendarPopup=True)
        self.expiry_date_to.setSpecialValueText("Не выбрано")
        self.expiry_date_to.clear()
        layout.addWidget(self.expiry_date_to)

        # --- Статус ---
        layout.addWidget(QLabel("Статус:"))
        self.status = QComboBox()
        self.status.addItems([SkziStatus.ACTIVE, SkziStatus.DESTROYED])
        self.status.setCurrentText(SkziStatus.ACTIVE)
        layout.addWidget(self.status)

        # --- Кнопки ---
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
        """Устанавливает значения виджетов из словаря фильтров."""
        if 'department_id' in filters and filters['department_id'] is not None:
            idx = self.department_combo.findData(filters['department_id'])
            if idx >= 0:
                self.department_combo.setCurrentIndex(idx)
        if 'fio' in filters:
            self.fio.setText(filters['fio'])
        if 'skzi_name_id' in filters and filters['skzi_name_id'] is not None:
            idx = self.skzi_name_combo.findData(filters['skzi_name_id'])
            if idx >= 0:
                self.skzi_name_combo.setCurrentIndex(idx)
        if 'arm_type_id' in filters and filters['arm_type_id'] is not None:
            idx = self.arm_type_combo.findData(filters['arm_type_id'])
            if idx >= 0:
                self.arm_type_combo.setCurrentIndex(idx)
        if 'cabinet_number' in filters:
            self.cabinet.setText(filters['cabinet_number'])
        if 'install_date_from' in filters and filters['install_date_from']:
            date = QDate.fromString(filters['install_date_from'], "yyyy-MM-dd")
            if date.isValid():
                self.install_date_from.setDate(date)
        if 'install_date_to' in filters and filters['install_date_to']:
            date = QDate.fromString(filters['install_date_to'], "yyyy-MM-dd")
            if date.isValid():
                self.install_date_to.setDate(date)
        if 'expiry_date_from' in filters and filters['expiry_date_from']:
            date = QDate.fromString(filters['expiry_date_from'], "yyyy-MM-dd")
            if date.isValid():
                self.expiry_date_from.setDate(date)
        if 'expiry_date_to' in filters and filters['expiry_date_to']:
            date = QDate.fromString(filters['expiry_date_to'], "yyyy-MM-dd")
            if date.isValid():
                self.expiry_date_to.setDate(date)
        if 'status' in filters:
            idx = self.status.findText(filters['status'])
            if idx >= 0:
                self.status.setCurrentIndex(idx)

    def clear_filters(self):
        self.department_combo.setCurrentIndex(0)
        self.fio.clear()
        self.skzi_name_combo.setCurrentIndex(0)
        self.arm_type_combo.setCurrentIndex(0)
        self.cabinet.clear()
        self.install_date_from.clear()
        self.install_date_to.clear()
        self.expiry_date_from.clear()
        self.expiry_date_to.clear()
        self.status.setCurrentText(SkziStatus.ACTIVE)

    def get_filters(self):
        filters = {}
        dept_id = self.department_combo.currentData()
        if dept_id is not None:
            filters['department_id'] = dept_id
        if self.fio.text():
            filters['fio'] = self.fio.text().strip()
        skzi_name_id = self.skzi_name_combo.currentData()
        if skzi_name_id is not None:
            filters['skzi_name_id'] = skzi_name_id
        arm_type_id = self.arm_type_combo.currentData()
        if arm_type_id is not None:
            filters['arm_type_id'] = arm_type_id
        if self.cabinet.text():
            filters['cabinet_number'] = self.cabinet.text().strip()

        # Проверяем, что дата валидна и не пуста
        if self.install_date_from.date().isValid() and not self.install_date_from.date().isNull():
            filters['install_date_from'] = self.install_date_from.date().toString("yyyy-MM-dd")
        if self.install_date_to.date().isValid() and not self.install_date_to.date().isNull():
            filters['install_date_to'] = self.install_date_to.date().toString("yyyy-MM-dd")
        if self.expiry_date_from.date().isValid() and not self.expiry_date_from.date().isNull():
            filters['expiry_date_from'] = self.expiry_date_from.date().toString("yyyy-MM-dd")
        if self.expiry_date_to.date().isValid() and not self.expiry_date_to.date().isNull():
            filters['expiry_date_to'] = self.expiry_date_to.date().toString("yyyy-MM-dd")

        filters['status'] = self.status.currentText()
        return filters