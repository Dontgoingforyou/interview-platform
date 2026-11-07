import pytest
from datetime import date, time

from companies.models import Company
from interviews.models import Interview


@pytest.fixture
def company_a(db):
    return Company.objects.create(name='Яндекс', is_bigtech=True, aliases='Yandex\nYandex Cloud')


@pytest.fixture
def company_b(db):
    return Company.objects.create(name='Яндекс GO', is_bigtech=True)


@pytest.fixture
def company_c(db):
    return Company.objects.create(name='Неизвестная компания', is_bigtech=False)


@pytest.fixture
def interview_for_company(db, intern, direction, company_a):
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        company=company_a,
        manager_email='admin@example.com',
        interview_type='hr',
        date=date(2025, 12, 5),
        time=time(10, 0),
    )
