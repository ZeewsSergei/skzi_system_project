from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from services.training_service import TrainingService
from services.employee_service import EmployeeService
from services.department_service import DepartmentService

class TrainingDialog(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.result_combo = None
        self.date_edit = None
        self.department_combo = None
        self.position_combo = None
        self.emp_combo = None
        self.user = user
        self.training_service = TrainingService()
        self.emp_service = EmployeeService()
        self.dept_service = DepartmentService()
        self.setWindowTitle("Регистрация обучения")
        self.setMinimumWidth(450)
        self.init_ui()
        self.load_employees()
        self.load_positions()
        self.load_departments()

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Сотрудник:"))
        self.emp_combo = QComboBox()
        layout.addWidget(self.emp_combo)

        layout.addWidget(QLabel("Дата обучения:"))
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addWidget(self.date_edit)

        layout.addWidget(QLabel("Результат:"))
        self.result_combo = QComboBox()
        self.result_combo.addItems(["удовлетворительно", "неудовлетворительно"])
        layout.addWidget(self.result_combo)

        layout.addWidget(QLabel("Должность (на момент обучения):"))
        self.position_combo = QComboBox()
        self.position_combo.setEditable(True)
        layout.addWidget(self.position_combo)

        layout.addWidget(QLabel("Отдел (на момент обучения):"))
        self.department_combo = QComboBox()
        self.department_combo.setEditable(True)
        layout.addWidget(self.department_combo)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def load_employees(self):
        emps = self.emp_service.get_all_employees()
        self.emp_combo.clear()
        for e in emps:
            self.emp_combo.addItem(f"{e['fio']} ({e['position']})", e['id'])
        self.emp_combo.currentIndexChanged.connect(self.fill_employee_data)

    def fill_employee_data(self):
        emp_id = self.emp_combo.currentData()
        if emp_id:
            emp = self.emp_service.repo.get_by_id(emp_id)
            if emp:
                idx = self.position_combo.findText(emp['position'] or "")
                if idx >= 0:
                    self.position_combo.setCurrentIndex(idx)
                else:
                    self.position_combo.setCurrentText(emp['position'] or "")
                dept = self.dept_service.repo.get_by_id(emp['department_id']) if emp['department_id'] else None
                dept_name = dept['name'] if dept else ""
                idx = self.department_combo.findText(dept_name)
                if idx >= 0:
                    self.department_combo.setCurrentIndex(idx)
                else:
                    self.department_combo.setCurrentText(dept_name)

    def load_positions(self):
        emps = self.emp_service.get_all_employees()
        positions = sorted(set(e['position'] for e in emps if e['position']))
        self.position_combo.clear()
        self.position_combo.addItems(positions)

    def load_departments(self):
        depts = self.dept_service.get_all_departments()
        self.department_combo.clear()
        self.department_combo.addItems([d['name'] for d in depts])

    def save(self):
        emp_id = self.emp_combo.currentData()
        if emp_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
            return
        date = self.date_edit.date().toString("dd.MM.yyyy")
        result = self.result_combo.currentText()
        position = self.position_combo.currentText().strip()
        department = self.department_combo.currentText().strip()
        try:
            self.training_service.register_training(emp_id, date, result, position, department, self.user['username'])
            QMessageBox.information(self, "Успех", "Результат обучения сохранён")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))