# utils/backup.py

import os
import zipfile
from utils.path_helper import get_db_path

# Имя файла БД внутри архива — константа, чтобы не опечататься в двух местах
_DB_ARCNAME = 'skzi_registry.db'


def backup_db(target_path, password=None):
    """
    Создаёт резервную копию БД в ZIP-архиве.

    password: параметр зарезервирован для будущей реализации шифрования.
    Сейчас архив создаётся без шифрования — пароль игнорируется.
    Если передан пароль, функция выбрасывает NotImplementedError,
    чтобы пользователь не думал, что шифрование уже работает.
    """
    if password:
        raise NotImplementedError(
            "Шифрование резервной копии пока не реализовано.\n"
            "Создайте копию без пароля или используйте внешний архиватор."
        )

    db_path = get_db_path()
    if not os.path.exists(db_path):
        raise FileNotFoundError("База данных не найдена по пути: " + db_path)

    # Создаём директорию для копии, если её нет
    target_dir = os.path.dirname(target_path)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)

    with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, arcname=_DB_ARCNAME)

    # Проверяем, что архив создан и не пустой
    if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
        raise RuntimeError("Резервная копия создана, но файл пустой. Проверьте диск.")


def restore_db(backup_path, password=None):
    """
    Восстанавливает БД из резервной копии.

    ВАЖНО: после восстановления приложение должно быть перезапущено
    (или синглтон DatabaseManager пересоздан). Функция сбрасывает
    синглтон, чтобы следующий вызов DatabaseManager() открыл новое
    соединение к восстановленному файлу.
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError("Файл резервной копии не найден: " + backup_path)

    # --- Проверяем целостность ZIP до начала операции ---
    try:
        with zipfile.ZipFile(backup_path, 'r') as zf:
            bad = zf.testzip()
            if bad is not None:
                raise zipfile.BadZipFile(f"Повреждённый файл в архиве: {bad}")
            # Проверяем, что нужный файл вообще есть в архиве
            names = zf.namelist()
            if _DB_ARCNAME not in names:
                raise KeyError(
                    f"В архиве не найден файл '{_DB_ARCNAME}'.\n"
                    f"Содержимое архива: {names}"
                )
    except zipfile.BadZipFile as e:
        raise RuntimeError(f"Архив повреждён или не является ZIP-файлом.\nДетали: {e}")

    db_path = get_db_path()

    # --- Закрываем текущее соединение и сбрасываем синглтон ---
    from db.db_manager import DatabaseManager
    instance = DatabaseManager._instance
    if instance is not None:
        try:
            instance.conn.close()
        except Exception:
            pass  # соединение могло быть уже закрыто
        # Сбрасываем синглтон — следующий DatabaseManager() создаст новое соединение
        DatabaseManager._instance = None

    # --- Извлекаем файл БД из архива ---
    db_dir = os.path.dirname(db_path)
    with zipfile.ZipFile(backup_path, 'r') as zf:
        zf.extract(_DB_ARCNAME, path=db_dir)

    # Если extract положил файл в подпапку — перемещаем в нужное место
    extracted = os.path.join(db_dir, _DB_ARCNAME)
    if os.path.abspath(extracted) != os.path.abspath(db_path):
        os.replace(extracted, db_path)

    # Финальная проверка: файл существует и не пустой
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        raise RuntimeError(
            "Восстановление завершено, но файл БД отсутствует или пустой. "
            "Проверьте права доступа к папке базы данных."
        )