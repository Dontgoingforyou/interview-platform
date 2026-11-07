import logging
import pandas as pd
import re
from datetime import datetime

from django.db import transaction

from core.constants import MAX_NAME_LENGTH, MAX_TELEGRAM_LENGTH, MAX_GROUP_LENGTH
from sad_intern.models import SadIntern

from .models import Intern
from core.base_services import BaseImportService
from core.intern_utils import find_intern_by_name
from .utils import (
    parse_date,
    extract_email_from_string,
    normalize_type_of_training,
    truncate_string,
    clean_hr_field,
    resolve_cv_from_row,
    resolve_url_field,
    fill_if_empty,
)

logger = logging.getLogger('intern_import')

INTERN_SYNC_MERGE_FIELDS = (
    'city',
    'cv',
    'legend',
    'telegram_username',
    'email',
    'group',
    'hiring_hr',
    'responsible_hr',
    'manager_email',
    'date_of_birth',
    'date_of_receipt',
    'type_of_training',
    'hr_feedback',
)


class InternRowParserMixin:
    """Общий парсинг строки импорта студентов из файла."""

    logger = logging.getLogger('intern_import')

    def _make_unique_key(self, full_name, direction_id):
        return (full_name, direction_id)

    def _parse_row_data(self, row, index):
        """
        Парсит строку CSV/XLSX в словарь полей Intern.
        Возвращает (data, None) или (None, error_message).
        """
        full_name = truncate_string(row.get('full_name'), MAX_NAME_LENGTH)
        if not full_name:
            return None, f'Пустое имя в строке {index + 2}.'

        direction_name = str(row.get('direction_name', '')).strip()
        manager_name = str(row.get('manager_name', '')).strip()
        type_of_training_label = str(row.get('type_of_training_label', '')).strip()
        date_of_birth_str = str(row.get('date_of_birth_str', '')).strip()
        date_of_receipt_str = str(row.get('date_of_receipt_str', '')).strip()
        telegram_username = truncate_string(row.get('telegram_username'), MAX_TELEGRAM_LENGTH)
        group = truncate_string(row.get('group', ''), MAX_GROUP_LENGTH)
        hiring_hr = clean_hr_field(row.get('hiring_hr'))
        responsible_hr = clean_hr_field(row.get('responsible_hr'))
        city = truncate_string(row.get('city', ''), MAX_NAME_LENGTH) or None
        cv = resolve_cv_from_row(row, index)
        legend = resolve_url_field(row, 'legend', 'legend', index)
        hr_feedback = truncate_string(row.get('hr_feedback', ''), MAX_NAME_LENGTH) or None
        additional_contacts_val = row.get('additional_contacts_str')
        additional_contacts = str(additional_contacts_val).strip() if pd.notna(additional_contacts_val) else ''

        direction_id, success = self._get_direction_id(direction_name, index, required=True)
        if not success:
            return None, None

        manager_email, _ = self._get_manager_email(manager_name, index, required=False, use_tc_mapping=True)

        date_of_birth, err = parse_date(date_of_birth_str, 'рождения', index)
        if err:
            return None, err

        date_of_receipt, err = parse_date(date_of_receipt_str, 'подписи', index)
        if err:
            logger.warning(err)
            date_of_receipt = None

        type_of_training, err = normalize_type_of_training(type_of_training_label)
        if err:
            return None, err

        email = extract_email_from_string(additional_contacts)

        return {
            'full_name': full_name,
            'direction_id': direction_id,
            'manager_email': manager_email,
            'email': email,
            'telegram_username': telegram_username or None,
            'group': group,
            'hiring_hr': hiring_hr,
            'responsible_hr': responsible_hr,
            'city': city,
            'cv': cv,
            'legend': legend,
            'hr_feedback': hr_feedback,
            'date_of_birth': date_of_birth,
            'date_of_receipt': date_of_receipt,
            'type_of_training': type_of_training,
        }, None


