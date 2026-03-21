import pandas as pd

class ExcelExporter:
    def __init__(self, db):
        self.db = db

    def fetch_dataframe(self, query, params=()):
        return pd.read_sql_query(query, self.db.conn, params=params)

    def export_install_act(self, start_date, end_date, file_path):
        query = """
        SELECT
            e.fio AS 'Фамилия, имя, отчество',
            a.cabinet_number AS 'Номер помещения и рабочего места',
            a.arm_serial AS 'Заводской номер АРМ',
            sn.name AS 'Наименование и версия СКЗИ',
            ov.name AS 'Наименование и версия операционной системы',
            av.name AS 'Антивирус',
            sz.name AS 'СЗИ от НСД',
            r.install_date AS 'Дата установки'
        FROM skzi_registry r
        JOIN employees e ON r.employee_id = e.id
        JOIN arm a ON r.arm_id = a.id
        LEFT JOIN skzi_names sn ON r.skzi_name_id = sn.id
        LEFT JOIN os_versions ov ON a.os_version_id = ov.id
        LEFT JOIN antiviruses av ON a.antivirus_id = av.id
        LEFT JOIN szi_nsd_names sz ON a.szi_nsd_id = sz.id
        WHERE r.install_date BETWEEN ? AND ?
        ORDER BY r.install_date
        """
        df = self.fetch_dataframe(query, (start_date, end_date))
        if not df.empty:
            df.insert(0, '№ п/п', range(1, len(df)+1))
        df.to_excel(file_path, index=False)

    def export_destruction_act(self, start_date, end_date, file_path):
        query = """
        SELECT
            r.media_number AS 'Учетный номер ключевого носителя',
            r.skzi_number AS 'Номер криптографического ключа, наименование документа',
            e.fio AS 'Владелец ключа (документа)',
            1 AS 'Количество ключевых носителей',
            r.skzi_instance_number AS 'Номера экземпляров',
            1 AS 'Всего ключей',
            '' AS 'Примечание',
            r.withdrawal_date AS 'Дата уничтожения'
        FROM skzi_registry r
        JOIN employees e ON r.employee_id = e.id
        WHERE r.status = 'DESTROYED' AND r.withdrawal_date BETWEEN ? AND ?
        ORDER BY r.withdrawal_date
        """
        df = self.fetch_dataframe(query, (start_date, end_date))
        if not df.empty:
            df.insert(0, '№ п/п', range(1, len(df)+1))
        df.to_excel(file_path, index=False)

    def export_training_sheet(self, start_date, end_date, file_path):
        query = """
        SELECT
            e.fio AS 'Фамилия, имя, отчество',
            t.position AS 'Должность',
            t.department AS 'Отдел',
            t.result AS 'Отметка о результатах проверки знаний'
        FROM training_logs t
        JOIN employees e ON t.employee_id = e.id
        WHERE t.training_date BETWEEN ? AND ?
        ORDER BY t.training_date
        """
        df = self.fetch_dataframe(query, (start_date, end_date))
        if not df.empty:
            df.insert(0, '№ п/п', range(1, len(df)+1))
        df.to_excel(file_path, index=False)

    def export_full_data(self, file_path):
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Реестр
            df_reg = self.fetch_dataframe("""
                SELECT r.id, e.fio as Сотрудник, sn.name as СКЗИ, r.skzi_number as 'Заводской №',
                       r.skzi_instance_number as '№ экземпляра', a.cabinet_number as Кабинет,
                       r.install_date as 'Дата установки', r.withdrawal_date as 'Дата изъятия',
                       r.status as Статус
                FROM skzi_registry r
                JOIN employees e ON r.employee_id = e.id
                JOIN arm a ON r.arm_id = a.id
                LEFT JOIN skzi_names sn ON r.skzi_name_id = sn.id
            """)
            df_reg.to_excel(writer, sheet_name='Реестр', index=False)

            # Сотрудники
            df_emp = self.fetch_dataframe("""
                SELECT e.fio as ФИО, e.position as Должность,
                       s.name as Сектор, d.name as Отдел,
                       e.knowledge_check as 'Проверка знаний'
                FROM employees e
                LEFT JOIN sectors s ON e.sector_id = s.id
                LEFT JOIN departments d ON e.department_id = d.id
            """)
            df_emp.to_excel(writer, sheet_name='Сотрудники', index=False)

            # АРМ (с учетом справочников)
            df_arm = self.fetch_dataframe("""
                SELECT a.id, a.arm_name as 'Имя АРМ', a.arm_serial as 'Серийный №',
                       at.name as 'Тип АРМ', ov.name as 'ОС', av.name as 'Антивирус',
                       sz.name as 'СЗИ от НСД', a.cabinet_number as 'Кабинет',
                       addr.name as 'Адрес установки'
                FROM arm a
                LEFT JOIN arm_types at ON a.arm_type_id = at.id
                LEFT JOIN os_versions ov ON a.os_version_id = ov.id
                LEFT JOIN antiviruses av ON a.antivirus_id = av.id
                LEFT JOIN szi_nsd_names sz ON a.szi_nsd_id = sz.id
                LEFT JOIN addresses addr ON a.install_address_id = addr.id
            """)
            df_arm.to_excel(writer, sheet_name='АРМ', index=False)

            # Обучение
            df_train = self.fetch_dataframe("""
                SELECT t.training_date as Дата, e.fio as Сотрудник,
                       t.position as Должность, t.department as Отдел,
                       t.result as Результат
                FROM training_logs t
                JOIN employees e ON t.employee_id = e.id
            """)
            df_train.to_excel(writer, sheet_name='Обучение', index=False)