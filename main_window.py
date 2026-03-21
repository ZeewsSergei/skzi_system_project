import os
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QDate, Qt, QTimer
from db.db_manager import DatabaseManager
from services.employee_service import EmployeeService
from services.skzi_service import SkziService
from services.audit_service import AuditService
from services.dictionary_service import DictionaryService
from forms.mass_destruction_dialog import MassDestructionDialog
from forms.filter_dialog import FilterDialog
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
        self.filter_btn = None
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
        self.emp_form = None
        self.tray_icon = None
        self.current_filters = None
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
        export_menu.addAction(QAction("🔥 Акт уничтожения СКЗИ", self, triggered=self.export_destruction_act))
        export_menu.addAction(QAction("🎓 Ведомость обучения", self, triggered=self.export_training_sheet))
        export_menu.addSeparator()
        export_menu.addAction(QAction("📁 Все сведения учета", self, triggered=self.export_full_data))

        help_menu = menubar.addMenu("Справка")
        help_menu.addAction(QAction("📖 Содержание", self, triggered=self.show_help_tab))
        help_menu.addSeparator()
        help_menu.addAction(QAction("ℹ️ О программе", self, triggered=self.show_about_dialog))

        sys_menu = menubar.addMenu("Система")
        sys_menu.addAction(QAction("🔑 Сменить пароль", self, triggered=self.open_change_password))
        sys_menu.addSeparator()
        sys_menu.addAction(QAction("🚪 Выход", self, triggered=self.close))

        backup_menu = menubar.addMenu("Резервное копирование")
        backup_menu.addAction(QAction("💾 Создать резервную копию", self, triggered=self.backup_database))
        backup_menu.addAction(QAction("🔄 Восстановить из резервной копии", self, triggered=self.restore_database))

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
        self.statusBar().showMessage("© Учет СКЗИ v.4.1 Все права защищены. (Колесов С.А.)")

    def create_registry_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        toolbar = QHBoxLayout()
        self.reg_search = QLineEdit(placeholderText="🔍 Быстрый поиск...")
        self.reg_search.textChanged.connect(self.filter_registry)
        toolbar.addWidget(self.reg_search)

        self.filter_btn = QPushButton("🔍 Расширенный фильтр")
        self.filter_btn.clicked.connect(self.open_filter_dialog)
        toolbar.addWidget(self.filter_btn)
        layout.addLayout(toolbar)

        # Таблица с чекбоксом + 12 колонок = 13 колонок
        self.reg_table = QTableWidget(0, 13)
        self.reg_table.setHorizontalHeaderLabels(
            ["", "ID", "Сотрудник", "Тип АРМ", "Серийный № АРМ", "СКЗИ", "Серийный №",
             "Тип носителя", "№ носителя ЭП", "Кабинет", "Дата установки", "Срок до", "Статус"]
        )
        self.reg_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.reg_table.setSortingEnabled(True)
        self.reg_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.reg_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
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

        layout.addLayout(btn_layout)

        return tab

    def create_audit_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.audit_table = QTableWidget(0, 5)
        self.audit_table.setHorizontalHeaderLabels(["Время", "Тип", "Таблица", "Кто", "Описание"])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.audit_table)
        return tab

    def load_registry(self, filters=None):
        print("MainWindow.load_registry() вызван")
        if filters is None:
            rows = self.skzi_service.get_all_active()
        else:
            rows = self.skzi_service.get_all_active_filtered(filters)

        self.reg_table.setSortingEnabled(False)
        self.reg_table.setRowCount(0)

        for i, row in enumerate(rows):
            self.reg_table.insertRow(i)
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Unchecked)
            self.reg_table.setItem(i, 0, chk)

            self.reg_table.setItem(i, 1, QTableWidgetItem(str(row['id'])))
            self.reg_table.setItem(i, 2, QTableWidgetItem(row['fio']))
            self.reg_table.setItem(i, 3, QTableWidgetItem(row['arm_type'] or ""))
            self.reg_table.setItem(i, 4, QTableWidgetItem(row['arm_serial'] or ""))
            self.reg_table.setItem(i, 5, QTableWidgetItem(row['skzi_name']))
            self.reg_table.setItem(i, 6, QTableWidgetItem(row['skzi_number']))
            self.reg_table.setItem(i, 7, QTableWidgetItem(row['media_type'] or ""))
            self.reg_table.setItem(i, 8, QTableWidgetItem(row['media_number'] or ""))
            self.reg_table.setItem(i, 9, QTableWidgetItem(row['cabinet_number'] or ""))
            self.reg_table.setItem(i, 10, QTableWidgetItem(row['install_date'] or ""))
            self.reg_table.setItem(i, 11, QTableWidgetItem(row['expiry_date'] or ""))
            self.reg_table.setItem(i, 12, QTableWidgetItem(row['status']))

        self.reg_table.setSortingEnabled(True)

        # Автоматическая подстройка ширины столбцов под содержимое
        self.reg_table.resizeColumnsToContents()
        # Устанавливаем, чтобы последний столбец занимал оставшееся пространство
        header = self.reg_table.horizontalHeader()
        header.setStretchLastSection(True)

        self.filter_registry()
        self.reg_table.viewport().update()
        print("Таблица реестра обновлена")

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

    def open_filter_dialog(self):
        dlg = FilterDialog(self, initial_filters=self.current_filters)
        if dlg.exec():
            self.current_filters = dlg.get_filters()
            self.load_registry(self.current_filters)

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

    def filter_registry(self):
        text = self.reg_search.text().lower()
        for i in range(self.reg_table.rowCount()):
            match = False
            for j in range(self.reg_table.columnCount()):
                item = self.reg_table.item(i, j)
                if item and text in item.text().lower():
                    match = True
                    break
            self.reg_table.setRowHidden(i, not match)

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

    def show_date_range_dialog(self, title, export_func, default_filename="отчет.xlsx"):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Начальная дата:"))
        start_date = QDateEdit(calendarPopup=True)
        start_date.setDate(QDate.currentDate().addMonths(-1))
        layout.addWidget(start_date)

        layout.addWidget(QLabel("Конечная дата:"))
        end_date = QDateEdit(calendarPopup=True)
        end_date.setDate(QDate.currentDate())
        layout.addWidget(end_date)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Экспорт")
        btn_ok.clicked.connect(lambda: self.do_export(dialog, start_date.date(), end_date.date(), export_func, default_filename))
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        dialog.exec()

    def do_export(self, dialog, start, end, export_func, default_filename):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", default_filename, "Excel (*.xlsx)")
        if path:
            try:
                export_func(start.toString("dd.MM.yyyy"), end.toString("dd.MM.yyyy"), path)
                QMessageBox.information(self, "Успех", "Отчёт успешно сохранён!")
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def show_help_tab(self):
        self.tabs.setCurrentWidget(self.help_tab)

    def show_about_dialog(self):
        about_text = """
        <h2>Учет СКЗИ</h2>
        <p><b>Версия:</b> 4.1</p>
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