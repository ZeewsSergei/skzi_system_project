from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate, Qt
from services.skzi_service import SkziService
from forms.destruction_dialog import DestructionDialog
from signals.app_signals import app_signals
from utils.date_utils import DateTableWidgetItem, format_date_for_display
from core.enums import UserRole


class DestructionTab(QWidget):
    def __init__(self, user, main_window):
        super().__init__()
        self.table = None
        self.search = None
        self.column_filters = []
        self.user = user
        self.main = main_window
        self.service = SkziService()
        self.init_ui()
        self.refresh()
        app_signals.destruction_changed.connect(self.refresh)

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.search = QLineEdit(placeholderText="🔍 Быстрый поиск...")
        self.search.textChanged.connect(self.filter_table)
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 9)
        headers = ["", "ID", "Сотрудник", "Отдел", "СКЗИ", "Серийный №", "Дата уничтожения", "№ акта", "Кто изъял"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)

        # Строка фильтров
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(2)
        for col, header in enumerate(headers):
            if col == 0:
                filter_edit = QLineEdit()
                filter_edit.setVisible(False)
                filter_layout.addWidget(filter_edit)
                self.column_filters.append(None)
            elif header == "Дата уничтожения":
                filter_combo = QComboBox()
                filter_combo.addItem("Все")
                filter_combo.currentTextChanged.connect(self.apply_column_filters)
                filter_layout.addWidget(filter_combo)
                self.column_filters.append(filter_combo)
            else:
                filter_edit = QLineEdit()
                filter_edit.setPlaceholderText(f"Фильтр {header}")
                filter_edit.textChanged.connect(self.apply_column_filters)
                filter_layout.addWidget(filter_edit)
                self.column_filters.append(filter_edit)
        layout.addWidget(filter_widget)
        layout.addWidget(self.table)

        self.btn_add = QPushButton("✚ Зарегистрировать уничтожение")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.clicked.connect(self.open_destruction_dialog)
        # AUDITOR не может регистрировать уничтожение
        if self.user.get('role') == UserRole.AUDITOR:
            self.btn_add.setVisible(False)
        layout.addWidget(self.btn_add)

    def refresh(self):
        rows = self.service.get_destroyed()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        withdrawal_dates = set()

        for i, row in enumerate(rows):
            self.table.insertRow(i)
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(i, 0, chk)

            self.table.setItem(i, 1, QTableWidgetItem(str(row['id'])))
            self.table.setItem(i, 2, QTableWidgetItem(row['fio'] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(row['department'] or ""))
            self.table.setItem(i, 4, QTableWidgetItem(row['skzi_name'] or ""))
            self.table.setItem(i, 5, QTableWidgetItem(row['skzi_number'] or ""))

            withdrawal_date = row['withdrawal_date'] or ""
            # Обработка возможного None
            if withdrawal_date is None:
                withdrawal_date = ""
            display_date = withdrawal_date
            qdate = QDate()
            if withdrawal_date:
                try:
                    # Попытка распарсить как dd.MM.yyyy, затем yyyy-MM-dd
                    qdate = QDate.fromString(withdrawal_date, "dd.MM.yyyy")
                    if not qdate.isValid():
                        qdate = QDate.fromString(withdrawal_date, "yyyy-MM-dd")
                    if qdate.isValid():
                        display_date = qdate.toString("dd.MM.yyyy")
                except:
                    pass
            item_date = DateTableWidgetItem(display_date, qdate)
            self.table.setItem(i, 6, item_date)
            if display_date:
                withdrawal_dates.add(display_date)

            self.table.setItem(i, 7, QTableWidgetItem(row['destruction_act_num'] or ""))
            self.table.setItem(i, 8, QTableWidgetItem(row['withdrawer_fio'] or ""))

        self.table.setSortingEnabled(True)

        combo = self.column_filters[6]  # Дата уничтожения
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Все")
        for val in sorted(withdrawal_dates):
            combo.addItem(val)
        idx = combo.findText(current)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.blockSignals(False)

        self.apply_column_filters()
        self.filter_table()
        self.table.viewport().update()

    def apply_column_filters(self):
        for row in range(self.table.rowCount()):
            visible = True
            for col in range(1, self.table.columnCount()):
                filter_widget = self.column_filters[col]
                if filter_widget is None:
                    continue
                item = self.table.item(row, col)
                if not item:
                    continue
                cell_text = item.text().lower()
                if isinstance(filter_widget, QLineEdit):
                    filter_text = filter_widget.text().lower().strip()
                    if filter_text and filter_text not in cell_text:
                        visible = False
                        break
                elif isinstance(filter_widget, QComboBox):
                    filter_text = filter_widget.currentText()
                    if filter_text != "Все" and cell_text != filter_text.lower():
                        visible = False
                        break
            self.table.setRowHidden(row, not visible)

    def filter_table(self):
        text = self.search.text().lower()
        for i in range(self.table.rowCount()):
            if self.table.isRowHidden(i):
                continue
            match = False
            for j in range(1, self.table.columnCount()):
                item = self.table.item(i, j)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(i, not match)

    def open_destruction_dialog(self):
        dlg = DestructionDialog(self.user, self)
        if dlg.exec():
            print("Диалог уничтожения завершён, данные обновятся по сигналу")