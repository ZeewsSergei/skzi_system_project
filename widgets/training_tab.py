from PyQt6.QtWidgets import *
from services.training_service import TrainingService
from forms.training_dialog import TrainingDialog
from signals.app_signals import app_signals

class TrainingTab(QWidget):
    def __init__(self, user, main_window):
        super().__init__()
        self.btn_add = None
        self.table = None
        self.search = None
        self.user = user
        self.main = main_window
        self.service = TrainingService()
        self.init_ui()
        self.refresh()
        app_signals.training_changed.connect(self.refresh)

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.search = QLineEdit(placeholderText="🔍 Поиск по обучению...")
        self.search.textChanged.connect(self.filter_table)
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Сотрудник", "Должность", "Отдел", "Дата", "Результат"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        self.btn_add = QPushButton("✚ Зарегистрировать обучение")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.clicked.connect(self.open_training_dialog)
        layout.addWidget(self.btn_add)

    def refresh(self):
        rows = self.service.get_all_trainings()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for i, row in enumerate(rows):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(row['fio']))
            self.table.setItem(i, 2, QTableWidgetItem(row['position'] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(row['department'] or ""))
            self.table.setItem(i, 4, QTableWidgetItem(row['training_date']))
            self.table.setItem(i, 5, QTableWidgetItem(row['result']))
        self.table.setSortingEnabled(True)
        self.search.clear()
        self.filter_table()
        self.table.viewport().update()

    def filter_table(self):
        text = self.search.text().lower()
        for i in range(self.table.rowCount()):
            match = False
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(i, not match)

    def open_training_dialog(self):
        dlg = TrainingDialog(self.user, self)
        if dlg.exec():
            print("Диалог обучения завершён, данные обновятся по сигналу")