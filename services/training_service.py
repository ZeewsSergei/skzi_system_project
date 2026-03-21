from repositories.training_repository import TrainingRepository
from services.audit_service import AuditService
from services.employee_service import EmployeeService
from signals.app_signals import app_signals

class TrainingService:
    def __init__(self):
        self.repo = TrainingRepository()
        self.audit = AuditService()

    def get_all_trainings(self):
        rows = self.repo.get_all()
        return rows

    def register_training(self, employee_id, training_date, result, position, department, username):
        record_id = self.repo.add(employee_id, training_date, result, position, department)
        self.audit.log("TRAINING", "training_logs", record_id, username,
                       f"Сотрудник ID {employee_id}, результат: {result}, отдел: {department}")
        # Обновляем поле knowledge_check у сотрудника
        emp_service = EmployeeService()
        emp = emp_service.repo.get_by_id(employee_id)
        if emp:
            # Передаём sector_id (четвёртый параметр) и department_id (пятый)
            emp_service.update_employee(
                employee_id,
                emp['fio'],
                emp['position'],
                emp['sector_id'],
                emp['department_id'],
                result,
                username
            )
        app_signals.training_changed.emit()
        app_signals.employee_changed.emit()