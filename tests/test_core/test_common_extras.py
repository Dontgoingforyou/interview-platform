"""
Тесты для core/templatetags/common_extras.py.

Покрывает:
- get_item: получение значения из словаря, поддержка объектов с .name
- get_month_name: название месяца по номеру, граничные случаи
- starts_with_page_prefix: проверка префикса 'page_'
- get_range: создание диапазона, обработка некорректных значений
- aliases_preview: превью псевдонимов с ограничением по символам
- is_active_url: проверка активного URL по списку имён
- metric_percent, metric_percent_ratio: проценты для SSR метрик
- format_subtitle_count, format_days: подписи метрик
- decimal_dot, metric_currency: числа и рубли для SSR
"""
import pytest

from core.templatetags.common_extras import (
    aliases_preview,
    decimal_dot,
    format_days,
    format_subtitle_count,
    get_item,
    get_month_name,
    get_range,
    is_active_url,
    metric_currency,
    metric_percent,
    metric_percent_ratio,
    starts_with_page_prefix,
    transliterate_name,
)


class SimpleObj:
    """Вспомогательный объект с атрибутом name для тестирования get_item."""

    def __init__(self, name):
        self.name = name


class TestGetItem:
    """Тесты для фильтра get_item."""

    def test_returns_plain_value(self):
        """Значение без атрибута name возвращается как есть."""
        assert get_item({'key': 'value'}, 'key') == 'value'

    def test_returns_name_attribute_when_present(self):
        """Если значение имеет атрибут name — возвращается obj.name."""
        obj = SimpleObj('Направление А')
        assert get_item({'dir': obj}, 'dir') == 'Направление А'

    def test_missing_key_returns_none(self):
        """Отсутствующий ключ → None."""
        assert get_item({'a': 1}, 'b') is None

    @pytest.mark.parametrize('bad_dict,bad_key', [
        (None, 'key'),
        ({}, None),
        (None, None),
    ])
    def test_none_dict_or_key_returns_none(self, bad_dict, bad_key):
        """None-словарь или None-ключ → None."""
        assert get_item(bad_dict, bad_key) is None

    def test_integer_key(self):
        """Целочисленный ключ работает корректно."""
        assert get_item({1: 'один'}, 1) == 'один'


class TestGetMonthName:
    """Тесты для фильтра get_month_name."""

    @pytest.mark.parametrize('month_num,expected', [
        (1, 'Январь'),
        (2, 'Февраль'),
        (3, 'Март'),
        (4, 'Апрель'),
        (5, 'Май'),
        (6, 'Июнь'),
        (7, 'Июль'),
        (8, 'Август'),
        (9, 'Сентябрь'),
        (10, 'Октябрь'),
        (11, 'Ноябрь'),
        (12, 'Декабрь'),
    ])
    def test_valid_months(self, month_num, expected):
        """Числа 1–12 возвращают корректные русские названия месяцев."""
        assert get_month_name(month_num) == expected

    @pytest.mark.parametrize('bad_val', [13, None, 'abc', ''])
    def test_invalid_values_return_dash(self, bad_val):
        """Некорректные значения (13, None, строки) → '—'."""
        assert get_month_name(bad_val) == '—'

    @pytest.mark.parametrize('index,expected', [
        (0, 'Декабрь'),
        (-1, 'Ноябрь'),
    ])
    def test_zero_and_negative_use_python_list_wrapping(self, index, expected):
        """0 и отрицательные числа используют Python-индексацию с конца списка."""
        assert get_month_name(index) == expected

    def test_string_digit_is_parsed(self):
        """Строковое числовое значение '6' парсится как номер месяца."""
        assert get_month_name('6') == 'Июнь'


class TestStartsWithPagePrefix:
    """Тесты для фильтра starts_with_page_prefix."""

    @pytest.mark.parametrize('value,expected', [
        ('page_1', True),
        ('page_', True),
        ('page_something', True),
        ('paginator', False),
        ('', False),
        ('PAGE_1', False),
        (123, False),
        (None, False),
    ])
    def test_prefix_detection(self, value, expected):
        """Строки с префиксом 'page_' → True, остальные → False."""
        assert starts_with_page_prefix(value) is expected