class InternImportService(InternRowParserMixin, BaseImportService):

    logger = logging.getLogger('intern_import')

    def _load_existing_keys(self):
        existing_interns = Intern.objects.values_list('full_name', 'direction_id')
        return {self._make_unique_key(*row) for row in existing_interns}

    def _process_row(self, row, index, existing_keys):
        try:
            data, err = self._parse_row_data(row, index)
            if err:
                self._log_error(err, index)
                return False
            if data is None:
                return False

            unique_key = self._make_unique_key(data['full_name'], data['direction_id'])
            if unique_key in existing_keys:
                self._log_skip()
                return False

            Intern.objects.create(
                manager_email=data['manager_email'],
                full_name=data['full_name'],
                email=data['email'],
                telegram_username=data['telegram_username'],
                direction_id=data['direction_id'],
                city=data['city'],
                cv=data['cv'],
                date_of_receipt=data['date_of_receipt'],
                date_of_birth=data['date_of_birth'],
                hiring_hr=data['hiring_hr'],
                responsible_hr=data['responsible_hr'],
                group=data['group'],
                type_of_training=data['type_of_training'],
                legend=data['legend'],
                hr_feedback=data['hr_feedback'],
            )

            existing_keys.add(unique_key)
            self.created_count += 1
            return True

        except Exception as e:
            self._log_error(f'Ошибка при обработке строки {index + 2}: {e}', index)
            return False

    def run(self):
        self._load_reference_data()
        total_rows = len(self.df)

        logger.info('Загрузка существующих студентов из БД...')
        existing_keys = self._load_existing_keys()
        logger.info(f'Загружено {len(existing_keys)} существующих студентов.')
        logger.info(f'Начинаю обработку {total_rows} строк студентов.')

        with transaction.atomic():
            for index, row in self.df.iterrows():
                self._process_row(row, index, existing_keys)
                if self.progress_callback:
                    self.progress_callback(index + 1, total_rows)

        logger.info(
            f'Обработка студентов завершена. '
            f'Создано: {self.created_count}, Дубликатов: {self.duplicates_count}, '
            f'Ошибок: {self.skipped_count}.'
        )
        return self.created_count, self.skipped_count, self.duplicates_count, self.errors_log


class InternSyncImportService(InternRowParserMixin, BaseImportService):
    """
    Синхронизация студентов из файла: дополняет пустые поля, не затирает заполненные.
    """

    logger = logging.getLogger('intern_import')

    def __init__(self, df, progress_callback=None, dry_run=False):
        super().__init__(df, progress_callback)
        self.dry_run = dry_run
        self.updated_count = 0
        self.unchanged_count = 0

    def _load_existing_interns_map(self):
        interns = Intern.objects.all()
        return {
            self._make_unique_key(intern.full_name, intern.direction_id): intern
            for intern in interns
        }

    def _merge_intern(self, intern, data):
        """Дополняет пустые поля существующей записи. Возвращает список изменённых полей."""
        changed_fields = []
        for field in INTERN_SYNC_MERGE_FIELDS:
            if fill_if_empty(intern, field, data.get(field)):
                changed_fields.append(field)
        return changed_fields

    def _process_row(self, row, index, existing_map):
        try:
            data, err = self._parse_row_data(row, index)
            if err:
                self._log_error(err, index)
                return False
            if data is None:
                return False

            unique_key = self._make_unique_key(data['full_name'], data['direction_id'])
            existing = existing_map.get(unique_key)

            if existing is None:
                if not self.dry_run:
                    intern = Intern.objects.create(
                        manager_email=data['manager_email'],
                        full_name=data['full_name'],
                        email=data['email'],
                        telegram_username=data['telegram_username'],
                        direction_id=data['direction_id'],
                        city=data['city'],
                        cv=data['cv'],
                        date_of_receipt=data['date_of_receipt'],
                        date_of_birth=data['date_of_birth'],
                        hiring_hr=data['hiring_hr'],
                        responsible_hr=data['responsible_hr'],
                        group=data['group'],
                        type_of_training=data['type_of_training'],
                        legend=data['legend'],
                        hr_feedback=data['hr_feedback'],
                    )
                    existing_map[unique_key] = intern
                self.created_count += 1
                logger.info(
                    f"Строка {index + 2}: создан студент '{data['full_name']}' "
                    f"(dry_run={self.dry_run})."
                )
                return True

            changed_fields = self._merge_intern(existing, data)
            if changed_fields:
                if not self.dry_run:
                    existing.save(update_fields=changed_fields)
                self.updated_count += 1
                logger.info(
                    f"Строка {index + 2}: обновлён '{data['full_name']}', "
                    f"поля: {', '.join(changed_fields)} (dry_run={self.dry_run})."
                )
                return True

            self.unchanged_count += 1
            self._log_skip()
            return False

        except Exception as e:
            self._log_error(f'Ошибка при обработке строки {index + 2}: {e}', index)
            return False

    def run(self):
        self._load_reference_data()
        total_rows = len(self.df)

        logger.info('Загрузка существующих студентов для синхронизации...')
        existing_map = self._load_existing_interns_map()
        logger.info(f'Загружено {len(existing_map)} существующих студентов.')
        logger.info(
            f'Начинаю синхронизацию {total_rows} строк (dry_run={self.dry_run}).'
        )

        with transaction.atomic():
            for index, row in self.df.iterrows():
                self._process_row(row, index, existing_map)
                if self.progress_callback:
                    self.progress_callback(index + 1, total_rows)
            if self.dry_run:
                transaction.set_rollback(True)

        logger.info(
            f'Синхронизация завершена. Создано: {self.created_count}, '
            f'Обновлено: {self.updated_count}, Без изменений: {self.unchanged_count}, '
            f'Ошибок: {self.skipped_count}.'
        )
        # created + updated — успешные изменения; unchanged — duplicates для API
        return (
            self.created_count + self.updated_count,
            self.skipped_count,
            self.unchanged_count,
            self.errors_log,
        )


