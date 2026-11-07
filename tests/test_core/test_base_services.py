"""
Тесты для core/base_services.py — только непокрытые ветки.

Основная логика (счётчики, _get_direction_id required=True, _get_intern, _get_manager_email,
_map_direction_name) уже прогоняется через TestOfferImportService и TestInternImportService.

Здесь тестируем только то, чего там нет:
- _safe_string_strip: специальные nan/NaT/<NA> значения
- _get_string_field: обрезка по max_length
- _get_direction_id: ветка required=False (пустое имя / не найдено)
- _reset_table: валидация имени последовательности (защита от недопустимых символов)
- _load_directions, _load_managers, _load_companies: загрузка справочников из БД
- _map_direction_name, _map_manager_name, _map_manager_tc_name: маппинги
- _get_manager_email: все ветки логики (required, use_tc_mapping)
- _run_import_loop: вызов _process_row, progress_callback, continue при False
- _reset_multiple_tables: делегирование _reset_table
"""
import pandas as pd
import pytest
from unittest.mock import MagicMock

from core.base_services import BaseImportService


class ConcreteService(BaseImportService):
    """Минимальный подкласс для тестирования методов BaseImportService."""
    def run(self):
        pass


class TestSafeStringStrip:
    """Тесты для BaseImportService._safe_string_strip."""

    def setup_method(self):
        self.svc = ConcreteService(df=pd.DataFrame())

    @pytest.mark.parametrize('value, expected', [
        (float('nan'), ''),
        (pd.NA, ''),
        (pd.NaT, ''),
        ('nan', ''),
        ('None', ''),
        ('<NA>', ''),
        ('NaT', ''),
        ('', ''),
    ])
    def test_special_values_return_default(self, value, expected):
        """nan, None, <NA>, NaT, пустая строка → default=''."""
        assert self.svc._safe_string_strip(value) == expected

    def test_regular_string_stripped(self):
        """Обычная строка с пробелами → stripped."""
        assert self.svc._safe_string_strip('  Привет  ') == 'Привет'

    def test_regular_string_without_spaces(self):
        """Строка без пробелов → без изменений."""
        assert self.svc._safe_string_strip('Backend') == 'Backend'

    def test_custom_default_returned_for_nan(self):
        """Кастомный default возвращается для nan-значений."""
        assert self.svc._safe_string_strip(float('nan'), default='N/A') == 'N/A'

    def test_zero_and_false_not_treated_as_nan(self):
        """Числовой 0 и False не являются nan — обрабатываются как строки."""
        assert self.svc._safe_string_strip(0) == '0'
        assert self.svc._safe_string_strip(False) == 'False'


class TestGetStringField:
    """Тесты для BaseImportService._get_string_field — ветка max_length."""

    def setup_method(self):
        self.svc = ConcreteService(df=pd.DataFrame())

    def _row(self, **kwargs):
        return pd.Series(kwargs)

    def test_value_truncated_when_exceeds_max_length(self):
        """Значение длиннее max_length → обрезается."""
        row = self._row(name='Абвгдеёжзийклмн')
        result = self.svc._get_string_field(row, 'name', max_length=5)
        assert result == 'Абвгд'
        assert len(result) == 5

    def test_value_not_truncated_when_within_max_length(self):
        """Значение короче max_length → без изменений."""
        row = self._row(name='Abc')
        result = self.svc._get_string_field(row, 'name', max_length=10)
        assert result == 'Abc'

    def test_missing_field_returns_default(self):
        """Поле отсутствует в row → возвращает default."""
        row = self._row()
        result = self.svc._get_string_field(row, 'nonexistent', default='EMPTY')
        assert result == 'EMPTY'

    def test_no_max_length_returns_full_value(self):
        """Без max_length длинное значение возвращается целиком."""
        row = self._row(name='А' * 500)
        result = self.svc._get_string_field(row, 'name')
        assert len(result) == 500


