import pytest
from datetime import date
from decimal import Decimal

from debts.models import Debt, PaymentHistory


@pytest.fixture
def debt(db, intern):
    """Долг, принадлежащий менеджеру 1 (через intern.manager_email)."""
    return Debt.objects.create(
        intern=intern,
        total_amount=Decimal('10000.00'),
        paid_amount=Decimal('3000.00'),
        payment_status='paying',
        telegram_username='@testuser',
        email='test@example.com',
        act_date=date(2025, 1, 15),
    )


@pytest.fixture
def debt_other(db, intern_other):
    """Долг, принадлежащий менеджеру 2."""
    return Debt.objects.create(
        intern=intern_other,
        total_amount=Decimal('15000.00'),
        paid_amount=Decimal('5000.00'),
        payment_status='searching',
    )


@pytest.fixture
def payment(db, debt):
    """Запись истории платежа для debt."""
    return PaymentHistory.objects.create(
        debt=debt,
        month=1,
        year=2025,
        amount=Decimal('1000.00'),
    )
