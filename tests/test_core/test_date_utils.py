"""
Тесты для core/date_utils.py.

Покрывает:
- parse_date: парсинг строк дат в нескольких форматах, обработка пустых и невалидных значений
- parse_datetime_for_interview: парсинг даты и времени для собеседований, граничные случаи
- format_month_year: форматирование месяца/года в разных форматах
"""
from datetime import date, time

import math
import pytest

from core.date_utils import format_month_year, parse_date, parse_datetime_for_interview


class TestParseDate:
    """Тесты для функции parse_date."""

    @pytest.mark.parametrize('empty_val', [None, 'nan', '', '   '])
    def test_empty_values_return_none(self, empty_val):
        """Пустые, nan и None значения → (None, None)."""
        result_date, result_error = parse_date(empty_val)
        assert result_date is None
        assert result_error is None

    def test_parse_dd_mm_yyyy_format(self):
        """Формат DD.MM.YYYY парсится корректно."""
        result_date, error = parse_date('25.12.2025')
        assert error is None
        assert result_date == date(2025, 12, 25)

    def test_parse_yyyy_mm_dd_format(self):
        """Формат YYYY-MM-DD парсится корректно."""
        result_date, error = parse_date('2025-06-15')
        assert error is None
        assert result_date == date(2025, 6, 15)

    def test_parse_dd_mm_yyyy_with_time_part(self):
        """DD.MM.YYYY с временем после пробела — берётся только дата."""
        result_date, error = parse_date('01.03.2025 10:00:00')
        assert error is None
        assert result_date == date(2025, 3, 1)

    def test_parse_gmt_suffix(self):
        """Дата с GMT-суффиксом вида '25.12.2025 (GMT+3)' парсится корректно."""
        result_date, error = parse_date('25.12.2025 (GMT+3)')
        assert error is None
        assert result_date == date(2025, 12, 25)

    def test_invalid_string_returns_error_message(self):
        """Невалидная строка → (None, сообщение об ошибке)."""
        result_date, error = parse_date('not-a-date', field_name='дата_начала', row_index=2)
        assert result_date is None
        assert error is not None
        assert 'дата_начала' in error

    def test_result_type_is_date_not_datetime(self):
        """Результат — datetime.date, а не datetime."""
        result_date, _ = parse_date('2025-01-01')
        assert type(result_date) is date

    def test_pandas_nan_value(self):
        """pandas.NaN → (None, None)."""
        result_date, error = parse_date(math.nan)
        assert result_date is None
        assert error is None


class TestParseDatetimeForInterview:
    """Тесты для функции parse_datetime_for_interview."""

    @pytest.mark.parametrize('empty_val', [None, ''])
    def test_empty_date_returns_triple_none(self, empty_val):
        """Пустая дата → (None, None, None)."""
        assert parse_datetime_for_interview(empty_val) == (None, None, None)

    def test_valid_date_no_time(self):
        """Корректная дата без времени → (date, None, None)."""
        result_date, result_time, error = parse_datetime_for_interview('2025-06-01')
        assert error is None
        assert result_date == date(2025, 6, 1)
        assert result_time is None

    def test_valid_date_with_hhmm_time(self):
        """Корректная дата + время HH:MM → (date, time, None)."""
        result_date, result_time, error = parse_datetime_for_interview('2025-06-01', '14:30')
        assert error is None
        assert result_date == date(2025, 6, 1)
        assert result_time == time(14, 30)

    def test_valid_date_with_hhmmss_time(self):
        """Корректная дата + время HH:MM:SS → (date, time, None)."""
        result_date, result_time, error = parse_datetime_for_interview('2025-06-01', '09:00:30')
        assert error is None
        assert result_date == date(2025, 6, 1)
        assert result_time == time(9, 0, 30)

    def test_invalid_time_format_silently_dropped(self):
        """Некорректное время → время None, дата возвращается, ошибка None."""
        result_date, result_time, error = parse_datetime_for_interview('2025-06-01', 'invalid-time')
        assert error is None
        assert result_date == date(2025, 6, 1)
        assert result_time is None

    def test_date_before_2024_returns_error(self):
        """Дата до 2024 года → (None, None, сообщение об ошибке)."""
        result_date, result_time, error = parse_datetime_for_interview('2023-12-31')
        assert result_date is None
        assert result_time is None
        assert error is not None
        assert '2023' in error

    def test_boundary_date_2024_01_01_is_valid(self):
        """Граничная дата 2024-01-01 считается валидной."""
        result_date, result_time, error = parse_datetime_for_interview('2024-01-01')
        assert error is None
        assert result_date == date(2024, 1, 1)

    def test_invalid_date_string_returns_error(self):
        """Невалидная строка даты → (None, None, сообщение об ошибке)."""
        result_date, result_time, error = parse_datetime_for_interview('not-a-date')
        assert result_date is None
        assert result_time is None
        assert error is not None
        assert 'not-a-date' in error

    def test_dd_mm_yyyy_format_parsed(self):
        """Формат DD.MM.YYYY для parse_datetime_for_interview."""
        result_date, _, error = parse_datetime_for_interview('15.07.2025', '10:00')
        assert error is None
        assert result_date == date(2025, 7, 15)


class TestFormatMonthYear:
    """Тесты для функции format_month_year."""

    @pytest.mark.parametrize('month, year, fmt, expected', [
        (1, 2025, 'MM/YY', '01/25'),
        (12, 2025, 'MM/YY', '12/25'),
        (1, 2025, 'MM/YYYY', '01/2025'),
        (6, 2024, 'MM/YYYY', '06/2024'),
        (3, 2026, 'name_YYYY', 'Март 2026'),
        (1, 2025, 'name_YYYY', 'Январь 2025'),
        (12, 2025, 'name_YYYY', 'Декабрь 2025'),
        (1, 2025, 'unknown', '1/2025'),
    ])
    def test_format_variants(self, month, year, fmt, expected):
        """Форматирование месяца/года в разных форматах."""
        assert format_month_year(month, year, fmt) == expected

    def test_default_format_is_mm_yy(self):
        """По умолчанию используется формат MM/YY."""
        assert format_month_year(5, 2025) == '05/25'
