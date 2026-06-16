# services/control_service.py

from repositories.control_repository import ControlRepository
from services.audit_service import AuditService
from signals.app_signals import app_signals


class ControlService:
    def __init__(self):
        self.repo = ControlRepository()
        self.audit = AuditService()

    def get_all_controls(self):
        """Вернуть все контрольные проверки."""
        return self.repo.get_all()

    def register_control(self, skzi_id, check_date, conditions_met, inspector,
                         notes="", username="system"):
        """Зарегистрировать контрольную проверку с аудитом."""
        record_id = self.repo.add(skzi_id, check_date, conditions_met, inspector, notes)
        self.audit.log(
            "CREATE", "control_checks", record_id, username,
            f"СКЗИ ID {skzi_id}, дата {check_date}, результат: {conditions_met}, "
            f"проверяющий: {inspector}"
        )
        app_signals.control_changed.emit()
        return record_id

    def remove_control(self, control_id, username="system"):
        """Удалить контрольную проверку с аудитом."""
        self.repo.delete(control_id)
        self.audit.log(
            "DELETE", "control_checks", control_id, username,
            "Удалена запись контрольной проверки"
        )
        app_signals.control_changed.emit()