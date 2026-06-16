# utils/date_utils.py
"""
Утилиты для работы с датами в таблицах PyQt6.
Вынесено из main_window, training_tab, szi_nsd_tab,
destruction_tab, vipnet_tab во избежание дублирования.
"""

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import QTableWidgetItem


class DateTableWidgetItem(QTableWidgetItem):
    """
    Элемент таблицы с поддержкой корректной сортировки дат.

    Принимает строку даты в формате dd.MM.yyyy или yyyy-MM-dd
    и сохраняет QDate для сравнения при сортировке.
    Пустые / нераспознанные строки считаются «минимальной» датой
    и оказываются в конце при сортировке по возрастанию.
    """

    # Форматы разбора — порядок важен: сначала отображаемый, потом ISO
    _PARSE_FORMATS = ("dd.MM.yyyy", "yyyy-MM-dd")

    def __init__(self, date_str: str, qdate: QDate = None):
        super().__init__(date_str or "")
        if qdate is not None:
            self.qdate = qdate
        elif date_str:
            self.qdate = self._parse(date_str)
        else:
            self.qdate = QDate()  # невалидная дата — сортируется последней

        self.setData(Qt.ItemDataRole.UserRole, self.qdate)

    @classmethod
    def _parse(cls, date_str: str) -> QDate:
        """Пробует разобрать строку по известным форматам."""
        for fmt in cls._PARSE_FORMATS:
            q = QDate.fromString(date_str, fmt)
            if q.isValid():
                return q
        return QDate()  # не распознано

    def __lt__(self, other) -> bool:
        if isinstance(other, DateTableWidgetItem):
            # Невалидные даты уходят в конец (считаем их «максимальными»)
            if not self.qdate.isValid():
                return False
            if not other.qdate.isValid():
                return True
            return self.qdate < other.qdate
        return super().__lt__(other)


def format_date_for_display(date_str: str) -> tuple[str, QDate]:
    """
    Вспомогательная функция: принимает строку даты из БД (yyyy-MM-dd
    или dd.MM.yyyy), возвращает кортеж (отображаемая строка, QDate).

    Используется в методах refresh() вкладок для единообразного
    преобразования дат перед заполнением таблицы.

    Пример:
        display, qdate = format_date_for_display(row['install_date'])
        table.setItem(i, col, DateTableWidgetItem(display, qdate))
    """
    if not date_str:
        return "", QDate()

    item = DateTableWidgetItem(date_str)
    display = item.qdate.toString("dd.MM.yyyy") if item.qdate.isValid() else date_str
    return display, item.qdate