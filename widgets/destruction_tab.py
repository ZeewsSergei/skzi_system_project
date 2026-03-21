from PyQt6.QtWidgets import *
from services.skzi_service import SkziService
from forms.destruction_dialog import DestructionDialog
from signals.app_signals import app_signals

class DestructionTab(QWidget):
    def __init__(self, user, main_window):
        super().__init__()
        self.test_btn = None
        self.btn_add = None
        self.table = None
        self.search = None
        self.user = user
        self.main = main_window
        self.service = SkziService()
        self.init_ui()
        self.refresh()
        app_signals.destruction_changed.connect(self.refresh)

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.search = QLineEdit(placeholderText="🔍 Поиск по уничтоженным...")
        self.search.textChanged.connect(self.filter_table)
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Сотрудник", "СКЗИ", "Серийный №", "Дата уничтожения", "№ акта", "Кто изъял"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        self.btn_add = QPushButton("✚ Зарегистрировать уничтожение")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.clicked.connect(self.open_destruction_dialog)
        layout.addWidget(self.btn_add)

        # Кнопка принудительного обновления (для отладки)
        self.test_btn = QPushButton("🔄 Принудительно обновить")
        self.test_btn.clicked.connect(self.refresh)
        layout.addWidget(self.test_btn)

    def refresh(self):
        print("DestructionTab.refresh() вызван")
        rows = self.service.get_destroyed()
        print(f"Получено записей: {len(rows)}")

        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for i, row in enumerate(rows):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(row['fio']))
            self.table.setItem(i, 2, QTableWidgetItem(row['skzi_name']))
            self.table.setItem(i, 3, QTableWidgetItem(row['skzi_number']))
            self.table.setItem(i, 4, QTableWidgetItem(row['withdrawal_date'] or ""))
            self.table.setItem(i, 5, QTableWidgetItem(row['destruction_act_num'] or ""))
            self.table.setItem(i, 6, QTableWidgetItem(row['withdrawer_fio'] or ""))

        self.table.setSortingEnabled(True)
        self.search.clear()
        self.filter_table()
        self.table.viewport().update()
        print("Таблица уничтожения обновлена")

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

    def open_destruction_dialog(self):
        dlg = DestructionDialog(self.user, self)
        if dlg.exec():
            print("Диалог уничтожения завершён, данные обновятся по сигналу")
            # refresh() вызовется автоматически