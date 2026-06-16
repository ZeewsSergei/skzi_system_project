from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate, Qt
from services.training_service import TrainingService
from forms.training_dialog import TrainingDialog
from signals.app_signals import app_signals
from utils.date_utils import DateTableWidgetItem, format_date_for_display
from core.enums import UserRole


class TrainingTab(QWidget):
    def __init__(self, user, main_window):
        super().__init__()
        self.table = None
        self.search = None
        self.column_filters = []
        self.user = user
        self.main = main_window
        self.service = TrainingService()
        self.init_ui()
        self.refresh()
        app_signals.training_changed.connect(self.refresh)

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.search = QLineEdit(placeholderText="🔍 Быстрый поиск...")
        self.search.textChanged.connect(self.filter_table)
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 6)
        headers = ["ID", "Сотрудник", "Должность", "Отдел", "Дата", "Результат"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)

        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(2)
        for col, header in enumerate(headers):
            if header == "Результат":
                filter_combo = QComboBox()
                filter_combo.addItem("Все")
                filter_combo.addItems(["удовлетворительно", "неудовлетворительно"])
                filter_combo.currentTextChanged.connect(self.apply_column_filters)
                filter_layout.addWidget(filter_combo)
                self.column_filters.append(filter_combo)
            elif header == "Дата":
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

        # Блок кнопок
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("✚ Зарегистрировать обучение")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.clicked.connect(self.open_training_dialog)
        btn_layout.addWidget(self.btn_add)

        btn_edit = QPushButton("✏ Редактировать")
        btn_edit.clicked.connect(self.edit_selected)
        btn_layout.addWidget(btn_edit)

        btn_delete = QPushButton("🗑 Удалить запись")
        btn_delete.clicked.connect(self.delete_selected)
        btn_layout.addWidget(btn_delete)

        # AUDITOR не может изменять данные
        if self.user.get('role') == UserRole.AUDITOR:
            self.btn_add.setVisible(False)
            btn_edit.setVisible(False)
            btn_delete.setVisible(False)

        layout.addLayout(btn_layout)

    def refresh(self):
        rows = self.service.get_all_trainings()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        training_dates = set()
        for i, row in enumerate(rows):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(row['fio']))
            self.table.setItem(i, 2, QTableWidgetItem(row['position'] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(row['department'] or ""))

            training_date = row['training_date']
            display_date = training_date
            qdate = QDate()
            if training_date:
                try:
                    qdate = QDate.fromString(training_date, "dd.MM.yyyy")
                    if not qdate.isValid():
                        qdate = QDate.fromString(training_date, "yyyy-MM-dd")
                    display_date = qdate.toString("dd.MM.yyyy")
                except:
                    pass
            item_date = DateTableWidgetItem(display_date, qdate)
            self.table.setItem(i, 4, item_date)
            if display_date:
                training_dates.add(display_date)

            self.table.setItem(i, 5, QTableWidgetItem(row['result']))

        self.table.setSortingEnabled(True)

        combo = self.column_filters[4]  # Дата
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Все")
        for val in sorted(training_dates):
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
            for col, filter_widget in enumerate(self.column_filters):
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

    def get_selected_id(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        return int(self.table.item(current_row, 0).text())

    def edit_selected(self):
        training_id = self.get_selected_id()
        if not training_id:
            QMessageBox.warning(self, "Внимание", "Выберите запись для редактирования.")
            return
        dlg = TrainingDialog(self.user, self, record_id=training_id)
        if dlg.exec():
            self.refresh()

    def delete_selected(self):
        training_id = self.get_selected_id()
        if not training_id:
            QMessageBox.warning(self, "Внимание", "Выберите запись для удаления.")
            return
        reply = QMessageBox.question(self, "Подтверждение",
                                     "Вы действительно хотите удалить запись об обучении?\nЭто действие нельзя отменить.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.delete_training(training_id, self.user['username'])
                QMessageBox.information(self, "Успех", "Запись удалена.")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))