class TestGetDirectionIdOptional:
    """Тесты для ветки required=False в BaseImportService._get_direction_id."""

    def setup_method(self):
        self.svc = ConcreteService(df=pd.DataFrame())
        # 'Backend' → DIRECTION_MAPPING → 'Python', поэтому в map кладём 'Python'
        self.svc.directions_map = {'Python': 10, 'Frontend': 20}

    def test_empty_name_required_false_returns_none_true(self):
        """Пустое имя + required=False → (None, True), ошибка НЕ логируется."""
        result, ok = self.svc._get_direction_id('', index=0, required=False)
        assert result is None
        assert ok is True
        assert self.svc.skipped_count == 0

    def test_not_found_required_false_returns_none_true(self):
        """Направление не найдено + required=False → (None, True), ошибка НЕ логируется."""
        result, ok = self.svc._get_direction_id('Несуществующее', index=0, required=False)
        assert result is None
        assert ok is True
        assert self.svc.skipped_count == 0

    def test_found_returns_id_and_true(self):
        """Направление найдено → (id, True). 'Backend' маппится в 'Python' через DIRECTION_MAPPING."""
        result, ok = self.svc._get_direction_id('Backend', index=0, required=False)
        assert result == 10
        assert ok is True


class TestResetTableSequenceValidation:
    """Тесты валидации имени последовательности в BaseImportService._reset_table."""

    def setup_method(self):
        self.svc = ConcreteService(df=pd.DataFrame())

    @pytest.mark.parametrize('invalid_name', [
        '; DROP TABLE offers_offer',
        'table-name',
        'table name',
        'table;seq',
        '../path',
        'name!',
    ])
    def test_invalid_sequence_name_raises_value_error(self, invalid_name):
        """Недопустимые символы в sequence_name → ValueError (проверка до обращения к БД)."""
        mock_model = MagicMock()
        mock_model.objects.all().delete.return_value = (0, {})
        with pytest.raises(ValueError, match='Недопустимое имя последовательности'):
            self.svc._reset_table(
                model=mock_model,
                table_name='test_table',
                sequence_name=invalid_name,
            )


# ---------------------------------------------------------------------------
# _load_directions / _load_managers / _load_companies (требуют БД)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
class TestLoadDirections:
    """Тесты для BaseImportService._load_directions."""

    def test_returns_name_to_id_map(self, direction):
        """_load_directions возвращает {name: id} для всех направлений."""
        svc = ConcreteService(df=pd.DataFrame())
        result = svc._load_directions()
        assert result[direction.name] == direction.id

    def test_empty_when_no_directions(self, db):
        """Без направлений возвращает пустой dict."""
        from directions.models import Direction
        Direction.objects.all().delete()
        svc = ConcreteService(df=pd.DataFrame())
        result = svc._load_directions()
        assert result == {}


@pytest.mark.django_db(databases=['default'])
class TestLoadManagers:
    """Тесты для BaseImportService._load_managers."""

    def test_active_manager_full_name_in_result(self, manager):
        """Активный менеджер присутствует в результате по full_name."""
        svc = ConcreteService(df=pd.DataFrame())
        result = svc._load_managers()
        assert result.get(manager.full_name) == manager.email

    def test_inactive_manager_not_in_result(self, db):
        """Неактивный менеджер НЕ попадает в результат по full_name."""
        from managers.models import Manager
        inactive = Manager.objects.create(
            email='inactive@example.com',
            full_name='Неактивный Менеджер',
            username='inactive',
            groups=[],
            is_active=False,
        )
        svc = ConcreteService(df=pd.DataFrame())
        result = svc._load_managers()
        assert inactive.full_name not in result

    def test_includes_username_map_from_constants(self, db):
        """Результат содержит username → email из MANAGER_EMAIL_MAPPING."""
        from core.constants import MANAGER_EMAIL_MAPPING
        svc = ConcreteService(df=pd.DataFrame())
        result = svc._load_managers()
        first_username, first_email = next(iter(MANAGER_EMAIL_MAPPING.items()))
        assert result.get(first_username) == first_email


