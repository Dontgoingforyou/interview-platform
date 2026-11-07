import logging

from .models import SadIntern
from core.constants import SAD_INTERN_STATUS_MAPPING, MONTH_NAME_TO_NUMBER
from core.base_services import BaseImportService

logger = logging.getLogger('sad_intern_import')


class SadInternImportService(BaseImportService):
    """ Сервисный класс, отвечающий за логику импорта 'грустящих' студентов из .csv или .xlsx файлов. """

    logger = logging.getLogger('sad_intern_import')

    def _make_unique_key(self, intern_id):
        """Создает уникальный ключ для проверки дубликатов."""
        return intern_id

    def _load_existing_keys(self):
        """Загружает существующих 'грустящих' из БД в память."""
        existing_sad_interns = SadIntern.objects.values_list('intern_id', flat=True)
        existing_keys = set(existing_sad_interns)
        return existing_keys

    def _map_status(self, status_name):
        """ Применяет маппинг к статусу. """
        if not status_name:
            return None
        return SAD_INTERN_STATUS_MAPPING.get(status_name.strip(), None)

    def _process_row(self, row, index, existing_keys):
        """
        Обрабатывает одну строку данных 'грустящего'.
        Возвращает True, если строка была успешно создана.
        """
        try:
            # ОПТИМИЗАЦИЯ: Используем новые универсальные методы из BaseImportService
            full_name = self._get_string_field(row, 'full_name')
            waiting_since_str = self._get_string_field(row, 'waiting_since')
            telegram_username = self._get_string_field(row, 'telegram_username')
            manager_name = self._get_string_field(row, 'manager_name')
            status_name = self._get_string_field(row, 'status')
            note = self._get_string_field(row, 'note')

            # Пропускаем пустые строки
            if not full_name and not waiting_since_str and not telegram_username and not manager_name and not status_name and not note:
                return True  # Пропускаем пустую строку

            # Проверяем, не является ли строка заголовком месяца (например, "JAVA")
            # В данном случае, в файле заголовки направлений (JAVA, PYTHON) — их можно игнорировать
            # или использовать для фильтрации в будущем. Пока пропускаем.
            if full_name.upper() in MONTH_NAME_TO_NUMBER or full_name.upper() in ['JAVA', 'PYTHON', 'GO', 'СИСТЕМНЫЙ АНАЛИТИК']:
                logger.info(f"Найден заголовок направления/месяца: {full_name}")
                return True  # Пропускаем строку заголовка

            # Обработка полей
            if not full_name:
                self._log_error(f"ФИО не указано для строки {index + 2}.", index)
                return False

            if not waiting_since_str:
                self._log_error(f"Дата ожидания не указана для строки {index + 2}.", index)
                return False

            # Парсим дату
            from datetime import datetime
            try:
                waiting_since = datetime.strptime(waiting_since_str, "%d.%m.%Y").date()
            except ValueError:
                self._log_error(f"Неверный формат даты '{waiting_since_str}' в строке {index + 2}. Ожидается ДД.ММ.ГГГГ.", index)
                return False

            # Обработка студента
            intern, success = self._get_intern(full_name, index, required=True)
            if not success:
                return False

            # Обработка Telegram
            if telegram_username:
                if not telegram_username.startswith('@'):
                    telegram_username = '@' + telegram_username

            # Обработка менеджера
            # Если менеджер указан, он должен быть найден, иначе - ошибка
            manager_email = None
            if manager_name:
                manager_email, success = self._get_manager_email(manager_name, index, required=True)
                if not success:
                    return False

            # Обработка статуса
            status_code = self._map_status(status_name)
            if status_name and not status_code:
                self._log_error(f"Статус '{status_name}' не распознан для строки {index + 2}.", index)
                return False

            # Проверка существования через set в памяти
            unique_key = self._make_unique_key(intern.id)

            if unique_key in existing_keys:
                # Запись уже существует - пропускаем
                self._log_skip()
                return False

            # Создание записи
            SadIntern.objects.create(
                intern=intern,
                waiting_since=waiting_since,
                telegram_username=telegram_username or None,
                manager_email=manager_email,
                status=status_code,
                note=note or None,
            )

            # Добавляем ключ в set чтобы избежать дублей внутри файла
            existing_keys.add(unique_key)

            self.created_count += 1
            return True

        except Exception as e:
            self._log_error(f"Ошибка при обработке строки {index + 2}: {e}", index)
            return False

    def run(self):
        """Запускает процесс импорта 'грустящих'."""
        self._load_reference_data()

        total_rows = len(self.df)

        # Загружаем существующие ключи в память для быстрой проверки
        logger.info("Загрузка существующих 'грустящих' из БД...")
        existing_keys = self._load_existing_keys()
        logger.info(f"Загружено {len(existing_keys)} существующих 'грустящих'.")

        logger.info(f"Начинаю обработку {total_rows} строк 'грустящих'.")

        for index, row in self.df.iterrows():
            success = self._process_row(row, index, existing_keys)

            # Обновляем прогресс для Celery
            if self.progress_callback:
                self.progress_callback(index + 1, total_rows)

            if not success:
                continue  # Пропускаем строку

        logger.info(
            f"Обработка 'грустящих' завершена. "
            f"Создано: {self.created_count}, Дубликатов: {self.duplicates_count}, Ошибок: {self.skipped_count}."
        )
        return self.created_count, self.skipped_count, self.duplicates_count, self.errors_log
