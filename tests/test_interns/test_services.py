"""
Тесты для сервисов приложения interns.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.services - для группировки тестов сервисов
"""
import pytest
import pandas as pd
from datetime import date
from unittest.mock import MagicMock

from interns.services import InternImportService, InternSyncImportService, RealInterviewDateImportService
from interns.models import Intern


@pytest.mark.django_db(databases=['default'])
@pytest.mark.services
class TestInternImportService:
    """Тесты для InternImportService."""

    def test_service_initialization(self, sample_df):
        """Проверка инициализации сервиса."""
        service = InternImportService(sample_df)
        assert service.df is not None
        assert service.errors_log == []
        assert service.created_count == 0
        assert service.skipped_count == 0

    def test_load_reference_data(self, sample_df, direction_python):
        """Проверка загрузки справочников."""
        service = InternImportService(sample_df)
        service._load_reference_data()
        assert hasattr(service, 'directions_map')
        assert hasattr(service, 'managers_map')
        assert len(service.directions_map) == 1
        assert isinstance(service.managers_map, dict)
        assert 'Python' in service.directions_map

    def test_process_row_success(self, sample_df, direction_python):
        """Проверка успешной обработки строки."""
        service = InternImportService(sample_df)
        service._load_reference_data()

        row = sample_df.iloc[0]
        result = service._process_row(row, 0, set())

        assert result is True
        assert service.created_count == 1
        assert Intern.objects.filter(full_name='Иван Иванов').exists()

    def test_process_row_empty_name(self, sample_df, direction_python):
        """Проверка обработки строки с пустым именем."""
        service = InternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({'full_name': ''})
        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1
        assert len(service.errors_log) == 1

    def test_process_row_missing_direction(self, sample_df):
        """Проверка обработки строки с отсутствующим направлением."""
        service = InternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Тест',
            'direction_name': 'Несуществующее направление',
            'manager_name': '',
            'type_of_training_label': 'outstaff',
            'date_of_birth_str': '01.01.2000',
            'date_of_receipt_str': '01.01.2025',
            'telegram_username': '',
            'group': 'GR1',
            'hiring_hr': 'HR1',
            'responsible_hr': 'HR2',
            'cv': '',
            'legend': '',
            'hr_feedback': '',
            'additional_contacts_str': '',
        })
        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1

    def test_process_row_missing_manager(self, sample_df, direction_python):
        """Проверка обработки строки с отсутствующим менеджером."""
        service = InternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Тест',
            'direction_name': 'Python',
            'manager_name': 'Несуществующий менеджер',
            'type_of_training_label': 'outstaff',
            'date_of_birth_str': '01.01.2000',
            'date_of_receipt_str': '01.01.2025',
            'telegram_username': '',
            'group': 'GR1',
            'hiring_hr': 'HR1',
            'responsible_hr': 'HR2',
            'cv': '',
            'legend': '',
            'hr_feedback': '',
            'additional_contacts_str': '',
        })
        result = service._process_row(row, 0, set())

        # Менеджер не обязателен, строка должна быть обработана
        assert result is True
        intern = Intern.objects.get(full_name='Тест')
        assert intern.manager_email is None

    def test_process_row_invalid_date_of_birth(self, sample_df, direction_python):
        """Проверка обработки строки с невалидной датой рождения."""
        service = InternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Тест',
            'direction_name': 'Python',
            'manager_name': '',
            'type_of_training_label': 'outstaff',
            'date_of_birth_str': 'невалидная дата',
            'date_of_receipt_str': '01.01.2025',
            'telegram_username': '',
            'group': 'GR1',
            'hiring_hr': 'HR1',
            'responsible_hr': 'HR2',
            'cv': '',
            'legend': '',
            'hr_feedback': '',
            'additional_contacts_str': '',
        })
        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1

    def test_process_row_invalid_type_of_training(self, sample_df, direction_python):
        """Проверка обработки строки с невалидным типом обучения."""
        service = InternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Тест',
            'direction_name': 'Python',
            'manager_name': '',
            'type_of_training_label': 'недопустимый тип',
            'date_of_birth_str': '01.01.2000',
            'date_of_receipt_str': '01.01.2025',
            'telegram_username': '',
            'group': 'GR1',
            'hiring_hr': 'HR1',
            'responsible_hr': 'HR2',
            'cv': '',
            'legend': '',
            'hr_feedback': '',
            'additional_contacts_str': '',
        })
        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1

    def test_process_row_extract_email(self, sample_df, direction_python):
        """Проверка извлечения email из дополнительных контактов."""
        service = InternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Тест Email',
            'direction_name': 'Python',
            'manager_name': '',
            'type_of_training_label': 'outstaff',
            'date_of_birth_str': '01.01.2000',
            'date_of_receipt_str': '01.01.2025',
            'telegram_username': '',
            'group': 'GR1',
            'hiring_hr': 'HR1',
            'responsible_hr': 'HR2',
            'cv': '',
            'legend': '',
            'hr_feedback': '',
            'additional_contacts_str': 'Связь: test@example.com или телефон',
        })
        result = service._process_row(row, 0, set())

        assert result is True
        intern = Intern.objects.get(full_name='Тест Email')
        assert intern.email == 'test@example.com'

    def test_run_method(self, sample_df, direction_python):
        """Проверка метода run: из 2 строк импортируется 1 (Backend→Python есть),
        вторая пропускается (Frontend не существует в БД)."""
        service = InternImportService(sample_df)
        created, skipped, duplicates, errors = service.run()

        assert created == 1
        assert skipped == 1
        assert duplicates == 0
        assert len(errors) == 1

    def test_run_incremental_import(self, sample_df, direction_python):
        """Проверка инкрементального импорта (не перезаписывает существующие данные)."""
        # Создаём существующего студента
        existing_intern = Intern.objects.create(
            full_name='Старый студент',
            direction=direction_python,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )

        service = InternImportService(sample_df)
        created, skipped, duplicates, errors = service.run()

        # Проверяем, что старый студент НЕ удалён (инкрементальный режим)
        assert Intern.objects.filter(id=existing_intern.id).exists()
        # Проверяем, что новые студенты добавлены
        assert created == 1

    def test_process_row_exception_handling(self, sample_df, direction_python):
        """Проверка обработки исключений при обработке строки."""
        service = InternImportService(sample_df)
        service._load_reference_data()

        # Создаём строку, которая вызовет исключение
        row = MagicMock()
        row.get.side_effect = Exception("Тестовая ошибка")

        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1
        assert len(service.errors_log) == 1

    def test_process_row_duplicate_in_existing_keys(self, sample_df, direction_python):
        """Дубликат в existing_keys → False, duplicates_count увеличивается."""
        service = InternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'direction_name': 'Python',
            'manager_name': '',
            'type_of_training_label': 'outstaff',
            'date_of_birth_str': '01.01.2000',
            'date_of_receipt_str': '01.01.2025',
            'telegram_username': '',
            'group': 'GR1',
            'hiring_hr': 'HR1',
            'responsible_hr': 'HR2',
            'cv': '',
            'legend': '',
            'hr_feedback': '',
            'additional_contacts_str': '',
        })
        direction_id = service.directions_map.get('Python')
        existing_keys = {('Иван Иванов', direction_id)}

        result = service._process_row(row, 0, existing_keys)

        assert result is False
        assert service.duplicates_count == 1
        assert service.created_count == 0

    def test_process_row_adds_key_after_create(self, sample_df, direction_python):
        """После создания студента ключ добавляется в existing_keys, повторная строка — дубликат."""
        service = InternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Уникальный Студент',
            'direction_name': 'Python',
            'manager_name': '',
            'type_of_training_label': 'outstaff',
            'date_of_birth_str': '01.01.2000',
            'date_of_receipt_str': '01.01.2025',
            'telegram_username': '',
            'group': 'GR1',
            'hiring_hr': 'HR1',
            'responsible_hr': 'HR2',
            'cv': '',
            'legend': '',
            'hr_feedback': '',
            'additional_contacts_str': '',
        })
        existing_keys = set()

        first = service._process_row(row, 0, existing_keys)
        second = service._process_row(row, 1, existing_keys)

        assert first is True
        assert second is False
        assert service.created_count == 1
        assert service.duplicates_count == 1

    def test_process_row_invalid_date_of_receipt_continues(self, sample_df, direction_python):
        """Невалидная date_of_receipt → только warning, студент создаётся с date_of_receipt=None."""
        service = InternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Студент Без Даты',
            'direction_name': 'Python',
            'manager_name': '',
            'type_of_training_label': 'outstaff',
            'date_of_birth_str': '01.01.2000',
            'date_of_receipt_str': 'не дата',
            'telegram_username': '',
            'group': 'GR1',
            'hiring_hr': 'HR1',
            'responsible_hr': 'HR2',
            'cv': '',
            'legend': '',
            'hr_feedback': '',
            'additional_contacts_str': '',
        })
        result = service._process_row(row, 0, set())

        assert result is True
        assert service.created_count == 1
        intern = Intern.objects.get(full_name='Студент Без Даты')
        assert intern.date_of_receipt is None

    def test_load_existing_keys(self, sample_df, direction_python):
        """_load_existing_keys возвращает set с ключами (full_name, direction_id) существующих студентов."""
        Intern.objects.create(
            full_name='Существующий Студент',
            direction=direction_python,
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
        )
        service = InternImportService(sample_df)

        keys = service._load_existing_keys()

        assert isinstance(keys, set)
        assert ('Существующий Студент', direction_python.id) in keys

    def test_run_progress_callback(self, sample_df, direction_python):
        """progress_callback вызывается для каждой строки DataFrame."""
        callback = MagicMock()
        service = InternImportService(sample_df, progress_callback=callback)
        service.run()

        total_rows = len(sample_df)
        assert callback.call_count == total_rows


