"""
Тесты для моделей приложения debts.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.models - для группировки тестов моделей
"""
import pytest
from datetime import date
from decimal import Decimal

from debts.models import Debt, PaymentHistory


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestDebtModel:
    """Тесты для модели Debt."""

    def test_create_debt(self, intern):
        """Создание долга."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('5000.00'),
            payment_status='paying'
        )
        assert debt.pk is not None
        assert debt.intern == intern
        assert debt.total_amount == Decimal('10000.00')
        assert debt.paid_amount == Decimal('5000.00')
        assert debt.balance == Decimal('5000.00')  # Автоматически вычисляется
        assert debt.payment_status == 'paying'

    def test_debt_str(self, intern):
        """Проверка строкового представления."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('3000.00')
        )
        expected = f"Долг: {intern.full_name} - {Decimal('7000.00')}"
        assert str(debt) == expected

    def test_debt_balance_calculation(self, intern):
        """Проверка автоматического вычисления balance."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('15000.00'),
            paid_amount=Decimal('7000.00')
        )
        assert debt.balance == Decimal('8000.00')

    def test_debt_balance_zero(self, intern):
        """Проверка balance при полной оплате."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('10000.00')
        )
        assert debt.balance == Decimal('0.00')

    def test_debt_balance_negative(self, intern):
        """Проверка balance при переплате."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('12000.00')
        )
        assert debt.balance == Decimal('-2000.00')

    @pytest.mark.parametrize('status', ['searching', 'paying', 'unknown'])
    def test_debt_payment_status_choices(self, intern, status):
        """Проверка всех допустимых статусов платежа."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            payment_status=status
        )
        assert debt.payment_status == status

    def test_debt_nullable_fields(self, intern):
        """Проверка nullable полей."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            direction=None,
            telegram_username=None,
            email=None,
            act_date=None
        )
        assert debt.direction_id is None
        assert debt.telegram_username is None
        assert debt.email is None
        assert debt.act_date is None

    def test_debt_with_act_date(self, intern):
        """Проверка создания долга с датой акта."""
        act_date = date(2025, 1, 15)
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            act_date=act_date
        )
        assert debt.act_date == act_date

    def test_debt_direction_property(self, intern, direction):
        """Проверка свойства direction."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            direction=direction
        )
        assert debt.direction is not None
        assert debt.direction.id == direction.id
        assert debt.direction.name == direction.name

    def test_debt_direction_null(self, intern):
        """Проверка, что direction может быть None (nullable FK)."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            direction=None
        )
        assert debt.direction is None
        assert debt.direction_id is None

    def test_debt_last_payment_month_year_no_payments(self, intern):
        """Проверка last_payment_month_year при отсутствии платежей."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        month, year = debt.last_payment_month_year
        assert month is None
        assert year is None

    def test_debt_last_payment_month_year_with_payments(self, intern):
        """Проверка last_payment_month_year при наличии платежей."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        PaymentHistory.objects.create(
            debt=debt,
            month=1,
            year=2025,
            amount=Decimal('1000.00')
        )
        PaymentHistory.objects.create(
            debt=debt,
            month=3,
            year=2025,
            amount=Decimal('2000.00')
        )
        month, year = debt.last_payment_month_year
        assert month == 3
        assert year == 2025

    def test_debt_last_three_payments(self, intern):
        """Проверка last_three_payments."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        # Создаём 5 платежей
        for i in range(1, 6):
            PaymentHistory.objects.create(
                debt=debt,
                month=i,
                year=2025,
                amount=Decimal(f'{i * 1000}.00')
            )
        last_three = debt.last_three_payments
        assert len(last_three) == 3
        # Должны быть последние 3 (месяцы 5, 4, 3)
        assert last_three[0].month == 5
        assert last_three[1].month == 4
        assert last_three[2].month == 3

    def test_debt_update_balance_on_save(self, intern):
        """Проверка пересчёта balance при обновлении."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('3000.00')
        )
        assert debt.balance == Decimal('7000.00')

        debt.paid_amount = Decimal('8000.00')
        debt.save()
        assert debt.balance == Decimal('2000.00')

    def test_debt_related_name(self, intern):
        """Проверка related_name для связи с Intern."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        assert debt in intern.debts.all()


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestPaymentHistoryModel:
    """Тесты для модели PaymentHistory."""

    def test_create_payment_history(self, intern):
        """Создание записи истории платежа."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        payment = PaymentHistory.objects.create(
            debt=debt,
            month=1,
            year=2025,
            amount=Decimal('2000.00')
        )
        assert payment.pk is not None
        assert payment.debt == debt
        assert payment.month == 1
        assert payment.year == 2025
        assert payment.amount == Decimal('2000.00')

    def test_payment_history_str(self, intern):
        """Проверка строкового представления."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        payment = PaymentHistory.objects.create(
            debt=debt,
            month=2,
            year=2025,
            amount=Decimal('3000.00')
        )
        expected = f"{intern.full_name} - 2/2025 - {Decimal('3000.00')}"
        assert str(payment) == expected

    def test_payment_history_unique_together(self, intern):
        """Проверка уникальности комбинации debt, month, year."""
        from django.db import IntegrityError
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        PaymentHistory.objects.create(
            debt=debt,
            month=1,
            year=2025,
            amount=Decimal('1000.00')
        )
        # Попытка создать дубликат должна вызвать ошибку
        with pytest.raises((IntegrityError, Exception)):  # IntegrityError или подобное
            PaymentHistory.objects.create(
                debt=debt,
                month=1,
                year=2025,
                amount=Decimal('2000.00')
            )

    def test_payment_history_ordering(self, intern):
        """Проверка сортировки по убыванию года и месяца."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        PaymentHistory.objects.create(debt=debt, month=1, year=2024, amount=Decimal('1000.00'))
        PaymentHistory.objects.create(debt=debt, month=3, year=2025, amount=Decimal('2000.00'))
        PaymentHistory.objects.create(debt=debt, month=2, year=2025, amount=Decimal('1500.00'))

        payments = list(PaymentHistory.objects.all())
        # Должны быть отсортированы по убыванию года, затем месяца
        assert payments[0].year == 2025 and payments[0].month == 3
        assert payments[1].year == 2025 and payments[1].month == 2
        assert payments[2].year == 2024 and payments[2].month == 1

    def test_payment_history_month_validation(self, intern):
        """Проверка валидации месяца (1-12)."""
        from django.core.exceptions import ValidationError
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        # Месяц должен быть >= 1
        payment = PaymentHistory(
            debt=debt,
            month=0,  # Невалидное значение
            year=2025,
            amount=Decimal('1000.00')
        )
        with pytest.raises(ValidationError):
            payment.full_clean()

    def test_payment_history_related_name(self, intern):
        """Проверка related_name для связи с Debt."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        payment = PaymentHistory.objects.create(
            debt=debt,
            month=1,
            year=2025,
            amount=Decimal('1000.00')
        )
        assert payment in debt.payment_history.all()

    def test_payment_history_created_at_auto(self, intern):
        """Проверка автоматического создания created_at."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        payment = PaymentHistory.objects.create(
            debt=debt,
            month=1,
            year=2025,
            amount=Decimal('1000.00')
        )
        assert payment.created_at is not None

    def test_payment_history_month_upper_boundary(self, intern):
        """Проверка верхней границы месяца (12)."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        # Месяц 12 должен быть валидным
        payment = PaymentHistory.objects.create(
            debt=debt,
            month=12,
            year=2025,
            amount=Decimal('1000.00')
        )
        assert payment.month == 12

    def test_payment_history_decimal_amount(self, intern):
        """Проверка работы с десятичными суммами."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        payment = PaymentHistory.objects.create(
            debt=debt,
            month=1,
            year=2025,
            amount=Decimal('1234.56')
        )
        assert payment.amount == Decimal('1234.56')


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestDebtModelEdgeCases:
    """Тесты для граничных случаев модели Debt."""

    def test_debt_with_zero_amounts(self, intern):
        """Проверка создания долга с нулевыми суммами."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('0.00'),
            paid_amount=Decimal('0.00')
        )
        assert debt.balance == Decimal('0.00')

    def test_debt_with_large_amounts(self, intern):
        """Проверка работы с большими суммами."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('9999999999.99'),
            paid_amount=Decimal('5000000000.50')
        )
        assert debt.balance == Decimal('4999999999.49')

    def test_debt_direction_property_with_null(self, intern):
        """Проверка свойства direction при direction=None."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            direction=None
        )
        assert debt.direction is None

    def test_debt_last_three_payments_with_less_than_three(self, intern):
        """Проверка last_three_payments когда платежей меньше трёх."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        PaymentHistory.objects.create(
            debt=debt,
            month=1,
            year=2025,
            amount=Decimal('1000.00')
        )
        PaymentHistory.objects.create(
            debt=debt,
            month=2,
            year=2025,
            amount=Decimal('2000.00')
        )
        last_three = debt.last_three_payments
        assert len(last_three) == 2

    def test_debt_last_three_payments_empty(self, intern):
        """Проверка last_three_payments при отсутствии платежей."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        last_three = debt.last_three_payments
        assert len(last_three) == 0

    def test_debt_multiple_saves_update_balance(self, intern):
        """Проверка, что balance обновляется при каждом save()."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('1000.00')
        )
        assert debt.balance == Decimal('9000.00')

        debt.paid_amount = Decimal('2000.00')
        debt.save()
        assert debt.balance == Decimal('8000.00')

        debt.paid_amount = Decimal('3000.00')
        debt.save()
        assert debt.balance == Decimal('7000.00')

    def test_debt_email_max_length(self, intern):
        """Проверка максимальной длины email."""
        # EmailField по умолчанию имеет max_length=254
        long_email = 'a' * 240 + '@example.com'
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            email=long_email
        )
        assert debt.email == long_email

    def test_debt_telegram_username_max_length(self, intern):
        """Проверка максимальной длины telegram_username."""
        # max_length=100
        long_username = '@' + 'a' * 99
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            telegram_username=long_username
        )
        assert debt.telegram_username == long_username

    def test_debt_default_values(self, intern):
        """Проверка значений по умолчанию."""
        debt = Debt.objects.create(
            intern=intern
        )
        assert debt.payment_status == 'unknown'
        assert debt.total_amount == Decimal('0')
        assert debt.paid_amount == Decimal('0')
        assert debt.balance == Decimal('0')

    def test_debt_cascade_delete_from_intern(self, intern):
        """Проверка каскадного удаления при удалении intern."""
        debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        debt_id = debt.pk
        intern_id = intern.pk

        intern.delete()

        assert not Debt.objects.filter(pk=debt_id).exists()

    def test_payment_history_multiple_debts_same_month(self, intern):
        """Проверка, что разные долги могут иметь платежи в одном месяце."""
        debt1 = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00')
        )
        debt2 = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('15000.00')
        )

        payment1 = PaymentHistory.objects.create(
            debt=debt1,
            month=1,
            year=2025,
            amount=Decimal('1000.00')
        )
        payment2 = PaymentHistory.objects.create(
            debt=debt2,
            month=1,
            year=2025,
            amount=Decimal('2000.00')
        )

        assert payment1.pk != payment2.pk
        assert payment1.month == payment2.month == 1
        assert payment1.year == payment2.year == 2025

    def test_debt_ordering_in_queryset(self, intern):
        """Проверка, что можно сортировать долги по различным полям."""
        debt1 = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('2000.00')
        )
        debt2 = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('15000.00'),
            paid_amount=Decimal('5000.00')
        )

        # Сортировка по balance (по убыванию)
        debts = Debt.objects.all().order_by('-balance')
        assert debts[0].balance > debts[1].balance
