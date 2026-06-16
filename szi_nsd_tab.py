from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from services.szi_nsd_service import SziNsdService
from forms.szi_nsd_form import SziNsdForm
from signals.app_signals import app_signals

class SziNsdTab(QWidget):
    def __init__(self, user, main_window):
        super().__init__()
        self.table = None
        self.search = None
        self.user = user
        self.main = main_window
        self.service = SziNsdService()
        self.init_ui()
        self.refresh()
        app_signals.skzi_changed.connect(self.refresh)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Поиск
        self.search = QLineEdit(placeholderText="🔍 Поиск по всем полям...")
        self.search.textChanged.connect(self.filter_table)
        layout.addWidget(self.search)

        # Таблица – копия настроек из реестра
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            ["", "ID", "ФИО", "Отдел", "Имя АРМ", "Серийный № АРМ", "Кабинет", "СЗИ от НСД", "Адрес установки", "Дата установки"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("✚ Зарегистрировать выдачу")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self.open_szi_nsd_form)
        btn_layout.addWidget(btn_add)

        btn_edit = QPushButton("✏ Редактировать")
        btn_edit.clicked.connect(self.edit_selected)
        btn_layout.addWidget(btn_edit)

        layout.addLayout(btn_layout)

    def refresh(self):
        rows = self.service.get_all_active()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

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
            self.table.setItem(i, 9, QTableWidgetItem(row['install_date'] or ""))

        self.table.setSortingEnabled(True)
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