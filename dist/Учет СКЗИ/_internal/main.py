import sys
import os
import ctypes
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt6.QtGui import QIcon
from login_window import LoginWindow
from database_init import create_database
from utils.path_helper import get_app_root, get_db_path
from db.db_manager import DatabaseManager
from forms.first_run_dialog import FirstRunDialog

MODERN_STYLE = """
QMainWindow, QDialog { 
    background-color: #f5f7fa; 
    font-family: 'Segoe UI', sans-serif; 
}
QTabWidget::pane { 
    border: 1px solid #cfd8dc; 
    background: white; 
    border-radius: 5px; 
}
QTabBar::tab { 
    background: #e0e0e0; 
    padding: 10px 20px; 
    border-top-left-radius: 4px; 
    border-top-right-radius: 4px; 
    margin-right: 2px; 
}
QTabBar::tab:selected { 
    background: white; 
    font-weight: bold; 
}
QTableWidget { 
    background-color: white; 
    gridline-color: #eceff1; 
    border: 1px solid #cfd8dc; 
    selection-background-color: #e3f2fd; 
}
QPushButton { 
    padding: 8px 15px; 
    border-radius: 4px; 
    border: 1px solid #bdc3c7; 
    background: white; 
}
QPushButton:hover { 
    background: #f8f9fa; 
    border-color: #95a5a6; 
}
QPushButton#primaryButton { 
    background: #2ecc71; 
    color: white; 
    border: none; 
    font-weight: bold; 
    font-size: 14px; 
}
QPushButton#primaryButton:hover { 
    background: #27ae60; 
}
QLineEdit, QComboBox { 
    padding: 6px; 
    border: 1px solid #cfd8dc; 
    border-radius: 4px; 
    background: white; 
}
QHeaderView::section { 
    background-color: #f5f5f5; 
    padding: 5px; 
    border: 1px solid #cfd8dc; 
    font-weight: bold; 
}
"""

def get_icon_path():
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

def global_exception_handler(exctype, value, tb):
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    print("НЕПЕРЕХВАЧЕННОЕ ИСКЛЮЧЕНИЕ:", error_msg)
    try:
        QMessageBox.critical(None, "Критическая ошибка",
                             f"Произошла непредвиденная ошибка:\n{str(value)}\n\nПодробности в консоли.")
    except:
        pass
    sys.exit(1)

def main():
    sys.excepthook = global_exception_handler

    # Принудительное создание базы данных при каждом запуске (безопасно)
    try:
        print("Инициализация базы данных...")
        create_database()
        print("База данных готова.")
    except Exception as e:
        print(f"Ошибка при инициализации БД: {e}")
        traceback.print_exc()
        try:
            QMessageBox.critical(None, "Ошибка БД", f"Не удалось инициализировать базу данных:\n{e}\n\nПриложение может работать некорректно.")
        except:
            pass
        sys.exit(1)

    app = QApplication(sys.argv)

    try:
        myappid = 'kolesov.skzi.registry.v6.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    icon_path = get_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    app.setStyleSheet(MODERN_STYLE)
    app.setQuitOnLastWindowClosed(True)

    # Проверка наличия пользователей
    db_manager = DatabaseManager()
    cursor = db_manager.execute_query("SELECT COUNT(*) as cnt FROM users")
    row = cursor.fetchone()
    has_users = row and row['cnt'] > 0

    if not has_users:
        # Первый запуск – создаём администратора
        first_run = FirstRunDialog()
        if first_run.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)  # Пользователь закрыл окно – выходим

    # Запуск окна авторизации
    login = LoginWindow()
    if icon_path:
        login.setWindowIcon(QIcon(icon_path))
    login.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()