class TestGetRange:
    """Тесты для фильтра get_range."""

    @pytest.mark.parametrize('value,expected', [
        (5, range(5)),
        ('3', range(3)),
        (0, range(0)),
        ('0', range(0)),
    ])
    def test_valid_values(self, value, expected):
        """Числа и строковые числа → корректный range."""
        assert get_range(value) == expected

    @pytest.mark.parametrize('bad_val', [None, 'abc', ''])
    def test_invalid_values_return_empty(self, bad_val):
        """Некорректные значения (None, строки) → []."""
        assert list(get_range(bad_val)) == []

    def test_float_truncates_to_int(self):
        """Вещественное число 3.7 усекается до int(3) и возвращает range(3)."""
        assert get_range(3.7) == range(3)


class TestAliasesPreview:
    """Тесты для фильтра aliases_preview."""

    def test_empty_list_returns_empty_string(self):
        """Пустой список → ''."""
        assert aliases_preview([]) == ''

    def test_none_returns_empty_string(self):
        """None → ''."""
        assert aliases_preview(None) == ''

    def test_single_alias_no_separator(self):
        """Один элемент возвращается без разделителей и суффикса."""
        result = str(aliases_preview(['Alpha']))
        assert 'Alpha' in result
        assert 'ещё' not in result

    def test_short_list_all_visible(self):
        """Короткий список — все элементы умещаются, суффикса нет."""
        result = str(aliases_preview(['A', 'B', 'C'], char_limit=80))
        assert 'A' in result
        assert 'B' in result
        assert 'C' in result
        assert 'ещё' not in result

    def test_long_list_shows_remaining_count(self):
        """Длинный список — часть скрывается, появляется '+ ещё N'."""
        aliases = ['Первый длинный псевдоним', 'Второй длинный псевдоним', 'Третий длинный псевдоним']
        result = str(aliases_preview(aliases, char_limit=20))
        assert 'ещё' in result

    def test_all_fit_exactly(self):
        """Список ровно умещающийся в лимит не имеет суффикса."""
        result = str(aliases_preview(['abc', 'de'], char_limit=8))
        assert 'ещё' not in result

    def test_special_chars_are_escaped(self):
        """Специальные HTML-символы экранируются."""
        result = str(aliases_preview(['<script>']))
        assert '<script>' not in result
        assert '&lt;script&gt;' in result


class TestMetricPercent:
    """Тесты для фильтра metric_percent (SSR метрики)."""

    @pytest.mark.parametrize('value,expected', [
        (50.0, '50.0%'),
        (0, '0.0%'),
        (100, '100.0%'),
        (33.333, '33.3%'),
    ])
    def test_valid_values(self, value, expected):
        """Число форматируется как процент с одним знаком после запятой."""
        assert metric_percent(value) == expected

    def test_none_returns_dash(self):
        """None → '—'."""
        assert metric_percent(None) == '—'

    @pytest.mark.parametrize('bad_val', ['abc', ''])
    def test_invalid_returns_dash(self, bad_val):
        """Некорректное значение → '—'."""
        assert metric_percent(bad_val) == '—'


class TestMetricPercentRatio:
    """Тесты для фильтра metric_percent_ratio (доля 0–1 в проценты)."""

    @pytest.mark.parametrize('value,expected', [
        (0.5, '50.0%'),
        (0, '0.0%'),
        (1.0, '100.0%'),
        (0.333, '33.3%'),
    ])
    def test_valid_values(self, value, expected):
        """Доля умножается на 100 и форматируется как процент."""
        assert metric_percent_ratio(value) == expected

    def test_none_returns_dash(self):
        """None → '—'."""
        assert metric_percent_ratio(None) == '—'

    @pytest.mark.parametrize('bad_val', ['x', None])
    def test_invalid_returns_dash(self, bad_val):
        """Некорректное значение → '—'."""
        assert metric_percent_ratio(bad_val) == '—'


class TestFormatSubtitleCount:
    """Тесты для фильтра format_subtitle_count."""

    @pytest.mark.parametrize('value,suffix,expected', [
        (5, 'интервью за 30 дней', '(5 интервью за 30 дней)'),
        (0, 'кандидатов', '(0 кандидатов)'),
        (1, 'оффер', '(1 оффер)'),
    ])
    def test_valid_values(self, value, suffix, expected):
        """Число и суффикс дают подпись в скобках."""
        assert format_subtitle_count(value, suffix) == expected

    def test_none_returns_empty(self):
        """None → ''."""
        assert format_subtitle_count(None, 'шт.') == ''

    @pytest.mark.parametrize('bad_val', ['abc', ''])
    def test_invalid_value_returns_empty(self, bad_val):
        """Некорректное число → ''."""
        assert format_subtitle_count(bad_val, 'шт.') == ''


