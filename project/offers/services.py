import logging
import re

from core.constants import MONTH_NAME_TO_NUMBER
from .models import Offer
from core.base_services import BaseImportService

logger = logging.getLogger('offers_import')


class OfferImportService(BaseImportService):
    """ Сервисный класс, отвечающий за логику импорта офферов из .csv или .xlsx файлов. """

    logger = logging.getLogger('offers_import')

    def __init__(self, df, progress_callback=None):
        super().__init__(df, progress_callback)
        self.current_month = None
        self.current_year = 2025  # Если год не указан в файле — берем 2025

    def _make_unique_key(self, intern_id, month, year):
        """Создает уникальный ключ для проверки дубликатов."""
        return (intern_id, month, year)

    def _load_existing_keys(self):
        """Загружает существующие офферы из БД в память."""
        existing_offers = Offer.objects.values_list('intern_id', 'month', 'year')
        existing_keys = set()
        for row in existing_offers:
            key = self._make_unique_key(*row)
            existing_keys.add(key)
        return existing_keys

    def _process_row(self, row, index, existing_keys):
        """
        Обрабатывает одну строку данных оффера.
        Возвращает True, если строка была успешно создана.
        """
        try:
            # ОПТИМИЗАЦИЯ: Используем новые универсальные методы из BaseImportService
            full_name = self._get_string_field(row, 'full_name')
            direction_name = self._get_string_field(row, 'direction_name')
            company_name = self._get_string_field(row, 'company_name')
            amount_str = self._get_string_field(row, 'amount')

            # Пропускаем пустые строки
            if not full_name and not direction_name and not company_name and not amount_str:
                return True  # Пропускаем пустую строку

            # Проверяем, не является ли строка заголовком месяца (например, "ФЕВРАЛЬ")
            if full_name.upper() in MONTH_NAME_TO_NUMBER:
                self.current_month = MONTH_NAME_TO_NUMBER[full_name.upper()]
                logger.info(f"Найден заголовок месяца: {full_name} -> {self.current_month}")
                return True  # Пропускаем строку заголовка

            # Обработка полей
            if not full_name:
                self._log_error(f"ФИО не указано для строки {index + 2}.", index)
                return False

            if not direction_name:
                self._log_error(f"Направление не указано для строки {index + 2}.", index)
                return False

            if not company_name:
                company_name = '—'

            # Обработка суммы
            if not amount_str:
                logger.warning(f"Сумма не указана для строки {index + 2}. Ставим 0.0")
                amount = 0.0
            else:
                amount = self._parse_amount(amount_str)
                if amount is None:
                    self._log_error(f"Невозможно извлечь сумму из '{amount_str}' в строке {index + 2}.", index)
                    return False

            # Обработка направления
            direction_id, success = self._get_direction_id(direction_name, index, required=True)
            if not success:
                return False

            # Обработка студента
            intern, success = self._get_intern(full_name, index, required=True)
            if not success:
                return False

            # Обработка месяца
            if self.current_month is None:
                self._log_error(f"Неизвестный месяц для строки {index + 2}. Убедитесь, что перед строкой есть заголовок месяца (например, 'ФЕВРАЛЬ').", index)
                return False

            # Проверка существования через set в памяти
            unique_key = self._make_unique_key(intern.id, self.current_month, self.current_year)

            if unique_key in existing_keys:
                # Запись уже существует - пропускаем
                self._log_skip()
                return False

            # Создание записи
            Offer.objects.create(
                intern=intern,
                direction_id=direction_id,
                company=company_name,
                amount=amount,
                month=self.current_month,
                year=self.current_year,
            )

            # Добавляем ключ в set чтобы избежать дублей внутри файла
            existing_keys.add(unique_key)

            self.created_count += 1
            return True

        except Exception as e:
            self._log_error(f"Ошибка при обработке строки {index + 2}: {e}", index)
            return False

    def _parse_amount(self, amount_str):
        """
        Извлекает сумму из строки.
        Если в строке несколько чисел (например, '140 000/160 000'), берёт максимальное.
        """
        # Убираем всё, кроме цифр, пробелов, запятых, точек, слэшей
        cleaned = re.sub(r'[^\d\s,./\\]', '', amount_str)
        # Разбиваем по слэшу
        parts = re.split(r'[\/\\]', cleaned)
        numbers = []
        for part in parts:
            # Убираем пробелы и запятые, оставляем как одно число
            normalized = part.replace(' ', '').replace(',', '').replace(' ', '')
            if normalized:
                try:
                    num = float(normalized)
                    numbers.append(num)
                except ValueError:
                    continue

        if not numbers:
            return None

        return max(numbers)

    def run(self):
        """Запускает процесс импорта офферов."""
        self._load_reference_data()

        total_rows = len(self.df)

        # Загружаем существующие ключи в память для быстрой проверки
        logger.info("Загрузка существующих офферов из БД...")
        existing_keys = self._load_existing_keys()
        logger.info(f"Загружено {len(existing_keys)} существующих офферов.")

        logger.info(f"Начинаю обработку {total_rows} строк офферов.")

        for index, row in self.df.iterrows():
            success = self._process_row(row, index, existing_keys)

            # Обновляем прогресс для Celery
            if self.progress_callback:
                self.progress_callback(index + 1, total_rows)

            if not success:
                continue  # Пропускаем строку

        logger.info(
            f"Обработка офферов завершена. "
            f"Создано: {self.created_count}, Дубликатов: {self.duplicates_count}, Ошибок: {self.skipped_count}."
        )
        return self.created_count, self.skipped_count, self.duplicates_count, self.errors_log
