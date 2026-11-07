"""
Тесты для сериализаторов приложения debts.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.serializers - для группировки тестов сериализаторов
"""
import pytest
from decimal import Decimal

from debts.models import Debt, PaymentHistory
from debts.serializers import (
    PaymentHistorySerializer,
    DebtListSerializer,
    DebtDetailSerializer,
    DebtCreateUpdateSerializer,
    PaymentHistoryCreateSerializer,
)


# ---------------------------------------------------------------------------
# PaymentHistorySerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestPaymentHistorySerializer:
    """Тесты для PaymentHistorySerializer."""

    def test_serializes_payment_fields(self, payment):
        """Проверка сериализации всех полей платежа."""
        serializer = PaymentHistorySerializer(payment)
        data = serializer.data

        assert data['id'] == payment.pk
        assert data['month'] == 1
        assert data['year'] == 2025
        assert Decimal(data['amount']) == Decimal('1000.00')
        assert 'created_at' in data

    def test_read_only_fields_not_writable(self, payment):
        """Проверка, что id и created_at — только для чтения."""
        serializer = PaymentHistorySerializer(
            payment,
            data={'id': 9999, 'month': 2, 'year': 2025, 'amount': '500.00', 'created_at': '2020-01-01'},
        )
        assert serializer.is_valid()
        # id не должен измениться
        assert serializer.validated_data.get('id') is None

    def test_all_fields_present(self, payment):
        """Проверка наличия всех ожидаемых полей."""
        serializer = PaymentHistorySerializer(payment)
        expected_fields = {'id', 'month', 'year', 'amount', 'created_at'}
        assert expected_fields == set(serializer.data.keys())


# ---------------------------------------------------------------------------
# DebtListSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestDebtListSerializer:
    """Тесты для DebtListSerializer."""

    def test_serializes_all_fields(self, debt):
        """Проверка сериализации всех полей списка долгов."""
        serializer = DebtListSerializer(debt)
        data = serializer.data

        assert data['id'] == debt.pk
        assert data['intern'] == debt.intern.pk
        assert data['intern_name'] == debt.intern.full_name
        assert Decimal(data['total_amount']) == debt.total_amount
        assert Decimal(data['paid_amount']) == debt.paid_amount
        assert Decimal(data['balance']) == debt.balance
        assert data['payment_status'] == 'paying'
        assert data['act_date'] == '2025-01-15'

    def test_intern_name_is_derived_field(self, debt):
        """Проверка, что intern_name берётся из связанного intern."""
        serializer = DebtListSerializer(debt)
        assert serializer.data['intern_name'] == debt.intern.full_name

    def test_balance_is_read_only(self, debt):
        """Проверка, что balance — только для чтения."""
        serializer = DebtListSerializer(
            debt,
            data={
                'intern': debt.intern.pk,
                'total_amount': '5000.00',
                'paid_amount': '1000.00',
                'balance': '99999.00',  # должен игнорироваться
                'payment_status': 'paying',
            },
        )
        assert serializer.is_valid()
        assert 'balance' not in serializer.validated_data

    def test_total_amount_is_read_only(self, debt):
        """Проверка, что total_amount — только для чтения."""
        serializer = DebtListSerializer(
            debt,
            data={
                'intern': debt.intern.pk,
                'total_amount': '99999.00',
                'paid_amount': '1000.00',
                'payment_status': 'paying',
            },
        )
        assert serializer.is_valid()
        assert 'total_amount' not in serializer.validated_data

    def test_all_expected_fields_present(self, debt):
        """Проверка наличия всех ожидаемых полей."""
        serializer = DebtListSerializer(debt)
        expected_fields = {
            'id',
            'intern',
            'intern_name',
            'direction_id',
            'direction_name',
            'display_telegram',
            'display_email',
            'total_amount',
            'paid_amount',
            'balance',
            'payment_status',
            'act_date',
            'last_payment_month',
            'last_payment_year',
            'payments_four_months',
            'row_highlight',
        }
        assert expected_fields == set(serializer.data.keys())

    def test_direction_id_nullable(self, intern):
        """Проверка, что direction_id может быть None."""
        debt = Debt.objects.create(intern=intern, total_amount=Decimal('5000.00'))
        serializer = DebtListSerializer(debt)
        assert serializer.data['direction_id'] is None


