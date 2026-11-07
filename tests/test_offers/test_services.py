"""
Тесты для сервисов приложения offers.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.services - для группировки тестов сервисов
"""
import pytest
import pandas as pd
from decimal import Decimal
from unittest.mock import patch

from offers.services import OfferImportService
from offers.models import Offer


@pytest.mark.django_db(databases=['default'])
@pytest.mark.services
class TestOfferImportService:
    """Тесты для OfferImportService."""

    def test_service_initialization(self, sample_df):
        """Проверка инициализации сервиса."""
        service = OfferImportService(sample_df)
        assert service.df is not None
        assert service.errors_log == []
        assert service.created_count == 0
        assert service.skipped_count == 0
        assert service.current_month is None
        assert service.current_year == 2025

    def test_load_reference_data(self, sample_df, direction_backend):
        """Проверка загрузки справочников."""
        service = OfferImportService(sample_df)
        service._load_reference_data()
        assert hasattr(service, 'directions_map')
        assert hasattr(service, 'managers_map')
        assert len(service.directions_map) > 0

    @pytest.mark.parametrize('raw, expected', [
        ('150000', 150000.0),
        ('120000.50', 120000.50),
        ('150 000', 150000.0),
        ('1 500 000', 1500000.0),
        ('140000/160000', 160000.0),
        ('100 000 / 150 000', 150000.0),
        ('140000\\160000', 160000.0),
        ('₽150000', 150000.0),
        ('150,000', 150000.0),
        ('1,500,000.50', 1500000.50),
        ('', None),
        ('invalid', None),
    ])
    def test_parse_amount(self, sample_df, raw, expected):
        """Проверка парсинга суммы из строки."""
        service = OfferImportService(sample_df)
        assert service._parse_amount(raw) == expected

    def test_process_row_valid(self, sample_df, intern, direction_backend):
        """Проверка обработки валидной строки."""
        service = OfferImportService(sample_df)
        service._load_reference_data()
        service.current_month = 1
        service.current_year = 2025

        row = pd.Series({
            'full_name': intern.full_name,
            'direction_name': 'Backend',
            'company_name': 'Google',
            'amount': '150000'
        })
        existing_keys = set()

        # Патчим в месте использования, а не в месте определения
        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            result = service._process_row(row, 0, existing_keys)

        assert result is True
        assert service.created_count == 1
        assert Offer.objects.filter(company='Google').exists()

    def test_process_row_month_header(self, sample_df):
        """Проверка обработки заголовка месяца."""
        service = OfferImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'ФЕВРАЛЬ',
            'direction_name': '',
            'company_name': '',
            'amount': ''
        })
        existing_keys = set()

        result = service._process_row(row, 0, existing_keys)
        assert result is True
        assert service.current_month == 2  # Февраль

    def test_process_row_empty(self, sample_df):
        """Проверка обработки пустой строки."""
        service = OfferImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': '',
            'direction_name': '',
            'company_name': '',
            'amount': ''
        })
        existing_keys = set()

        result = service._process_row(row, 0, existing_keys)
        assert result is True  # Пустые строки пропускаются

    def test_process_row_missing_full_name(self, sample_df):
        """Проверка обработки строки без ФИО."""
        service = OfferImportService(sample_df)
        service._load_reference_data()
        service.current_month = 1

        row = pd.Series({
            'full_name': '',
            'direction_name': 'Backend',
            'company_name': 'Google',
            'amount': '150000'
        })
        existing_keys = set()

        result = service._process_row(row, 0, existing_keys)
        assert result is False
        assert len(service.errors_log) > 0

    def test_process_row_missing_direction(self, sample_df, intern):
        """Проверка обработки строки без направления."""
        service = OfferImportService(sample_df)
        service._load_reference_data()
        service.current_month = 1

        row = pd.Series({
            'full_name': intern.full_name,
            'direction_name': '',
            'company_name': 'Google',
            'amount': '150000'
        })
        existing_keys = set()

        result = service._process_row(row, 0, existing_keys)
        assert result is False
        assert len(service.errors_log) > 0

    def test_process_row_default_company(self, sample_df, intern, direction_backend):
        """Проверка обработки строки без компании (ставится дефолтное значение)."""
        service = OfferImportService(sample_df)
        service._load_reference_data()
        service.current_month = 1

        row = pd.Series({
            'full_name': intern.full_name,
            'direction_name': 'Backend',
            'company_name': '',
            'amount': '150000'
        })
        existing_keys = set()

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            result = service._process_row(row, 0, existing_keys)

        assert result is True
        # Компания должна быть установлена в '—'
        offer = Offer.objects.get(intern=intern)
        assert offer.company == '—'

    def test_process_row_zero_amount(self, sample_df, intern, direction_backend):
        """Проверка обработки строки с нулевой суммой."""
        service = OfferImportService(sample_df)
        service._load_reference_data()
        service.current_month = 1

        row = pd.Series({
            'full_name': intern.full_name,
            'direction_name': 'Backend',
            'company_name': 'Google',
            'amount': ''
        })
        existing_keys = set()

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            result = service._process_row(row, 0, existing_keys)

        assert result is True
        offer = Offer.objects.get(intern=intern)
        assert offer.amount == 0.0

    def test_process_row_invalid_amount(self, sample_df, intern, direction_backend):
        """Проверка обработки строки с невалидной суммой."""
        service = OfferImportService(sample_df)
        service._load_reference_data()
        service.current_month = 1

        row = pd.Series({
            'full_name': intern.full_name,
            'direction_name': 'Backend',
            'company_name': 'Google',
            'amount': 'invalid'
        })
        existing_keys = set()

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            result = service._process_row(row, 0, existing_keys)

        assert result is False
        assert len(service.errors_log) > 0

    def test_process_row_direction_not_found(self, sample_df, intern):
        """Проверка обработки строки с несуществующим направлением."""
        service = OfferImportService(sample_df)
        service._load_reference_data()
        service.current_month = 1

        row = pd.Series({
            'full_name': intern.full_name,
            'direction_name': 'NonexistentDirection',
            'company_name': 'Google',
            'amount': '150000'
        })
        existing_keys = set()

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            result = service._process_row(row, 0, existing_keys)

        assert result is False
        assert len(service.errors_log) > 0

    def test_process_row_intern_not_found(self, sample_df, direction_backend):
        """Проверка обработки строки с несуществующим студентом."""
        service = OfferImportService(sample_df)
        service._load_reference_data()
        service.current_month = 1

        row = pd.Series({
            'full_name': 'Несуществующий Студент',
            'direction_name': 'Backend',
            'company_name': 'Google',
            'amount': '150000'
        })
        existing_keys = set()

        with patch('core.intern_utils.find_intern_by_name', return_value=None):
            result = service._process_row(row, 0, existing_keys)

        assert result is False
        assert len(service.errors_log) > 0

    def test_process_row_no_month_set(self, sample_df, intern, direction_backend):
        """Проверка обработки строки без установленного месяца."""
        service = OfferImportService(sample_df)
        service._load_reference_data()
        # Не устанавливаем current_month

        row = pd.Series({
            'full_name': intern.full_name,
            'direction_name': 'Backend',
            'company_name': 'Google',
            'amount': '150000'
        })
        existing_keys = set()

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            result = service._process_row(row, 0, existing_keys)

        assert result is False
        assert len(service.errors_log) > 0

    def test_run_service_success(self, intern, direction_backend):
        """Проверка полного запуска сервиса."""
        df = pd.DataFrame({
            'full_name': ['ФЕВРАЛЬ', intern.full_name],
            'direction_name': ['', 'Backend'],
            'company_name': ['', 'Google'],
            'amount': ['', '150000']
        })

        service = OfferImportService(df)

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            created, skipped, duplicates, errors = service.run()

        assert created == 1
        offer = Offer.objects.first()
        assert offer.company == 'Google'
        assert offer.month == 2  # Февраль

    def test_run_service_with_errors(self, intern, direction_backend):
        """Проверка запуска сервиса с ошибками."""
        df = pd.DataFrame({
            'full_name': ['ФЕВРАЛЬ', intern.full_name, 'Несуществующий'],
            'direction_name': ['', 'Backend', 'Backend'],
            'company_name': ['', 'Google', 'Yandex'],
            'amount': ['', '150000', '120000']
        })

        service = OfferImportService(df)

        with patch('core.intern_utils.find_intern_by_name') as mock_find:
            # Первый вызов возвращает intern, второй None
            mock_find.side_effect = [intern, None]
            created, skipped, duplicates, errors = service.run()

        assert created == 1
        assert len(errors) == 1

    def test_run_service_incremental_import(self, intern, direction_backend):
        """Проверка инкрементального импорта (не перезаписывает существующие данные)."""
        # Создаём существующий оффер
        existing_offer = Offer.objects.create(
            intern=intern,
            direction=direction_backend,
            company='OldCompany',
            amount=Decimal('100000.00'),
            month=1,
            year=2025
        )
        assert Offer.objects.count() == 1

        df = pd.DataFrame({
            'full_name': ['ФЕВРАЛЬ', intern.full_name],
            'direction_name': ['', 'Backend'],
            'company_name': ['', 'NewCompany'],
            'amount': ['', '150000']
        })

        service = OfferImportService(df)

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            created, skipped, duplicates, errors = service.run()

        # Проверяем, что старый оффер НЕ был удалён (инкрементальный режим)
        assert Offer.objects.filter(id=existing_offer.id).exists()
        # После импорта должно быть два оффера (старый + новый)
        assert Offer.objects.count() == 2
        assert Offer.objects.filter(company='NewCompany').exists()

    def test_run_service_with_progress_callback(self, intern, direction_backend):
        """Проверка работы callback для прогресса."""
        df = pd.DataFrame({
            'full_name': ['ФЕВРАЛЬ', intern.full_name],
            'direction_name': ['', 'Backend'],
            'company_name': ['', 'Google'],
            'amount': ['', '150000']
        })

        progress_calls = []

        def progress_callback(current, total):
            progress_calls.append((current, total))

        service = OfferImportService(df, progress_callback=progress_callback)

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            service.run()

        # Проверяем, что callback был вызван для каждой строки df
        assert len(progress_calls) == 2

    def test_map_direction_name(self, sample_df):
        """Проверка маппинга названий направлений."""
        service = OfferImportService(sample_df)
        # 'Backend' маппится в 'Python' через DIRECTION_MAPPING
        assert service._map_direction_name('Backend') == 'Python'
        # Имя, отсутствующее в маппинге, возвращается без изменений
        assert service._map_direction_name('Frontend') == 'Frontend'
        # Пустая строка возвращает None
        assert service._map_direction_name('') is None

    def test_process_row_with_exception(self, sample_df, intern):
        """Проверка обработки исключения в процессе обработки строки."""
        service = OfferImportService(sample_df)
        service._load_reference_data()
        service.current_month = 1

        row = pd.Series({
            'full_name': intern.full_name,
            'direction_name': 'Backend',
            'company_name': 'Google',
            'amount': '150000'
        })
        existing_keys = set()

        # Мокируем исключение
        with patch('core.intern_utils.find_intern_by_name', side_effect=Exception('Test error')):
            result = service._process_row(row, 0, existing_keys)

        assert result is False
        assert len(service.errors_log) > 0

    def test_service_current_year_default(self, sample_df):
        """Проверка дефолтного значения года."""
        service = OfferImportService(sample_df)
        assert service.current_year == 2025

    def test_multiple_month_headers_in_import(self, intern, direction_backend):
        """Проверка импорта с несколькими месяцами."""
        df = pd.DataFrame({
            'full_name': ['ЯНВАРЬ', intern.full_name, 'ФЕВРАЛЬ', intern.full_name],
            'direction_name': ['', 'Backend', '', 'Backend'],
            'company_name': ['', 'Google', '', 'Yandex'],
            'amount': ['', '150000', '', '120000']
        })

        service = OfferImportService(df)

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            created, skipped, duplicates, errors = service.run()

        assert created == 2
        offers = Offer.objects.all().order_by('month')
        assert offers[0].month == 1  # Январь
        assert offers[1].month == 2  # Февраль
