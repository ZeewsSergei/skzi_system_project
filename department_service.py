from repositories.department_repository import DepartmentRepository
from services.audit_service import AuditService
from signals.app_signals import app_signals

class DepartmentService:
    def __init__(self):
        self.repo = DepartmentRepository()
        self.audit = AuditService()

    def get_all_departments(self):
        return self.repo.get_all()

    def add_department(self, name, username):
        dept_id = self.repo.add(name)
        self.audit.log("CREATE", "departments", dept_id, username,
                       f"Отдел: {name}")
        app_signals.department_changed.emit()
        return dept_id