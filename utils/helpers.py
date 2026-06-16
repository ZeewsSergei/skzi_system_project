import pandas as pd
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from services.sector_service import SectorService
from services.dictionary_service import DictionaryService
from logger import app_logger
from signals.app_signals import app_signals


# ========== Импорт сотрудников (без изменений) ==========
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

        app_signals.employee_changed.emit()
        app_signals.department_changed.emit()

        QMessageBox.information(parent, "Импорт завершён",
                                f"Добавлено: {added}\nПропущено (дубликаты): {skipped}")
    except Exception as e:
        QMessageBox.critical(parent, "Ошибка импорта", str(e))


# ========== Импорт справочников (общая функция) ==========
def import_dictionary_from_excel(parent, repo, name_field, dict_name):
    """Универсальная функция для импорта справочников."""
    path, _ = QFileDialog.getOpenFileName(parent, f"Выберите файл для импорта {dict_name}", "", "Excel (*.xlsx)")
    if not path:
        return
    try:
        df = pd.read_excel(path)
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


# ========== Импорт журнала учета ЭП ==========
def import_ep_journal(parent, dict_service, emp_service, arm_service, skzi_service):
    """
    Импорт журнала учёта ЭП из Excel.
    Ожидаемые колонки:
    - Тип носителя
    - Номер носителя ЭП
    - № сертификата ЭП
    - От кого получен
    - № письма
    - Дата получения письма
    - ФИО
    - Отдел
    - Дата установки
    - Кто установил
    - Кабинет
    - Серийный № АРМ
    - Срок до
    - Адрес установки
    """
    file_path, _ = QFileDialog.getOpenFileName(parent, "Выберите файл для импорта журнала ЭП", "", "Excel (*.xlsx *.xls)")
    if not file_path:
        return

    try:
        df = pd.read_excel(file_path)
        df.columns = [str(col).strip() for col in df.columns]

        required_columns = [
            'Тип носителя', 'Номер носителя ЭП', '№ сертификата ЭП',
            'От кого получен', '№ письма', 'Дата получения письма',
            'ФИО', 'Отдел', 'Дата установки', 'Кто установил',
            'Кабинет', 'Серийный № АРМ', 'Срок до', 'Адрес установки'
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            QMessageBox.warning(parent, "Ошибка", f"В файле отсутствуют колонки: {', '.join(missing)}")
            return

        success_count = 0
        error_count = 0
        errors = []

        dept_cache = {}
        dept_service = DepartmentService()

        for idx, row in df.iterrows():
            try:
                fio = str(row['ФИО']).strip()
                department_name = str(row['Отдел']).strip()
                if not fio:
                    raise Exception(f"Строка {idx+2}: ФИО не указано")

                dept_id = None
                if department_name:
                    if department_name in dept_cache:
                        dept_id = dept_cache[department_name]
                    else:
                        dept_id = dept_service.get_or_create_department(department_name, "system")
                        dept_cache[department_name] = dept_id

                emp = emp_service.get_by_fio(fio)
                if emp:
                    emp_id = emp['id']
                else:
                    emp_id = emp_service.add_employee(fio, '', None, dept_id, "не проводилась", "system")

                media_type_text = str(row['Тип носителя']).strip()
                media_number = str(row['Номер носителя ЭП']).strip()
                cert_number = str(row['№ сертификата ЭП']).strip()
                received_from_text = str(row['От кого получен']).strip()
                letter_num = str(row['№ письма']).strip()
                receive_date = str(row['Дата получения письма']).strip()
                install_date = str(row['Дата установки']).strip()
                installer = str(row['Кто установил']).strip()
                cabinet = str(row['Кабинет']).strip()
                arm_serial = str(row['Серийный № АРМ']).strip()
                expiry_date = str(row['Срок до']).strip()
                address_text = str(row['Адрес установки']).strip()

                # Преобразование дат (если есть время)
                if receive_date and ' ' in receive_date:
                    receive_date = receive_date.split()[0]
                if install_date and ' ' in install_date:
                    install_date = install_date.split()[0]
                if expiry_date and ' ' in expiry_date:
                    expiry_date = expiry_date.split()[0]

                # Проверка уникальности cert_number (если заполнен)
                if cert_number:
                    cursor = skzi_service.db.execute_query(
                        "SELECT id FROM skzi_registry WHERE cert_number = ?", (cert_number,)
                    )
                    if cursor.fetchone():
                        raise Exception(f"Сертификат ЭП с номером '{cert_number}' уже существует в базе.")

                media_type_id = dict_service.get_or_create_media_type(media_type_text, "system") if media_type_text else None
                received_from_id = dict_service.get_or_create_received_from(received_from_text, "system") if received_from_text else None
                address_id = dict_service.get_or_create_address(address_text, "system") if address_text else None

                arm_data = {
                    'arm_name': '',
                    'arm_serial': arm_serial,
                    'arm_type': '',
                    'cabinet_number': cabinet,
                    'install_address': address_text,
                    'os_version': '',
                    'antivirus': '',
                    'szi_nsd': ''
                }
                arm_id = arm_service.get_or_create_arm(arm_data)

                # skzi_number в журнале ЭП не используется
                skzi_number_val = ''

                data = {
                    'employee_id': emp_id,
                    'arm_id': arm_id,
                    'skzi_name': '',
                    'skzi_number': skzi_number_val,
                    'skzi_instance_number': '',
                    'media_type': media_type_text,
                    'media_number': media_number,
                    'cert_number': cert_number,
                    'received_from': received_from_text,
                    'receive_letter_num': letter_num,
                    'receive_date': receive_date,
                    'install_date': install_date,
                    'expiry_date': expiry_date,
                    'installer_fio': installer,
                    'knowledge_check': "не проводилась",
                    'arm_name': '',
                    'arm_serial': arm_serial,
                    'arm_type': '',
                    'os_version': '',
                    'antivirus': '',
                    'szi_nsd': '',
                    'cabinet_number': cabinet,
                    'install_address': address_text
                }
                skzi_service.register_skzi(data, "system")
                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"Строка {idx+2}: {str(e)}")
                app_logger.error(f"Ошибка импорта строки {idx+2}: {e}")

        app_signals.skzi_changed.emit()
        app_signals.employee_changed.emit()
        app_signals.department_changed.emit()

        QMessageBox.information(parent, "Результат импорта",
                                f"Импорт завершён.\nУспешно: {success_count}\nОшибок: {error_count}" +
                                (f"\n\nОшибки:\n" + "\n".join(errors[:10]) if errors else ""))
    except Exception as e:
        app_logger.exception(f"Ошибка при импорте журнала ЭП: {e}")
        QMessageBox.critical(parent, "Ошибка", f"Не удалось импортировать данные: {str(e)}")


