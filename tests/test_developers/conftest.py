"""
Фикстуры для тестов приложения developers.
"""
import pytest
from datetime import date
from offers.models import Offer


@pytest.fixture
def offer(db, intern, direction):
    """Создаёт тестовый оффер."""
    return Offer.objects.create(
        intern=intern,
        direction=direction,
        company='Google',
        amount=150000,
        month=11,
        year=2025
    )


@pytest.fixture
def offer_other(db, intern_other, direction):
    """Создаёт другой тестовый оффер."""
    return Offer.objects.create(
        intern=intern_other,
        direction=direction,
        company='Yandex',
        amount=140000,
        month=11,
        year=2025
    )


@pytest.fixture
def offer_last_month(db, intern, direction):
    """Создаёт оффер за последний месяц."""
    today = date.today()
    last_month = today.month - 1 if today.month > 1 else 12
    last_month_year = today.year if today.month > 1 else today.year - 1

    return Offer.objects.create(
        intern=intern,
        direction=direction,
        company='Google',
        amount=150000,
        month=last_month,
        year=last_month_year
    )


@pytest.fixture
def offer_this_year(db, intern, direction):
    """Создаёт оффер за текущий год."""
    today = date.today()

    return Offer.objects.create(
        intern=intern,
        direction=direction,
        company='Google',
        amount=150000,
        month=today.month,
        year=today.year
    )
