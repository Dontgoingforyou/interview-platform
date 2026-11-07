import logging

from interviews.models import Interview
from core.constants import INTERVIEW_TYPE_MAPPING, INTERVIEW_TYPE_SCREENING
from core.base_services import BaseImportService
from .utils import parse_datetime_for_interview, get_or_create_company, map_company_name

logger = logging.getLogger('interview_import')


class InterviewImportService(BaseImportService):
    """ Сервисный класс, отвечающий за логику импорта из .csv или .xlsx файлов. """

    logger = logging.getLogger('interview_import')

    def __init__(self, df, progress_callback=None):
        """
        Инициализация сервиса импорта.

        Args:
            df: DataFrame с данными для импорта
            progress_callback: Функция для отслеживания прогресса (опционально)
        """
        super().__init__(df)
        self.progress_callback = progress_callback

    def _load_additional_reference_data(self):
        """Загружает дополнительные справочники для собеседований."""
        # Загружаем компании (дополнительно к базовым справочникам)
        self.companies_map = self._load_companies()
        self.logger.info(f"Загружено: Компаний - {len(self.companies_map)}")

    def _make_unique_key(
            self, intern_id, date, direction_id, company_id, manager_email, time,
            vacancy_link, interview_link, hr_name):
        """
        Создает уникальный ключ для поиска существующих записей.
        НЕ включает interview_type, чтобы можно было обновлять тип при повторном импорте.
        """
        return (
            intern_id,
            date,
            direction_id,
            company_id or '',
            manager_email or '',
            time or '',
            vacancy_link or '',
            interview_link or '',
            hr_name or '',
        )

    def _load_existing_records(self):
        """Загружает существующие собеседования из БД в память как словарь."""
        existing_interviews = Interview.objects.all()
        existing_dict = {}
        for interview in existing_interviews:
            key = self._make_unique_key(
                interview.intern_id,
                interview.date,
                interview.direction_id,
                interview.company_id,
                interview.manager_email,
                interview.time,
                interview.vacancy_link,
                interview.interview_link,
                interview.hr_name
            )
            existing_dict[key] = interview
        return existing_dict

    def _process_row(self, row, index, existing_keys):
        """
        Обрабатывает одну строку данных собеседования.
        Возвращает True, если строка была успешно создана.
        """
        try:
            full_name = self._get_string_field(row, 'full_name')
            direction_name = self._get_string_field(row, 'direction_name')
            interview_type_label = self._get_string_field(row, 'interview_type_label')
            date_str = self._get_string_field(row, 'date_str')
            time_str = self._get_string_field(row, 'time_str')
            company_name = self._get_string_field(row, 'company_name')
            manager_name = self._get_string_field(row, 'manager_name')
            link = self._get_string_field(row, 'link')
            vacancy_link = self._get_string_field(row, 'vacancy_link')
            interview_link = self._get_string_field(row, 'interview_link')
            hr_name = self._get_string_field(row, 'hr_name')
            hr_contacts = self._get_string_field(row, 'hr_contacts')

            # --- Поиск студента по ФИО ---
            intern_obj, success = self._get_intern(full_name, index, required=True)
            if not success:
                return False

            # --- Обработка направления ---
            direction_id, success = self._get_direction_id(direction_name, index, required=True)
            if not success:
                return False

            # --- Обработка компании с нормализацией и созданием ---
            company_id = None
            if company_name:
                # Нормализуем название (для бигтехов) или используем как есть
                effective_name = map_company_name(company_name) or company_name
                company_id = self.companies_map.get(effective_name)
                if company_id is None:
                    try:
                        company_id = get_or_create_company(company_name)
                        if company_id:
                            self.companies_map[effective_name] = company_id
                    except Exception as e:
                        self.logger.error(f"Ошибка при создании компании '{company_name}': {e}")

            # --- Обработка менеджера ---
            manager_email, _ = self._get_manager_email(manager_name, index, required=False)

            # --- Обработка типа собеседования ---
            interview_type = INTERVIEW_TYPE_MAPPING.get(interview_type_label, INTERVIEW_TYPE_SCREENING)

            # --- Обработка даты и времени ---
            date_obj, time_obj, err = parse_datetime_for_interview(date_str, time_str, index)
            if err:
                self._log_error(err, index)
                return False

            # --- Проверка существования (без учета interview_type) ---
            unique_key = self._make_unique_key(
                intern_obj.id, date_obj, direction_id, company_id,
                manager_email, time_obj, vacancy_link, interview_link, hr_name
            )

            # Проверяем, существует ли уже такая запись
            existing_interview = existing_keys.get(unique_key)

            if existing_interview:
                # Обновляем существующую запись (например, если изменился тип интервью)
                existing_interview.interview_type = interview_type
                existing_interview.link = link or None
                existing_interview.manager_email = manager_email
                existing_interview.hr_contacts = hr_contacts or None
                existing_interview.save()

                self._log_skip()
                return False

            # --- Создание новой записи ---
            new_interview = Interview.objects.create(
                intern=intern_obj,
                direction_id=direction_id,
                company_id=company_id,
                manager_email=manager_email,
                interview_type=interview_type,
                date=date_obj,
                time=time_obj,
                link=link or None,
                vacancy_link=vacancy_link or None,
                interview_link=interview_link or None,
                hr_name=hr_name or None,
                hr_contacts=hr_contacts or None,
            )

            # Добавляем в словарь чтобы избежать дублей внутри файла
            existing_keys[unique_key] = new_interview

            self.created_count += 1
            return True

        except Exception as e:
            self._log_error(f"Ошибка при обработке строки {index + 2}: {e}", index)
            return False

    def run(self):
        """Запускает процесс импорта собеседований."""
        self._load_reference_data()

        total_rows = len(self.df)

        # Загружаем существующие записи в память для быстрой проверки и обновления
        self.logger.info("Загрузка существующих собеседований из БД...")
        existing_keys = self._load_existing_records()
        self.logger.info(f"Загружено {len(existing_keys)} существующих собеседований.")

        self.logger.info(f"Начинаю обработку {total_rows} строк собеседований.")

        for index, row in self.df.iterrows():
            success = self._process_row(row, index, existing_keys)

            # Обновляем прогресс для Celery
            if self.progress_callback:
                self.progress_callback(index + 1, total_rows)

            if not success:
                continue  # Пропускаем строку

        self.logger.info(
            f"Обработка собеседований завершена. "
            f"Создано: {self.created_count}, Дубликатов: {self.duplicates_count}, Ошибок: {self.skipped_count}."
        )
        return self.created_count, self.skipped_count, self.duplicates_count, self.errors_log
