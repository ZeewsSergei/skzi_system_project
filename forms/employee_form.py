from PyQt6.QtWidgets import *
from services.department_service import DepartmentService
from services.sector_service import SectorService
from services.employee_service import EmployeeService

class EmployeeForm(QDialog):
    def __init__(self, parent=None, username="admin"):
        super().__init__(parent)
        self.emp_table = None
        self.clear_btn = None
        self.save_btn = None
        self.sector_combo = None
        self.dept_combo = None
        self.pos_input = None
        self.fio_input = None
        self.username = username
        self.current_edit_id = None
        self.current_knowledge = "не проводилась"
        self.emp_service = EmployeeService()
        self.dept_service = DepartmentService()
        self.sector_service = SectorService()
        self.init_ui()
        self.load_departments()
        self.load_sectors()
        self.load_employees()

    def init_ui(self):
        self.setWindowTitle("Реестр сотрудников")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        main_layout = QHBoxLayout()

        # Левая панель: форма ввода
        form_widget = QVBoxLayout()
        form_widget.addWidget(QLabel("<b>Данные сотрудника:</b>"))

        self.fio_input = QLineEdit(placeholderText="ФИО сотрудника полностью")
        self.pos_input = QLineEdit(placeholderText="Должность")

        # Отдел (редактируемый)
        form_widget.addWidget(QLabel("Отдел:"))
        self.dept_combo = QComboBox()
        self.dept_combo.setEditable(True)
        self.dept_combo.currentIndexChanged.connect(self.on_department_changed)
        form_widget.addWidget(self.dept_combo)

        # Сектор (редактируемый)
        form_widget.addWidget(QLabel("Сектор:"))
        self.sector_combo = QComboBox()
        self.sector_combo.setEditable(True)
        form_widget.addWidget(self.sector_combo)

        form_widget.addWidget(QLabel("ФИО:"))
        form_widget.addWidget(self.fio_input)
        form_widget.addWidget(QLabel("Должность:"))
        form_widget.addWidget(self.pos_input)

        self.save_btn = QPushButton("💾 Сохранить / Обновить")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.save_employee)
        form_widget.addWidget(self.save_btn)

        self.clear_btn = QPushButton("Очистить форму")
        self.clear_btn.clicked.connect(self.clear_inputs)
        form_widget.addWidget(self.clear_btn)

        form_widget.addStretch()
        main_layout.addLayout(form_widget, 1)

        # Правая панель: список сотрудников
        list_widget = QVBoxLayout()
        list_widget.addWidget(QLabel("<b>Список зарегистрированных сотрудников:</b>"))

        self.emp_table = QTableWidget(0, 5)
        self.emp_table.setHorizontalHeaderLabels(["ID", "ФИО", "Сектор", "Отдел", "Знания ЗИ"])
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.emp_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.emp_table.doubleClicked.connect(self.load_to_edit)
        list_widget.addWidget(self.emp_table)

        main_layout.addLayout(list_widget, 2)
        self.setLayout(main_layout)

    def load_departments(self):
        self.dept_combo.clear()
        self.dept_combo.addItem("", None)  # пустой отдел
        try:
            depts = self.dept_service.get_all_departments()
            for d in depts:
                self.dept_combo.addItem(d['name'], d['id'])
        except Exception as e:
            print(f"Ошибка загрузки отделов: {e}")

    def load_sectors(self, department_id=None):
        self.sector_combo.clear()
        self.sector_combo.addItem("", None)
        if department_id:
            try:
                sectors = self.sector_service.get_sectors_by_department(department_id)
                for s in sectors:
                    self.sector_combo.addItem(s['name'], s['id'])
            except Exception as e:
                print(f"Ошибка загрузки секторов: {e}")

    def on_department_changed(self):
        dept_id = self.dept_combo.currentData()
        self.load_sectors(dept_id)

    def load_employees(self):
        try:
            rows = self.emp_service.get_all_employees()
            self.emp_table.setRowCount(0)
            for i, row in enumerate(rows):
                self.emp_table.insertRow(i)
                self.emp_table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                self.emp_table.setItem(i, 1, QTableWidgetItem(row['fio']))
                self.emp_table.setItem(i, 2, QTableWidgetItem(row['sector_name'] or ""))
                self.emp_table.setItem(i, 3, QTableWidgetItem(row['department_name'] or ""))
                self.emp_table.setItem(i, 4, QTableWidgetItem(row['knowledge_check']))
        except Exception as e:
            print(f"Ошибка загрузки сотрудников: {e}")

    def load_to_edit(self):
        row = self.emp_table.currentRow()
        if row < 0:
            return
        emp_id = int(self.emp_table.item(row, 0).text())
        data = self.emp_service.repo.get_by_id(emp_id)
        if data:
            self.fio_input.setText(data['fio'])
            self.pos_input.setText(data['position'] or "")
            # отдел
            index = self.dept_combo.findData(data['department_id'])
            if index >= 0:
                self.dept_combo.setCurrentIndex(index)
            else:
                self.dept_combo.setCurrentText("")
            # сектор (после загрузки секторов)
            self.load_sectors(data['department_id'])
            index = self.sector_combo.findData(data['sector_id'])
            if index >= 0:
                self.sector_combo.setCurrentIndex(index)
            else:
                self.sector_combo.setCurrentText("")
            self.current_knowledge = data['knowledge_check'] or "не проводилась"
            self.current_edit_id = emp_id

    def save_employee(self):
        fio = self.fio_input.text().strip()
        pos = self.pos_input.text().strip()
        dept_text = self.dept_combo.currentText().strip()
        sector_text = self.sector_combo.currentText().strip()

        if not fio:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО")
            return

        # Обработка отдела
        dept_id = self.dept_combo.currentData()
        if dept_id is None and dept_text:
            # Новый отдел
            try:
                dept_id = self.dept_service.add_department(dept_text, self.username)
                # Добавляем в комбобокс для последующего использования
                self.dept_combo.addItem(dept_text, dept_id)
                self.dept_combo.setCurrentIndex(self.dept_combo.count() - 1)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать отдел: {e}")
                return
        elif not dept_text:
            dept_id = None

        # Обработка сектора
        sector_id = None
        if sector_text:
            # Проверяем, существует ли сектор с таким именем глобально
            existing = self.sector_service.get_by_name(sector_text)
            if existing:
                # Сектор уже существует
                if dept_id and existing['department_id'] != dept_id:
                    QMessageBox.critical(self, "Ошибка",
                                         f"Сектор '{sector_text}' уже существует в отделе "
                                         f"'{existing['department_name']}'. Нельзя использовать в текущем отделе.")
                    return
                sector_id = existing['id']
            else:
                # Новый сектор – обязателен отдел
                if not dept_id:
                    QMessageBox.critical(self, "Ошибка",
                                         "Для создания нового сектора необходимо выбрать или создать отдел.")
                    return
                try:
                    sector_id = self.sector_service.add_sector(sector_text, dept_id, self.username)
                    self.sector_combo.addItem(sector_text, sector_id)
                    self.sector_combo.setCurrentIndex(self.sector_combo.count() - 1)
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось создать сектор: {e}")
                    return

        try:
            if self.current_edit_id:
                self.emp_service.update_employee(
                    self.current_edit_id,
                    fio,
                    pos,
                    sector_id,
                    dept_id,
                    self.current_knowledge,
                    self.username
                )
                QMessageBox.information(self, "Успех", "Данные обновлены")
            else:
                self.emp_service.add_employee(
                    fio,
                    pos,
                    sector_id,
                    dept_id,
                    "не проводилась",
                    self.username
                )
                QMessageBox.information(self, "Успех", "Сотрудник добавлен")
            self.load_employees()
            self.clear_inputs()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def clear_inputs(self):
        self.fio_input.clear()
        self.pos_input.clear()
        self.dept_combo.setCurrentIndex(0)
        self.sector_combo.clear()
        self.sector_combo.addItem("", None)
        self.current_edit_id = None
        self.current_knowledge = "не проводилась"