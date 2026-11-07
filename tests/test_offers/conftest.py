import pytest
import pandas as pd
from decimal import Decimal

from offers.models import Offer


@pytest.fixture
def sample_df():
    """Создаёт тестовый DataFrame для OfferImportService."""
    return pd.DataFrame({
        'full_name': ['Иван Иванов', 'Петр Петров', 'ФЕВРАЛЬ'],
        'direction_name': ['Backend', 'Frontend', ''],
        'company_name': ['Google', 'Yandex', ''],
        'amount': ['150000', '120000', ''],
    })


@pytest.fixture
def direction_backend(db):
    """Создаёт тестовое направление Python (Backend мапится в Python)."""
    from directions.models import Direction
    return Direction.objects.create(id=10, name='Python')


@pytest.fixture
def direction_frontend(db):
    """Создаёт тестовое направление Frontend."""
    from directions.models import Direction
    return Direction.objects.create(id=20, name='Frontend')


@pytest.fixture
def offer(db, intern, direction):
    """Создаёт тестовый оффер, принадлежащий менеджеру manager@example.com (через intern)."""
    return Offer.objects.create(
        intern=intern,
        direction=direction,
        company='Google',
        amount=Decimal('150000.00'),
        month=1,
        year=2025,
    )


@pytest.fixture
def offer_other(db, intern_other, direction):
    """Создаёт тестовый оффер, принадлежащий менеджеру manager2@example.com (через intern_other)."""
    return Offer.objects.create(
        intern=intern_other,
        direction=direction,
        company='Yandex',
        amount=Decimal('120000.00'),
        month=2,
        year=2025,
    )


@pytest.fixture
def offer_no_company(db, intern, direction):
    """Оффер без компании (nullable)."""
    return Offer.objects.create(
        intern=intern,
        direction=direction,
        company=None,
        amount=Decimal('100000.00'),
        month=2,
        year=2025,
    )


@pytest.fixture
def offer_no_amount(db, intern, direction):
    """Оффер без суммы (nullable)."""
    return Offer.objects.create(
        intern=intern,
        direction=direction,
        company='Yandex',
        amount=None,
        month=3,
        year=2025,
    )
