from repositories.department_repository import DepartmentRepository
from logger import app_logger
from signals.app_signals import app_signals  # добавлен импорт сигналов

class DepartmentService:
    def __init__(self):
        self.repo = DepartmentRepository()

    def get_all_departments(self):
        return self.repo.get_all()

    def get_by_id(self, dept_id):
        return self.repo.get_by_id(dept_id)

    def get_by_name(self, name):
        return self.repo.get_by_name(name)

    def add_department(self, name, username=None):
        """
        Добавляет отдел, если его ещё нет, и возвращает ID.
        При создании нового отдела отправляет сигнал department_changed.
        """
        if not name or not name.strip():
            raise ValueError("Название отдела не может быть пустым")
        name = name.strip()
        existing = self.get_by_name(name)
        if existing:
            return existing['id']
        dept_id = self.repo.add(name)
        if username:
            app_logger.info(f"Пользователь {username} добавил отдел: {name}")
        # Уведомляем приложение об изменении списка отделов
        app_signals.department_changed.emit()
        return dept_id

    def get_or_create_department(self, name, username=None):
        """
        Безопасно возвращает ID отдела, создавая его при необходимости.
        """
        if not name or not name.strip():
            return None
        name = name.strip()
        existing = self.get_by_name(name)
        if existing:
            return existing['id']
        return self.add_department(name, username)