# ========== Импорт журнала учета СКЗИ ==========
def import_skzi_journal(parent, dict_service, emp_service, arm_service, skzi_service):
    """
    Импорт журнала учёта СКЗИ из Excel.
    Ожидаемые колонки:
    - Наименование СКЗИ
    - Серийный (заводской) № СКЗИ
    - № экземпляра
    - От кого получен
    - ФИО
    - Кабинет
    - Серийный № АРМ
    - Адрес установки
    """
    file_path, _ = QFileDialog.getOpenFileName(parent, "Выберите файл для импорта журнала СКЗИ", "", "Excel (*.xlsx *.xls)")
    if not file_path:
        return

    try:
        df = pd.read_excel(file_path)
        df.columns = [str(col).strip() for col in df.columns]

        required_columns = [
            'Наименование СКЗИ', 'Серийный (заводской) № СКЗИ', '№ экземпляра',
            'От кого получен', 'ФИО', 'Кабинет', 'Серийный № АРМ', 'Адрес установки'
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            QMessageBox.warning(parent, "Ошибка", f"В файле отсутствуют колонки: {', '.join(missing)}")
            return

        success_count = 0
        error_count = 0
        errors = []

        dept_service = DepartmentService()

        for idx, row in df.iterrows():
            try:
                fio = str(row['ФИО']).strip()
                skzi_name_text = str(row['Наименование СКЗИ']).strip()
                skzi_number = str(row['Серийный (заводской) № СКЗИ']).strip()
                skzi_instance = str(row['№ экземпляра']).strip()
                received_from_text = str(row['От кого получен']).strip()
                cabinet = str(row['Кабинет']).strip()
                arm_serial = str(row['Серийный № АРМ']).strip()
                address_text = str(row['Адрес установки']).strip()

                if not fio:
                    raise Exception(f"Строка {idx+2}: ФИО не указано")
                if not skzi_name_text:
                    raise Exception(f"Строка {idx+2}: Наименование СКЗИ не указано")
                if not arm_serial:
                    raise Exception(f"Строка {idx+2}: Серийный № АРМ не указан")

                # Проверка на дубликат skzi_number
                if skzi_number:
                    cursor = skzi_service.db.execute_query(
                        "SELECT id FROM skzi_registry WHERE skzi_number = ?", (skzi_number,)
                    )
                    if cursor.fetchone():
                        raise Exception(f"СКЗИ с заводским номером '{skzi_number}' уже существует в базе.")

                # Проверка на дубликат cert_number – в журнале СКЗИ его нет, но если бы был

                dept_id = None
                emp = emp_service.get_by_fio(fio)
                if emp:
                    emp_id = emp['id']
                else:
                    emp_id = emp_service.add_employee(fio, '', None, dept_id, "не проводилась", "system")

                skzi_name_id = dict_service.get_or_create_skzi_name(skzi_name_text, "system")
                received_from_id = dict_service.get_or_create_received_from(received_from_text, "system") if received_from_text else None
                address_id = dict_service.get_or_create_address(address_text, "system") if address_text else None

                arm_data = {
                    'arm_name': '',
                    'arm_serial': arm_serial,
                    'arm_type': '',
                    'cabinet_number': cabinet,
                    'install_address': address_text,
                    'os_version': '',
                    'antivirus': '',
                    'szi_nsd': ''
                }
                arm_id = arm_service.get_or_create_arm(arm_data)

                data = {
                    'employee_id': emp_id,
                    'arm_id': arm_id,
                    'skzi_name': skzi_name_text,
                    'skzi_number': skzi_number,
                    'skzi_instance_number': skzi_instance,
                    'media_type': '',
                    'media_number': '',
                    'cert_number': '',
                    'received_from': received_from_text,
                    'receive_letter_num': '',
                    'receive_date': '',
                    'install_date': '',
                    'expiry_date': '',
                    'installer_fio': 'system',
                    'knowledge_check': "не проводилась",
                    'arm_name': '',
                    'arm_serial': arm_serial,
                    'arm_type': '',
                    'os_version': '',
                    'antivirus': '',
                    'szi_nsd': '',
                    'cabinet_number': cabinet,
                    'install_address': address_text
                }
                skzi_service.register_skzi(data, "system")
                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"Строка {idx+2}: {str(e)}")
                app_logger.error(f"Ошибка импорта строки {idx+2}: {e}")

        app_signals.skzi_changed.emit()
        app_signals.employee_changed.emit()

        QMessageBox.information(parent, "Результат импорта",
                                f"Импорт завершён.\nУспешно: {success_count}\nОшибок: {error_count}" +
                                (f"\n\nОшибки:\n" + "\n".join(errors[:10]) if errors else ""))
    except Exception as e:
        app_logger.exception(f"Ошибка при импорте журнала СКЗИ: {e}")
        QMessageBox.critical(parent, "Ошибка", f"Не удалось импортировать данные: {str(e)}")


