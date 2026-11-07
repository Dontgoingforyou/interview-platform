import logging
import re
from django.db import connection
from directions.models import Direction
import pandas as pd
from companies.models import Company
from core.constants import DIRECTION_MAPPING, MANAGER_MAPPING, MANAGER_TC_MAPPING

logger = logging.getLogger(__name__)


class BaseImportService:
    """
    Базовый класс для сервисов импорта данных.
    Содержит общую логику для всех import services.
    """

    # Атрибут класса, переопределяется в подклассах
    logger = logger

    def __init__(self, df, progress_callback=None):
        self.df = df
        self.progress_callback = progress_callback
        self.errors_log = []
        self.created_count = 0
        self.skipped_count = 0  # Ошибки (невалидные данные)
        self.duplicates_count = 0  # Дубликаты (уже есть в БД)

    def _load_reference_data(self):
        """
        Загружает справочники из БД.
        Переопределяется в подклассах для загрузки специфичных справочников.
        """
        self.logger.info("Загрузка справочников из БД...")
        try:
            # Базовые справочники, которые используются во многих сервисах
            self.directions_map = self._load_directions()
            self.managers_map = self._load_managers()

            # Кэш студентов — предзагружается один раз для всех import services,
            # чтобы избежать N+1 запросов в find_intern_by_name внутри цикла обработки строк
            self.interns_cache = self._load_interns_cache()

            # Дополнительные справочники (переопределяются в подклассах)
            self._load_additional_reference_data()

            self.logger.info(
                f"Загружено: Направлений - {len(self.directions_map)}, "
                f"Менеджеров - {len(self.managers_map)}, "
                f"Студентов - {len(self.interns_cache)}"
            )
        except Exception as e:
            self.logger.error(
                f"Критическая ошибка при загрузке справочников: {e}. "
                f"Тип ошибки: {type(e).__name__}"
            )
            raise

    def _load_interns_cache(self):
        """Загружает всех студентов одним запросом для поиска в памяти."""
        from interns.models import Intern
        return list(Intern.objects.all())

    def _load_directions(self):
        """Загружает направления из основной БД."""
        return {d.name: d.id for d in Direction.objects.all()}

    def _load_managers(self):
        """
        Загружает менеджеров из основной БД (SSO/Keycloak).
        Возвращает два маппинга:
        - full_name -> email (для поиска по ФИО)
        - username -> email (для поиска по username)
        """
        from managers.models import Manager

        managers = Manager.objects.filter(is_active=True)

        # Создаём маппинг full_name -> email
        full_name_map = {m.full_name: m.email for m in managers}

        # Создаём маппинг username -> email из констант
        from core.constants import MANAGER_EMAIL_MAPPING
        username_map = MANAGER_EMAIL_MAPPING.copy()

        # Объединяем оба маппинга для обратной совместимости
        # Приоритет отдаём маппингу по full_name
        return {**username_map, **full_name_map}

    def _load_companies(self):
        """Загружает компании из основной БД."""
        return {c.name: c.id for c in Company.objects.all()}

    def _load_additional_reference_data(self):
        """
        Переопределение метода для загрузки дополнительных справочников.
        Вызывается после загрузки базовых справочников.
        """
        pass

    def _map_direction_name(self, name, mapping=None):
        """ Применяет маппинг к названию направления. """
        if not name:
            return None
        mapping = mapping or DIRECTION_MAPPING
        return mapping.get(name, name)

    def _map_manager_name(self, name, mapping=None):
        """ Применяет маппинг к имени менеджера. """
        if not name:
            return None
        name = str(name).strip()
        mapping = mapping or MANAGER_MAPPING
        return mapping.get(name, name)

    def _map_manager_tc_name(self, name):
        """ Применяет маппинг к имени менеджера для TC (Training Center). """
        if not name:
            return None
        name = str(name).strip()
        return MANAGER_TC_MAPPING.get(name, name)

    def _reset_table(self, model, table_name, sequence_name=None):
        """ Очищает таблицу и сбрасывает ID. """
        self.logger.info(f"Начинаю очистку таблицы {table_name} перед импортом.")
        deleted_count, _ = model.objects.all().delete()
        self.logger.info(f"Удалено {deleted_count} старых записей из {table_name}.")

        if sequence_name is None:
            sequence_name = f"{table_name}_id_seq"

        if not re.match(r'^[a-zA-Z0-9_]+$', sequence_name):
            self.logger.error(f"Недопустимое имя последовательности: {sequence_name}")
            raise ValueError(f"Недопустимое имя последовательности: {sequence_name}")

        self.logger.info(f"Сбрасываю счетчик ID таблицы {table_name}.")
        with connection.cursor() as cursor:

            cursor.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1;")
        self.logger.info("Счетчик ID сброшен.")

    def _reset_multiple_tables(self, models_with_sequences):
        """
        Очищает несколько связанных таблиц и сбрасывает их ID.
        Порядок важен - сначала удаляются зависимые таблицы.
        """
        for model, table_name, sequence_name in models_with_sequences:
            self._reset_table(model, table_name, sequence_name)

    def _log_error(self, message, index):
        """Логирует ошибку и увеличивает счетчик пропущенных записей."""
        self.logger.error(message)
        self.errors_log.append(message)
        self.skipped_count += 1

    def _log_success(self):
        """Увеличивает счетчик созданных записей."""
        self.created_count += 1

    def _log_skip(self):
        """Увеличивает счетчик дубликатов (запись уже существует в БД)."""
        self.duplicates_count += 1

    def _safe_string_strip(self, value, default=''):
        """
        Безопасно приводит значение к строке, убирает пробелы.
        Заменяет 'nan', 'None', '<NA>' и пустые строки на default.

        Args:
            value: значение для обработки
            default: значение по умолчанию
        """
        if pd.isna(value):
            return default
        str_val = str(value).strip()
        if str_val in ['nan', 'None', '<NA>', '', 'NaT']:
            return default
        return str_val

    def _get_string_field(self, row, field_name, default='', max_length=None):
        """
        Безопасно извлекает строковое поле из row.

        Args:
            row: строка DataFrame
            field_name: имя поля
            default: значение по умолчанию
            max_length: максимальная длина (если указано, обрезает)

        """
        value = self._safe_string_strip(row.get(field_name), default)
        if max_length and len(value) > max_length:
            value = value[:max_length]
        return value

    def _get_intern(self, full_name, index, required=True):
        """
        Универсальный метод поиска Intern по имени.

        Args:
            full_name: ФИО для поиска
            index: индекс строки (для логирования)
            required: если True, логирует ошибку при отсутствии

        """
        from core.intern_utils import find_intern_by_name

        if not full_name:
            if required:
                self._log_error(f"Пустое ФИО в строке {index + 2}.", index)
            return None, False

        interns_cache = getattr(self, 'interns_cache', None)
        intern_obj = find_intern_by_name(full_name, interns_cache=interns_cache)
        if intern_obj is None and required:
            self._log_error(
                f"Студент с ФИО '{full_name}' не найден в БД для строки {index + 2}.",
                index
            )
            return None, False

        return intern_obj, (intern_obj is not None)

    def _get_direction_id(self, direction_name, index, required=True):
        """
        Универсальный метод получения direction_id по названию.

        Args:
            direction_name: название направления
            index: индекс строки (для логирования)
            required: если True, логирует ошибку при отсутствии
        """
        if not direction_name:
            if required:
                self._log_error(f"Пустое направление в строке {index + 2}.", index)
                return None, False
            # Если не обязательно - просто возвращаем None без логирования
            return None, True  # Успех, но direction_id = None

        mapped_name = self._map_direction_name(direction_name)
        direction_id = self.directions_map.get(mapped_name)

        if direction_id is None:
            if required:
                self._log_error(
                    f"Направление '{direction_name}' (-> '{mapped_name}') "
                    f"не найдено в БД для строки {index + 2}.",
                    index
                )
                return None, False
            else:
                # Для необязательных направлений логируем warning, но не считаем ошибкой
                self.logger.warning(
                    f"Направление '{direction_name}' (-> '{mapped_name}') "
                    f"не найдено в БД для строки {index + 2}. Создаю запись без направления."
                )
                return None, True

        return direction_id, True

    def _get_manager_email(self, manager_name, index, required=False, use_tc_mapping=False):
        """
        Универсальный метод получения manager_email по имени (для SSO).
        Преобразует имя → username → email используя маппинги и таблицу managers.
        """
        if not manager_name:
            if required:
                self._log_error(f"Пустое имя менеджера в строке {index + 2}.", index)
                return None, False
            return None, True

        # Шаг 1: Имя → username (применяем соответствующий маппинг)
        if use_tc_mapping:
            mapped_name = self._map_manager_tc_name(manager_name)
        else:
            mapped_name = self._map_manager_name(manager_name)

        if not mapped_name:
            if required:
                self._log_error(
                    f"Менеджер '{manager_name}' не найден в маппинге для строки {index + 2}.",
                    index
                )
                return None, False
            else:
                self.logger.warning(
                    f"Менеджер '{manager_name}' не найден в маппинге для строки {index + 2}. "
                    f"Оставляем manager_email пустым."
                )
                return None, True

        # Шаг 2: username/full_name → email (используем загруженный справочник)
        manager_email = self.managers_map.get(mapped_name)

        if manager_email is None:
            if required:
                self._log_error(
                    f"Email для менеджера '{manager_name}' (маппинг: '{mapped_name}') "
                    f"не найден в системе для строки {index + 2}.",
                    index
                )
                return None, False
            else:
                self.logger.warning(
                    f"Email для менеджера '{manager_name}' (маппинг: '{mapped_name}') "
                    f"не найден в системе для строки {index + 2}. Оставляем manager_email пустым."
                )
                return None, True

        return manager_email, True

    def _run_import_loop(self, total_rows, log_message):
        """
        Общая логика цикла обработки строк с обновлением прогресса.
        """
        self.logger.info(log_message)

        for index, row in self.df.iterrows():
            success = self._process_row(row, index)

            # Обновляем прогресс для Celery
            if self.progress_callback:
                self.progress_callback(index + 1, total_rows)

            if not success:
                continue  # Пропускаем строку

    def run(self):
        """
        Запускает процесс импорта.
        Переопределяется в подклассах.
        """
        raise NotImplementedError("Subclasses must implement run()")
