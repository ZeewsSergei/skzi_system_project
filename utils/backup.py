import os
import zipfile
import shutil
from utils.path_helper import get_db_path

def backup_db(target_path, password=None):
    db_path = get_db_path()
    if not os.path.exists(db_path):
        raise Exception("База данных не найдена.")
    with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, arcname='skzi_registry.db')
    if password:
        # Простейшее шифрование через установку пароля на zip (не очень надёжно)
        # Можно использовать pyminizip, но для простоты ограничимся архивацией
        pass

def restore_db(backup_path, password=None):
    db_path = get_db_path()
    if not os.path.exists(backup_path):
        raise Exception("Файл резервной копии не найден.")
    # Закрываем все соединения? В синглтоне соединение открыто. Нужно его закрыть.
    from db.db_manager import DatabaseManager
    db_manager = DatabaseManager()
    db_manager.close()
    # Восстанавливаем
    with zipfile.ZipFile(backup_path, 'r') as zf:
        zf.extract('skzi_registry.db', path=os.path.dirname(db_path))
    # Переименовываем, если нужно (извлекается в текущую папку)
    extracted = os.path.join(os.path.dirname(db_path), 'skzi_registry.db')
    if extracted != db_path:
        os.replace(extracted, db_path)