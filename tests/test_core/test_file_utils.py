"""
Тесты для core/file_utils.py.

Покрывает:
- read_file_content: чтение CSV и XLSX, проверка размера, неподдерживаемые форматы
- rename_columns: переименование столбцов DataFrame по маппингу
- validate_required_columns: проверка обязательных столбцов с маппингом и без
- truncate_string: обрезка строк, обработка NaN и числовых значений
- clean_field: нормализация строк, обработка 'nan', None, NaN
"""
import math
from io import BytesIO

import pandas as pd
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from core.file_utils import clean_field, read_file_content, rename_columns, truncate_string, validate_required_columns


def _make_xlsx_bytes(data: dict) -> bytes:
    """Создаёт XLSX-файл в памяти из словаря {колонка: [значения]}."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    columns = list(data.keys())
    ws.append(columns)
    for row in zip(*data.values()):
        ws.append(list(row))
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestReadFileContent:
    """Тесты для функции read_file_content."""

    def test_csv_returns_dataframe_with_correct_columns(self):
        """CSV-файл с заголовком читается в DataFrame с нужными столбцами."""
        csv_content = b'name,age\n\xd0\x98\xd0\xb2\xd0\xb0\xd0\xbd,25\n'
        uploaded = SimpleUploadedFile('test.csv', csv_content, content_type='text/csv')
        df = read_file_content(uploaded)
        assert list(df.columns) == ['name', 'age']
        assert len(df) == 1

    def test_xlsx_returns_dataframe(self):
        """XLSX-файл читается в DataFrame корректно."""
        xlsx_bytes = _make_xlsx_bytes({'Имя': ['Пётр'], 'Возраст': [30]})
        xlsx_content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        uploaded = SimpleUploadedFile('test.xlsx', xlsx_bytes, content_type=xlsx_content_type)
        df = read_file_content(uploaded)
        assert list(df.columns) == ['Имя', 'Возраст']
        assert len(df) == 1

    def test_file_exceeds_size_limit_raises_value_error(self):
        """Файл, превышающий лимит, вызывает ValueError с описанием размера."""
        csv_content = b'a,b\n1,2\n'
        uploaded = SimpleUploadedFile('big.csv', csv_content, content_type='text/csv')
        with pytest.raises(ValueError, match='слишком большой'):
            read_file_content(uploaded, max_size_mb=0)

    def test_unsupported_format_raises_value_error(self):
        """Файл с расширением .txt вызывает ValueError о неподдерживаемом формате."""
        uploaded = SimpleUploadedFile('data.txt', b'some text', content_type='text/plain')
        with pytest.raises(ValueError, match='Неподдерживаемый формат'):
            read_file_content(uploaded)

    def test_empty_csv_raises_empty_data_error(self):
        """Пустой CSV-файл (без строк) вызывает pd.errors.EmptyDataError."""
        uploaded = SimpleUploadedFile('empty.csv', b'', content_type='text/csv')
        with pytest.raises(pd.errors.EmptyDataError, match='No columns to parse'):
            read_file_content(uploaded)


class TestRenameColumns:
    """Тесты для функции rename_columns."""

    def test_columns_in_mapping_are_renamed(self):
        """Столбцы, присутствующие в маппинге, переименовываются."""
        df = pd.DataFrame({'Имя': ['Иван'], 'Возраст': [25]})
        result = rename_columns(df, {'Имя': 'name', 'Возраст': 'age'})
        assert list(result.columns) == ['name', 'age']

    def test_columns_not_in_mapping_stay_unchanged(self):
        """Столбцы, не входящие в маппинг, остаются как есть."""
        df = pd.DataFrame({'Имя': ['Иван'], 'extra': [1]})
        result = rename_columns(df, {'Имя': 'name'})
        assert 'extra' in result.columns
        assert 'name' in result.columns

    def test_mapping_with_nonexistent_columns_no_error(self):
        """Маппинг с несуществующими столбцами не вызывает ошибок."""
        df = pd.DataFrame({'a': [1]})
        result = rename_columns(df, {'nonexistent': 'b'})
        assert list(result.columns) == ['a']

    def test_empty_mapping_returns_unchanged_df(self):
        """Пустой маппинг возвращает DataFrame без изменений."""
        df = pd.DataFrame({'x': [1], 'y': [2]})
        result = rename_columns(df, {})
        assert list(result.columns) == ['x', 'y']


class TestValidateRequiredColumns:
    """Тесты для функции validate_required_columns."""

    @pytest.mark.parametrize('required,columns,expected_ok,expected_missing', [
        (['name', 'age'], ['name', 'age', 'extra'], True, []),
        (['name', 'age'], ['name'], False, ['age']),
        ([], ['name'], True, []),
    ])
    def test_without_mapping(self, required, columns, expected_ok, expected_missing):
        """Проверка без маппинга: True когда все столбцы есть, False если нет."""
        df = pd.DataFrame(columns=columns)
        ok, missing = validate_required_columns(df, required)
        assert ok is expected_ok
        assert missing == expected_missing

    def test_without_mapping_missing_columns_listed(self):
        """Без маппинга отсутствующие столбцы перечислены в результате."""
        df = pd.DataFrame(columns=['name'])
        ok, missing = validate_required_columns(df, ['name', 'age'])
        assert ok is False
        assert 'age' in missing

    def test_with_mapping_all_present(self):
        """С маппингом — все обязательные поля найдены → (True, [])."""
        df = pd.DataFrame(columns=['Имя', 'Возраст'])
        mapping = {'Имя': 'name', 'Возраст': 'age'}
        ok, missing = validate_required_columns(df, ['name', 'age'], column_mapping=mapping)
        assert ok is True
        assert missing == []

    def test_with_mapping_missing_column(self):
        """С маппингом — отсутствует один столбец → (False, ['Возраст'])."""
        df = pd.DataFrame(columns=['Имя'])
        mapping = {'Имя': 'name', 'Возраст': 'age'}
        ok, missing = validate_required_columns(df, ['name', 'age'], column_mapping=mapping)
        assert ok is False
        assert missing == ['Возраст']


class TestTruncateString:
    """Тесты для функции truncate_string."""

    @pytest.mark.parametrize('value,max_length,expected', [
        ('abcdef', 3, 'abc'),
        ('ab', 10, 'ab'),
        (12345, 3, '123'),
        ('abc', 3, 'abc'),
    ])
    def test_truncate_and_passthrough(self, value, max_length, expected):
        """Строка длиннее лимита обрезается; короче или равна — без изменений."""
        assert truncate_string(value, max_length) == expected

    @pytest.mark.parametrize('nan_val', [None, math.nan, float('nan')])
    def test_nan_and_none_return_default(self, nan_val):
        """None и NaN возвращают default."""
        assert truncate_string(nan_val, 10) == ''

    def test_custom_default_returned_for_nan(self):
        """Кастомный default возвращается при NaN."""
        assert truncate_string(None, 10, default='N/A') == 'N/A'


class TestCleanField:
    """Тесты для функции clean_field."""

    @pytest.mark.parametrize('value', ['nan', None, float('nan'), math.nan])
    def test_nan_variants_return_default(self, value):
        """'nan', None и NaN-числа возвращают default ('')."""
        assert clean_field(value) == ''

    def test_custom_default(self):
        """Кастомный default используется при NaN."""
        assert clean_field(None, default='—') == '—'

    @pytest.mark.parametrize('value,expected', [
        ('  Привет  ', 'Привет'),
        ('  ', ''),
        ('текст', 'текст'),
    ])
    def test_string_is_stripped(self, value, expected):
        """Строка очищается от пробелов по краям."""
        assert clean_field(value) == expected

    def test_number_converted_to_string(self):
        """Числовое значение преобразуется в строку."""
        assert clean_field(42) == '42'
