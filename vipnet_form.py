from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from services.vipnet_service import VipNetService
from services.employee_service import EmployeeService
from services.arm_service import ArmService
from services.dictionary_service import DictionaryService

class VipNetForm(QDialog):
    def __init__(self, user, parent=None, record_id=None):
        super().__init__(parent)
        self.cabinet = None
        self.arm_serial = None
        self.installer = None
        self.arm_type = None
        self.emp_combo = None
        self.from_who = None
        self.address = None
        self.arm_name = None
        self.letter_num = None
        self.skzi_account = None
        self.install_date = None
        self.skzi_name = None
        self.user = user
        self.record_id = record_id
        self.vipnet_service = VipNetService()
        self.emp_service = EmployeeService()
        self.arm_service = ArmService()
        self.dict_service = DictionaryService()
        self.init_ui()
        self.load_employees()
        self.load_dictionaries()
        if record_id:
            self.load_record()
            self.setWindowTitle("Редактирование записи ViPNet Client")
        else:
            self.setWindowTitle("Регистрация выдачи ViPNet Client")

    def init_ui(self):
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        grid = QGridLayout()

        row = 0
        grid.addWidget(QLabel("Пользователь (ФИО):"), row, 0)
        self.emp_combo = QComboBox()
        grid.addWidget(self.emp_combo, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("Наименование СКЗИ:"), row, 0)
        self.skzi_name = QComboBox()
        self.skzi_name.setEditable(True)
        grid.addWidget(self.skzi_name, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("Наименование узла ViPNet Client:"), row, 0)
        self.skzi_account = QLineEdit()
        grid.addWidget(self.skzi_account, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("Дата установки:"), row, 0)
        self.install_date = QDateEdit(calendarPopup=True)
        self.install_date.setDate(QDate.currentDate())
        grid.addWidget(self.install_date, row, 1)
        row += 1

        grid.addWidget(QLabel("От кого получен:"), row, 0)
        self.from_who = QComboBox()
        self.from_who.setEditable(True)
        grid.addWidget(self.from_who, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("Номер письма:"), row, 0)
        self.letter_num = QLineEdit()
        grid.addWidget(self.letter_num, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("<b>Параметры АРМ:</b>"), row, 0, 1, 3)
        row += 1

        grid.addWidget(QLabel("Имя АРМ:"), row, 0)
        self.arm_name = QLineEdit()
        grid.addWidget(self.arm_name, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("Тип АРМ:"), row, 0)
        self.arm_type = QComboBox()
        self.arm_type.setEditable(True)
        grid.addWidget(self.arm_type, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("Серийный № АРМ:"), row, 0)
        self.arm_serial = QLineEdit()
        grid.addWidget(self.arm_serial, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("Кабинет:"), row, 0)
        self.cabinet = QLineEdit()
        grid.addWidget(self.cabinet, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("Адрес установки:"), row, 0)
        self.address = QComboBox()
        self.address.setEditable(True)
        grid.addWidget(self.address, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("Кто установил:"), row, 0)
        self.installer = QLineEdit()
        self.installer.setText(self.user['username'])
        grid.addWidget(self.installer, row, 1, 1, 2)
        row += 1

        layout.addLayout(grid)

        btn_save = QPushButton("💾 Сохранить запись" if not self.record_id else "💾 Обновить запись")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self.save_data)
        layout.addWidget(btn_save)

    def load_employees(self):
        emps = self.emp_service.get_all_employees()
        self.emp_combo.clear()
        for e in emps:
            self.emp_combo.addItem(e['fio'], e['id'])

    def load_dictionaries(self):
        skzi_names = self.dict_service.get_skzi_names()
        self.skzi_name.clear()
        self.skzi_name.addItem("", None)
        for item in skzi_names:
            self.skzi_name.addItem(item['name'], item['id'])

        received_from = self.dict_service.get_received_from()
        self.from_who.clear()
        self.from_who.addItem("", None)
        for item in received_from:
            self.from_who.addItem(item['name'], item['id'])

        arm_types = self.dict_service.get_arm_types()
        self.arm_type.clear()
        self.arm_type.addItem("", None)
        for item in arm_types:
            self.arm_type.addItem(item['name'], item['id'])

        addresses = self.dict_service.get_addresses()
        self.address.clear()
        self.address.addItem("", None)
        for item in addresses:
            self.address.addItem(item['name'], item['id'])

    def load_record(self):
        record = self.vipnet_service.get_by_id(self.record_id)
        if not record:
            return
        index = self.emp_combo.findData(record['employee_id'])
        if index >= 0:
            self.emp_combo.setCurrentIndex(index)

        skzi_name_id = record.get('skzi_name_id')
        if skzi_name_id:
            idx = self.skzi_name.findData(skzi_name_id)
            if idx >= 0:
                self.skzi_name.setCurrentIndex(idx)

        self.skzi_account.setText(record['skzi_account'] or "")
        if record['install_date']:
            self.install_date.setDate(QDate.fromString(record['install_date'], "dd.MM.yyyy"))

        received_from_id = record.get('received_from_id')
        if received_from_id:
            idx = self.from_who.findData(received_from_id)
            if idx >= 0:
                self.from_who.setCurrentIndex(idx)

        self.letter_num.setText(record['receive_letter_num'] or "")
        self.installer.setText(record['installer_fio'] or self.user['username'])

        arm = self.arm_service.get_arm_by_id(record['arm_id'])
        if arm:
            self.arm_name.setText(arm['arm_name'] or "")
            self.cabinet.setText(arm['cabinet_number'] or "")
            arm_type_id = arm.get('arm_type_id')
            if arm_type_id:
                idx = self.arm_type.findData(arm_type_id)
                if idx >= 0:
                    self.arm_type.setCurrentIndex(idx)
            self.arm_serial.setText(arm['arm_serial'] or "")
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
            if not self.skzi_account.text().strip():
                QMessageBox.warning(self, "Ошибка", "Введите наименование узла ViPNet Client")
                return
            if not self.arm_serial.text().strip():
                QMessageBox.warning(self, "Ошибка", "Введите серийный номер АРМ")
                return

            skzi_name_text = self.skzi_name.currentText().strip()
            received_from_text = self.from_who.currentText().strip()
            arm_type_text = self.arm_type.currentText().strip()
            address_text = self.address.currentText().strip()

            data = {
                'employee_id': emp_id,
                'skzi_name': skzi_name_text,
                'skzi_account': self.skzi_account.text(),
                'received_from': received_from_text,
                'receive_letter_num': self.letter_num.text(),
                'install_date': self.install_date.date().toString("dd.MM.yyyy"),
                'installer_fio': self.installer.text(),
                'arm_name': self.arm_name.text(),
                'arm_serial': self.arm_serial.text(),
                'arm_type': arm_type_text,
                'cabinet_number': self.cabinet.text(),
                'install_address': address_text
            }

            if self.record_id:
                self.vipnet_service.update(self.record_id, data, self.user['username'])
                QMessageBox.information(self, "Успех", "Запись успешно обновлена")
            else:
                self.vipnet_service.register(data, self.user['username'])
                QMessageBox.information(self, "Успех", "Запись успешно добавлена")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить данные: {str(e)}")