# ========== Экспорт шаблонов для импорта ==========
def export_template_ep_journal(parent):
    """
    Экспортирует пустой шаблон Excel для импорта журнала учёта ЭП.
    """
    path, _ = QFileDialog.getSaveFileName(
        parent,
        "Сохранить шаблон журнала учёта ЭП",
        "Шаблон_журнала_ЭП.xlsx",
        "Excel (*.xlsx)"
    )
    if not path:
        return

    columns = [
        'Тип носителя', 'Номер носителя ЭП', '№ сертификата ЭП',
        'От кого получен', '№ письма', 'Дата получения письма',
        'ФИО', 'Отдел', 'Дата установки', 'Кто установил',
        'Кабинет', 'Серийный № АРМ', 'Срок до', 'Адрес установки'
    ]
    df = pd.DataFrame(columns=columns)
    df.to_excel(path, index=False)
    QMessageBox.information(parent, "Успех", f"Шаблон сохранён:\n{path}")


def export_template_skzi_journal(parent):
    """
    Экспортирует пустой шаблон Excel для импорта журнала учёта СКЗИ.
    """
    path, _ = QFileDialog.getSaveFileName(
        parent,
        "Сохранить шаблон журнала учёта СКЗИ",
        "Шаблон_журнала_СКЗИ.xlsx",
        "Excel (*.xlsx)"
    )
    if not path:
        return

    columns = [
        'Наименование СКЗИ', 'Серийный (заводской) № СКЗИ', '№ экземпляра',
        'От кого получен', 'ФИО', 'Кабинет', 'Серийный № АРМ', 'Адрес установки'
    ]
    df = pd.DataFrame(columns=columns)
    df.to_excel(path, index=False)
    QMessageBox.information(parent, "Успех", f"Шаблон сохранён:\n{path}")