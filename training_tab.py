from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLineEdit

from repositories.training_repository import get_all_trainings
from services.training_service import TrainingService
from signals.app_signals import app_signals
from forms.training_dialog import TrainingDialog

class TrainingTab(QWidget):
    def __init__(self, user, main_window):
        super().__init__()
        self.table = None
        self.btn_add = None
        self.search = None
        self.user = user
        self.main = main_window
        self.service = TrainingService()
        self.init_ui()
        self.refresh()
        # Подключаемся к сигналу
        app_signals.training_changed.connect(self.refresh)

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.search = QLineEdit(placeholderText="🔍 Поиск по обучению...")
        self.search.textChanged.connect(self.filter_table)
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Сотрудник", "Дата", "Результат", "Должность"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        self.btn_add = QPushButton("✚ Зарегистрировать обучение")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.clicked.connect(self.open_training_dialog)
        layout.addWidget(self.btn_add)

    def refresh(self):
        rows = get_all_trainings()
        self.table.setRowCount(0)
        for i, row in enumerate(rows):
            self.table.insertRow(i)
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val) if val else ""))
        self.filter_table()  # применить текущий поиск

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
            # Данные уже обновятся через сигнал
            pass