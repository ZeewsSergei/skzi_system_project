import pandas as pd
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from services.sector_service import SectorService
from services.dictionary_service import DictionaryService

def import_employees_from_excel(parent):
    path, _ = QFileDialog.getOpenFileName(parent, "Выберите файл Excel", "", "Excel (*.xlsx)")
    if not path:
        return
    try:
        df = pd.read_excel(path)
        required = ['ФИО']
        for col in required:
            if col not in df.columns:
                QMessageBox.critical(parent, "Ошибка", f"В файле отсутствует колонка '{col}'")
                return

        emp_service = EmployeeService()
        dept_service = DepartmentService()
        sector_service = SectorService()
        skipped = 0
        added = 0

        depts_by_name = {d['name']: d['id'] for d in dept_service.get_all_departments()}
        all_sectors = sector_service.get_all_sectors()
        sectors_by_name = {s['name']: s for s in all_sectors}

        for _, row in df.iterrows():
            fio = row['ФИО']
            if emp_service.get_by_fio(fio):
                skipped += 1
                continue

            position = row.get('Должность', '')
            sector_raw = row.get('Сектор', '')
            if pd.isna(sector_raw) or str(sector_raw).strip() == '':
                sector_name = ''
            else:
                sector_name = str(sector_raw).strip()

            dept_raw = row.get('Отдел', '')
            if pd.isna(dept_raw) or str(dept_raw).strip() == '':
                dept_name = ''
            else:
                dept_name = str(dept_raw).strip()

            dept_id = None
            if dept_name:
                if dept_name in depts_by_name:
                    dept_id = depts_by_name[dept_name]
                else:
                    dept_id = dept_service.repo.add(dept_name)
                    depts_by_name[dept_name] = dept_id

            sector_id = None
            if sector_name:
                if sector_name in sectors_by_name:
                    sector = sectors_by_name[sector_name]
                    if dept_id and sector['department_id'] != dept_id:
                        dept_of_sector = next((d for d in dept_service.get_all_departments() if d['id'] == sector['department_id']), {}).get('name', 'неизвестный отдел')
                        raise Exception(
                            f"Сектор '{sector_name}' уже существует в отделе '{dept_of_sector}'. "
                            f"Нельзя использовать в отделе '{dept_name}'."
                        )
                    sector_id = sector['id']
                else:
                    if dept_id:
                        sector_id = sector_service.repo.add(sector_name, dept_id)
                        sectors_by_name[sector_name] = {
                            'id': sector_id,
                            'department_id': dept_id,
                            'name': sector_name
                        }
                    else:
                        print(f"Предупреждение: сектор '{sector_name}' указан без отдела для сотрудника {fio}. Сектор не будет сохранён.")

            emp_service.add_employee(fio, position, sector_id, dept_id, "не проводилась", "admin")
            added += 1

        QMessageBox.information(parent, "Импорт завершён",
                                f"Добавлено: {added}\nПропущено (дубликаты): {skipped}")
    except Exception as e:
        QMessageBox.critical(parent, "Ошибка импорта", str(e))


def import_dictionary_from_excel(parent, repo, name_field, dict_name):
    """Универсальная функция для импорта справочников."""
    path, _ = QFileDialog.getOpenFileName(parent, f"Выберите файл для импорта {dict_name}", "", "Excel (*.xlsx)")
    if not path:
        return
    try:
        df = pd.read_excel(path)
        # ожидаем колонку 'name' или 'Наименование'
        name_col = None
        for col in ['name', 'Наименование']:
            if col in df.columns:
                name_col = col
                break
        if name_col is None:
            QMessageBox.critical(parent, "Ошибка", "В файле должна быть колонка 'Наименование'")
            return

        count = 0
        for _, row in df.iterrows():
            val = str(row[name_col]).strip()
            if val and not repo.get_by_name(val):
                repo.add(val)
                count += 1
        QMessageBox.information(parent, "Импорт завершён", f"Добавлено записей: {count}")
    except Exception as e:
        QMessageBox.critical(parent, "Ошибка импорта", str(e))

# Удобные обёртки для каждого справочника
def import_skzi_names(parent, dict_service):
    import_dictionary_from_excel(parent, dict_service.skzi_name_repo, 'name', 'наименований СКЗИ')

def import_media_types(parent, dict_service):
    import_dictionary_from_excel(parent, dict_service.media_type_repo, 'name', 'типов носителей')

def import_received_from(parent, dict_service):
    import_dictionary_from_excel(parent, dict_service.received_from_repo, 'name', 'от кого получен')

def import_arm_types(parent, dict_service):
    import_dictionary_from_excel(parent, dict_service.arm_type_repo, 'name', 'типов АРМ')

def import_os_versions(parent, dict_service):
    import_dictionary_from_excel(parent, dict_service.os_version_repo, 'name', 'версий ОС')

def import_antiviruses(parent, dict_service):
    import_dictionary_from_excel(parent, dict_service.antivirus_repo, 'name', 'антивирусов')

def import_szi_nsd_names(parent, dict_service):
    import_dictionary_from_excel(parent, dict_service.szi_nsd_name_repo, 'name', 'СЗИ от НСД')

def import_addresses(parent, dict_service):
    import_dictionary_from_excel(parent, dict_service.address_repo, 'name', 'адресов')