class TestFormatDays:
    """Тесты для фильтра format_days."""

    @pytest.mark.parametrize('value,expected', [
        (10, '10 дн.'),
        (0, '0 дн.'),
        (1.7, '1 дн.'),
    ])
    def test_valid_values(self, value, expected):
        """Число форматируется как «X дн.»."""
        assert format_days(value) == expected

    def test_none_returns_empty(self):
        """None → ''."""
        assert format_days(None) == ''

    @pytest.mark.parametrize('bad_val', ['x', ''])
    def test_invalid_returns_empty(self, bad_val):
        """Некорректное значение → ''."""
        assert format_days(bad_val) == ''


class TestDecimalDot:
    """Тесты для фильтра decimal_dot."""

    @pytest.mark.parametrize('value,decimals,expected', [
        (3.14, None, '3.14'),
        (3.14, 2, '3.14'),
        (3.1, 1, '3.1'),
        (100.5, 0, '100'),
        (0, None, '0.00'),
    ])
    def test_valid_values(self, value, decimals, expected):
        """Число форматируется с точкой и заданным числом знаков."""
        if decimals is None:
            assert decimal_dot(value) == expected
        else:
            assert decimal_dot(value, decimals) == expected

    def test_none_returns_dash(self):
        """None → '—'."""
        assert decimal_dot(None) == '—'

    @pytest.mark.parametrize('bad_val', ['abc', ''])
    def test_invalid_returns_dash(self, bad_val):
        """Некорректное значение → '—'."""
        assert decimal_dot(bad_val) == '—'


class TestMetricCurrency:
    """Тесты для фильтра metric_currency (рубли для SSR)."""

    @pytest.mark.parametrize('value,expected', [
        (1000, '1 000 ₽'),
        (50000, '50 000 ₽'),
        (0, '0 ₽'),
        (1234567, '1 234 567 ₽'),
    ])
    def test_valid_values(self, value, expected):
        """Число форматируется как рубли с пробелом как разделителем тысяч."""
        assert metric_currency(value) == expected

    def test_none_returns_dash(self):
        """None → '—'."""
        assert metric_currency(None) == '—'

    @pytest.mark.parametrize('bad_val', ['x', ''])
    def test_invalid_returns_dash(self, bad_val):
        """Некорректное значение → '—'."""
        assert metric_currency(bad_val) == '—'


class TestIsActiveUrl:
    """Тесты для фильтра is_active_url."""

    @pytest.mark.parametrize('url_name,url_names,expected', [
        ('offers_list', 'offers_list', True),
        ('offers_list', 'offers_list, interns_list', True),
        ('interns_list', 'offers_list, interns_list', True),
        ('other_view', 'offers_list, interns_list', False),
        ('', 'offers_list', False),
        (None, 'offers_list', False),
    ])
    def test_active_url_detection(self, url_name, url_names, expected):
        """URL в списке → True, иначе → False."""
        assert is_active_url(url_name, url_names) is expected

    def test_url_names_with_spaces_trimmed(self):
        """Пробелы вокруг имён в строке url_names игнорируются."""
        assert is_active_url('my_view', '  my_view  ,  other_view  ') is True


class TestTransliterateName:
    """Тесты для фильтра transliterate_name (латиница → кириллица для отображения)."""

    def test_latin_to_cyrillic(self):
        """Латинское имя транслитерируется в кириллицу."""
        assert transliterate_name('Yuliya Sorokina') == 'Юлия Сорокина'
        assert transliterate_name('Alexey') == 'Алексей'

    def test_cyrillic_passthrough(self):
        """Кириллица возвращается без изменений."""
        assert transliterate_name('Юлия Сорокина') == 'Юлия Сорокина'

    def test_none_returns_none(self):
        """None → None."""
        assert transliterate_name(None) is None

    def test_empty_string_returns_empty(self):
        """Пустая строка возвращается как есть."""
        assert transliterate_name('') == ''

    def test_whitespace_only_returns_as_is(self):
        """Строка из пробелов возвращается как есть."""
        assert transliterate_name('   ') == '   '

    def test_fallback_when_result_empty(self):
        """Фоллбэк: при пустом результате транслитерации возвращается исходное значение."""
        from unittest.mock import patch
        with patch('core.templatetags.common_extras.transliterate_name_to_cyrillic', return_value=''):
            assert transliterate_name('Unknown Name') == 'Unknown Name'
