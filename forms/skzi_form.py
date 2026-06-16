from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from services.skzi_service import SkziService
from services.employee_service import EmployeeService
from services.arm_service import ArmService
from services.dictionary_service import DictionaryService


class SkziForm(QDialog):
    def __init__(self, user, parent=None, record_id=None):
        super().__init__(parent)
        self.from_who = None
        self.skzi_inst = None
        self.expiry_date = None
        self.user = user
        self.record_id = record_id
        self.skzi_service = SkziService()
        self.emp_service = EmployeeService()
        self.arm_service = ArmService()
        self.dict_service = DictionaryService()
        self.init_ui()
        self.load_employees()
        self.load_dictionaries()
        if record_id:
            self.load_record()
            self.setWindowTitle("Редактирование записи СКЗИ")
        else:
            self.setWindowTitle("Регистрация выдачи и установки СКЗИ")

    def init_ui(self):
        self.setMinimumWidth(700)
        layout = QVBoxLayout(self)
        grid = QGridLayout()

        # Сотрудник
        grid.addWidget(QLabel("Пользователь (ФИО):"), 0, 0)
        self.emp_combo = QComboBox()
        grid.addWidget(self.emp_combo, 0, 1, 1, 2)

        # СКЗИ
        grid.addWidget(QLabel("<b>Параметры СКЗИ и ЭП:</b>"), 1, 0, 1, 3)

        grid.addWidget(QLabel("Наименование СКЗИ:"), 2, 0)
        self.skzi_name = QComboBox()
        self.skzi_name.setEditable(True)
        grid.addWidget(self.skzi_name, 2, 1, 1, 2)

        grid.addWidget(QLabel("Заводской № СКЗИ:"), 3, 0)
        self.skzi_serial = QLineEdit()
        grid.addWidget(self.skzi_serial, 3, 1)

        grid.addWidget(QLabel("№ экземпляра:"), 3, 2)
        self.skzi_inst = QLineEdit()
        grid.addWidget(self.skzi_inst, 3, 3)

        grid.addWidget(QLabel("№ сертификата ЭП:"), 4, 2)
        self.cert_num = QLineEdit()
        grid.addWidget(self.cert_num, 4, 3)

        # Дата установки (текущая дата)
        grid.addWidget(QLabel("Дата установки:"), 5, 2)
        self.install_date = QDateEdit(calendarPopup=True)
        self.install_date.setDate(QDate.currentDate())
        grid.addWidget(self.install_date, 5, 3)

        # Срок до (+15 месяцев от даты установки)
        grid.addWidget(QLabel("Срок до:"), 6, 2)
        self.expiry_date = QDateEdit(calendarPopup=True)
        self.expiry_date.setDate(QDate.currentDate().addMonths(15))
        grid.addWidget(self.expiry_date, 6, 3)

        # Сигнал изменения даты установки для автоматического пересчёта срока
        self.install_date.dateChanged.connect(self.update_expiry_from_install)

        # Тип носителя
        grid.addWidget(QLabel("Тип носителя:"), 7, 0)
        self.token_type = QComboBox()
        self.token_type.setEditable(True)
        grid.addWidget(self.token_type, 7, 1)

        grid.addWidget(QLabel("Номер носителя ЭП:"), 7, 2)
        self.token_num = QLineEdit()
        grid.addWidget(self.token_num, 7, 3)

        # От кого получен
        grid.addWidget(QLabel("От кого получен:"), 8, 0)
        self.from_who = QComboBox()
        self.from_who.setEditable(True)
        grid.addWidget(self.from_who, 8, 1)

        grid.addWidget(QLabel("№ письма:"), 8, 2)
        self.letter_num = QLineEdit()
        grid.addWidget(self.letter_num, 8, 3)

        # Дата получения письма (текущая дата)
        grid.addWidget(QLabel("Дата получения письма:"), 9, 0)
        self.receive_date = QDateEdit(calendarPopup=True)
        self.receive_date.setDate(QDate.currentDate())
        grid.addWidget(self.receive_date, 9, 1)

        # АРМ
        grid.addWidget(QLabel("<b>Параметры АРМ и Установки:</b>"), 10, 0, 1, 4)

        grid.addWidget(QLabel("Имя АРМ:"), 11, 0)
        self.arm_name = QLineEdit()
        grid.addWidget(self.arm_name, 11, 1)

        grid.addWidget(QLabel("Тип АРМ:"), 11, 2)
        self.arm_type = QComboBox()
        self.arm_type.setEditable(True)
        grid.addWidget(self.arm_type, 11, 3)

        grid.addWidget(QLabel("Серийный № АРМ:"), 12, 0)
        self.arm_serial = QLineEdit()
        grid.addWidget(self.arm_serial, 12, 1)

        grid.addWidget(QLabel("Кабинет:"), 12, 2)
        self.cabinet = QLineEdit()
        grid.addWidget(self.cabinet, 12, 3)

        grid.addWidget(QLabel("Адрес установки:"), 13, 0)
        self.address = QComboBox()
        self.address.setEditable(True)
        grid.addWidget(self.address, 13, 1, 1, 3)

        grid.addWidget(QLabel("Кто установил:"), 14, 2)
        self.installer = QLineEdit()
        self.installer.setText(self.user['username'])
        grid.addWidget(self.installer, 14, 3)

        layout.addLayout(grid)

        btn_save = QPushButton("💾 Сохранить запись" if not self.record_id else "💾 Обновить запись")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self.save_data)
        layout.addWidget(btn_save)

    def update_expiry_from_install(self):
        new_date = self.install_date.date().addMonths(15)
        self.expiry_date.setDate(new_date)

    def load_employees(self):
        emps = self.emp_service.get_all_employees()
        self.emp_combo.clear()
        for e in emps:
            self.emp_combo.addItem(e['fio'], e['id'])

    def load_dictionaries(self):
        # Наименования СКЗИ
        skzi_names = self.dict_service.get_skzi_names()
        self.skzi_name.clear()
        self.skzi_name.addItem("", None)
        for item in skzi_names:
            self.skzi_name.addItem(item['name'], item['id'])

        # Типы носителей
        media_types = self.dict_service.get_media_types()
        self.token_type.clear()
        self.token_type.addItem("", None)
        for item in media_types:
            self.token_type.addItem(item['name'], item['id'])

        # От кого получен
        received_from = self.dict_service.get_received_from()
        self.from_who.clear()
        self.from_who.addItem("", None)
        for item in received_from:
            self.from_who.addItem(item['name'], item['id'])

        # Типы АРМ
        arm_types = self.dict_service.get_arm_types()
        self.arm_type.clear()
        self.arm_type.addItem("", None)
        for item in arm_types:
            self.arm_type.addItem(item['name'], item['id'])

        # Адреса
        addresses = self.dict_service.get_addresses()
        self.address.clear()
        self.address.addItem("", None)
        for item in addresses:
            self.address.addItem(item['name'], item['id'])

    def load_record(self):
        record = self.skzi_service.get_skzi_by_id(self.record_id)
        if not record:
            return

        # Сотрудник
        emp_id = record.get('employee_id')
        if emp_id:
            index = self.emp_combo.findData(emp_id)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)

        # СКЗИ
        skzi_name_id = record.get('skzi_name_id')
        if skzi_name_id:
            idx = self.skzi_name.findData(skzi_name_id)
            if idx >= 0:
                self.skzi_name.setCurrentIndex(idx)
        else:
            self.skzi_name.setCurrentText(record.get('skzi_name', ''))

        self.skzi_serial.setText(record.get('skzi_number', ''))
        self.skzi_inst.setText(record.get('skzi_instance_number', ''))
        self.cert_num.setText(record.get('cert_number', ''))

        # Тип носителя
        media_type_id = record.get('media_type_id')
        if media_type_id:
            idx = self.token_type.findData(media_type_id)
            if idx >= 0:
                self.token_type.setCurrentIndex(idx)
        else:
            self.token_type.setCurrentText(record.get('media_type', ''))

        self.token_num.setText(record.get('media_number', ''))

        # От кого получен
        received_from_id = record.get('received_from_id')
        if received_from_id:
            idx = self.from_who.findData(received_from_id)
            if idx >= 0:
                self.from_who.setCurrentIndex(idx)
        else:
            self.from_who.setCurrentText(record.get('received_from', ''))

        self.letter_num.setText(record.get('receive_letter_num', ''))

        # Даты
        receive_date = record.get('receive_date')
        if receive_date:
            self.receive_date.setDate(QDate.fromString(receive_date, "yyyy-MM-dd"))
        install_date = record.get('install_date')
        if install_date:
            self.install_date.setDate(QDate.fromString(install_date, "yyyy-MM-dd"))
        expiry_date = record.get('expiry_date')
        if expiry_date:
            self.expiry_date.setDate(QDate.fromString(expiry_date, "yyyy-MM-dd"))

        self.installer.setText(record.get('installer_fio', self.user['username']))

        # АРМ
        arm = self.arm_service.get_arm_by_id(record.get('arm_id'))
        if arm:
            self.arm_name.setText(arm.get('arm_name', ''))
            self.cabinet.setText(arm.get('cabinet_number', ''))
            arm_type_id = arm.get('arm_type_id')
            if arm_type_id:
                idx = self.arm_type.findData(arm_type_id)
                if idx >= 0:
                    self.arm_type.setCurrentIndex(idx)
            self.arm_serial.setText(arm.get('arm_serial', ''))
            address_id = arm.get('install_address_id')
            if address_id:
                idx = self.address.findData(address_id)
                if idx >= 0:
                    self.address.setCurrentIndex(idx)

    def save_data(self):
        try:
            emp_id = self.emp_combo.currentData()
            if not emp_id:
                QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
                return
            if not self.skzi_name.currentText().strip():
                QMessageBox.warning(self, "Ошибка", "Введите наименование СКЗИ")
                return
            if not self.arm_serial.text().strip():
                QMessageBox.warning(self, "Ошибка", "Введите серийный номер АРМ")
                return

            # Получаем текстовые значения из комбобоксов (могут быть новые)
            skzi_name_text = self.skzi_name.currentText().strip()
            media_type_text = self.token_type.currentText().strip()
            received_from_text = self.from_who.currentText().strip()
            arm_type_text = self.arm_type.currentText().strip()
            address_text = self.address.currentText().strip()

            data = {
                'employee_id': emp_id,
                'skzi_name': skzi_name_text,
                'skzi_number': self.skzi_serial.text(),
                'skzi_instance_number': self.skzi_inst.text(),
                'media_type': media_type_text,
                'media_number': self.token_num.text(),
                'cert_number': self.cert_num.text() or None,
                'received_from': received_from_text,
                'receive_letter_num': self.letter_num.text(),
                'receive_date': self.receive_date.date().toString("yyyy-MM-dd"),
                'install_date': self.install_date.date().toString("yyyy-MM-dd"),
                'expiry_date': self.expiry_date.date().toString("yyyy-MM-dd"),
                'installer_fio': self.installer.text(),
                'knowledge_check': "не проводилась",
                'arm_name': self.arm_name.text(),
                'arm_serial': self.arm_serial.text(),
                'arm_type': arm_type_text,
                'cabinet_number': self.cabinet.text(),
                'install_address': address_text
            }

            if self.record_id:
                self.skzi_service.update_skzi(self.record_id, data, self.user['username'])
                QMessageBox.information(self, "Успех", "Запись успешно обновлена")
            else:
                self.skzi_service.register_skzi(data, self.user['username'])
                QMessageBox.information(self, "Успех", "Запись успешно добавлена")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить данные: {str(e)}")