class RealInterviewDateImportService(BaseImportService):
    """
    Сервис для импорта дат выхода на реальные собеседования.
    НЕ сбрасывает БД, только обновляет существующих студентов.
    """

    def __init__(self, df, progress_callback=None):
        super().__init__(df, progress_callback)
        self.updated_count = 0

    def _parse_date_from_cell(self, date_str):
        """
        Парсит дату из строки, извлекая первую найденную дату.
        Поддерживает форматы: DD.MM.YYYY, DD.MM.YY, DD.MM, YYYY-MM-DD, и datetime из pandas.
        Игнорирует весь остальной текст, скобки и комментарии.
        """
        if pd.isna(date_str) or not date_str:
            return None

        date_str = str(date_str).strip()

        if not date_str or date_str == 'nan':
            return None

        date_pattern_4y = r'\b(\d{2})\.(\d{2})\.(\d{4})\b'
        match = re.search(date_pattern_4y, date_str)

        if match:
            day, month, year = match.groups()
            try:
                parsed_date = datetime.strptime(f'{day}.{month}.{year}', '%d.%m.%Y').date()
                logger.info(f"Извлечена дата '{parsed_date}' из строки '{date_str}'")
                return parsed_date
            except ValueError as e:
                logger.warning(f"Найдена дата '{day}.{month}.{year}' в строке '{date_str}', но она невалидна: {e}")

        date_pattern_2y = r'\b(\d{2})\.(\d{2})\.(\d{2})\b'
        match_2y = re.search(date_pattern_2y, date_str)

        if match_2y:
            day, month, year_2d = match_2y.groups()
            year_int = int(year_2d)
            full_year = 2000 + year_int if year_int <= 50 else 1900 + year_int
            try:
                parsed_date = datetime.strptime(f'{day}.{month}.{full_year}', '%d.%m.%Y').date()
                logger.info(f"Извлечена дата '{parsed_date}' из строки '{date_str}' (2-значный год)")
                return parsed_date
            except ValueError as e:
                logger.warning(f"Найдена дата '{day}.{month}.{year_2d}' в строке '{date_str}', но она невалидна: {e}")

        date_pattern_iso = r'(\d{4})-(\d{2})-(\d{2})'
        match_iso = re.search(date_pattern_iso, date_str)

        if match_iso:
            year, month, day = match_iso.groups()
            try:
                parsed_date = datetime.strptime(f'{year}-{month}-{day}', '%Y-%m-%d').date()
                logger.info(f"Извлечена дата '{parsed_date}' из строки '{date_str}'")
                return parsed_date
            except ValueError as e:
                logger.warning(f"Найдена дата '{year}-{month}-{day}' в строке '{date_str}', но она невалидна: {e}")

        date_pattern_no_year = r'\b(\d{2})\.(\d{2})\b'
        match_no_year = re.search(date_pattern_no_year, date_str)

        if match_no_year:
            day, month = match_no_year.groups()
            from datetime import date
            today = date.today()
            current_year = today.year

            try:
                parsed_date = datetime.strptime(f'{day}.{month}.{current_year}', '%d.%m.%Y').date()
                days_diff = (today - parsed_date).days
                if days_diff > 60:
                    parsed_date = datetime.strptime(f'{day}.{month}.{current_year + 1}', '%d.%m.%Y').date()
                    logger.info(
                        f"Извлечена дата '{parsed_date}' из строки '{date_str}' "
                        f'(без года, использован следующий год)'
                    )
                else:
                    logger.info(
                        f"Извлечена дата '{parsed_date}' из строки '{date_str}' "
                        f'(без года, использован текущий год)'
                    )
                return parsed_date
            except ValueError as e:
                logger.warning(f"Найдена дата '{day}.{month}' в строке '{date_str}', но она невалидна: {e}")

        logger.warning(f"Не удалось найти дату в строке: '{date_str}'")
        return None

    def _process_row(self, row, index):
        try:
            full_name_raw = row.get('ФИ', '')

            if pd.isna(full_name_raw):
                self._log_error(f'Пустое имя в строке {index + 2}', index)
                return False

            full_name = str(full_name_raw).strip()

            if not full_name or full_name == 'nan':
                self._log_error(f'Пустое имя в строке {index + 2}', index)
                return False

            date_value = row.get('Дата', '')
            parsed_date = self._parse_date_from_cell(date_value)
            if not parsed_date:
                self._log_error(
                    f"Не удалось распарсить дату '{date_value}' для {full_name} в строке {index + 2}",
                    index,
                )
                return False

            interns_cache = getattr(self, 'interns_cache', None)
            intern = find_intern_by_name(full_name, interns_cache=interns_cache)
            if not intern:
                logger.info(f"Студент '{full_name}' не найден в БД (строка {index + 2}), пропускаем")
                self.skipped_count += 1
                return False

            if intern.real_interview_date == parsed_date:
                logger.info(f"Дата для студента '{full_name}' уже существует ({parsed_date}), пропускаем")
                self._log_skip()
                return False

            intern.real_interview_date = parsed_date
            intern.save(update_fields=['real_interview_date'])

            try:
                sad_intern = SadIntern.objects.filter(intern=intern).first()
                if sad_intern:
                    sad_intern.waiting_since = parsed_date
                    sad_intern.save()
            except Exception as e:
                logger.warning(f'Не удалось обновить SadIntern для {full_name}: {e}')

            logger.info(f"Обновлена дата для студента '{full_name}': {parsed_date}")
            self.updated_count += 1
            return True

        except Exception as e:
            self._log_error(f'Ошибка при обработке строки {index + 2}: {e}', index)
            return False

    def run(self):
        self._load_reference_data()
        total_rows = len(self.df)
        self._run_import_loop(
            total_rows,
            f'Начинаю обработку {total_rows} строк с датами собеседований.',
        )

        logger.info(
            f'Обработка завершена. '
            f'Обновлено: {self.updated_count}, Дубликатов: {self.duplicates_count}, '
            f'Пропущено: {self.skipped_count}.'
        )
        return self.updated_count, self.skipped_count, self.duplicates_count, self.errors_log