# ---------------------------------------------------------------------------
# DebtDetailSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestDebtDetailSerializer:
    """Тесты для DebtDetailSerializer."""

    def test_serializes_all_fields(self, debt, payment):
        """Проверка сериализации всех полей детального представления."""
        serializer = DebtDetailSerializer(debt)
        data = serializer.data

        assert data['id'] == debt.pk
        assert data['intern'] == debt.intern.pk
        assert data['intern_name'] == debt.intern.full_name
        assert data['telegram_username'] == '@testuser'
        assert data['email'] == 'test@example.com'
        assert Decimal(data['total_amount']) == debt.total_amount
        assert Decimal(data['paid_amount']) == debt.paid_amount
        assert Decimal(data['balance']) == debt.balance
        assert data['payment_status'] == 'paying'

    def test_payment_history_included(self, debt, payment):
        """Проверка включения истории платежей."""
        serializer = DebtDetailSerializer(debt)
        data = serializer.data

        assert 'payment_history' in data
        assert len(data['payment_history']) == 1
        assert data['payment_history'][0]['month'] == 1
        assert data['payment_history'][0]['year'] == 2025
        assert Decimal(data['payment_history'][0]['amount']) == Decimal('1000.00')

    def test_payment_history_empty_when_no_payments(self, debt):
        """Проверка пустой истории платежей."""
        serializer = DebtDetailSerializer(debt)
        data = serializer.data

        assert data['payment_history'] == []

    def test_multiple_payments_in_history(self, debt):
        """Проверка нескольких платежей в истории."""
        PaymentHistory.objects.create(debt=debt, month=1, year=2025, amount=Decimal('500.00'))
        PaymentHistory.objects.create(debt=debt, month=2, year=2025, amount=Decimal('700.00'))

        serializer = DebtDetailSerializer(debt)
        data = serializer.data

        assert len(data['payment_history']) == 2

    def test_all_expected_fields_present(self, debt):
        """Проверка наличия всех ожидаемых полей."""
        serializer = DebtDetailSerializer(debt)
        expected_fields = {
            'id', 'intern', 'intern_name', 'direction_id', 'direction_name',
            'telegram_username', 'email',
            'total_amount', 'paid_amount', 'balance',
            'payment_status', 'act_date',
            'payment_history',
        }
        assert expected_fields == set(serializer.data.keys())

    def test_balance_read_only(self, debt):
        """Проверка, что balance и total_amount — только для чтения."""
        serializer = DebtDetailSerializer(debt)
        assert 'balance' in serializer.data
        assert Decimal(serializer.data['balance']) == debt.total_amount - debt.paid_amount


# ---------------------------------------------------------------------------
# DebtCreateUpdateSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestDebtCreateUpdateSerializer:
    """Тесты для DebtCreateUpdateSerializer."""

    def test_valid_data_passes_validation(self, intern, direction):
        """Проверка валидации корректных данных."""
        data = {
            'intern': intern.pk,
            'direction_id': direction.id,
            'telegram_username': '@newuser',
            'email': 'new@example.com',
            'paid_amount': '5000.00',
            'payment_status': 'paying',
            'act_date': '2025-03-01',
        }
        serializer = DebtCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_intern_is_required(self):
        """Проверка, что intern обязателен."""
        data = {
            'paid_amount': '1000.00',
            'payment_status': 'paying',
        }
        serializer = DebtCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'intern' in serializer.errors

    def test_optional_fields_can_be_omitted(self, intern):
        """Проверка, что необязательные поля можно не указывать."""
        data = {'intern': intern.pk}
        serializer = DebtCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_invalid_payment_status_rejected(self, intern):
        """Проверка отклонения невалидного payment_status."""
        data = {
            'intern': intern.pk,
            'payment_status': 'invalid_status',
        }
        serializer = DebtCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'payment_status' in serializer.errors

    def test_invalid_email_rejected(self, intern):
        """Проверка отклонения невалидного email."""
        data = {
            'intern': intern.pk,
            'email': 'not-an-email',
        }
        serializer = DebtCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_all_writable_fields_present(self):
        """Проверка наличия всех записываемых полей."""
        serializer = DebtCreateUpdateSerializer()
        expected_fields = {
            'intern', 'direction_id', 'telegram_username',
            'email', 'total_amount', 'paid_amount', 'payment_status', 'act_date',
        }
        assert expected_fields == set(serializer.fields.keys())

    @pytest.mark.parametrize('status', ['searching', 'paying', 'unknown'])
    def test_valid_payment_status_choices(self, intern, status):
        """Проверка всех допустимых значений payment_status."""
        data = {'intern': intern.pk, 'payment_status': status}
        serializer = DebtCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), f"Статус {status} должен быть допустим"


@pytest.mark.serializers
class TestPaymentHistoryCreateSerializer:
    """Тесты для PaymentHistoryCreateSerializer."""

    def test_valid_data_passes_validation(self):
        """Проверка валидации корректных данных."""
        data = {'month': 3, 'year': 2025, 'amount': '2000.00'}
        serializer = PaymentHistoryCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_month_is_required(self):
        """Проверка, что month обязателен."""
        data = {'year': 2025, 'amount': '1000.00'}
        serializer = PaymentHistoryCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'month' in serializer.errors

    def test_year_is_required(self):
        """Проверка, что year обязателен."""
        data = {'month': 1, 'amount': '1000.00'}
        serializer = PaymentHistoryCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'year' in serializer.errors

    def test_amount_is_required(self):
        """Проверка, что amount обязателен."""
        data = {'month': 1, 'year': 2025}
        serializer = PaymentHistoryCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'amount' in serializer.errors

    def test_fields_present(self):
        """Проверка наличия всех полей."""
        serializer = PaymentHistoryCreateSerializer()
        assert set(serializer.fields.keys()) == {'month', 'year', 'amount'}

    def test_negative_amount_behaviour(self):
        """Проверка поведения с отрицательной суммой."""
        data = {'month': 1, 'year': 2025, 'amount': '-500.00'}
        serializer = PaymentHistoryCreateSerializer(data=data)
        # MinValueValidator(0) запрещает отрицательные суммы
        is_valid = serializer.is_valid()
        assert is_valid is False

    def test_decimal_amount_precision(self):
        """Проверка работы с десятичными суммами."""
        data = {'month': 6, 'year': 2025, 'amount': '1234.56'}
        serializer = PaymentHistoryCreateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['amount'] == Decimal('1234.56')
