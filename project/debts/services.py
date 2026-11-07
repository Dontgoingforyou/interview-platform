import logging
import re
import pandas as pd

from django.db import transaction

from .models import Debt, PaymentHistory
from core.base_services import BaseImportService
from core.date_utils import parse_date
from core.constants import DEBT_PAYMENT_STATUS_UNKNOWN
from .utils import parse_money_string, find_payment_columns


logger = logging.getLogger('debts_import')


class DebtImportService(BaseImportService):

    logger = logging.getLogger('debts_import')

    def _make_unique_key(self, intern_id):
        """Создает уникальный ключ для проверки дубликатов."""
        return intern_id

    def _load_existing_keys(self):
        """Загружает существующие долги из БД в память."""
        existing_debts = Debt.objects.values_list('intern_id', flat=True)
        existing_keys = set(existing_debts)
        return existing_keys

    def _load_additional_reference_data(self):
        """Загружает дополнительные справочники для долгов."""
        # Студенты теперь ищутся динамически через find_intern_by_name
        # для более гибкого поиска (не требуется точное совпадение ФИО)
        pass

    def _get_direction_id(self, direction_name, index, required=False):
        """
        Переопределяем метод для DebtImportService с required=False по умолчанию.
        Для долгов направление не обязательно.
        """
        return super()._get_direction_id(direction_name, index, required)

    def _get_payment_status(self, total_amount, paid_amount):
        """ (Опционально) Определяет payment_status на основе сумм. """
        # Пример логики: если оплачено >= общей суммы, то платит. Или по-другому.
        # Пока возвращает default
        return DEBT_PAYMENT_STATUS_UNKNOWN

    def _get_act_date(self, act_date_str_raw, index):
        """ Обрабатывает строку даты акта. """

        act_date_str = self._safe_string_strip(act_date_str_raw)
        if not act_date_str:
            return None, None

        # Проверяем, не является ли строка явно текстом, а не датой
        # Если строка слишком длинная (> 50 символов) или содержит много букв, пропускаем
        if len(act_date_str) > 50:
            logger.warning(f"Строка даты акта слишком длинная (>{len(act_date_str)} символов), пропускаем: '{act_date_str[:50]}...' в строке {index + 2}.")
            return None, None

        # Если строка содержит более 3 букв подряд (не считая короткие слова типа "GMT"), вероятно это текст
        if re.search(r'[а-яА-Яa-zA-Z]{4,}', act_date_str):
            logger.warning(f"Строка даты акта содержит много букв, вероятно это текст, пропускаем: '{act_date_str}' в строке {index + 2}.")
            return None, None

        act_date, date_error = parse_date(act_date_str, 'акта', index)
        if date_error:
            # Возвращаем предупреждение, но не считаем это фатальной ошибкой
            return None, date_error
        return act_date, None

    def _prepare_payment_history(self, debt_obj, row, full_name):
        """ Подготавливает записи PaymentHistory для bulk_create (НЕ создает в БД). """

        payment_columns = find_payment_columns(self.df.columns)
        payment_objects = []
        for col_name in payment_columns:
            amount_raw = row.get(col_name)
            if pd.notna(amount_raw) and amount_raw != 0:
                amount = parse_money_string(amount_raw)
                if amount != 0:
                    parts = col_name.split('/')
                    if len(parts) == 2:
                        try:
                            month = int(parts[0])
                            year = int('20' + parts[1])
                            payment_objects.append(PaymentHistory(
                                debt=debt_obj,
                                month=month,
                                year=year,
                                amount=amount
                            ))
                            logger.debug(f"Подготовлен платёж {amount} за {month}/{year} для {full_name}")
                        except ValueError:
                            logger.warning(f"Невозможно распознать месяц/год из названия столбца '{col_name}'.")
                    elif col_name.isdigit() and len(col_name) == 4:
                        logger.info(f"Обнаружен столбец с годом '{col_name}', пропускаем как не содержащий месячную информацию.")
        return payment_objects

    def _process_row(self, row, index, existing_keys):
        """
        Обрабатывает одну строку данных.
        Возвращает True, если строка была успешно создана.
        """
        try:
            # Используем новые универсальные методы из BaseImportService
            full_name = self._get_string_field(row, 'full_name')

            intern_obj, success = self._get_intern(full_name, index, required=True)
            if not success:
                return False

            direction_id, success = self._get_direction_id(
                self._get_string_field(row, 'direction_name'),
                index,
                required=False
            )
            if not success:
                return False  # Ошибка уже залогирована в _get_direction_id

            total_amount_raw = row.get('total_amount_raw')
            paid_amount_raw = row.get('paid_amount_raw')
            total_amount = parse_money_string(total_amount_raw) if pd.notna(total_amount_raw) else 0
            paid_amount = parse_money_string(paid_amount_raw) if pd.notna(paid_amount_raw) else 0

            act_date, warning = self._get_act_date(row.get('act_date_str'), index)
            if warning:
                logger.warning(warning)  # Не прерываем, просто логируем

            email = self._get_string_field(row, 'email')
            telegram_username = self._get_string_field(row, 'telegram_username')

            # Проверка существования через set в памяти
            unique_key = self._make_unique_key(intern_obj.id)

            if unique_key in existing_keys:
                # Запись уже существует - пропускаем
                self._log_skip()
                return False

            # Создание основной записи долга и истории платежей в одной транзакции
            payment_status = self._get_payment_status(total_amount, paid_amount)

            with transaction.atomic():
                debt_obj = Debt.objects.create(
                    direction_id=direction_id,
                    intern=intern_obj,
                    telegram_username=telegram_username,
                    email=email,
                    total_amount=total_amount,
                    paid_amount=paid_amount,
                    act_date=act_date,
                    payment_status=payment_status,
                )

                payment_history_list = self._prepare_payment_history(debt_obj, row, full_name)
                if payment_history_list:
                    PaymentHistory.objects.bulk_create(payment_history_list)

            # Добавляем ключ в set чтобы избежать дублей внутри файла
            existing_keys.add(unique_key)

            self.created_count += 1
            return True

        except Exception as e:
            self._log_error(f"Ошибка при обработке строки {index + 2}: {e}", index)
            return False

    def run(self):
        """Запускает процесс импорта долгов."""
        self._load_reference_data()

        total_rows = len(self.df)

        # Загружаем существующие ключи в память для быстрой проверки
        logger.info("Загрузка существующих долгов из БД...")
        existing_keys = self._load_existing_keys()
        logger.info(f"Загружено {len(existing_keys)} существующих долгов.")

        logger.info(f"Начинаю обработку {total_rows} строк долгов.")

        for index, row in self.df.iterrows():
            success = self._process_row(row, index, existing_keys)

            # Обновляем прогресс для Celery
            if self.progress_callback:
                self.progress_callback(index + 1, total_rows)

            if not success:
                continue  # Пропускаем строку

        logger.info(
            f"Обработка долгов завершена. "
            f"Создано: {self.created_count}, Дубликатов: {self.duplicates_count}, Ошибок: {self.skipped_count}."
        )
        return self.created_count, self.skipped_count, self.duplicates_count, self.errors_log
