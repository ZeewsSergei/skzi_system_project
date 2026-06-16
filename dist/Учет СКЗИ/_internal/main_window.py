# main_window.py

import os
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QAction, QIcon, QColor, QBrush
from PyQt6.QtCore import QDate, Qt, QTimer
from db.db_manager import DatabaseManager
from services.employee_service import EmployeeService
from services.skzi_service import SkziService
from services.audit_service import AuditService
from services.dictionary_service import DictionaryService
from services.arm_service import ArmService
from forms.mass_destruction_dialog import MassDestructionDialog
from forms.backup_dialog import BackupDialog
from forms.employee_form import EmployeeForm
from forms.skzi_form import SkziForm
from forms.department_form import DepartmentForm
from forms.change_password_dialog import ChangePasswordDialog
from widgets.vipnet_tab import VipNetTab
from widgets.szi_nsd_tab import SziNsdTab
from widgets.destruction_tab import DestructionTab
from widgets.training_tab import TrainingTab
from widgets.help_tab import HelpTab
from utils.excel_exporter import ExcelExporter
from utils.tray_icon import SystemTrayIcon
from signals.app_signals import app_signals
from utils.date_utils import DateTableWidgetItem, format_date_for_display
from core.enums import SkziStatus, UserRole
from forms.user_management_dialog import UserManagementDialog
from forms.dictionary_manager import DictionaryManagerDialog
from forms.dictionary_manager import DictionaryManagerDialog
from utils.helpers import (
    import_employees_from_excel,
    import_skzi_names,
    import_media_types,
    import_received_from,
    import_arm_types,
    import_os_versions,
    import_antiviruses,
    import_szi_nsd_names,
    import_addresses
)
from logger import app_logger

# ── Константы подсветки истекающих СКЗИ ──────────────────────────
# Число дней до истечения срока, при котором строка красится жёлтым
_EXPIRY_WARN_DAYS = 30
# Цвет строки: срок истёк (красный фон)
_COLOR_EXPIRED   = QColor(255, 200, 200)   # светло-красный
# Цвет строки: срок истекает в ближайшие 30 дней (жёлтый фон)
_COLOR_EXPIRING  = QColor(255, 255, 180)   # светло-жёлтый
# Цвет текста для обоих случаев
_COLOR_TEXT_WARN = QColor(120, 40, 40)     # тёмно-красный текст



