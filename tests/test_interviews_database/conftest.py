"""
Фикстуры для тестов приложения interviews_database.

Создаёт интервью с различными состояниями ссылки на запись созвона,
используемые в тестах views базы собеседований.
"""
import pytest
from datetime import date, time

from interviews.models import Interview
from interns.models import Intern


@pytest.fixture
def intern_unique(db, direction):
    """Уникальный студент для тестирования пустых ссылок на запись созвона."""
    return Intern.objects.create(
        full_name='Эксклюзив Эксклюзивов',
        email='excl@example.com',
        manager_email='manager@example.com',
        direction=direction,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR',
        responsible_hr='HR',
        group='G1',
        type_of_training='internal',
    )


@pytest.fixture
def interview_with_link(db, intern, direction):
    """Собеседование с заполненной ссылкой на запись созвона."""
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        manager_email='manager@example.com',
        interview_type='tech',
        date=date(2025, 11, 10),
        time=time(11, 0),
        link='https://zoom.us/rec/abc123',
        hr_name='Ольга HR',
        hr_contacts='olga@company.com',
    )


@pytest.fixture
def interview_with_link_and_company(db, intern, direction, company):
    """Собеседование с записью созвона и привязанной компанией."""
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        company=company,
        manager_email='manager@example.com',
        interview_type='final',
        date=date(2025, 11, 20),
        time=time(15, 0),
        link='https://zoom.us/rec/xyz789',
        hr_name='Анна HR',
        hr_contacts='anna@google.com',
        vacancy_link='https://example.com/vacancy',
    )


@pytest.fixture
def interview_without_link(db, intern, direction):
    """Собеседование БЕЗ ссылки на запись — не должно попадать в базу собесов."""
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        manager_email='manager@example.com',
        interview_type='screening',
        date=date(2025, 11, 5),
        link=None,
    )


@pytest.fixture
def interview_with_empty_link(db, intern_unique, direction):
    """Собеседование с пустой строкой в ссылке — не должно попадать в базу собесов.

    Использует отдельного студента (intern_unique), чтобы имя можно было
    однозначно проверить в содержимом страницы.
    """
    return Interview.objects.create(
        intern=intern_unique,
        direction=direction,
        manager_email='manager@example.com',
        interview_type='hr',
        date=date(2025, 11, 6),
        link='',
    )


@pytest.fixture
def interview_other_with_link(db, intern_other, direction):
    """Собеседование другого студента с записью созвона."""
    return Interview.objects.create(
        intern=intern_other,
        direction=direction,
        manager_email='manager2@example.com',
        interview_type='screening',
        date=date(2025, 10, 1),
        link='https://meet.google.com/rec/other',
    )
