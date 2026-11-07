"""
Тесты для сервисов приложения sad_intern.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.services - для группировки тестов сервисов
"""
import pytest
import pandas as pd
from datetime import date
from unittest.mock import MagicMock

from sad_intern.services import SadInternImportService
from sad_intern.models import SadIntern


@pytest.mark.django_db(databases=['default'])
@pytest.mark.services
class TestSadInternImportService:
    """Тесты для SadInternImportService."""

    def test_service_initialization(self, sample_df):
        """Проверка инициализации сервиса."""
        service = SadInternImportService(sample_df)
        assert service.df is not None
        assert service.errors_log == []
        assert service.created_count == 0
        assert service.skipped_count == 0

    def test_load_reference_data(self, sample_df, direction_python):
        """Проверка загрузки справочников."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()
        assert hasattr(service, 'managers_map')
        # managers_map теперь может быть пустым, если нет менеджеров в таблице managers
        assert isinstance(service.managers_map, dict)

    def test_map_status(self, sample_df):
        """Проверка маппинга статусов."""
        service = SadInternImportService(sample_df)
        assert service._map_status('Отказ') == 'rejected'
        assert service._map_status('Взяли') == 'accepted'
        assert service._map_status('Предложили') == 'offered'
        assert service._map_status('Уволили') == 'fired'
        assert service._map_status('Вышел на проект') == 'on_project'
        assert service._map_status('Неизвестный') is None
        assert service._map_status(None) is None

    def test_process_row_success(self, sample_df, test_intern, manager):
        """Проверка успешной обработки строки."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        # Обновляем sample_df чтобы использовать имя существующего менеджера
        sample_df.loc[0, 'manager_name'] = manager.full_name

        row = sample_df.iloc[0]
        # Используем пустой set для existing_keys, чтобы запись могла быть создана
        result = service._process_row(row, 0, set())

        assert result is True
        assert service.created_count == 1
        assert SadIntern.objects.filter(intern=test_intern).exists()

    def test_process_row_empty_name(self, sample_df):
        """Проверка обработки строки с пустым именем."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': '',
            'waiting_since': '01.11.2025',
            'telegram_username': '',
            'manager_name': '',
            'status': '',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1
        assert len(service.errors_log) > 0

    def test_process_row_empty_waiting_since(self, sample_df, test_intern):
        """Проверка обработки строки с пустой датой ожидания."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'waiting_since': '',
            'telegram_username': '',
            'manager_name': '',
            'status': '',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1

    def test_process_row_invalid_date_format(self, sample_df, test_intern):
        """Проверка обработки строки с невалидным форматом даты."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'waiting_since': 'невалидная дата',
            'telegram_username': '',
            'manager_name': '',
            'status': '',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1

    def test_process_row_intern_not_found(self, sample_df):
        """Проверка обработки строки с несуществующим студентом."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Несуществующий Студент',
            'waiting_since': '01.11.2025',
            'telegram_username': '',
            'manager_name': '',
            'status': '',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1

    def test_process_row_telegram_auto_prefix(self, sample_df, test_intern):
        """Проверка автоматического добавления @ к telegram."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'waiting_since': '01.11.2025',
            'telegram_username': 'ivan_without_at',
            'manager_name': '',
            'status': '',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is True
        sad_intern = SadIntern.objects.get(intern=test_intern)
        assert sad_intern.telegram_username == '@ivan_without_at'

    def test_process_row_telegram_already_has_prefix(self, sample_df, test_intern):
        """Проверка, что @ не дублируется."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'waiting_since': '01.11.2025',
            'telegram_username': '@ivan',
            'manager_name': '',
            'status': '',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is True
        sad_intern = SadIntern.objects.get(intern=test_intern)
        assert sad_intern.telegram_username == '@ivan'

    def test_process_row_manager_not_found(self, sample_df, test_intern):
        """Проверка обработки строки с несуществующим менеджером."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'waiting_since': '01.11.2025',
            'telegram_username': '',
            'manager_name': 'Несуществующий менеджер',
            'status': '',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1

    def test_process_row_without_manager(self, sample_df, test_intern):
        """Проверка обработки строки без менеджера."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'waiting_since': '01.11.2025',
            'telegram_username': '@ivan',
            'manager_name': '',
            'status': '',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is True
        sad_intern = SadIntern.objects.get(intern=test_intern)
        assert sad_intern.manager_email is None

    def test_process_row_invalid_status(self, sample_df, test_intern):
        """Проверка обработки строки с невалидным статусом."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'waiting_since': '01.11.2025',
            'telegram_username': '',
            'manager_name': '',
            'status': 'Неизвестный статус',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1

    def test_process_row_empty_status(self, sample_df, test_intern):
        """Проверка обработки строки с пустым статусом."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'waiting_since': '01.11.2025',
            'telegram_username': '',
            'manager_name': '',
            'status': '',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is True
        sad_intern = SadIntern.objects.get(intern=test_intern)
        assert sad_intern.status is None

    @pytest.mark.parametrize('header', ['JAVA', 'PYTHON', 'GO', 'СИСТЕМНЫЙ АНАЛИТИК'])
    def test_process_row_skip_header_rows(self, sample_df, header):
        """Строки-заголовки направлений пропускаются без ошибки."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': header,
            'waiting_since': '',
            'telegram_username': '',
            'manager_name': '',
            'status': '',
            'note': '',
        })
        result = service._process_row(row, 0, set())
        assert result is True

    def test_process_row_skip_empty_rows(self, sample_df):
        """Проверка пропуска пустых строк."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': '',
            'waiting_since': '',
            'telegram_username': '',
            'manager_name': '',
            'status': '',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is True  # Пустая строка пропускается без ошибки

    def test_process_row_with_note(self, sample_df, test_intern):
        """Проверка обработки строки с примечанием."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'waiting_since': '01.11.2025',
            'telegram_username': '',
            'manager_name': '',
            'status': '',
            'note': 'Тестовое примечание'
        })
        result = service._process_row(row, 0, set())

        assert result is True
        sad_intern = SadIntern.objects.get(intern=test_intern)
        assert sad_intern.note == 'Тестовое примечание'

    def test_run_method(self, sample_df, test_intern, test_intern2):
        """Проверка метода run."""
        service = SadInternImportService(sample_df)
        created, skipped, duplicates, errors = service.run()

        assert created == 1
        assert skipped == 1
        assert duplicates == 0
        assert len(errors) == 1

    def test_run_incremental_import(self, sample_df, test_intern, test_intern2, manager):
        """Проверка инкрементального импорта (не перезаписывает существующие данные)."""
        # Создаём существующего грустящего студента
        existing_sad = SadIntern.objects.create(
            intern=test_intern,
            waiting_since=date(2025, 10, 1),
        )

        # Обновляем sample_df чтобы использовать имя существующего менеджера
        sample_df.loc[0, 'manager_name'] = manager.full_name

        service = SadInternImportService(sample_df)
        created, skipped, duplicates, errors = service.run()

        # Проверяем, что существующая запись НЕ была удалена
        assert SadIntern.objects.filter(id=existing_sad.id).exists()
        # Проверяем, что дубликаты были обнаружены (test_intern уже есть в БД)
        assert duplicates >= 1

    def test_process_row_exception_handling(self, sample_df):
        """Проверка обработки исключений при обработке строки."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        # Создаём строку, которая вызовет исключение
        row = MagicMock()
        row.get.side_effect = Exception("Тестовая ошибка")

        result = service._process_row(row, 0, set())

        assert result is False
        assert service.skipped_count == 1
        assert len(service.errors_log) > 0

    def test_process_row_with_all_fields(self, sample_df, test_intern):
        """Проверка обработки строки со всеми заполненными полями (без manager_name, так как нет менеджеров)."""
        service = SadInternImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'waiting_since': '01.11.2025',
            'telegram_username': '@ivan_full',
            'manager_name': '',  # Пропускаем, так как нет менеджеров в БД
            'status': 'Взяли',
            'note': 'Полное примечание'
        })
        result = service._process_row(row, 0, set())

        assert result is True
        sad_intern = SadIntern.objects.get(intern=test_intern)
        assert sad_intern.telegram_username == '@ivan_full'
        assert sad_intern.manager_email is None
        assert sad_intern.status == 'accepted'
        assert sad_intern.note == 'Полное примечание'
        assert sad_intern.waiting_since == date(2025, 11, 1)

    def test_process_row_date_parsing(self, sample_df, test_intern):
        """Проверка парсинга различных форматов дат."""
        # Удаляем существующие записи для чистого теста
        SadIntern.objects.filter(intern=test_intern).delete()

        service = SadInternImportService(sample_df)
        service._load_reference_data()

        # Проверяем формат ДД.ММ.ГГГГ (используем прошлую дату)
        row = pd.Series({
            'full_name': 'Иван Иванов',
            'waiting_since': '15.10.2024',
            'telegram_username': '',
            'manager_name': '',
            'status': '',
            'note': ''
        })
        result = service._process_row(row, 0, set())

        assert result is True
        sad_intern = SadIntern.objects.get(intern=test_intern)
        assert sad_intern.waiting_since == date(2024, 10, 15)
