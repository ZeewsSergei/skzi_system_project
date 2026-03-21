from repositories.employee_repository import EmployeeRepository
from services.audit_service import AuditService
from signals.app_signals import app_signals

class EmployeeService:
    def __init__(self):
        self.repo = EmployeeRepository()
        self.audit = AuditService()

    def get_all_employees(self):
        return self.repo.get_all()

    def get_by_fio(self, fio):
        return self.repo.get_by_fio(fio)

    def add_employee(self, fio, position, sector_id, department_id, knowledge_check, username):
        emp_id = self.repo.add(fio, position, sector_id, department_id, knowledge_check)
        self.audit.log("CREATE", "employees", emp_id, username,
                       new_value=f"Сотрудник: {fio}, должность: {position}")
        app_signals.employee_changed.emit()
        return emp_id

    def update_employee(self, emp_id, fio, position, sector_id, department_id, knowledge_check, username):
        old = self.repo.get_by_id(emp_id)
        old_data = dict(old) if old else {}
        self.repo.update(emp_id, fio, position, sector_id, department_id, knowledge_check)
        new_data = {'fio': fio, 'position': position, 'sector_id': sector_id,
                    'department_id': department_id, 'knowledge_check': knowledge_check}
        changed = {k: (old_data.get(k), new_data[k]) for k in new_data if old_data.get(k) != new_data[k]}
        self.audit.log("UPDATE", "employees", emp_id, username,
                       new_value=str(new_data),
                       old_value=str(old_data) if old_data else None,
                       changed_fields=str(changed))
        app_signals.employee_changed.emit()