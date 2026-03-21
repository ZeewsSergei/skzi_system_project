from repositories.sector_repository import SectorRepository
from services.audit_service import AuditService

class SectorService:
    def __init__(self):
        self.repo = SectorRepository()
        self.audit = AuditService()

    def get_all_sectors(self):
        return self.repo.get_all()

    def get_sectors_by_department(self, department_id):
        return self.repo.get_by_department(department_id)

    def get_by_name(self, name):
        """Возвращает сектор по имени (глобально уникальному) или None."""
        return self.repo.get_by_name(name)

    def add_sector(self, name, department_id, username):
        sector_id = self.repo.add(name, department_id)
        self.audit.log("CREATE", "sectors", sector_id, username,
                       new_value=f"Сектор: {name} (отдел ID {department_id})")
        return sector_id