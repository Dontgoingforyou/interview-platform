import re
import logging
import pandas as pd
from datetime import datetime
from dateutil import parser

logger = logging.getLogger(__name__)


def parse_date(date_str, field_name='date', row_index=0):
    """
    Парсит строку даты в объект datetime.date.
    Пытается несколько форматов.
    """
    if pd.isna(date_str) or date_str == 'nan':
        return None, None

    date_str = str(date_str).strip()
    if not date_str:
        return None, None

    parsed_date = None

    # Пробуем разные форматы парсинга
    parse_functions = [
        lambda s: datetime.strptime(s.split(' ')[0], '%d.%m.%Y'),  # DD.MM.YYYY
        lambda s: datetime.strptime(s.split(' ')[0], '%Y-%m-%d'),  # YYYY-MM-DD
        lambda s: parser.parse(re.sub(r'\s*\(GMT[+-]\d+\)', '', s).strip()),  # С GMT
    ]

    for parse_func in parse_functions:
        try:
            parsed_date = parse_func(date_str)
            break
        except Exception:
            continue

    if parsed_date:
        if isinstance(parsed_date, datetime):
            parsed_date = parsed_date.date()
        return parsed_date, None
    else:
        error_msg = f"Невозможно распознать дату {field_name} '{date_str}' в строке {row_index + 2}."
        logger.warning(error_msg)
        return None, error_msg


def parse_datetime_for_interview(date_str, time_str=None, row_index=0):
    """
    Парсит строку даты и времени для собеседования.
    Пытается объединить дату из date_str и время из time_str.
    """
    if pd.isna(date_str) or not str(date_str).strip():
        return None, None, None

    date_str = str(date_str).strip()
    time_str = str(time_str).strip() if pd.notna(time_str) and time_str else None

    date_obj = None
    time_obj = None

    # Парсинг даты
    parse_functions = [
        lambda s: datetime.strptime(s.split(' ')[0], '%d.%m.%Y').date(),
        lambda s: datetime.strptime(s.split(' ')[0], '%Y-%m-%d').date(),
        lambda s: parser.parse(re.sub(r'\s*\(GMT[+-]\d+\)', '', s).strip()).date(),
    ]

    for parse_func in parse_functions:
        try:
            date_obj = parse_func(date_str)
            break
        except Exception:
            continue

    if date_obj is None:
        error_msg = f"Невозможно распознать дату '{date_str}' в строке {row_index + 2}."
        logger.warning(error_msg)
        return None, None, error_msg

    # Парсинг времени
    if time_str:
        try:
            time_obj = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            try:
                time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
            except ValueError:
                logger.warning(
                    f"Невозможно распознать время '{time_str}' в строке {row_index + 2}. "
                    f"Оставляем время пустым."
                )

    # Проверка диапазона дат
    if date_obj.year < 2024:
        error_msg = f"Дата '{date_obj}' в строке {row_index + 2} до 2024 года."
        logger.warning(error_msg)
        return None, None, error_msg

    return date_obj, time_obj, None


def format_month_year(month, year, format='MM/YY'):
    """
    Форматирует месяц и год для отображения.

    Args:
        month: номер месяца (1-12)
        year: год (4 цифры)
        format: формат ('MM/YY', 'MM/YYYY', 'name_YYYY')
    """
    if format == 'MM/YY':
        return f"{month:02d}/{year % 100:02d}"
    elif format == 'MM/YYYY':
        return f"{month:02d}/{year}"
    elif format == 'name_YYYY':
        from core.constants import MONTH_NAMES
        month_name = MONTH_NAMES[month - 1] if 1 <= month <= 12 else str(month)
        return f"{month_name} {year}"
    return f"{month}/{year}"
