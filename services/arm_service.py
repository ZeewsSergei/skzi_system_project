from db.db_manager import DatabaseManager
from services.dictionary_service import DictionaryService

class ArmService:
    def __init__(self):
        self.db = DatabaseManager()
        self.dict_service = DictionaryService()

    def get_arm_by_id(self, arm_id):
        cursor = self.db.execute_query("SELECT * FROM arm WHERE id = ?", (arm_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_or_create_arm(self, arm_data):
        """
        arm_data должен содержать:
        - arm_name (str)
        - arm_serial (str) – обязательный
        - arm_type (str) – текст, будет преобразован в id через справочник
        - cabinet_number (str)
        - install_address (str) – текст, будет преобразован в id через справочник
        Возвращает ID существующего или нового АРМ.
        """
        # Сначала ищем по серийному номеру
        cursor = self.db.execute_query(
            "SELECT id FROM arm WHERE arm_serial = ?", (arm_data['arm_serial'],)
        )
        row = cursor.fetchone()
        if row:
            arm_id = row['id']
            # Обновляем существующий АРМ (кроме серийного номера)
            arm_type_id = self.dict_service.get_or_create_arm_type(arm_data.get('arm_type', ''))
            install_address_id = self.dict_service.get_or_create_address(arm_data.get('install_address', ''))

            self.db.execute_query("""
                UPDATE arm SET
                    arm_name = ?,
                    arm_type_id = ?,
                    cabinet_number = ?,
                    install_address_id = ?
                WHERE id = ?
            """, (
                arm_data.get('arm_name', ''),
                arm_type_id,
                arm_data.get('cabinet_number', ''),
                install_address_id,
                arm_id
            ))
            self.db.commit()
            return arm_id
        else:
            # Создаём новый АРМ
            arm_type_id = self.dict_service.get_or_create_arm_type(arm_data.get('arm_type', ''))
            install_address_id = self.dict_service.get_or_create_address(arm_data.get('install_address', ''))

            cursor = self.db.execute_query("""
                INSERT INTO arm (
                    arm_name, arm_serial, arm_type_id, cabinet_number, install_address_id
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                arm_data.get('arm_name', ''),
                arm_data['arm_serial'],
                arm_type_id,
                arm_data.get('cabinet_number', ''),
                install_address_id
            ))
            self.db.commit()
            return cursor.lastrowid