@pytest.mark.django_db(databases=['default'])
class TestLoadCompanies:
    """Тесты для BaseImportService._load_companies."""

    def test_returns_name_to_id_map(self, company):
        """_load_companies возвращает {name: id} для всех компаний."""
        svc = ConcreteService(df=pd.DataFrame())
        result = svc._load_companies()
        assert result[company.name] == company.id

    def test_empty_when_no_companies(self, db):
        """Без компаний возвращает пустой dict."""
        from companies.models import Company
        Company.objects.all().delete()
        svc = ConcreteService(df=pd.DataFrame())
        result = svc._load_companies()
        assert result == {}


# ---------------------------------------------------------------------------
# _map_direction_name / _map_manager_name / _map_manager_tc_name
# ---------------------------------------------------------------------------

class TestMapDirectionName:
    """Тесты для BaseImportService._map_direction_name."""

    def setup_method(self):
        self.svc = ConcreteService(df=pd.DataFrame())

    @pytest.mark.parametrize('input_name, expected', [
        ('Backend', 'Python'),
        ('Devops', 'DevOps'),
        ('SA', 'Системный аналитик'),
        ('QA', 'QA Manual'),
        ('Go', 'GO'),
        ('Python', 'Python'),    # не в маппинге → возвращается как есть
        ('Frontend', 'Frontend'),  # не в маппинге
    ])
    def test_known_and_unknown_names(self, input_name, expected):
        """Имена из маппинга маппятся, неизвестные возвращаются без изменений."""
        assert self.svc._map_direction_name(input_name) == expected

    @pytest.mark.parametrize('empty_val', [None, '', 0])
    def test_falsy_values_return_none(self, empty_val):
        """Пустые/falsy значения → None."""
        assert self.svc._map_direction_name(empty_val) is None

    def test_custom_mapping_overrides_default(self):
        """custom mapping переопределяет DIRECTION_MAPPING."""
        custom = {'X': 'Y'}
        assert self.svc._map_direction_name('X', mapping=custom) == 'Y'
        assert self.svc._map_direction_name('Backend', mapping=custom) == 'Backend'


class TestMapManagerName:
    """Тесты для BaseImportService._map_manager_name."""

    def setup_method(self):
        self.svc = ConcreteService(df=pd.DataFrame())

    @pytest.mark.parametrize('input_name, expected', [
        ('Анна', 'anna'),
        ('Иван', 'ivan'),
        ('Мария', 'maria'),
        ('Вася', 'Вася'),  # не в маппинге → без изменений
    ])
    def test_known_and_unknown_names(self, input_name, expected):
        """Имена из маппинга маппятся, неизвестные возвращаются как есть."""
        assert self.svc._map_manager_name(input_name) == expected

    def test_strips_whitespace_before_mapping(self):
        """Пробелы вокруг имени обрезаются перед маппингом."""
        assert self.svc._map_manager_name('  Анна  ') == 'anna'

    @pytest.mark.parametrize('empty_val', [None, ''])
    def test_empty_returns_none(self, empty_val):
        """Пустое значение → None."""
        assert self.svc._map_manager_name(empty_val) is None


class TestMapManagerTcName:
    """Тесты для BaseImportService._map_manager_tc_name."""

    def setup_method(self):
        self.svc = ConcreteService(df=pd.DataFrame())

    @pytest.mark.parametrize('input_name, expected', [
        ('@Анна Иванова', 'anna'),
        ('@Иван Петров', 'ivan'),
        ('@Неизвестный', '@Неизвестный'),  # не в маппинге
    ])
    def test_known_and_unknown_names(self, input_name, expected):
        """ТС-маппинг: известные маппятся, неизвестные без изменений."""
        assert self.svc._map_manager_tc_name(input_name) == expected

    @pytest.mark.parametrize('empty_val', [None, ''])
    def test_empty_returns_none(self, empty_val):
        """Пустое значение → None."""
        assert self.svc._map_manager_tc_name(empty_val) is None


