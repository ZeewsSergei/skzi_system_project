from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import *
from services.szi_nsd_service import SziNsdService
from forms.szi_nsd_form import SziNsdForm
from forms.destruction_nsd_dialog import DestructionNsdDialog
from signals.app_signals import app_signals
from utils.date_utils import DateTableWidgetItem, format_date_for_display
from core.enums import UserRole


class SziNsdTab(QWidget):
    def __init__(self, user, main_window):
        super().__init__()
        self.table = None
        self.search = None
        self.column_filters = []
        self.user = user
        self.main = main_window
        self.service = SziNsdService()
        self.init_ui()
        self.refresh()
        app_signals.skzi_changed.connect(self.refresh)

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.search = QLineEdit(placeholderText="🔍 Быстрый поиск...")
        self.search.textChanged.connect(self.filter_table)
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 11)
        headers = [
            "", "ID", "ФИО", "Отдел", "Имя АРМ", "Серийный № АРМ", "Кабинет", "СЗИ от НСД", "Адрес установки", "Дата установки", ""
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)

        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(2)
        for col, header in enumerate(headers):
            if col == 0 or header == "":
                filter_edit = QLineEdit()
                filter_edit.setVisible(False)
                filter_layout.addWidget(filter_edit)
                self.column_filters.append(None)
            elif header == "Дата установки":
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

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("✚ Зарегистрировать выдачу")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self.open_szi_nsd_form)
        btn_layout.addWidget(btn_add)

        btn_edit = QPushButton("✏ Редактировать")
        btn_edit.clicked.connect(self.edit_selected)
        btn_layout.addWidget(btn_edit)

        btn_destroy = QPushButton("🗑 Зарегистрировать уничтожение")
        btn_destroy.clicked.connect(self.open_destruction_dialog)
        btn_layout.addWidget(btn_destroy)

        # AUDITOR не может изменять данные
        if self.user.get('role') == UserRole.AUDITOR:
            btn_add.setVisible(False)
            btn_edit.setVisible(False)
            btn_destroy.setVisible(False)

        layout.addLayout(btn_layout)

    def refresh(self):
        rows = self.service.get_all_active()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        install_dates = set()
        for i, row in enumerate(rows):
            self.table.insertRow(i)
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(i, 0, chk)

            self.table.setItem(i, 1, QTableWidgetItem(str(row['id'])))
            self.table.setItem(i, 2, QTableWidgetItem(row['fio']))
            self.table.setItem(i, 3, QTableWidgetItem(row['department'] or ""))
            self.table.setItem(i, 4, QTableWidgetItem(row['arm_name'] or ""))
            self.table.setItem(i, 5, QTableWidgetItem(row['arm_serial'] or ""))
            self.table.setItem(i, 6, QTableWidgetItem(row['cabinet_number'] or ""))
            self.table.setItem(i, 7, QTableWidgetItem(row['szi_nsd'] or ""))
            self.table.setItem(i, 8, QTableWidgetItem(row['install_address'] or ""))

            install_date = row['install_date'] or ""
            display_date = install_date
            qdate = QDate()
            if install_date:
                try:
                    qdate = QDate.fromString(install_date, "dd.MM.yyyy")
                    if not qdate.isValid():
                        qdate = QDate.fromString(install_date, "yyyy-MM-dd")
                    display_date = qdate.toString("dd.MM.yyyy")
                except:
                    pass
            item_date = DateTableWidgetItem(display_date, qdate)
            self.table.setItem(i, 9, item_date)
            if display_date:
                install_dates.add(display_date)

            self.table.setItem(i, 10, QTableWidgetItem(""))

        self.table.setSortingEnabled(True)

        combo = self.column_filters[9]  # Дата установки
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Все")
        for val in sorted(install_dates):
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
            for j in range(1, self.table.columnCount() - 1):
                item = self.table.item(i, j)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(i, not match)

    def get_selected_ids(self):
        ids = []
        for i in range(self.table.rowCount()):
            chk = self.table.item(i, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked:
                id_item = self.table.item(i, 1)
                if id_item:
                    ids.append(int(id_item.text()))
        return ids

    def edit_selected(self):
        ids = self.get_selected_ids()
        if len(ids) == 0:
            QMessageBox.warning(self, "Внимание", "Не выбрано ни одной записи.")
            return
        if len(ids) > 1:
            QMessageBox.warning(self, "Внимание", "Выберите только одну запись для редактирования.")
            return
        dlg = SziNsdForm(self.user, self, record_id=ids[0])
        if dlg.exec():
            self.refresh()

    def open_szi_nsd_form(self):
        dlg = SziNsdForm(self.user, self)
        if dlg.exec():
            print("Диалог СЗИ от НСД завершён, данные обновятся по сигналу")

    def open_destruction_dialog(self):
        dlg = DestructionNsdDialog(self.user, self)
        if dlg.exec():
            print("Диалог уничтожения СЗИ от НСД завершён, данные обновятся по сигналу")