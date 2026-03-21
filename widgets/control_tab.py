# widgets/control_tab.py

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox
)

from services.control_service import ControlService


class ControlTab(QWidget):

    def __init__(self, user, parent=None):
        super().__init__(parent)

        self.user = user
        self.service = ControlService()

        self.init_ui()
        self.refresh()

    def init_ui(self):

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "СКЗИ",
            "Сотрудник",
            "Дата проверки",
            "Результат",
            "Проверил"
        ])

        layout.addWidget(self.table)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.refresh)

        layout.addWidget(refresh_btn)

        self.setLayout(layout)

    def refresh(self):

        try:

            rows = self.service.get_all_controls()

            self.table.setRowCount(len(rows))

            for row_index, row in enumerate(rows):

                for col_index, value in enumerate(row):

                    self.table.setItem(
                        row_index,
                        col_index,
                        QTableWidgetItem(str(value))
                    )

        except Exception as e:

            QMessageBox.critical(self, "Ошибка", str(e))