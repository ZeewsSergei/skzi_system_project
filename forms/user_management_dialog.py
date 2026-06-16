# forms/user_management_dialog.py
"""
Экран управления пользователями системы.
Доступен только пользователям с ролью ADMIN.

Возможности:
  • Просмотр списка всех пользователей
  • Создание нового пользователя
  • Разблокировка заблокированных учётных записей
  • Сброс пароля (установка временного с флагом must_change_password)
  • Изменение роли пользователя
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView,
    QGroupBox, QFormLayout, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush

from security.auth_service import AuthService
from core.enums import UserRole


class UserManagementDialog(QDialog):
    """Диалог управления пользователями (только для ADMIN)."""

    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.auth = AuthService()
        self.setWindowTitle("Управление пользователями")
        self.setMinimumSize(820, 520)
        self._init_ui()
        self._load_users()

    # ──────────────────────────────────────────────
    # Построение UI
    # ──────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)

        # ── Таблица пользователей ──
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Логин", "Роль", "Заблок.", "Попыток", "Смена пароля"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        root.addWidget(self.table)

        # ── Разделитель ──
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(line)

        panels = QHBoxLayout()
        panels.setSpacing(16)

        # ── Панель: создание пользователя ──
        create_box = QGroupBox("Создать пользователя")
        create_form = QFormLayout(create_box)
        create_form.setSpacing(8)

        self.new_login = QLineEdit()
        self.new_login.setPlaceholderText("Имя пользователя")
        create_form.addRow("Логин:", self.new_login)

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password.setPlaceholderText("Минимум 6 символов")
        create_form.addRow("Пароль:", self.new_password)

        self.new_password2 = QLineEdit()
        self.new_password2.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password2.setPlaceholderText("Повторите пароль")
        create_form.addRow("Подтверждение:", self.new_password2)

        self.new_role = QComboBox()
        for role in UserRole:
            self.new_role.addItem(role.value, role)
        self.new_role.setCurrentText(UserRole.OPERATOR)
        create_form.addRow("Роль:", self.new_role)

        btn_create = QPushButton("✚ Создать")
        btn_create.setObjectName("primaryButton")
        btn_create.clicked.connect(self._create_user)
        create_form.addRow("", btn_create)

        panels.addWidget(create_box)

        # ── Панель: действия над выбранным пользователем ──
        actions_box = QGroupBox("Действия над выбранным пользователем")
        actions_layout = QVBoxLayout(actions_box)
        actions_layout.setSpacing(8)

        self.selected_label = QLabel("Выберите пользователя из таблицы")
        self.selected_label.setStyleSheet("color: gray; font-style: italic;")
        actions_layout.addWidget(self.selected_label)

        # Изменение роли
        role_row = QHBoxLayout()
        role_row.addWidget(QLabel("Новая роль:"))
        self.change_role_combo = QComboBox()
        for role in UserRole:
            self.change_role_combo.addItem(role.value, role)
        role_row.addWidget(self.change_role_combo)
        self.btn_change_role = QPushButton("Изменить роль")
        self.btn_change_role.clicked.connect(self._change_role)
        self.btn_change_role.setEnabled(False)
        role_row.addWidget(self.btn_change_role)
        actions_layout.addLayout(role_row)

        # Сброс пароля
        reset_row = QHBoxLayout()
        reset_row.addWidget(QLabel("Временный пароль:"))
        self.reset_password_input = QLineEdit()
        self.reset_password_input.setPlaceholderText("Минимум 6 символов")
        reset_row.addWidget(self.reset_password_input)
        self.btn_reset_pwd = QPushButton("🔑 Сбросить пароль")
        self.btn_reset_pwd.clicked.connect(self._reset_password)
        self.btn_reset_pwd.setEnabled(False)
        reset_row.addWidget(self.btn_reset_pwd)
        actions_layout.addLayout(reset_row)

        # Разблокировать
        self.btn_unblock = QPushButton("🔓 Разблокировать учётную запись")
        self.btn_unblock.clicked.connect(self._unblock_user)
        self.btn_unblock.setEnabled(False)
        actions_layout.addWidget(self.btn_unblock)

        actions_layout.addStretch()

        # Предупреждение о себе
        self.self_warn = QLabel(
            "⚠ Нельзя заблокировать или изменить роль собственной учётной записи"
        )
        self.self_warn.setStyleSheet("color: #c0392b; font-size: 10px;")
        self.self_warn.setWordWrap(True)
        self.self_warn.setVisible(False)
        actions_layout.addWidget(self.self_warn)

        panels.addWidget(actions_box)
        root.addLayout(panels)

        # ── Кнопка закрыть ──
        close_row = QHBoxLayout()
        close_row.addStretch()
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        close_row.addWidget(btn_close)
        root.addLayout(close_row)

    # ──────────────────────────────────────────────
    # Загрузка данных
    # ──────────────────────────────────────────────

    def _load_users(self):
        """Обновляет таблицу из БД."""
        users = self.auth.get_all_users()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for i, u in enumerate(users):
            self.table.insertRow(i)

            self.table.setItem(i, 0, QTableWidgetItem(str(u['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(u['username']))
            self.table.setItem(i, 2, QTableWidgetItem(u['role']))

            blocked_text = "Да" if u['is_blocked'] else "Нет"
            blocked_item = QTableWidgetItem(blocked_text)
            if u['is_blocked']:
                blocked_item.setBackground(QBrush(QColor(255, 180, 180)))
            self.table.setItem(i, 3, blocked_item)

            attempts_item = QTableWidgetItem(str(u['failed_attempts']))
            if u['failed_attempts'] > 0:
                attempts_item.setForeground(QBrush(QColor(180, 60, 0)))
            self.table.setItem(i, 4, attempts_item)

            must_change = "Да" if u['must_change_password'] else "Нет"
            self.table.setItem(i, 5, QTableWidgetItem(must_change))

            # Текущий пользователь — выделяем серым
            if u['username'] == self.current_user['username']:
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    if item:
                        item.setBackground(QBrush(QColor(230, 230, 230)))

        self.table.setSortingEnabled(True)
        self._reset_actions()

    # ──────────────────────────────────────────────
    # Вспомогательные методы
    # ──────────────────────────────────────────────

    def _get_selected_username(self) -> str | None:
        """Возвращает логин выбранной строки или None."""
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 1)
        return item.text() if item else None

    def _is_self(self, username: str) -> bool:
        return username == self.current_user['username']

    def _reset_actions(self):
        """Сбрасывает панель действий в начальное состояние."""
        self.selected_label.setText("Выберите пользователя из таблицы")
        self.selected_label.setStyleSheet("color: gray; font-style: italic;")
        self.btn_change_role.setEnabled(False)
        self.btn_reset_pwd.setEnabled(False)
        self.btn_unblock.setEnabled(False)
        self.self_warn.setVisible(False)

    def _on_selection_changed(self):
        """Обновляет панель действий при смене выделения."""
        username = self._get_selected_username()
        if not username:
            self._reset_actions()
            return

        is_self = self._is_self(username)
        self.selected_label.setText(f"Выбран: {username}")
        self.selected_label.setStyleSheet("color: #2c3e50; font-weight: bold;")

        self.self_warn.setVisible(is_self)

        # Изменение роли и сброс пароля — доступны для всех кроме себя
        self.btn_change_role.setEnabled(not is_self)
        self.btn_reset_pwd.setEnabled(True)   # можно сбросить и себе

        # Разблокировка — только если заблокирован и не себя
        row = self.table.currentRow()
        blocked_item = self.table.item(row, 3)
        is_blocked = blocked_item and blocked_item.text() == "Да"
        self.btn_unblock.setEnabled(is_blocked and not is_self)

        # Выставляем текущую роль в комбобоксе
        role_item = self.table.item(row, 2)
        if role_item:
            idx = self.change_role_combo.findText(role_item.text())
            if idx >= 0:
                self.change_role_combo.setCurrentIndex(idx)

    # ──────────────────────────────────────────────
    # Действия
    # ──────────────────────────────────────────────

    def _create_user(self):
        login    = self.new_login.text().strip()
        password = self.new_password.text()
        confirm  = self.new_password2.text()
        role     = self.new_role.currentData()

        if not login:
            QMessageBox.warning(self, "Ошибка", "Введите логин.")
            return
        if len(login) < 3:
            QMessageBox.warning(self, "Ошибка", "Логин должен содержать минимум 3 символа.")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен содержать минимум 6 символов.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают.")
            return

        if self.auth.create_user(login, password, role.value):
            QMessageBox.information(self, "Успех",
                                    f"Пользователь «{login}» ({role.value}) создан.")
            self.new_login.clear()
            self.new_password.clear()
            self.new_password2.clear()
            self._load_users()
        else:
            QMessageBox.critical(self, "Ошибка",
                                 f"Пользователь с логином «{login}» уже существует.")

    def _change_role(self):
        username = self._get_selected_username()
        if not username:
            return
        if self._is_self(username):
            QMessageBox.warning(self, "Недопустимо",
                                "Нельзя изменить роль собственной учётной записи.")
            return

        new_role = self.change_role_combo.currentData()
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Изменить роль пользователя «{username}» на «{new_role.value}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.auth.db.execute_query(
                "UPDATE users SET role = ? WHERE username = ?",
                (new_role.value, username)
            )
            self.auth.db.commit()
            QMessageBox.information(self, "Успех",
                                    f"Роль «{username}» изменена на «{new_role.value}».")
            self._load_users()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось изменить роль:\n{e}")

    def _reset_password(self):
        username   = self._get_selected_username()
        new_passwd = self.reset_password_input.text()

        if not username:
            return
        if len(new_passwd) < 6:
            QMessageBox.warning(self, "Ошибка",
                                "Временный пароль должен содержать минимум 6 символов.")
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Сбросить пароль пользователя «{username}»?\n"
            "При следующем входе пользователь будет обязан его сменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Меняем пароль и устанавливаем must_change_password = 1
            pwd_hash = self.auth.hash_password(new_passwd)
            self.auth.db.execute_query(
                "UPDATE users SET password_hash = ?, must_change_password = 1 "
                "WHERE username = ?",
                (pwd_hash, username)
            )
            self.auth.db.commit()
            QMessageBox.information(
                self, "Успех",
                f"Пароль «{username}» сброшен.\n"
                "При следующем входе пользователь будет обязан его сменить."
            )
            self.reset_password_input.clear()
            self._load_users()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сбросить пароль:\n{e}")

    def _unblock_user(self):
        username = self._get_selected_username()
        if not username:
            return
        if self._is_self(username):
            QMessageBox.warning(self, "Недопустимо",
                                "Нельзя разблокировать собственную учётную запись.")
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Разблокировать учётную запись «{username}» и сбросить счётчик попыток?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.auth.unblock_user(username)
            QMessageBox.information(self, "Успех",
                                    f"Учётная запись «{username}» разблокирована.")
            self._load_users()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось разблокировать:\n{e}")