# ---------------------------------------------------------------------------
# _get_manager_email
# ---------------------------------------------------------------------------

class TestGetManagerEmail:
    """Тесты для BaseImportService._get_manager_email."""

    def setup_method(self):
        self.svc = ConcreteService(df=pd.DataFrame())
        self.svc.managers_map = {
            'anna': 'anna@example.com',
            'ivan': 'ivan@example.com',
            'Алексей Менеджеров': 'manager@example.com',
        }

    def test_empty_name_required_false_returns_none_true(self):
        """Пустое имя + required=False → (None, True), ошибка не логируется."""
        result, ok = self.svc._get_manager_email('', 0, required=False)
        assert result is None
        assert ok is True
        assert self.svc.skipped_count == 0

    def test_empty_name_required_true_logs_error(self):
        """Пустое имя + required=True → (None, False), ошибка логируется."""
        result, ok = self.svc._get_manager_email('', 0, required=True)
        assert result is None
        assert ok is False
        assert self.svc.skipped_count == 1

    def test_known_name_returns_email(self):
        """Имя есть в MANAGER_MAPPING и managers_map → email и ok=True."""
        result, ok = self.svc._get_manager_email('Анна', 0)
        assert result == 'anna@example.com'
        assert ok is True

    def test_name_not_in_managers_map_required_false_returns_none_true(self):
        """Маппинг есть, но email не найден + required=False → (None, True)."""
        result, ok = self.svc._get_manager_email('Мария', 0, required=False)
        # 'Мария' → 'maria' через MANAGER_MAPPING, 'maria' не в managers_map
        assert result is None
        assert ok is True

    def test_name_not_in_managers_map_required_true_logs_error(self):
        """Маппинг есть, но email не найден + required=True → (None, False)."""
        result, ok = self.svc._get_manager_email('Мария', 0, required=True)
        assert result is None
        assert ok is False
        assert self.svc.skipped_count == 1

    def test_tc_mapping_applied_when_use_tc_mapping_true(self):
        """use_tc_mapping=True → применяется MANAGER_TC_MAPPING."""
        result, ok = self.svc._get_manager_email('@Анна Иванова', 0, use_tc_mapping=True)
        assert result == 'anna@example.com'
        assert ok is True


# ---------------------------------------------------------------------------
# _run_import_loop
# ---------------------------------------------------------------------------

class TestRunImportLoop:
    """Тесты для BaseImportService._run_import_loop."""

    def test_process_row_called_for_each_row(self):
        """_process_row вызывается для каждой строки DataFrame."""
        df = pd.DataFrame({'name': ['Иван', 'Петр', 'Сергей']})

        class _Svc(ConcreteService):
            process_row_calls = 0

            def _process_row(self, row, index):
                self.process_row_calls += 1
                return True

        svc = _Svc(df=df)
        svc._run_import_loop(total_rows=3, log_message='Начинаю...')
        assert svc.process_row_calls == 3

    def test_progress_callback_called_after_each_row(self):
        """progress_callback вызывается после каждой строки с корректными аргументами."""
        df = pd.DataFrame({'name': ['Иван', 'Петр']})
        calls = []

        class _Svc(ConcreteService):
            def _process_row(self, row, index):
                return True

        svc = _Svc(df=df, progress_callback=lambda cur, tot: calls.append((cur, tot)))
        svc._run_import_loop(total_rows=2, log_message='...')

        assert len(calls) == 2
        assert calls[0] == (1, 2)
        assert calls[1] == (2, 2)

    def test_false_from_process_row_does_not_stop_loop(self):
        """Если _process_row возвращает False для строки — цикл продолжается."""
        df = pd.DataFrame({'name': ['А', 'Б', 'В']})
        processed = []

        class _Svc(ConcreteService):
            def _process_row(self, row, index):
                processed.append(index)
                return index != 1  # False для строки с индексом 1

        svc = _Svc(df=df)
        svc._run_import_loop(total_rows=3, log_message='...')
        assert len(processed) == 3

    def test_no_progress_callback_does_not_raise(self):
        """Без progress_callback цикл работает без ошибок."""
        df = pd.DataFrame({'name': ['Иван']})

        class _Svc(ConcreteService):
            def _process_row(self, row, index):
                return True

        svc = _Svc(df=df, progress_callback=None)
        svc._run_import_loop(total_rows=1, log_message='...')


