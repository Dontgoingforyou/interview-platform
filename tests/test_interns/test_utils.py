"""
Тесты для утилит приложения interns.

Используются маркеры pytest:
- @pytest.mark.utils - для группировки тестов утилит
"""
from datetime import date

import pytest
import pandas as pd

from interns.utils import (
    extract_email_from_string,
    fill_if_empty,
    is_field_empty,
    normalize_type_of_training,
    resolve_cv_from_row,
)


@pytest.mark.utils
class TestExtractEmailFromString:
    """Тесты для функции extract_email_from_string."""

    @pytest.mark.parametrize('input_val, expected', [
        ('test@example.com',                          'test@example.com'),
        ('Связь: user@example.com или телефон',       'user@example.com'),
        ('first@example.com и second@test.com',       'first@example.com'),
        ('Просто текст без email',                    None),
        ('',                                          None),
        ('user.name+tag@example-domain.com',          'user.name+tag@example-domain.com'),
    ])
    def test_extract_email(self, input_val, expected):
        """Извлечение email из различных строк."""
        assert extract_email_from_string(input_val) == expected

    def test_extract_email_nan(self):
        """Обработка pandas NA возвращает None."""
        assert extract_email_from_string(pd.NA) is None


@pytest.mark.utils
class TestNormalizeTypeOfTraining:
    """Тесты для функции normalize_type_of_training."""

    @pytest.mark.parametrize('input_val, expected_result, expected_error', [
        ('outstaff',        'outstaff',             None),
        ('во вне',          'external',             None),
        ('outstaff,во вне', 'external_or_outstaff', None),
        ('во вне,outstaff', 'external_or_outstaff', None),
        ('  outstaff  ',    'outstaff',             None),
        ('OUTSTAFF',        'outstaff',             None),
    ])
    def test_normalize_valid(self, input_val, expected_result, expected_error):
        """Корректные значения нормализуются без ошибок."""
        result, error = normalize_type_of_training(input_val)
        assert result == expected_result
        assert error == expected_error

    @pytest.mark.parametrize('input_val', [
        'недопустимое значение',
        '',
        'outstaff,,во вне',
    ])
    def test_normalize_invalid(self, input_val):
        """Некорректные значения возвращают None и сообщение об ошибке."""
        result, error = normalize_type_of_training(input_val)
        assert result is None
        assert error is not None


@pytest.mark.utils
class TestResolveCvFromRow:
    @pytest.mark.parametrize('cv,cv_au,expected', [
        ('https://example.com/cv', '', 'https://example.com/cv'),
        ('', 'https://example.com/cv-au', 'https://example.com/cv-au'),
        ('https://example.com/primary', 'https://example.com/au', 'https://example.com/primary'),
        ('', '', None),
    ])
    def test_resolve_cv_from_row(self, cv, cv_au, expected):
        row = pd.Series({'cv': cv, 'cv_au': cv_au})
        assert resolve_cv_from_row(row, 0) == expected


@pytest.mark.django_db(databases=['default'])
@pytest.mark.utils
class TestFillIfEmpty:
    def test_fill_if_empty_updates_blank_field(self, db, direction_python):
        from interns.models import Intern
        intern = Intern.objects.create(
            full_name='Test',
            direction=direction_python,
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            city=None,
        )
        assert fill_if_empty(intern, 'city', 'Казань') is True
        assert intern.city == 'Казань'

    def test_fill_if_empty_skips_when_filled(self, db, direction_python):
        from interns.models import Intern
        intern = Intern.objects.create(
            full_name='Test',
            direction=direction_python,
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            city='Москва',
        )
        assert fill_if_empty(intern, 'city', 'Казань') is False
        assert intern.city == 'Москва'


@pytest.mark.utils
class TestIsFieldEmpty:
    @pytest.mark.parametrize('value,expected', [
        (None, True),
        ('', True),
        ('   ', True),
        ('Москва', False),
    ])
    def test_is_field_empty(self, value, expected):
        assert is_field_empty(value) is expected
