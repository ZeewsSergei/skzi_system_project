# services/control_service.py

from repositories.control_repository import (
    get_all_controls,
    add_control,
    delete_control
)


class ControlService:

    def get_all_controls(self):
        return get_all_controls()

    def register_control(self, skzi_id, date, result, inspector):
        return add_control(skzi_id, date, result, inspector)

    def remove_control(self, control_id):
        return delete_control(control_id)