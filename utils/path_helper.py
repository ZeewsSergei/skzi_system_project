import os
import sys

def get_app_root():
    """
    Возвращает корень приложения.
    Работает и в PyCharm, и после сборки PyInstaller.
    """
    if getattr(sys, "frozen", False):
        # если программа собрана
        return os.path.dirname(sys.executable)
    # обычный запуск из проекта
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_db_path():
    """
    Путь к файлу базы данных
    """
    root = get_app_root()
    db_dir = os.path.join(root, "database")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "skzi_registry.db")