"""
Тесты для утилит приложения debts.

Используются маркеры pytest:
- @pytest.mark.utils - для группировки тестов утилит
"""
import pytest
import pandas as pd

from debts.utils import parse_money_string, find_payment_columns


@pytest.mark.utils
class TestParseMoneyString:
    """Тесты для функции parse_money_string."""

    @pytest.mark.parametrize('input_val, expected', [
        ('1000',              1000.0),
        ('1234.56',           1234.56),
        ('1 000 000',         1000000.0),
        ('1,000,000',         1000000.0),
        ('1234,56',           1234.56),
        ('1000 руб.',         1000.0),
        ('5000 р',            5000.0),
        ('не число',          0.0),
        ('0',                 0.0),
        ('',                  0.0),
        ('None',              0.0),
        ('nan',               0.0),
        ('руб.',              0.0),
        ('   ',               0.0),
        ('5',                 5.0),
        ('12345',             12345.0),
        ('1000.00',           1000.0),
        ('0001000',           1000.0),
        ('0.01',              0.01),
        ('999999999999.99',   999999999999.99),
        (pd.NA,               0.0),
        (pd.NaT,              0.0),
        (1234.56,             1234.56),
        (1000,                1000.0),
        (True,                0.0),
        ('1\u00a0000\u00a0000', 1000000.0),
        ('1.234,56',          1234.56),
        ('1,234.56',          1234.56),
        ('1 234 567,89 руб.', 123456789.0),
        ('$1,000.50',         1000.5),
    ])
    def test_parse(self, input_val, expected):
        """Парсинг различных форматов сумм."""
        assert parse_money_string(input_val) == expected

    @pytest.mark.parametrize('input_val, allowed_values', [
        ('1.000.000', (1000.0, 1000000.0)),
        ('-1000',     (0.0, -1000.0, 1000.0)),
        ('.50',       (0.0, 0.5, 50.0)),
        ('abc123def', (0.0, 123.0)),
        ('1.23.45',   None),
    ])
    def test_parse_ambiguous(self, input_val, allowed_values):
        """Форматы с неоднозначной интерпретацией — функция должна вернуть число."""
        result = parse_money_string(input_val)
        assert isinstance(result, float), f"Ожидался float, получен {type(result)}"
        if allowed_values is not None:
            assert result in allowed_values, f"Неожиданный результат {result} для '{input_val}'"

    @pytest.mark.parametrize('input_val, expected', [
        ('1000 руб.',  1000.0),
        ('2000 р.',    2000.0),
        ('3000р',      3000.0),
        ('4000 RUB',   4000.0),
    ])
    def test_parse_currency_variants(self, input_val, expected):
        """Парсинг различных обозначений рубля."""
        assert parse_money_string(input_val) == expected


@pytest.mark.utils
class TestFindPaymentColumns:
    """Тесты для функции find_payment_columns."""

    @pytest.mark.parametrize('columns, expected_found, expected_missing', [
        (
            ['01/25', '02/25', '03/25', 'ФИО', 'Email'],
            ['01/25', '02/25', '03/25'],
            ['ФИО', 'Email'],
        ),
        (
            ['2024', '2025', 'ФИО', 'Email'],
            ['2024', '2025'],
            ['ФИО', 'Email'],
        ),
        (
            ['01/25', '02/25', '2024', '2025', 'ФИО'],
            ['01/25', '02/25', '2024', '2025'],
            ['ФИО'],
        ),
        (
            ['ФИО', 'Email', 'Телефон', 'Направление'],
            [],
            ['ФИО', 'Email'],
        ),
    ])
    def test_find_columns(self, columns, expected_found, expected_missing):
        """Функция находит платёжные столбцы и не находит посторонние."""
        result = find_payment_columns(columns)
        assert all(col in result for col in expected_found)
        assert all(col not in result for col in expected_missing)

    @pytest.mark.parametrize('invalid_col, valid_col', [
        ('1/25', '01/25'),
        ('01/5', '01/25'),
        ('a01/25', '01/25'),
        ('01/25b', '03/25'),
        ('01-25', '01/25'),
        ('01.25', '01/25'),
        ('201', '2021'),
        ('20211', '2021'),
        ('01/25!', '03/25'),
        ('@02/25', '03/25'),
    ])
    def test_invalid_formats_not_found(self, invalid_col, valid_col):
        """Невалидные форматы не попадают в результат."""
        result = find_payment_columns([invalid_col, valid_col])
        assert invalid_col not in result
        assert valid_col in result

    @pytest.mark.parametrize('col', ['00/25', '01/25', '12/25', '13/25', '99/25'])
    def test_find_mm_yy_accepts_any_digits(self, col):
        """Паттерн MM/YY не валидирует значения, только формат."""
        columns = ['00/25', '01/25', '12/25', '13/25', '99/25']
        result = find_payment_columns(columns)
        assert col in result

    @pytest.mark.parametrize('col', [f'{i:02d}/25' for i in range(1, 13)])
    def test_find_all_months(self, col):
        """Все 12 месяцев распознаются."""
        columns = [f'{i:02d}/25' for i in range(1, 13)]
        result = find_payment_columns(columns)
        assert len(result) == 12
        assert col in result

    @pytest.mark.parametrize('year', ['2020', '2021', '2022', '2023', '2024', '2025'])
    def test_find_multiple_years(self, year):
        """Несколько четырёхзначных годов распознаются."""
        years = ['2020', '2021', '2022', '2023', '2024', '2025']
        result = find_payment_columns(years)
        assert len(result) == 6
        assert year in result

    def test_empty_list_returns_empty(self):
        """Пустой список — пустой результат."""
        assert len(find_payment_columns([])) == 0

    def test_pandas_index_supported(self):
        """Принимает pandas Index."""
        result = find_payment_columns(pd.Index(['01/25', '02/25', 'ФИО']))
        assert '01/25' in result
        assert '02/25' in result
        assert 'ФИО' not in result

    def test_pandas_index_with_numeric_values(self):
        """pandas Index с числовыми значениями обрабатывается без ошибок."""
        result = find_payment_columns(pd.Index([1, 2, 3, '01/25', '02/25']))
        assert '01/25' in result
        assert '02/25' in result

    def test_find_with_none_values_in_list(self):
        """None в списке столбцов не вызывает исключение, валидные столбцы распознаются."""
        result = find_payment_columns(['01/25', None, '02/25'])
        assert '01/25' in result
        assert '02/25' in result