# ---------------------------------------------------------------------------
# _reset_multiple_tables
# ---------------------------------------------------------------------------

class TestResetMultipleTables:
    """Тесты для BaseImportService._reset_multiple_tables."""

    def test_calls_reset_table_for_each_entry(self):
        """_reset_multiple_tables делегирует _reset_table для каждой записи в порядке."""
        svc = ConcreteService(df=pd.DataFrame())
        calls = []
        svc._reset_table = lambda model, table_name, seq: calls.append((table_name, seq))

        model1, model2 = MagicMock(), MagicMock()
        svc._reset_multiple_tables([
            (model1, 'table1', 'table1_id_seq'),
            (model2, 'table2', 'table2_id_seq'),
        ])

        assert calls == [('table1', 'table1_id_seq'), ('table2', 'table2_id_seq')]

    def test_empty_list_does_not_call_reset_table(self):
        """Пустой список → _reset_table не вызывается."""
        svc = ConcreteService(df=pd.DataFrame())
        svc._reset_table = MagicMock()
        svc._reset_multiple_tables([])
        svc._reset_table.assert_not_called()


# ---------------------------------------------------------------------------
# _load_interns_cache / interns_cache после _load_reference_data
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
class TestLoadInternsCache:
    """Тесты предзагрузки кэша студентов в BaseImportService."""

    def test_load_interns_cache_returns_list(self, intern):
        """_load_interns_cache возвращает список объектов Intern."""
        svc = ConcreteService(df=pd.DataFrame())
        result = svc._load_interns_cache()
        assert isinstance(result, list)

    def test_load_interns_cache_contains_intern(self, intern):
        """_load_interns_cache включает созданного студента."""
        svc = ConcreteService(df=pd.DataFrame())
        result = svc._load_interns_cache()
        assert intern in result

    def test_load_interns_cache_empty_when_no_interns(self, db):
        """_load_interns_cache возвращает пустой список, если студентов нет."""
        from interns.models import Intern
        Intern.objects.all().delete()
        svc = ConcreteService(df=pd.DataFrame())
        result = svc._load_interns_cache()
        assert result == []

    def test_load_reference_data_sets_interns_cache(self, intern):
        """После _load_reference_data атрибут interns_cache заполнен."""
        svc = ConcreteService(df=pd.DataFrame())
        svc._load_reference_data()
        assert hasattr(svc, 'interns_cache')
        assert isinstance(svc.interns_cache, list)
        assert intern in svc.interns_cache

    def test_get_intern_uses_cache_not_db(self, intern):
        """_get_intern передаёт interns_cache в find_intern_by_name, а не делает запрос к БД."""
        from unittest.mock import patch
        svc = ConcreteService(df=pd.DataFrame())
        svc.interns_cache = [intern]

        with patch('core.intern_utils.find_intern_by_name', return_value=intern) as mock_find:
            result, ok = svc._get_intern(intern.full_name, index=0)

        assert result is intern
        assert ok is True
        mock_find.assert_called_once_with(intern.full_name, interns_cache=[intern])

    def test_get_intern_falls_back_to_db_when_no_cache(self, intern):
        """_get_intern без interns_cache передаёт None в find_intern_by_name (режим БД)."""
        from unittest.mock import patch
        svc = ConcreteService(df=pd.DataFrame())

        with patch('core.intern_utils.find_intern_by_name', return_value=intern) as mock_find:
            result, ok = svc._get_intern(intern.full_name, index=0)

        assert result is intern
        assert ok is True
        mock_find.assert_called_once_with(intern.full_name, interns_cache=None)
