"""
Тесты для сервисов приложения interviews.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.services - для группировки тестов сервисов
"""
import pytest
import pandas as pd
from datetime import date, time
from unittest.mock import Mock, patch

from core.constants import INTERVIEW_TYPE_MAPPING
from interviews.services import InterviewImportService
from interviews.models import Interview


@pytest.mark.django_db(databases=['default'])
@pytest.mark.services
class TestInterviewImportService:
    """Тесты для InterviewImportService."""

    def test_service_initialization(self, sample_df):
        """Проверка инициализации сервиса."""
        service = InterviewImportService(sample_df)
        assert service.df is not None
        assert service.errors_log == []
        assert service.created_count == 0
        assert service.skipped_count == 0

    def test_load_additional_reference_data(self, sample_df, company_google):
        """Проверка загрузки дополнительных справочников."""
        service = InterviewImportService(sample_df)
        service._load_reference_data()
        assert hasattr(service, 'companies_map')
        assert len(service.companies_map) > 0
        assert (
            'Google' in service.companies_map.values()
            or company_google.id in service.companies_map.values()
        )

    def test_load_existing_records_empty(self, sample_df, db):
        """При отсутствии записей Interview _load_existing_records возвращает пустой словарь."""
        service = InterviewImportService(sample_df)
        service._load_reference_data()
        result = service._load_existing_records()
        assert result == {}

    def test_load_existing_records_with_records(
            self, sample_df, services_intern, direction_python, company_google, db):
        """При наличии записей _load_existing_records возвращает словарь с ключом из _make_unique_key."""
        existing = Interview.objects.create(
            intern=services_intern,
            direction=direction_python,
            company=company_google,
            date=date(2025, 12, 1),
            time=time(10, 0),
            interview_type='screening',
            vacancy_link='',
            interview_link='',
            hr_name='',
        )
        service = InterviewImportService(sample_df)
        service._load_reference_data()
        result = service._load_existing_records()
        expected_key = service._make_unique_key(
            services_intern.id,
            date(2025, 12, 1),
            direction_python.id,
            company_google.id,
            None,
            time(10, 0),
            '',
            '',
            '',
        )
        assert len(result) == 1
        assert expected_key in result
        assert result[expected_key] == existing

    def test_process_row_success(self, sample_df, services_intern, direction_python, company_google):
        """Проверка успешной обработки строки."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.services.get_or_create_company') as mock_create_company, \
             patch('interviews.utils.map_company_name') as mock_map_company, \
             patch('interviews.utils.parse_datetime_for_interview') as mock_parse_datetime:

            mock_find_intern.return_value = services_intern
            mock_map_company.return_value = 'Google'
            mock_create_company.return_value = company_google.id
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df)
            service._load_reference_data()

            row = sample_df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is True
            assert service.created_count == 1
            assert Interview.objects.filter(intern=services_intern).exists()

    def test_process_row_missing_intern(self, sample_df, direction_python):
        """Проверка обработки строки с отсутствующим студентом."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern:
            mock_find_intern.return_value = None

            service = InterviewImportService(sample_df)
            service._load_reference_data()

            row = sample_df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is False
            assert service.skipped_count == 1
            assert len(service.errors_log) > 0

    def test_process_row_missing_direction(self, sample_df, services_intern):
        """Проверка обработки строки с отсутствующим направлением."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern:
            mock_find_intern.return_value = services_intern

            service = InterviewImportService(sample_df)
            service._load_reference_data()
            service.directions_map = {}

            row = sample_df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is False
            assert service.skipped_count == 1

    def test_process_row_with_company(self, sample_df, services_intern, direction_python, company_google):
        """Проверка обработки строки с компанией."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.services.map_company_name') as mock_map_company, \
             patch('interviews.services.get_or_create_company') as mock_create_company, \
             patch('interviews.services.parse_datetime_for_interview') as mock_parse_datetime:

            mock_find_intern.return_value = services_intern
            mock_map_company.return_value = 'Google'
            mock_create_company.return_value = company_google.id
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df)
            service._load_reference_data()
            service.companies_map = {'Google': company_google.id}

            row = sample_df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is True
            interview = Interview.objects.get(intern=services_intern)
            assert interview.company_id == company_google.id

    def test_process_row_with_new_company(self, sample_df, services_intern, direction_python):
        """Проверка обработки строки с новой компанией (не найдена в кэше → создаётся)."""
        from companies.models import Company
        real_company = Company.objects.create(name='Google')

        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.services.map_company_name') as mock_map_company, \
             patch('interviews.services.get_or_create_company') as mock_create_company, \
             patch('interviews.services.parse_datetime_for_interview') as mock_parse_datetime:

            mock_find_intern.return_value = services_intern
            mock_map_company.return_value = None
            mock_create_company.return_value = real_company.id
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df)
            service._load_reference_data()
            service.companies_map = {}

            row = sample_df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is True
            mock_create_company.assert_called_once_with('Google')

    def test_process_row_company_creation_exception(
            self, sample_df, services_intern, direction_python):
        """При исключении в get_or_create_company ошибка логируется, интервью создаётся с company_id=None."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.services.map_company_name') as mock_map_company, \
             patch('interviews.services.get_or_create_company') as mock_create_company, \
             patch('interviews.services.parse_datetime_for_interview') as mock_parse_datetime:
            mock_find_intern.return_value = services_intern
            mock_map_company.return_value = 'Google'
            mock_create_company.side_effect = Exception('DB error')
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df)
            service._load_reference_data()
            service.companies_map = {}

            row = sample_df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is True
            assert service.created_count == 1
            interview = Interview.objects.get(intern=services_intern)
            assert interview.company_id is None
            mock_create_company.assert_called_once_with('Google')

    def test_process_row_with_new_bigtech_company(self, sample_df, services_intern, direction_python):
        """Проверка обработки строки с новой бигтех-компанией (канонизация, не найдена в кэше → создаётся)."""
        from companies.models import Company
        real_company = Company.objects.create(name='Google', is_bigtech=True)

        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.services.map_company_name') as mock_map_company, \
             patch('interviews.services.get_or_create_company') as mock_create_company, \
             patch('interviews.services.parse_datetime_for_interview') as mock_parse_datetime:

            mock_find_intern.return_value = services_intern
            mock_map_company.return_value = 'Google'
            mock_create_company.return_value = real_company.id
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df)
            service._load_reference_data()
            service.companies_map = {}

            row = sample_df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is True
            mock_create_company.assert_called_once_with('Google')

    def test_process_row_with_manager(self, sample_df, services_intern, direction_python):
        """Проверка обработки строки с менеджером (используется manager_email)."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.utils.parse_datetime_for_interview') as mock_parse_datetime:
            mock_find_intern.return_value = services_intern
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df)
            service._load_reference_data()
            service.managers_map = {'Алексей': 'aleksey@example.com'}

            row = sample_df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is True
            interview = Interview.objects.get(intern=services_intern)
            assert interview.manager_email == 'aleksey@example.com'

    def test_process_row_without_manager(self, sample_df, services_intern, direction_python):
        """Проверка обработки строки без менеджера."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.utils.parse_datetime_for_interview') as mock_parse_datetime:
            mock_find_intern.return_value = services_intern
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df)
            service._load_reference_data()

            row = sample_df.iloc[0].copy()
            row['manager_name'] = ''
            result = service._process_row(row, 0, {})

            assert result is True
            interview = Interview.objects.get(intern=services_intern)
            assert interview.manager_email is None

    def test_process_row_invalid_date(self, sample_df, services_intern, direction_python):
        """Проверка обработки строки с невалидной датой."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.services.parse_datetime_for_interview') as mock_parse:

            mock_find_intern.return_value = services_intern
            mock_parse.return_value = (None, None, 'Ошибка парсинга даты')

            service = InterviewImportService(sample_df)
            service._load_reference_data()

            row = sample_df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is False
            assert service.skipped_count == 1

    @pytest.mark.parametrize('err_msg', [
        "Дата '2023-01-01' в строке 2 до 2024 года.",
        "Невозможно распознать дату 'x' в строке 2.",
    ])
    def test_process_row_invalid_date_branches(
            self, sample_df, services_intern, direction_python, err_msg):
        """Обе ветки ошибки даты: «до 2024 года» и прочие — _log_error, return False."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.services.parse_datetime_for_interview') as mock_parse:
            mock_find_intern.return_value = services_intern
            mock_parse.return_value = (None, None, err_msg)

            service = InterviewImportService(sample_df)
            service._load_reference_data()

            row = sample_df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is False
            assert service.skipped_count == 1
            assert len(service.errors_log) == 1
            assert service.errors_log[0] == err_msg

    def test_process_row_duplicate_updates_existing(
            self, sample_df, services_intern, direction_python, company_google, db):
        """При совпадении unique_key существующая запись обновляется, дубликат не создаётся."""
        existing = Interview.objects.create(
            intern=services_intern,
            direction=direction_python,
            company=company_google,
            date=date(2025, 12, 1),
            time=time(10, 0),
            interview_type='screening',
            manager_email=None,
            vacancy_link='',
            interview_link='',
            hr_name='',
        )
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.services.map_company_name') as mock_map_company, \
             patch('interviews.services.get_or_create_company') as mock_create_company, \
             patch('interviews.services.parse_datetime_for_interview') as mock_parse_datetime:
            mock_find_intern.return_value = services_intern
            mock_map_company.return_value = 'Google'
            mock_create_company.return_value = company_google.id
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df)
            service._load_reference_data()
            service.companies_map = {'Google': company_google.id}
            existing_keys = service._load_existing_records()
            assert len(existing_keys) == 1

            row = sample_df.iloc[0].copy()
            row['manager_name'] = ''
            row['interview_type_label'] = 'Техническое собеседование'
            row['link'] = 'https://example.com/link'
            row['hr_contacts'] = '@telegram'

            result = service._process_row(row, 0, existing_keys)

            assert result is False
            assert service.created_count == 0
            assert service.duplicates_count == 1
            assert Interview.objects.count() == 1
            existing.refresh_from_db()
            assert existing.interview_type == 'tech'
            assert existing.link == 'https://example.com/link'
            assert existing.manager_email is None
            assert existing.hr_contacts == '@telegram'

    def test_process_row_exception(self, sample_df):
        """Проверка обработки исключения при обработке строки."""
        service = InterviewImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({'invalid': 'data'})
        result = service._process_row(row, 0, {})

        assert result is False
        assert service.skipped_count == 1
        assert len(service.errors_log) > 0

    def test_process_row_exception_on_create(
            self, sample_df, services_intern, direction_python, company_google):
        """При исключении в Interview.objects.create ошибка логируется, return False."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.services.map_company_name') as mock_map_company, \
             patch('interviews.services.get_or_create_company') as mock_create_company, \
             patch('interviews.services.parse_datetime_for_interview') as mock_parse_datetime, \
             patch('interviews.models.Interview.objects.create') as mock_create:
            mock_find_intern.return_value = services_intern
            mock_map_company.return_value = 'Google'
            mock_create_company.return_value = company_google.id
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)
            mock_create.side_effect = Exception('DB error')

            service = InterviewImportService(sample_df)
            service._load_reference_data()

            row = sample_df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is False
            assert service.skipped_count == 1
            assert len(service.errors_log) == 1
            assert 'Ошибка при обработке строки 2' in service.errors_log[0]
            assert 'DB error' in service.errors_log[0]

    def test_run_method(self, sample_df, services_intern, direction_python, company_google):
        """Проверка метода run."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.utils.map_company_name') as mock_map_company, \
             patch('interviews.services.get_or_create_company') as mock_create_company, \
             patch('interviews.utils.parse_datetime_for_interview') as mock_parse_datetime:

            mock_find_intern.return_value = services_intern
            mock_map_company.return_value = 'Google'
            mock_create_company.return_value = company_google.id
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df)
            service._load_reference_data()

            created, skipped, duplicates, errors = service.run()

            assert created == 1
            assert skipped == 1
            assert duplicates == 0
            assert Interview.objects.count() == 1

    def test_run_calls_progress_callback(
            self, sample_df, services_intern, direction_python, company_google):
        """run() вызывает progress_callback для каждой строки с (номер_строки, всего_строк)."""
        mock_callback = Mock()
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.utils.map_company_name') as mock_map_company, \
             patch('interviews.services.get_or_create_company') as mock_create_company, \
             patch('interviews.utils.parse_datetime_for_interview') as mock_parse_datetime:
            mock_find_intern.return_value = services_intern
            mock_map_company.return_value = 'Google'
            mock_create_company.return_value = company_google.id
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df, progress_callback=mock_callback)
            service._load_reference_data()
            service.run()

            assert mock_callback.call_count == len(sample_df)
            mock_callback.assert_any_call(1, 2)
            mock_callback.assert_any_call(2, 2)

    def test_interview_type_mapping(self, sample_df, services_intern, direction_python):
        """Проверка маппинга типа 'Скрининг' → 'screening'."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.utils.parse_datetime_for_interview') as mock_parse_datetime:
            mock_find_intern.return_value = services_intern
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df)
            service._load_reference_data()

            row = sample_df.iloc[0].copy()
            row['interview_type_label'] = 'Скрининг'
            result = service._process_row(row, 0, {})

            assert result is True
            interview = Interview.objects.get(intern=services_intern)
            assert interview.interview_type == 'screening'

    @pytest.mark.parametrize('label,expected_type', list(INTERVIEW_TYPE_MAPPING.items()))
    def test_all_interview_types(self, label, expected_type, services_intern, direction_python):
        """Каждый label из INTERVIEW_TYPE_MAPPING корректно маппируется в тип собеседования."""
        df = pd.DataFrame({
            'full_name': [services_intern.full_name],
            'direction_name': [direction_python.name],
            'interview_type_label': [label],
            'date_str': ['2025-12-01'],
            'time_str': ['10:00'],
            'company_name': [''],
            'manager_name': [''],
        })

        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.utils.parse_datetime_for_interview') as mock_parse_datetime:
            mock_find_intern.return_value = services_intern
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(df)
            service._load_reference_data()

            row = df.iloc[0]
            result = service._process_row(row, 0, {})

            assert result is True
            interview = Interview.objects.filter(
                intern=services_intern, interview_type=expected_type
            ).first()
            assert interview is not None
            interview.delete()

    def test_process_row_unknown_interview_type_label_default_screening(
            self, sample_df, services_intern, direction_python):
        """Неизвестный interview_type_label маппится в дефолт 'screening'."""
        with patch('core.intern_utils.find_intern_by_name') as mock_find_intern, \
             patch('interviews.utils.parse_datetime_for_interview') as mock_parse_datetime:
            mock_find_intern.return_value = services_intern
            mock_parse_datetime.return_value = (date(2025, 12, 1), time(10, 0), None)

            service = InterviewImportService(sample_df)
            service._load_reference_data()

            row = sample_df.iloc[0].copy()
            row['interview_type_label'] = 'Неизвестный тип'
            result = service._process_row(row, 0, {})

            assert result is True
            interview = Interview.objects.get(intern=services_intern)
            assert interview.interview_type == 'screening'
