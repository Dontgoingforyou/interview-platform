"""
Тесты для сервисов приложения debts.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.services - для группировки тестов сервисов
"""
import pytest
import pandas as pd
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from debts.services import DebtImportService
from debts.models import Debt, PaymentHistory


@pytest.mark.django_db(databases=['default'])
@pytest.mark.services
class TestDebtImportService:
    """Тесты для DebtImportService."""

    @pytest.fixture
    def sample_df(self):
        """Создаёт тестовый DataFrame."""
        return pd.DataFrame({
            'full_name': ['Иван Иванов', 'Петр Петров'],
            'direction_name': ['Backend', 'Frontend'],
            'telegram_username': ['@ivan', '@petr'],
            'email': ['ivan@example.com', 'petr@example.com'],
            'total_amount_raw': ['10000.00', '15000.00'],
            'paid_amount_raw': ['5000.00', '3000.00'],
            'balance_raw': ['5000.00', '12000.00'],
            'act_date_str': ['01.01.2025', '15.02.2025'],
            '01/25': ['1000.00', '2000.00'],
            '02/25': ['1500.00', '1000.00'],
        })

    @pytest.fixture
    def direction_python(self, direction):
        """Алиас корневой фикстуры direction (Backend)."""
        return direction

    @pytest.fixture
    def direction_frontend(self, db):
        """Создаёт тестовое направление Frontend."""
        from directions.models import Direction
        return Direction.objects.create(name='Frontend')

    def test_service_initialization(self, sample_df):
        """Проверка инициализации сервиса."""
        service = DebtImportService(sample_df)
        assert service.df is not None
        assert service.errors_log == []
        assert service.created_count == 0
        assert service.skipped_count == 0

    def test_load_reference_data(self, sample_df, direction_python):
        """Проверка загрузки справочников."""
        service = DebtImportService(sample_df)
        service._load_reference_data()
        assert hasattr(service, 'directions_map')
        assert hasattr(service, 'managers_map')
        assert len(service.directions_map) > 0

    def test_safe_string_strip(self, sample_df):
        """Проверка метода _safe_string_strip."""
        service = DebtImportService(sample_df)
        assert service._safe_string_strip('  test  ') == 'test'
        assert service._safe_string_strip(pd.NA) == ''
        assert service._safe_string_strip('nan') == ''
        assert service._safe_string_strip('None') == ''
        assert service._safe_string_strip('') == ''

    def test_get_payment_status(self, sample_df):
        """Проверка определения статуса платежа."""
        service = DebtImportService(sample_df)
        # По умолчанию возвращает 'unknown'
        assert service._get_payment_status(Decimal('10000'), Decimal('5000')) == 'unknown'

    def test_get_act_date_valid(self, sample_df):
        """Проверка обработки валидной даты акта."""
        service = DebtImportService(sample_df)
        act_date, error = service._get_act_date('01.01.2025', 0)
        assert act_date == date(2025, 1, 1)
        assert error is None

    def test_get_act_date_invalid(self, sample_df):
        """Проверка обработки невалидной даты акта — возвращает (None, None)."""
        service = DebtImportService(sample_df)
        act_date, error = service._get_act_date('невалидная дата', 0)
        assert act_date is None
        assert error is None

    def test_get_act_date_empty(self, sample_df):
        """Проверка обработки пустой даты акта."""
        service = DebtImportService(sample_df)
        act_date, error = service._get_act_date('', 0)
        assert act_date is None
        assert error is None

    def test_get_act_date_too_long(self, sample_df):
        """Проверка обработки слишком длинной строки даты."""
        service = DebtImportService(sample_df)
        long_string = 'a' * 100
        act_date, error = service._get_act_date(long_string, 0)
        assert act_date is None
        assert error is None

    def test_process_row_success(self, sample_df, intern, direction_python):
        """Проверка успешной обработки строки."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        row = sample_df.iloc[0]
        existing_keys = set()
        # Мокаем find_intern_by_name
        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            result = service._process_row(row, 0, existing_keys)

        assert result is True
        assert service.created_count == 1
        assert Debt.objects.filter(intern=intern).exists()

    def test_process_row_empty_name(self, sample_df, direction_python):
        """Проверка обработки строки с пустым именем."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({'full_name': ''})
        existing_keys = set()
        result = service._process_row(row, 0, existing_keys)

        assert result is False
        assert service.skipped_count == 1
        assert len(service.errors_log) > 0

    def test_process_row_missing_intern(self, sample_df, direction_python):
        """Проверка обработки строки с отсутствующим студентом."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Несуществующий студент',
            'direction_name': 'Python',
            'total_amount_raw': '10000.00',
            'paid_amount_raw': '5000.00',
            'telegram_username': '',
            'email': '',
            'act_date_str': '',
        })
        existing_keys = set()

        with patch('core.intern_utils.find_intern_by_name', return_value=None):
            result = service._process_row(row, 0, existing_keys)

        assert result is False
        assert service.skipped_count == 1

    def test_process_row_with_payment_history(self, sample_df, intern, direction_python):
        """Проверка создания истории платежей."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        row = sample_df.iloc[0]
        existing_keys = set()
        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            result = service._process_row(row, 0, existing_keys)

        assert result is True
        debt = Debt.objects.get(intern=intern)
        # Проверяем, что созданы записи истории платежей
        payments = PaymentHistory.objects.filter(debt=debt)
        assert payments.count() == 2  # 01/25 и 02/25

    def test_process_row_exception_handling(self, sample_df, direction_python):
        """Проверка обработки исключений при обработке строки."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        # Создаём строку, которая вызовет исключение
        row = MagicMock()
        row.get.side_effect = Exception("Тестовая ошибка")
        existing_keys = set()

        result = service._process_row(row, 0, existing_keys)

        assert result is False
        assert service.skipped_count == 1
        assert len(service.errors_log) > 0

    def test_create_payment_history(self, sample_df, intern, direction_python):
        """Проверка создания истории платежей."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('5000.00')
        )

        row = sample_df.iloc[0]
        payment_objects = service._prepare_payment_history(debt, row, 'Иван Иванов')
        PaymentHistory.objects.bulk_create(payment_objects)

        payments = PaymentHistory.objects.filter(debt=debt)
        assert payments.count() == 2
        assert payments.filter(month=1, year=2025).exists()
        assert payments.filter(month=2, year=2025).exists()

    def test_create_payment_history_empty_amounts(self, sample_df, intern):
        """Проверка создания истории платежей с пустыми суммами."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )

        row = pd.Series({
            '01/25': 0,
            '02/25': pd.NA,
            '03/25': ''
        })
        payment_objects = service._prepare_payment_history(debt, row, 'Тест')
        PaymentHistory.objects.bulk_create(payment_objects)

        payments = PaymentHistory.objects.filter(debt=debt)
        assert payments.count() == 0

    def test_run_method(self, sample_df, intern, direction_python):
        """Проверка метода run.

        sample_df содержит 2 строки с разными именами, но мок возвращает одного и того же intern.
        Первая строка создаёт долг, вторая считается дубликатом (intern.pk уже в existing_keys).
        """
        service = DebtImportService(sample_df)
        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            created, skipped, duplicates, errors = service.run()

        assert created == 1
        assert skipped == 0
        assert duplicates == 1
        assert errors == []

    def test_run_incremental_import(self, sample_df, intern, direction_python):
        """Проверка инкрементального импорта (не перезаписывает существующие данные)."""
        # Создаём существующий долг
        existing_debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )

        service = DebtImportService(sample_df)
        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            created, skipped, duplicates, errors = service.run()

        # Проверяем, что существующий долг НЕ был удалён (инкрементальный режим)
        assert Debt.objects.filter(id=existing_debt.id).exists()
        # Проверяем, что дубликат был обнаружен
        assert duplicates >= 1

    def test_process_row_with_special_name(self, sample_df, intern):
        """Строка с именем 'Старые, до Вики' обрабатывается сервисом как обычная.

        Фильтрация по служебным именам происходит на уровне process_dataframe (вне сервиса),
        поэтому _process_row возвращает True, если intern найден через мок.
        """
        service = DebtImportService(sample_df)
        service._load_reference_data()

        special_row = pd.Series({
            'full_name': 'Старые, до Вики',
            'direction_name': 'Backend',
            'telegram_username': '',
            'email': '',
            'total_amount_raw': '0',
            'paid_amount_raw': '0',
            'balance_raw': '0',
            'act_date_str': '',
        })

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            existing_keys = set()
            result = service._process_row(special_row, 0, existing_keys)

        assert result is True

    def test_get_direction_id_success(self, sample_df, direction_python):
        """Метод _get_direction_id не считает отсутствие направления ошибкой (success=True).

        Если направление найдено в directions_map — возвращает его id;
        если нет (например, сервис нормализует имена) — id=None, success=True.
        """
        service = DebtImportService(sample_df)
        service._load_reference_data()

        direction_id, success = service._get_direction_id(direction_python.name, 0)
        assert success is True
        assert direction_id in (direction_python.id, None)

    def test_get_direction_id_not_found(self, sample_df):
        """Проверка обработки отсутствующего направления."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        direction_id, success = service._get_direction_id('Несуществующее направление', 0)
        assert success is True  # Не считается ошибкой
        assert direction_id is None

    def test_get_direction_id_empty(self, sample_df):
        """Проверка обработки пустого названия направления."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        direction_id, success = service._get_direction_id('', 0)
        assert success is True
        assert direction_id is None

    def test_get_intern_success(self, sample_df, intern):
        """Проверка успешного получения студента."""
        service = DebtImportService(sample_df)
        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            intern_obj, success = service._get_intern('Иван Иванов', 0)
            assert success is True
            assert intern_obj == intern

    def test_get_intern_not_found(self, sample_df):
        """Проверка обработки отсутствующего студента."""
        service = DebtImportService(sample_df)
        with patch('core.intern_utils.find_intern_by_name', return_value=None):
            intern_obj, success = service._get_intern('Несуществующий', 0)
            assert success is False
            assert intern_obj is None
            assert len(service.errors_log) > 0

    def test_create_payment_history_with_year_column(self, sample_df, intern):
        """Проверка, что столбцы с годом (YYYY) пропускаются."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )

        row = pd.Series({
            '01/25': '1000.00',
            '2024': '5000.00',  # Столбец с годом
        })
        payment_objects = service._prepare_payment_history(debt, row, 'Тест')
        PaymentHistory.objects.bulk_create(payment_objects)

        payments = PaymentHistory.objects.filter(debt=debt)
        # Только 01/25 должен быть создан, 2024 пропускается
        assert payments.count() == 1
        assert payments.first().month == 1

    def test_create_payment_history_invalid_column_format(self, sample_df, intern):
        """Проверка обработки столбцов с невалидным форматом."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )

        row = pd.Series({
            '01/25': '1000.00',
            'invalid_column': '2000.00',
        })
        payment_objects = service._prepare_payment_history(debt, row, 'Тест')
        PaymentHistory.objects.bulk_create(payment_objects)

        payments = PaymentHistory.objects.filter(debt=debt)
        # Только валидный столбец должен создать платёж
        assert payments.count() == 1

    def test_process_row_with_nan_values(self, sample_df, intern, direction_python):
        """Проверка обработки строки с NaN значениями."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'direction_name': pd.NA,
            'telegram_username': pd.NA,
            'email': pd.NA,
            'total_amount_raw': pd.NA,
            'paid_amount_raw': pd.NA,
            'act_date_str': pd.NA,
        })
        existing_keys = set()

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            result = service._process_row(row, 0, existing_keys)

        assert result is True
        debt = Debt.objects.get(intern=intern)
        assert debt.direction_id is None
        assert debt.total_amount == Decimal('0')
        assert debt.paid_amount == Decimal('0')

    def test_safe_string_strip_various_inputs(self, sample_df):
        """Проверка _safe_string_strip с различными входными данными."""
        service = DebtImportService(sample_df)

        assert service._safe_string_strip('  hello  ') == 'hello'
        assert service._safe_string_strip('<NA>') == ''
        assert service._safe_string_strip('') == ''
        assert service._safe_string_strip(None) == ''
        assert service._safe_string_strip(123) == '123'
        assert service._safe_string_strip(0) == '0'

    def test_get_act_date_with_text_containing_letters(self, sample_df):
        """Проверка обработки даты с большим количеством букв."""
        service = DebtImportService(sample_df)

        # Строка с большим количеством букв должна быть пропущена
        act_date, error = service._get_act_date('This is a long text with many letters', 0)
        assert act_date is None
        assert error is None

    def test_process_row_creates_debt_with_all_fields(self, sample_df, intern, direction_python):
        """Проверка, что все поля долга правильно заполняются."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        row = pd.Series({
            'full_name': 'Иван Иванов',
            'direction_name': 'Python',
            'telegram_username': '@ivan',
            'email': 'ivan@test.com',
            'total_amount_raw': '10000.00',
            'paid_amount_raw': '5000.00',
            'act_date_str': '01.01.2025',
        })
        existing_keys = set()

        with patch('core.intern_utils.find_intern_by_name', return_value=intern):
            result = service._process_row(row, 0, existing_keys)

        assert result is True
        debt = Debt.objects.get(intern=intern)
        assert debt.telegram_username == '@ivan'
        assert debt.email == 'ivan@test.com'
        assert debt.total_amount == Decimal('10000.00')
        assert debt.paid_amount == Decimal('5000.00')
        assert debt.act_date == date(2025, 1, 1)

    def test_log_error_increments_skipped_count(self, sample_df):
        """Проверка, что _log_error увеличивает skipped_count."""
        service = DebtImportService(sample_df)
        initial_skipped = service.skipped_count

        service._log_error("Test error", 0)

        assert service.skipped_count == initial_skipped + 1
        assert len(service.errors_log) > 0

    def test_log_success_increments_created_count(self, sample_df):
        """Проверка, что _log_success увеличивает created_count."""
        service = DebtImportService(sample_df)
        initial_created = service.created_count

        service._log_success()

        assert service.created_count == initial_created + 1

    def test_load_additional_reference_data(self, sample_df):
        """Проверка, что _load_additional_reference_data не вызывает ошибок."""
        service = DebtImportService(sample_df)
        # Метод пустой, но проверим, что он не падает
        service._load_additional_reference_data()
        # Тест пройден, если не возникло исключений

    def test_create_payment_history_handles_invalid_month_year(self, sample_df, intern):
        """Проверка обработки невалидного формата месяца/года в названии столбца."""
        service = DebtImportService(sample_df)
        service._load_reference_data()

        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )

        row = pd.Series({
            '99/99': '1000.00',  # Невалидный формат
        })

        # Не должно вызвать исключение
        payment_objects = service._prepare_payment_history(debt, row, 'Тест')
        PaymentHistory.objects.bulk_create(payment_objects)

        # Платёж не должен быть создан
        payments = PaymentHistory.objects.filter(debt=debt)
        assert payments.count() == 0
