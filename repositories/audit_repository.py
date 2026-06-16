# repositories/audit_repository.py
"""
УСТАРЕВШИЙ МОДУЛЬ.
Оставлен для совместимости со сборкой PyInstaller (hiddenimports в .spec).

Вся логика аудита перенесена в services/audit_service.py (AuditService).
Используйте AuditService напрямую — он поддерживает old_value и changed_fields.

Этот класс является тонкой обёрткой и делегирует вызовы AuditService.
"""

import warnings
from services.audit_service import AuditService


class AuditRepository:
    """
    Устаревшая обёртка. Используйте AuditService.

    Оставлена только для обратной совместимости.
    Не добавляйте новые вызовы этого класса.
    """

    def __init__(self):
        warnings.warn(
            "AuditRepository устарел. Используйте AuditService напрямую.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._service = AuditService()

    def add(self, action_type, table_name, record_id, performed_by, new_value):
        """Делегирует в AuditService.log()."""
        self._service.log(
            action_type=action_type,
            table_name=table_name,
            record_id=record_id,
            user=performed_by,
            new_value=new_value,
        )

    def get_recent(self, limit=100):
        """Делегирует в AuditService.get_recent()."""
        return self._service.get_recent(limit=limit)