def find_icon_file():
    from utils.path_helper import get_app_root
    app_root = get_app_root()
    candidates = [
        os.path.join(app_root, 'resources', 'app_icon.ico'),
        os.path.join(app_root, 'app_icon.ico'),
        os.path.join(app_root, 'icon.ico'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None



class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.arm_service = ArmService()
        self.audit_table = None
        self.reg_table = None
        self.audit_tab = None
        self.reg_tab = None
        self.training_tab = None
        self.help_tab = None
        self.reg_search = None
        self.szi_nsd_tab = None
        self.vipnet_tab = None
        self.destruction_tab = None
        self.tabs = None
        self.user = user
        self.db = DatabaseManager()
        self.emp_service = EmployeeService()
        self.skzi_service = SkziService()
        self.audit_service = AuditService()
        self.dict_service = DictionaryService()
        self.exporter = ExcelExporter(self.db)
        self.exporter.set_parent(self)
        self.emp_form = None
        self.tray_icon = None
        self.column_filters = []  # список виджетов фильтров для реестра
        self.setup_tray_icon()

        self.setWindowTitle(f"Учет СКЗИ - [{user['username']} ({user['role']})]")
        self.resize(1300, 800)
        self.init_menu()
        self.init_toolbar()
        self.init_ui()

        app_signals.skzi_changed.connect(self.load_registry)
        app_signals.employee_changed.connect(self.on_employee_changed)
        app_signals.department_changed.connect(self.load_registry)

        self.load_registry()
        self.load_audit()

        # Показываем уведомление об истекающих сроках через 1 сек после запуска
        # (через QTimer чтобы окно успело полностью отобразиться)
        QTimer.singleShot(1000, self._check_expiry_on_startup)

    def _is_readonly(self) -> bool:
        """
        Возвращает True если пользователь имеет роль AUDITOR.
        AUDITOR может только читать данные — все кнопки изменения
        данных должны быть скрыты или отключены.
        """
        return self.user.get('role') == UserRole.AUDITOR

    def _highlight_expiry_row(self, row_index: int, expiry_qdate: QDate):
        """
        Окрашивает строку таблицы реестра в зависимости от срока действия:
          • красный фон  — срок уже истёк
          • жёлтый фон   — истекает в ближайшие _EXPIRY_WARN_DAYS дней
          • без цвета    — срок в норме или не задан
        """
        if not expiry_qdate.isValid():
            return

        today = QDate.currentDate()
        days_left = today.daysTo(expiry_qdate)   # < 0 если просрочен

        if days_left < 0:
            bg = QBrush(_COLOR_EXPIRED)
            fg = QBrush(_COLOR_TEXT_WARN)
        elif days_left <= _EXPIRY_WARN_DAYS:
            bg = QBrush(_COLOR_EXPIRING)
            fg = QBrush(_COLOR_TEXT_WARN)
        else:
            return   # норма — не красим

        for col in range(self.reg_table.columnCount()):
            item = self.reg_table.item(row_index, col)
            if item:
                item.setBackground(bg)
                item.setForeground(fg)

    def _check_expiry_on_startup(self):
        """
        Показывает итоговое уведомление при запуске если есть
        просроченные или истекающие СКЗИ.
        Вызывается один раз через QTimer после загрузки окна.
        """
        today = QDate.currentDate()
        expired_count  = 0
        expiring_count = 0

        for i in range(self.reg_table.rowCount()):
            item = self.reg_table.item(i, 12)   # колонка «Срок до»
            if not item or not item.text():
                continue
            # DateTableWidgetItem хранит QDate в UserRole
            from PyQt6.QtCore import Qt as _Qt
            qdate = item.data(_Qt.ItemDataRole.UserRole)
            if not qdate or not qdate.isValid():
                continue
            days = today.daysTo(qdate)
            if days < 0:
                expired_count += 1
            elif days <= _EXPIRY_WARN_DAYS:
                expiring_count += 1

        parts = []
        if expired_count:
            parts.append(f"🔴 Просрочено: {expired_count} шт.")
        if expiring_count:
            parts.append(
                f"🟡 Истекает в течение {_EXPIRY_WARN_DAYS} дней: "
                f"{expiring_count} шт."
            )

        if parts:
            QMessageBox.warning(
                self,
                "Внимание: сроки действия СКЗИ",
                "Обнаружены записи требующие внимания:\n\n"
                + "\n".join(parts)
                + "\n\nПроверьте вкладку «Реестр СКЗИ» — "
                  "проблемные строки выделены цветом."
            )

    def _reapply_expiry_highlights(self):
        """
        Переприменяет подсветку истекающих сроков после сортировки.
        Вызывается по сигналу sortIndicatorChanged заголовка таблицы.
        """
        from PyQt6.QtCore import Qt as _Qt
        for i in range(self.reg_table.rowCount()):
            # Сбрасываем цвет строки
            for col in range(self.reg_table.columnCount()):
                item = self.reg_table.item(i, col)
                if item:
                    item.setBackground(QBrush())
                    item.setForeground(QBrush())
            # Применяем цвет заново по сроку
            expiry_item = self.reg_table.item(i, 12)  # «Срок до»
            if expiry_item:
                qdate = expiry_item.data(_Qt.ItemDataRole.UserRole)
                if qdate and qdate.isValid():
                    self._highlight_expiry_row(i, qdate)

    def setup_tray_icon(self):
        icon_path = find_icon_file()
        if icon_path and os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.tray_icon = SystemTrayIcon(icon, self)
            self.tray_icon.show()
            self.tray_icon.showMessage(
                "Учет СКЗИ",
                "Приложение свернуто в трей. Для выхода используйте меню.",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
        else:
            print("Иконка для трея не найдена, трей не будет создан.")

    def closeEvent(self, event):
        if self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Учет СКЗИ",
                "Приложение продолжает работу в фоновом режиме.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            event.accept()

    def init_menu(self):
        menubar = self.menuBar()

        ref_menu = menubar.addMenu("Справочники")
        ref_menu.addAction(QAction("🏢 Отделы", self, triggered=self.open_dept_form))
        ref_menu.addAction(QAction("👤 Сотрудники", self, triggered=self.open_emp_form))
        # Редактирование справочников — только для ADMIN
        if self.user.get('role') == UserRole.ADMIN:
            ref_menu.addSeparator()
            ref_menu.addAction(QAction(
                "📋 Редактировать справочники", self,
                triggered=self.open_dictionary_manager
            ))
        ref_menu.addSeparator()
        ref_menu.addAction(QAction("📥 Импорт сотрудников из Excel", self, triggered=self.import_from_excel))

        import_dict_menu = ref_menu.addMenu("📥 Импорт справочников")
        import_dict_menu.addAction(QAction("Наименования СКЗИ", self, triggered=self.import_skzi_names))
        import_dict_menu.addAction(QAction("Типы носителей", self, triggered=self.import_media_types))
        import_dict_menu.addAction(QAction("От кого получен", self, triggered=self.import_received_from))
        import_dict_menu.addAction(QAction("Типы АРМ", self, triggered=self.import_arm_types))
        import_dict_menu.addAction(QAction("Версии ОС", self, triggered=self.import_os_versions))
        import_dict_menu.addAction(QAction("Антивирусы", self, triggered=self.import_antiviruses))
        import_dict_menu.addAction(QAction("СЗИ от НСД", self, triggered=self.import_szi_nsd_names))
        import_dict_menu.addAction(QAction("Адреса установки", self, triggered=self.import_addresses))

        export_menu = menubar.addMenu("Экспорт")
        export_menu.addAction(QAction("📄 Акт установки СКЗИ", self, triggered=self.export_install_act))
        export_menu.addAction(QAction("📄 Акт установки ViPNet Client", self, triggered=self.export_vipnet_install_act))
        export_menu.addAction(QAction("🔥 Акт уничтожения СКЗИ", self, triggered=self.export_destruction_act))
        export_menu.addAction(QAction("🎓 Ведомость обучения", self, triggered=self.export_training_sheet))
        export_menu.addSeparator()
        export_menu.addAction(QAction("📁 Все сведения учета", self, triggered=self.export_full_data))
        export_menu.addSeparator()
        export_menu.addAction(QAction("📘 Журнал учета ЭП", self, triggered=self.export_ep_journal))
        export_menu.addAction(QAction("📗 Журнал учета СКЗИ", self, triggered=self.export_skzi_journal))
        export_menu.addAction(QAction("📙 Журнал установки СЗИ от НСД", self, triggered=self.export_szi_nsd_journal))
        export_menu.addAction(QAction("📕 Журнал учета ViPNet Client", self, triggered=self.export_vipnet_journal_excel))


        import_menu = menubar.addMenu("Импорт")
        import_menu.addAction(QAction("📘 Импорт журнала учета ЭП", self, triggered=self.import_ep_journal))
        import_menu.addAction(QAction("📗 Импорт журнала учета СКЗИ", self, triggered=self.import_skzi_journal))
        import_menu.addSeparator()
        import_menu.addAction(QAction("📄 Экспорт шаблона журнала учета ЭП", self, triggered=self.export_ep_template))
        import_menu.addAction(QAction("📄 Экспорт шаблона журнала учета СКЗИ", self, triggered=self.export_skzi_template))

        help_menu = menubar.addMenu("Справка")
        help_menu.addAction(QAction("📖 Содержание", self, triggered=self.show_help_tab))
        help_menu.addSeparator()
        help_menu.addAction(QAction("ℹ️ О программе", self, triggered=self.show_about_dialog))


        sys_menu = menubar.addMenu("Система")
        sys_menu.addAction(QAction("🔑 Сменить пароль", self, triggered=self.open_change_password))
        # Управление пользователями — только для ADMIN
        if self.user.get('role') == UserRole.ADMIN:
            sys_menu.addSeparator()
            sys_menu.addAction(QAction(
                "👥 Управление пользователями", self,
                triggered=self.open_user_management
            ))
        sys_menu.addSeparator()
        sys_menu.addAction(QAction("🚪 Выход", self, triggered=self.close))

        backup_menu = menubar.addMenu("Резервное копирование")
        backup_menu.addAction(QAction("💾 Создать резервную копию", self, triggered=self.backup_database))
        backup_menu.addAction(QAction("🔄 Восстановить из резервной копии", self, triggered=self.restore_database))

        # Ограничения для роли AUDITOR: только чтение
        if self._is_readonly():
            ref_menu.setEnabled(False)
            import_menu.setEnabled(False)
            backup_menu.setEnabled(False)



    def import_ep_journal(self):
        from utils.helpers import import_ep_journal as import_ep_journal_impl
        import_ep_journal_impl(self, self.dict_service, self.emp_service, self.arm_service, self.skzi_service)

    def import_skzi_journal(self):
        from utils.helpers import import_skzi_journal as import_skzi_journal_impl
        import_skzi_journal_impl(self, self.dict_service, self.emp_service, self.arm_service, self.skzi_service)

    def open_dictionary_manager(self):
        """Открывает экран управления справочниками (только ADMIN)."""
        if self.user.get('role') != UserRole.ADMIN:
            QMessageBox.warning(self, "Доступ закрыт",
                                "Редактирование справочников доступно только администратору.")
            return
        dlg = DictionaryManagerDialog(self.user, self)
        dlg.exec()

    def open_dictionary_manager(self):
        """Открывает экран управления справочниками (только ADMIN)."""
        from core.enums import UserRole
        if self.user.get('role') != UserRole.ADMIN:
            QMessageBox.warning(self, "Доступ закрыт",
                                "Управление справочниками доступно только администратору.")
            return
        dlg = DictionaryManagerDialog(self.user, self)
        dlg.exec()
        # Перезагружаем реестр — справочники могли измениться
        self.load_registry()

    def open_user_management(self):
        """Открывает экран управления пользователями (только ADMIN)."""
        if self.user.get('role') != UserRole.ADMIN:
            QMessageBox.warning(self, "Доступ закрыт",
                                "Управление пользователями доступно только администратору.")
            return
        dlg = UserManagementDialog(self.user, self)
        dlg.exec()

    def open_change_password(self):
        dlg = ChangePasswordDialog(username=self.user['username'], parent=self)
        dlg.exec()

    def init_toolbar(self):
        toolbar = self.addToolBar("Основные действия")
        toolbar.setMovable(False)
        refresh_action = QAction("🔄 Обновить данные", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.manual_refresh)
        toolbar.addAction(refresh_action)

    def manual_refresh(self):
        self.load_registry()
        self.load_audit()
        if hasattr(self, 'destruction_tab'):
            self.destruction_tab.refresh()
        if hasattr(self, 'training_tab'):
            self.training_tab.refresh()
        if hasattr(self, 'vipnet_tab'):
            self.vipnet_tab.refresh()
        if hasattr(self, 'szi_nsd_tab'):
            self.szi_nsd_tab.refresh()
        if self.emp_form and self.emp_form.isVisible():
            self.emp_form.load_employees()

    def on_employee_changed(self):
        self.load_registry()
        if self.emp_form and self.emp_form.isVisible():
            self.emp_form.load_employees()

    def init_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        self.tabs = QTabWidget()

        self.reg_tab = self.create_registry_tab()
        self.tabs.addTab(self.reg_tab, "Реестр СКЗИ")

        self.destruction_tab = DestructionTab(self.user, self)
        self.tabs.addTab(self.destruction_tab, "Уничтожение СКЗИ")

        self.training_tab = TrainingTab(self.user, self)
        self.tabs.addTab(self.training_tab, "Обучение")

        self.vipnet_tab = VipNetTab(self.user, self)
        self.tabs.addTab(self.vipnet_tab, "ViPNet Client")

        self.szi_nsd_tab = SziNsdTab(self.user, self)
        self.tabs.addTab(self.szi_nsd_tab, "СЗИ от НСД")

        self.audit_tab = self.create_audit_tab()
        self.tabs.addTab(self.audit_tab, "Аудит")

        self.help_tab = HelpTab()
        self.tabs.addTab(self.help_tab, "Справка")

        layout.addWidget(self.tabs)
        self.setCentralWidget(central)
        self.statusBar().showMessage("© Учет СКЗИ v.6.0 Все права защищены. (Колесов С.А.)")

    def create_registry_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Быстрый поиск
        self.reg_search = QLineEdit(placeholderText="🔍 Быстрый поиск по всем полям...")
        self.reg_search.textChanged.connect(self.filter_registry)
        layout.addWidget(self.reg_search)

        # Таблица с чекбоксом + 14 колонок (добавлен "Отдел" после "Сотрудник")
        self.reg_table = QTableWidget(0, 14)
        headers = [
            "", "ID", "Сотрудник", "Отдел", "Тип АРМ", "Серийный № АРМ", "СКЗИ", "Серийный №",
            "Тип носителя", "№ носителя ЭП", "Кабинет", "Дата установки", "Срок до", "Статус"
        ]
        self.reg_table.setHorizontalHeaderLabels(headers)
        self.reg_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.reg_table.setSortingEnabled(True)
        self.reg_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.reg_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        # Переприменяем подсветку сроков после сортировки пользователем
        self.reg_table.horizontalHeader().sortIndicatorChanged.connect(
            self._reapply_expiry_highlights
        )

        # Строка фильтров под заголовками
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(2)
        self.column_filters = []
        # Для каждого столбца создаём поле ввода или комбобокс
        for col, header in enumerate(headers):
            if col == 0:  # чекбоксы – без фильтра
                filter_edit = QLineEdit()
                filter_edit.setVisible(False)
                filter_layout.addWidget(filter_edit)
                self.column_filters.append(None)
            elif header == "Статус":
                filter_combo = QComboBox()
                filter_combo.addItem("Все")
                filter_combo.addItems([SkziStatus.ACTIVE, SkziStatus.DESTROYED])
                filter_combo.currentTextChanged.connect(self.apply_column_filters)
                filter_layout.addWidget(filter_combo)
                self.column_filters.append(filter_combo)
            elif header in ("Дата установки", "Срок до"):
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
        layout.addWidget(self.reg_table)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("✚ Зарегистрировать выдачу")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self.open_skzi_form)
        btn_layout.addWidget(btn_add)

        btn_edit = QPushButton("✏ Редактировать")
        btn_edit.clicked.connect(self.edit_selected_skzi)
        btn_layout.addWidget(btn_edit)

        btn_mass_destroy = QPushButton("🔥 Массовое уничтожение")
        btn_mass_destroy.clicked.connect(self.mass_destroy_selected)
        btn_layout.addWidget(btn_mass_destroy)

        # Для AUDITOR скрываем кнопки изменения данных
        if self._is_readonly():
            btn_add.setVisible(False)
            btn_edit.setVisible(False)
            btn_mass_destroy.setVisible(False)

        layout.addLayout(btn_layout)

        # ── Легенда подсветки ──
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)

        lbl_expired = QLabel("  🔴 Срок истёк  ")
        lbl_expired.setStyleSheet(
            f"background-color: rgb(255,200,200); color: rgb(120,40,40); "
            f"border: 1px solid #ccc; border-radius: 3px; padding: 2px 6px; font-size: 11px;"
        )

        lbl_expiring = QLabel(f"  🟡 Истекает ≤ {_EXPIRY_WARN_DAYS} дней  ")
        lbl_expiring.setStyleSheet(
            f"background-color: rgb(255,255,180); color: rgb(120,40,40); "
            f"border: 1px solid #ccc; border-radius: 3px; padding: 2px 6px; font-size: 11px;"
        )

        lbl_ok = QLabel("  ✅ Срок в норме  ")
        lbl_ok.setStyleSheet(
            "background-color: white; color: gray; "
            "border: 1px solid #ccc; border-radius: 3px; padding: 2px 6px; font-size: 11px;"
        )

        # Кнопка быстрого фильтра — только истекающие
        self.btn_filter_expiring = QPushButton("⚠ Показать истекающие")
        self.btn_filter_expiring.setCheckable(True)
        self.btn_filter_expiring.setToolTip(
            "Показать только записи с истёкшим сроком "
            f"или истекающим в течение {_EXPIRY_WARN_DAYS} дней"
        )
        self.btn_filter_expiring.toggled.connect(self._toggle_expiry_filter)

        legend_layout.addWidget(lbl_expired)
        legend_layout.addWidget(lbl_expiring)
        legend_layout.addWidget(lbl_ok)
        legend_layout.addStretch()
        legend_layout.addWidget(self.btn_filter_expiring)
        layout.addLayout(legend_layout)

        return tab

    def _toggle_expiry_filter(self, checked: bool):
        """
        Быстрый фильтр: показывает только строки с истёкшим или
        истекающим (≤ _EXPIRY_WARN_DAYS дней) сроком действия СКЗИ.
        При повторном нажатии — снимает фильтр.
        """
        from PyQt6.QtCore import Qt as _Qt
        today = QDate.currentDate()

        if not checked:
            # Снимаем фильтр — показываем все строки (apply_column_filters восстановит)
            self.apply_column_filters()
            self.filter_registry()
            return

        # Скрываем строки где срок в норме
        for i in range(self.reg_table.rowCount()):
            expiry_item = self.reg_table.item(i, 12)  # «Срок до»
            show_row = False
            if expiry_item:
                qdate = expiry_item.data(_Qt.ItemDataRole.UserRole)
                if qdate and qdate.isValid():
                    days_left = today.daysTo(qdate)
                    show_row = days_left <= _EXPIRY_WARN_DAYS  # < 0 истёк, 0..30 истекает
            self.reg_table.setRowHidden(i, not show_row)

    def create_audit_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.audit_table = QTableWidget(0, 5)
        self.audit_table.setHorizontalHeaderLabels(["Время", "Тип", "Таблица", "Кто", "Описание"])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.audit_table)
        return tab

    def load_registry(self):
        rows = self.skzi_service.get_all_active()
        self.reg_table.setSortingEnabled(False)
        self.reg_table.setRowCount(0)

        # Собираем уникальные значения для столбцов с датами
        install_dates = set()
        expiry_dates = set()

        headers = ["", "ID", "Сотрудник", "Отдел", "Тип АРМ", "Серийный № АРМ", "СКЗИ", "Серийный №",
                   "Тип носителя", "№ носителя ЭП", "Кабинет", "Дата установки", "Срок до", "Статус"]

        for i, row in enumerate(rows):
            self.reg_table.insertRow(i)
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Unchecked)
            self.reg_table.setItem(i, 0, chk)

            self.reg_table.setItem(i, 1, QTableWidgetItem(str(row['id'])))
            self.reg_table.setItem(i, 2, QTableWidgetItem(row['fio']))
            self.reg_table.setItem(i, 3, QTableWidgetItem(row['department'] or ""))
            self.reg_table.setItem(i, 4, QTableWidgetItem(row['arm_type'] or ""))
            self.reg_table.setItem(i, 5, QTableWidgetItem(row['arm_serial'] or ""))
            self.reg_table.setItem(i, 6, QTableWidgetItem(row['skzi_name']))
            self.reg_table.setItem(i, 7, QTableWidgetItem(row['skzi_number']))
            self.reg_table.setItem(i, 8, QTableWidgetItem(row['media_type'] or ""))
            self.reg_table.setItem(i, 9, QTableWidgetItem(row['media_number'] or ""))
            self.reg_table.setItem(i, 10, QTableWidgetItem(row['cabinet_number'] or ""))

            install_date = row['install_date']
            display_install = ""
            qdate_install = QDate()
            if install_date:
                try:
                    qdate_install = QDate.fromString(install_date, "yyyy-MM-dd")
                    display_install = qdate_install.toString("dd.MM.yyyy")
                except Exception:
                    display_install = install_date
            item_install = DateTableWidgetItem(display_install, qdate_install)
            self.reg_table.setItem(i, 11, item_install)
            if display_install:
                install_dates.add(display_install)

            expiry_date = row['expiry_date']
            display_expiry = ""
            qdate_expiry = QDate()
            if expiry_date:
                try:
                    qdate_expiry = QDate.fromString(expiry_date, "yyyy-MM-dd")
                    display_expiry = qdate_expiry.toString("dd.MM.yyyy")
                except Exception:
                    display_expiry = expiry_date
            item_expiry = DateTableWidgetItem(display_expiry, qdate_expiry)
            self.reg_table.setItem(i, 12, item_expiry)
            if display_expiry:
                expiry_dates.add(display_expiry)

            self.reg_table.setItem(i, 13, QTableWidgetItem(row['status']))

            # Подсветка строк с истекающим/истёкшим сроком
            self._highlight_expiry_row(i, qdate_expiry)

        self.reg_table.setSortingEnabled(True)

        # Обновляем выпадающие списки для дат
        for col, header in enumerate(headers):
            if header == "Дата установки":
                combo = self.column_filters[col]
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
            elif header == "Срок до":
                combo = self.column_filters[col]
                current = combo.currentText()
                combo.blockSignals(True)
                combo.clear()
                combo.addItem("Все")
                for val in sorted(expiry_dates):
                    combo.addItem(val)
                idx = combo.findText(current)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                combo.blockSignals(False)

        self.apply_column_filters()
        self.filter_registry()  # быстрый поиск
        self.reg_table.resizeColumnsToContents()
        header_widget = self.reg_table.horizontalHeader()
        header_widget.setStretchLastSection(True)
        self.reg_table.viewport().update()
        app_logger.debug("Таблица реестра обновлена")

    def apply_column_filters(self):
        """Применяет фильтры по каждому столбцу (кроме чекбокса)."""
        for row in range(self.reg_table.rowCount()):
            visible = True
            for col, filter_widget in enumerate(self.column_filters):
                if col == 0 or filter_widget is None:
                    continue
                item = self.reg_table.item(row, col)
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
            self.reg_table.setRowHidden(row, not visible)

    def get_selected_skzi_ids(self):
        ids = []
        for i in range(self.reg_table.rowCount()):
            chk = self.reg_table.item(i, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked:
                id_item = self.reg_table.item(i, 1)
                if id_item:
                    ids.append(int(id_item.text()))
        return ids

    def edit_selected_skzi(self):
        ids = self.get_selected_skzi_ids()
        if len(ids) == 0:
            QMessageBox.warning(self, "Внимание", "Не выбрано ни одной записи.")
            return
        if len(ids) > 1:
            QMessageBox.warning(self, "Внимание", "Выберите только одну запись для редактирования.")
            return
        dlg = SkziForm(self.user, self, record_id=ids[0])
        if dlg.exec():
            self.load_registry()

    def mass_destroy_selected(self):
        ids = self.get_selected_skzi_ids()
        if not ids:
            QMessageBox.warning(self, "Внимание", "Не выбрано ни одной записи.")
            return
        dlg = MassDestructionDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if not data['act']:
                QMessageBox.warning(self, "Ошибка", "Введите номер акта.")
                return
            if not data['withdrawer']:
                data['withdrawer'] = self.user['username']
            reply = QMessageBox.question(self, "Подтверждение",
                                         f"Вы действительно хотите уничтожить {len(ids)} записей?\nАкт №{data['act']} от {data['date']}",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.skzi_service.mass_mark_destroyed(ids, data['date'], data['act'], data['withdrawer'], self.user['username'])
                QMessageBox.information(self, "Успех", f"{len(ids)} записей помечены как уничтоженные.")
                self.load_registry()

    def filter_registry(self):
        text = self.reg_search.text().lower()
        for i in range(self.reg_table.rowCount()):
            if self.reg_table.isRowHidden(i):  # уже скрыто столбцовыми фильтрами
                continue
            match = False
            for j in range(1, self.reg_table.columnCount()):  # пропускаем чекбокс
                item = self.reg_table.item(i, j)
                if item and text in item.text().lower():
                    match = True
                    break
            self.reg_table.setRowHidden(i, not match)

    def backup_database(self):
        from utils.backup import backup_db
        dlg = BackupDialog(mode='backup', parent=self)
        if dlg.exec():
            data = dlg.get_data()
            if not data['path']:
                return
            try:
                backup_db(data['path'], data['password'])
                QMessageBox.information(self, "Успех", "Резервная копия создана.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def restore_database(self):
        from utils.backup import restore_db
        dlg = BackupDialog(mode='restore', parent=self)
        if dlg.exec():
            data = dlg.get_data()
            if not data['path']:
                return
            reply = QMessageBox.question(self, "Подтверждение",
                                         "Восстановление закроет приложение. Продолжить?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    restore_db(data['path'], data['password'])
                    QMessageBox.information(self, "Успех", "База восстановлена. Приложение будет закрыто.")
                    QTimer.singleShot(2000, QApplication.quit)
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", str(e))

    def load_audit(self):
        rows = self.audit_service.get_recent(100)
        self.audit_table.setRowCount(0)
        for i, row in enumerate(rows):
            self.audit_table.insertRow(i)
            self.audit_table.setItem(i, 0, QTableWidgetItem(row['action_time']))
            self.audit_table.setItem(i, 1, QTableWidgetItem(row['action_type']))
            self.audit_table.setItem(i, 2, QTableWidgetItem(row['table_name']))
            self.audit_table.setItem(i, 3, QTableWidgetItem(row['performed_by']))
            desc = row['new_value']
            if row['old_value']:
                desc += f" (было: {row['old_value']})"
            if row['changed_fields']:
                desc += f" | изменено: {row['changed_fields']}"
            self.audit_table.setItem(i, 4, QTableWidgetItem(desc))

    def import_from_excel(self):
        import_employees_from_excel(self)

    def import_skzi_names(self):
        import_skzi_names(self, self.dict_service)

    def import_media_types(self):
        import_media_types(self, self.dict_service)

    def import_received_from(self):
        import_received_from(self, self.dict_service)

    def import_arm_types(self):
        import_arm_types(self, self.dict_service)

    def import_os_versions(self):
        import_os_versions(self, self.dict_service)

    def import_antiviruses(self):
        import_antiviruses(self, self.dict_service)

    def import_szi_nsd_names(self):
        import_szi_nsd_names(self, self.dict_service)

    def import_addresses(self):
        import_addresses(self, self.dict_service)

    def export_install_act(self):
        self.show_date_range_dialog("Акт установки СКЗИ", self.exporter.export_install_act, "Акт_установки_СКЗИ.xlsx")

    def export_destruction_act(self):
        self.show_date_range_dialog("Акт уничтожения СКЗИ", self.exporter.export_destruction_act, "Акт_уничтожения_СКЗИ.xlsx")

    def export_training_sheet(self):
        self.show_date_range_dialog("Ведомость обучения", self.exporter.export_training_sheet, "Ведомость_обучения.xlsx")

    def export_full_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить все сведения", "Полный_учет.xlsx", "Excel (*.xlsx)")
        if path:
            try:
                self.exporter.export_full_data(path)
                QMessageBox.information(self, "Успех", "Данные экспортированы")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def export_ep_journal(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить журнал учета ЭП", "Журнал учета ЭП.xlsx", "Excel (*.xlsx)")
        if path:
            try:
                self.exporter.export_ep_journal(path)
                QMessageBox.information(self, "Успех", "Журнал учета ЭП экспортирован")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def export_skzi_journal(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить журнал учета СКЗИ", "Журнал учета СКЗИ.xlsx", "Excel (*.xlsx)")
        if path:
            try:
                self.exporter.export_skzi_journal(path)
                QMessageBox.information(self, "Успех", "Журнал учета СКЗИ экспортирован")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def export_szi_nsd_journal(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить журнал установки СЗИ от НСД", "Журнал_установки_СЗИ_от_НСД.xlsx", "Excel (*.xlsx)")
        if path:
            try:
                self.exporter.export_szi_nsd_journal(path)
                QMessageBox.information(self, "Успех", "Журнал установки СЗИ от НСД экспортирован")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def export_vipnet_journal_excel(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить журнал учета ViPNet Client",
            "Журнал_ViPNet_Client.xlsx", "Excel (*.xlsx)"
        )
        if path:
            try:
                self.exporter.export_vipnet_journal(path)
                QMessageBox.information(self, "Успех", "Журнал учета ViPNet Client экспортирован")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def export_ep_template(self):
        from utils.helpers import export_template_ep_journal
        export_template_ep_journal(self)

    def export_skzi_template(self):
        from utils.helpers import export_template_skzi_journal
        export_template_skzi_journal(self)

    def export_vipnet_install_act(self):
        self.show_date_range_dialog("Акт установки ViPNet Client", self.exporter.export_vipnet_install_act,
                                    "Акт_установки_ViPNet.xlsx")


    def show_date_range_dialog(self, title, export_func, default_filename="отчет.xlsx"):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)

        export_all_checkbox = QCheckBox("Экспортировать все записи (без фильтра по датам)")
        export_all_checkbox.setChecked(False)
        layout.addWidget(export_all_checkbox)

        date_frame = QFrame()
        date_layout = QVBoxLayout(date_frame)
        date_layout.addWidget(QLabel("Начальная дата:"))
        start_date = QDateEdit(calendarPopup=True)
        start_date.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(start_date)

        date_layout.addWidget(QLabel("Конечная дата:"))
        end_date = QDateEdit(calendarPopup=True)
        end_date.setDate(QDate.currentDate())
        date_layout.addWidget(end_date)
        layout.addWidget(date_frame)

        def on_export_all_changed(checked):
            start_date.setEnabled(not checked)
            end_date.setEnabled(not checked)

        export_all_checkbox.toggled.connect(on_export_all_changed)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Экспорт")
        btn_ok.clicked.connect(lambda: self.do_export(
            dialog, export_all_checkbox, start_date, end_date, export_func, default_filename
        ))
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        dialog.exec()

    def do_export(self, dialog, export_all_checkbox, start_date_widget, end_date_widget, export_func, default_filename):
        if export_all_checkbox.isChecked():
            start = None
            end = None
        else:
            start = start_date_widget.date().toString("yyyy-MM-dd")
            end = end_date_widget.date().toString("yyyy-MM-dd")

        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", default_filename, "Excel (*.xlsx)")
        if path:
            try:
                export_func(start, end, path)
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def show_help_tab(self):
        if hasattr(self, 'tabs') and hasattr(self, 'help_tab'):
            self.tabs.setCurrentWidget(self.help_tab)

    def show_about_dialog(self):
        about_text = """
        <h2>Учет СКЗИ</h2>
        <p><b>Версия:</b> 5.0</p>
        <p><b>Назначение:</b> Автоматизированная система учета средств криптографической защиты информации (СКЗИ).</p>
        <p><b>Разработчик:</b> Колесов С.А.</p>
        <p><b>Год выпуска:</b> 2026</p>
        <p><b>Все права защищены.</b></p>
        <p>Данное программное обеспечение предназначено для ведения реестра СКЗИ, контроля выдачи и уничтожения, обучения сотрудников и формирования отчетной документации.</p>
        <p>По всем вопросам обращаться: kolesov@example.com</p>
        <p>© 2026 Учет СКЗИ</p>
        """
        QMessageBox.about(self, "О программе", about_text)

    def open_skzi_form(self):
        dlg = SkziForm(self.user, self)
        if dlg.exec():
            print("Диалог СКЗИ завершён, данные обновятся по сигналу")

    def open_dept_form(self):
        dlg = DepartmentForm(self)
        if dlg.exec():
            print("Диалог отдела завершён, данные обновятся по сигналу")

    def open_emp_form(self):
        self.emp_form = EmployeeForm(self)
        self.emp_form.show()