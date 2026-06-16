# forms/dictionary_manager.py
"""
Экран управления справочниками системы.
Доступен только пользователям с ролью ADMIN.

Поддерживаемые справочники (8 штук):
  • Наименования СКЗИ       (skzi_names)
  • Типы носителей           (media_types)
  • От кого получен          (received_from)
  • Типы АРМ                 (arm_types)
  • Версии ОС                (os_versions)
  • Антивирусы               (antiviruses)
  • СЗИ от НСД               (szi_nsd_names)
  • Адреса установки         (addresses)

Возможности:
  • Просмотр записей выбранного справочника
  • Добавление новой записи
  • Переименование существующей
  • Удаление (с проверкой — нельзя удалить используемую запись)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QLineEdit,
    QPushButton, QMessageBox, QComboBox,
    QFrame, QSplitter, QWidget
)
from PyQt6.QtCore import Qt

from db.db_manager import DatabaseManager
from services.audit_service import AuditService
from signals.app_signals import app_signals


# ── Конфигурация справочников ──────────────────────────────────────────────
# Каждый элемент: (отображаемое имя, имя таблицы в БД, таблицы использования)
# «таблицы использования» — для проверки перед удалением
_DICTIONARIES = [
    (
        "📋 Наименования СКЗИ",
        "skzi_names",
        [("skzi_registry",          "skzi_name_id"),
         ("vipnet_installations",   "skzi_name_id")],
    ),
    (
        "💾 Типы носителей",
        "media_types",
        [("skzi_registry", "media_type_id")],
    ),
    (
        "📨 От кого получен",
        "received_from",
        [("skzi_registry",        "received_from_id"),
         ("vipnet_installations", "received_from_id")],
    ),
    (
        "🖥 Типы АРМ",
        "arm_types",
        [("arm", "arm_type_id")],
    ),
    (
        "🐧 Версии ОС",
        "os_versions",
        [("arm", "os_version_id")],
    ),
    (
        "🛡 Антивирусы",
        "antiviruses",
        [("arm", "antivirus_id")],
    ),
    (
        "🔒 СЗИ от НСД",
        "szi_nsd_names",
        [("arm",                     "szi_nsd_id"),
         ("szi_nsd_installations",   "szi_nsd_id")],
    ),
    (
        "📍 Адреса установки",
        "addresses",
        [("arm", "install_address_id")],
    ),
]


class DictionaryManagerDialog(QDialog):
    """Диалог CRUD-управления всеми справочниками."""

    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.db    = DatabaseManager()
        self.audit = AuditService()
        self._current_table = None   # имя текущей таблицы-справочника
        self._current_usage = []     # список (table, fk_col) для проверки при удалении

        self.setWindowTitle("Управление справочниками")
        self.setMinimumSize(780, 500)
        self._init_ui()

    # ──────────────────────────────────────────────
    # Построение UI
    # ──────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)

        # ── Выбор справочника ──
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Справочник:"))
        self.dict_combo = QComboBox()
        self.dict_combo.setMinimumWidth(280)
        for display_name, table, usage in _DICTIONARIES:
            self.dict_combo.addItem(display_name, (table, usage))
        self.dict_combo.currentIndexChanged.connect(self._on_dict_changed)
        top_row.addWidget(self.dict_combo)
        top_row.addStretch()

        lbl_hint = QLabel("Нельзя удалить запись, используемую в реестре")
        lbl_hint.setStyleSheet("color: gray; font-size: 11px;")
        top_row.addWidget(lbl_hint)
        root.addLayout(top_row)

        # ── Разделитель ──
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(line)

        # ── Основная область: список + панель действий ──
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая часть: список записей
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)

        left_layout.addWidget(QLabel("Записи справочника:"))
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.currentItemChanged.connect(self._on_item_selected)
        left_layout.addWidget(self.list_widget)

        self.count_label = QLabel("Всего: 0")
        self.count_label.setStyleSheet("color: gray; font-size: 10px;")
        left_layout.addWidget(self.count_label)

        splitter.addWidget(left)

        # Правая часть: панель действий
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(12)

        # Добавление
        add_group_label = QLabel("Добавить запись:")
        add_group_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(add_group_label)

        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText("Введите новое значение")
        self.add_input.returnPressed.connect(self._add_item)
        right_layout.addWidget(self.add_input)

        btn_add = QPushButton("✚ Добавить")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self._add_item)
        right_layout.addWidget(btn_add)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        right_layout.addWidget(line2)

        # Переименование
        rename_label = QLabel("Переименовать выбранную:")
        rename_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(rename_label)

        self.rename_input = QLineEdit()
        self.rename_input.setPlaceholderText("Новое название")
        self.rename_input.setEnabled(False)
        right_layout.addWidget(self.rename_input)

        self.btn_rename = QPushButton("✏ Переименовать")
        self.btn_rename.clicked.connect(self._rename_item)
        self.btn_rename.setEnabled(False)
        right_layout.addWidget(self.btn_rename)

        line3 = QFrame()
        line3.setFrameShape(QFrame.Shape.HLine)
        line3.setFrameShadow(QFrame.Shadow.Sunken)
        right_layout.addWidget(line3)

        # Удаление
        del_label = QLabel("Удалить выбранную:")
        del_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(del_label)

        self.btn_delete = QPushButton("🗑 Удалить")
        self.btn_delete.setStyleSheet(
            "QPushButton { color: #c0392b; border: 1px solid #c0392b; }"
            "QPushButton:hover { background: #fdecea; }"
            "QPushButton:disabled { color: gray; border-color: gray; }"
        )
        self.btn_delete.clicked.connect(self._delete_item)
        self.btn_delete.setEnabled(False)
        right_layout.addWidget(self.btn_delete)

        self.usage_label = QLabel("")
        self.usage_label.setStyleSheet("color: #e67e22; font-size: 10px;")
        self.usage_label.setWordWrap(True)
        right_layout.addWidget(self.usage_label)

        right_layout.addStretch()

        splitter.addWidget(right)
        splitter.setSizes([450, 300])
        root.addWidget(splitter)

        # ── Кнопка закрыть ──
        close_row = QHBoxLayout()
        close_row.addStretch()
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        close_row.addWidget(btn_close)
        root.addLayout(close_row)

        # Загружаем первый справочник
        self._on_dict_changed(0)

    # ──────────────────────────────────────────────
    # Загрузка данных
    # ──────────────────────────────────────────────

    def _on_dict_changed(self, index: int):
        """Вызывается при смене справочника в комбобоксе."""
        data = self.dict_combo.itemData(index)
        if data is None:
            return
        self._current_table, self._current_usage = data
        self._load_items()
        self._reset_actions()

    def _load_items(self):
        """Перезагружает список из текущей таблицы-справочника."""
        self.list_widget.clear()
        if not self._current_table:
            return
        try:
            cursor = self.db.execute_query(
                f"SELECT id, name FROM {self._current_table} ORDER BY name"
            )
            rows = cursor.fetchall()
            for row in rows:
                item = QListWidgetItem(row['name'])
                item.setData(Qt.ItemDataRole.UserRole, row['id'])
                self.list_widget.addItem(item)
            self.count_label.setText(f"Всего: {len(rows)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить справочник:\n{e}")

    # ──────────────────────────────────────────────
    # Вспомогательные
    # ──────────────────────────────────────────────

    def _reset_actions(self):
        self.rename_input.clear()
        self.rename_input.setEnabled(False)
        self.btn_rename.setEnabled(False)
        self.btn_delete.setEnabled(False)
        self.usage_label.setText("")

    def _on_item_selected(self, current: QListWidgetItem, _previous):
        """Обновляет панель действий при выборе записи."""
        if current is None:
            self._reset_actions()
            return

        name = current.text()
        record_id = current.data(Qt.ItemDataRole.UserRole)

        self.rename_input.setText(name)
        self.rename_input.setEnabled(True)
        self.btn_rename.setEnabled(True)

        # Проверяем использование
        use_count = self._count_usages(record_id)
        if use_count > 0:
            self.btn_delete.setEnabled(False)
            self.usage_label.setText(
                f"⛔ Используется в {use_count} записях — удаление невозможно"
            )
        else:
            self.btn_delete.setEnabled(True)
            self.usage_label.setText("✅ Не используется — можно удалить")

    def _count_usages(self, record_id: int) -> int:
        """Подсчитывает сколько раз запись используется во всех связанных таблицах."""
        total = 0
        for table, fk_col in self._current_usage:
            try:
                cursor = self.db.execute_query(
                    f"SELECT COUNT(*) as cnt FROM {table} WHERE {fk_col} = ?",
                    (record_id,)
                )
                row = cursor.fetchone()
                if row:
                    total += row['cnt']
            except Exception:
                pass   # таблица может не существовать в старых версиях БД
        return total

    def _get_selected(self) -> tuple[int, str] | tuple[None, None]:
        """Возвращает (id, name) выбранной записи или (None, None)."""
        item = self.list_widget.currentItem()
        if item is None:
            return None, None
        return item.data(Qt.ItemDataRole.UserRole), item.text()

    # ──────────────────────────────────────────────
    # CRUD-операции
    # ──────────────────────────────────────────────

    def _add_item(self):
        name = self.add_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите значение для добавления.")
            return
        if len(name) > 200:
            QMessageBox.warning(self, "Ошибка", "Значение слишком длинное (макс. 200 символов).")
            return

        # Проверяем дубликат
        cursor = self.db.execute_query(
            f"SELECT id FROM {self._current_table} WHERE LOWER(name) = LOWER(?)",
            (name,)
        )
        if cursor.fetchone():
            QMessageBox.warning(self, "Дубликат",
                                f"Запись «{name}» уже существует в этом справочнике.")
            return

        try:
            cursor = self.db.execute_query(
                f"INSERT INTO {self._current_table} (name) VALUES (?)", (name,)
            )
            new_id = cursor.lastrowid
            self.db.commit()
            self.audit.log(
                "CREATE", self._current_table, new_id,
                self.current_user['username'],
                f"Добавлена запись в справочник: {name}"
            )
            self.add_input.clear()
            self._load_items()
            # Выбираем только что добавленную запись
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).data(Qt.ItemDataRole.UserRole) == new_id:
                    self.list_widget.setCurrentRow(i)
                    break
            app_signals.skzi_changed.emit()  # обновляем комбобоксы в формах
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись:\n{e}")

    def _rename_item(self):
        record_id, old_name = self._get_selected()
        if record_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для переименования.")
            return

        new_name = self.rename_input.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Ошибка", "Введите новое название.")
            return
        if new_name == old_name:
            return   # ничего не изменилось — молча выходим

        # Проверяем дубликат (кроме самой записи)
        cursor = self.db.execute_query(
            f"SELECT id FROM {self._current_table} "
            f"WHERE LOWER(name) = LOWER(?) AND id != ?",
            (new_name, record_id)
        )
        if cursor.fetchone():
            QMessageBox.warning(self, "Дубликат",
                                f"Запись «{new_name}» уже существует.")
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Переименовать «{old_name}» → «{new_name}»?\n\n"
            "Изменение затронет все связанные записи реестра.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.execute_query(
                f"UPDATE {self._current_table} SET name = ? WHERE id = ?",
                (new_name, record_id)
            )
            self.db.commit()
            self.audit.log(
                "UPDATE", self._current_table, record_id,
                self.current_user['username'],
                f"Переименовано: {old_name} → {new_name}",
                old_value=old_name
            )
            self._load_items()
            # Восстанавливаем выделение на переименованной записи
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).data(Qt.ItemDataRole.UserRole) == record_id:
                    self.list_widget.setCurrentRow(i)
                    break
            app_signals.skzi_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось переименовать:\n{e}")

    def _delete_item(self):
        record_id, name = self._get_selected()
        if record_id is None:
            return

        # Финальная проверка использования прямо перед удалением
        use_count = self._count_usages(record_id)
        if use_count > 0:
            QMessageBox.warning(
                self, "Невозможно удалить",
                f"Запись «{name}» используется в {use_count} записях реестра.\n"
                "Сначала измените или удалите связанные записи."
            )
            return

        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Удалить «{name}» из справочника?\nЭто действие необратимо.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.execute_query(
                f"DELETE FROM {self._current_table} WHERE id = ?", (record_id,)
            )
            self.db.commit()
            self.audit.log(
                "DELETE", self._current_table, record_id,
                self.current_user['username'],
                f"Удалена запись из справочника: {name}"
            )
            self._load_items()
            self._reset_actions()
            app_signals.skzi_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить:\n{e}")