@pytest.mark.django_db(databases=['default'])
@pytest.mark.services
class TestInternSyncImportService:
    """Тесты для InternSyncImportService (merge-only синхронизация)."""

    def _sync_row(self, **overrides):
        base = {
            'full_name': 'Синх Студент',
            'direction_name': 'Python',
            'manager_name': '',
            'type_of_training_label': 'outstaff',
            'date_of_birth_str': '01.01.2000',
            'date_of_receipt_str': '01.01.2025',
            'telegram_username': '',
            'group': 'GR1',
            'hiring_hr': 'HR1',
            'responsible_hr': 'HR2',
            'city': 'Москва',
            'cv': 'https://docs.google.com/document/d/test-cv',
            'cv_au': '',
            'legend': '',
            'hr_feedback': '',
            'additional_contacts_str': '',
        }
        base.update(overrides)
        return pd.Series(base)

    def test_sync_updates_empty_cv(self, direction_python):
        intern = Intern.objects.create(
            full_name='Синх Студент',
            direction=direction_python,
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            cv=None,
        )
        df = pd.DataFrame([self._sync_row()])
        service = InternSyncImportService(df)
        created_or_updated, skipped, unchanged, errors = service.run()

        assert created_or_updated == 1
        assert skipped == 0
        assert unchanged == 0
        assert errors == []
        intern.refresh_from_db()
        assert intern.cv == 'https://docs.google.com/document/d/test-cv'
        assert intern.city == 'Москва'

    def test_sync_does_not_overwrite_existing_cv(self, direction_python):
        existing_cv = 'https://site.example/cv-existing'
        intern = Intern.objects.create(
            full_name='Синх Студент',
            direction=direction_python,
            date_of_birth=date(2000, 1, 1),
            date_of_receipt=date(2025, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            city='Москва',
            cv=existing_cv,
        )
        df = pd.DataFrame([self._sync_row(cv='https://docs.google.com/other', city='Москва')])
        service = InternSyncImportService(df)
        created_or_updated, skipped, unchanged, errors = service.run()

        assert unchanged == 1
        assert created_or_updated == 0
        intern.refresh_from_db()
        assert intern.cv == existing_cv

    def test_sync_does_not_overwrite_existing_city(self, direction_python):
        intern = Intern.objects.create(
            full_name='Синх Студент',
            direction=direction_python,
            date_of_birth=date(2000, 1, 1),
            date_of_receipt=date(2025, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            city='Москва',
            cv='https://docs.google.com/existing-cv',
        )
        df = pd.DataFrame([self._sync_row(city='Казань', cv='https://docs.google.com/existing-cv')])
        service = InternSyncImportService(df)
        created_or_updated, skipped, unchanged, errors = service.run()

        assert unchanged == 1
        assert created_or_updated == 0
        intern.refresh_from_db()
        assert intern.city == 'Москва'

    def test_sync_cv_fallback_from_cv_au(self, direction_python):
        intern = Intern.objects.create(
            full_name='Синх Студент',
            direction=direction_python,
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
        )
        cv_au_url = 'https://docs.google.com/document/d/cv-au-only'
        df = pd.DataFrame([self._sync_row(cv='', cv_au=cv_au_url)])
        service = InternSyncImportService(df)
        created_or_updated, skipped, unchanged, errors = service.run()

        assert created_or_updated == 1
        intern.refresh_from_db()
        assert intern.cv == cv_au_url

    def test_sync_dry_run_does_not_persist(self, direction_python):
        df = pd.DataFrame([
            self._sync_row(full_name='Новый Dry Run', city='СПб'),
        ])
        service = InternSyncImportService(df, dry_run=True)
        created_or_updated, skipped, unchanged, errors = service.run()

        assert created_or_updated == 1
        assert Intern.objects.filter(full_name='Новый Dry Run').count() == 0


@pytest.mark.services
class TestParseDateFromCell:
    """Тесты для метода _parse_date_from_cell в RealInterviewDateImportService."""

    @pytest.fixture
    def service(self):
        df = pd.DataFrame({'ФИ': [], 'Дата': []})
        return RealInterviewDateImportService(df)

    @pytest.mark.parametrize('input_val, expected', [
        (None, None),
        (float('nan'), None),
        ('', None),
        ('nan', None),
        ('15.03.2025', date(2025, 3, 15)),
        ('текст (15.03.2025) конец', date(2025, 3, 15)),
        ('15.03.25', date(2025, 3, 15)),
        ('2025-03-15', date(2025, 3, 15)),
        ('без даты', None),
    ])
    def test_parse_date_from_cell(self, service, input_val, expected):
        """Проверка парсинга дат в различных форматах."""
        assert service._parse_date_from_cell(input_val) == expected

    def test_parse_date_from_cell_invalid_day(self, service):
        """Невалидная дата (32.03.2025) → None."""
        assert service._parse_date_from_cell('32.03.2025') is None

    def test_parse_date_no_year_returns_date(self, service):
        """Формат DD.MM без года → возвращает валидную дату с корректным днём и месяцем."""
        result = service._parse_date_from_cell('15.06')
        assert result is not None
        assert result.day == 15
        assert result.month == 6


@pytest.mark.django_db(databases=['default'])
@pytest.mark.services
class TestRealInterviewDateImportService:
    """Тесты для RealInterviewDateImportService."""

    def test_initialization(self, real_date_df):
        """Проверка инициализации: updated_count и created_count равны 0."""
        service = RealInterviewDateImportService(real_date_df)
        assert service.updated_count == 0
        assert service.created_count == 0
        assert service.errors_log == []

    def test_process_row_success(self, real_date_df, intern_for_date_import):
        """Студент найден, дата обновляется, updated_count увеличивается."""
        service = RealInterviewDateImportService(real_date_df)
        row = pd.Series({'ФИ': intern_for_date_import.full_name, 'Дата': '15.03.2025'})

        result = service._process_row(row, 0)

        assert result is True
        assert service.updated_count == 1
        intern_for_date_import.refresh_from_db()
        assert intern_for_date_import.real_interview_date == date(2025, 3, 15)

    def test_process_row_empty_name(self, real_date_df):
        """Пустое имя → False, ошибка в errors_log."""
        service = RealInterviewDateImportService(real_date_df)
        row = pd.Series({'ФИ': '', 'Дата': '15.03.2025'})

        result = service._process_row(row, 0)

        assert result is False
        assert len(service.errors_log) > 0

    def test_process_row_nan_name(self, real_date_df):
        """NaN имя → False, ошибка в errors_log."""
        service = RealInterviewDateImportService(real_date_df)
        row = pd.Series({'ФИ': float('nan'), 'Дата': '15.03.2025'})

        result = service._process_row(row, 0)

        assert result is False
        assert len(service.errors_log) > 0

    def test_process_row_intern_not_found(self, real_date_df):
        """Студент не найден в БД → False, skipped_count увеличивается."""
        service = RealInterviewDateImportService(real_date_df)
        row = pd.Series({'ФИ': 'Несуществующий Человек', 'Дата': '15.03.2025'})

        result = service._process_row(row, 0)

        assert result is False
        assert service.skipped_count == 1

    def test_process_row_date_already_same(self, real_date_df, intern_for_date_import):
        """Дата уже совпадает с существующей → False, duplicates_count увеличивается."""
        intern_for_date_import.real_interview_date = date(2025, 3, 15)
        intern_for_date_import.save(update_fields=['real_interview_date'])

        service = RealInterviewDateImportService(real_date_df)
        row = pd.Series({'ФИ': intern_for_date_import.full_name, 'Дата': '15.03.2025'})

        result = service._process_row(row, 0)

        assert result is False
        assert service.duplicates_count == 1

    def test_process_row_unparseable_date(self, real_date_df, intern_for_date_import):
        """Нераспознаваемая дата → False, ошибка в errors_log."""
        service = RealInterviewDateImportService(real_date_df)
        row = pd.Series({'ФИ': intern_for_date_import.full_name, 'Дата': 'не дата вовсе'})

        result = service._process_row(row, 0)

        assert result is False
        assert len(service.errors_log) > 0

    def test_process_row_updates_sad_intern(self, real_date_df, intern_for_date_import):
        """Если у студента есть SadIntern, его waiting_since обновляется."""
        from sad_intern.models import SadIntern
        sad = SadIntern.objects.create(
            intern=intern_for_date_import,
            waiting_since=date(2025, 1, 1),
        )

        service = RealInterviewDateImportService(real_date_df)
        row = pd.Series({'ФИ': intern_for_date_import.full_name, 'Дата': '15.03.2025'})
        service._process_row(row, 0)

        sad.refresh_from_db()
        assert sad.waiting_since == date(2025, 3, 15)

    def test_run_method(self, real_date_df, intern_for_date_import):
        """run() возвращает (updated, skipped, duplicates, errors) и обновляет студента."""
        service = RealInterviewDateImportService(real_date_df)
        updated, skipped, duplicates, errors = service.run()

        assert updated == 1
        assert skipped == 0
        assert duplicates == 0
        assert errors == []
        intern_for_date_import.refresh_from_db()
        assert intern_for_date_import.real_interview_date == date(2025, 3, 15)
