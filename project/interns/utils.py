import re
import logging
import pandas as pd

from core.constants import MAX_URL_LENGTH, TYPE_OF_TRAINING_MAPPING
from core.date_utils import parse_date  # noqa: F401
from core.file_utils import truncate_string, clean_field as clean_hr_field  # noqa: F401

logger = logging.getLogger('intern_import')

_SAFE_URL_SCHEMES = ('http://', 'https://')


def sanitize_url(value, field_name, row_index):
    """
    Проверяет, что URL начинается с безопасной схемы (http/https).
    При нарушении логирует предупреждение и возвращает None.
    Пустые значения пропускаются.
    """
    if not value:
        return value or None
    if not any(value.startswith(s) for s in _SAFE_URL_SCHEMES):
        logger.warning(
            f"Строка {row_index + 2}: поле '{field_name}' содержит небезопасный URL, поле очищено."
        )
        return None
    return value


def normalize_url_raw(value):
    """Нормализует сырое значение URL из CSV (пробелы, экранирование)."""
    if pd.isna(value) or value is None:
        return ''
    text = str(value).strip()
    if not text or text.lower() == 'nan':
        return ''
    return text.replace('\\+', '+')


def resolve_cv_from_row(row, row_index):
    """
    Возвращает CV из строки импорта: приоритет колонке cv, затем cv_au (CV (ау)).
    """
    for field_name, raw_key in (('cv', 'cv'), ('cv', 'cv_au')):
        raw = normalize_url_raw(row.get(raw_key, ''))
        if not raw:
            continue
        truncated = truncate_string(raw, MAX_URL_LENGTH)
        url = sanitize_url(truncated, field_name, row_index)
        if url:
            return url
    return None


def resolve_url_field(row, field_key, field_name, row_index):
    """Нормализует URL-поле (legend и т.п.) из строки импорта."""
    raw = normalize_url_raw(row.get(field_key, ''))
    if not raw:
        return None
    truncated = truncate_string(raw, MAX_URL_LENGTH)
    return sanitize_url(truncated, field_name, row_index)


def is_field_empty(value):
    """Пустое значение поля для merge-синхронизации."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def fill_if_empty(instance, field, new_value):
    """
    Заполняет поле модели, если на сайте оно пустое, а в источнике есть значение.
    Возвращает True, если поле изменено.
    """
    if is_field_empty(new_value):
        return False
    if not is_field_empty(getattr(instance, field)):
        return False
    setattr(instance, field, new_value)
    return True


def extract_email_from_string(contact_str):
    """
    Извлекает первый найденный email из строки.
    """
    if pd.isna(contact_str):
        return None

    contact_str = str(contact_str)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    found_emails = re.findall(email_pattern, contact_str)
    if found_emails:
        return found_emails[0]
    return None


def normalize_type_of_training(raw_label):
    """ Нормализует строку типа обучения к внутреннему значению. """

    raw_label = str(raw_label).strip()
    normalized = ','.join([x.strip().lower() for x in raw_label.split(',')])

    if normalized in TYPE_OF_TRAINING_MAPPING:
        return TYPE_OF_TRAINING_MAPPING[normalized], None
    error_msg = f"Тип обучения '{raw_label}' не является допустимым."
    logger.warning(error_msg)
    return None, error_msg
