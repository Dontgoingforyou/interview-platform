"""
Фикстуры для тестов приложения sad_intern.

Содержит фикстуры, специфичные для тестов sad_intern:
- sad_intern_other — второй объект SadIntern (sad_intern определён в tests/conftest.py)
- sample_df, direction_python, test_intern, test_intern2 — для тестов сервиса импорта
- two_ordered_sad_interns — для тестов сортировки во вью
"""
import pytest
import pandas as pd
from datetime import date, timedelta

from directions.models import Direction
from interns.models import Intern
from interviews.models import Interview
from sad_intern.models import SadIntern


@pytest.fixture
def sad_intern_other(db, intern_other, direction):
    """Создаёт второго грустящего студента (менеджер manager2@example.com, статус accepted)."""
    from django.utils import timezone

    today = timezone.now().date()
    intern_other.real_interview_date = today - timedelta(days=15)
    intern_other.save()

    Interview.objects.create(
        intern=intern_other,
        direction=direction,
        manager_email='manager2@example.com',
        interview_type='tech',
        date=today - timedelta(days=5)
    )

    return SadIntern.objects.create(
        intern=intern_other,
        waiting_since=date(2025, 10, 15),
        telegram_username='@petr_tg',
        manager_email='manager2@example.com',
        status='accepted',
        note='Другое примечание'
    )


# ---------------------------------------------------------------------------
# Фикстуры для TestSadInternImportService
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df():
    """Тестовый DataFrame для SadInternImportService."""
    return pd.DataFrame({
        'full_name': ['Иван Иванов', 'Петр Петров'],
        'waiting_since': ['01.11.2025', '15.10.2025'],
        'telegram_username': ['@ivan', '@petr'],
        'manager_name': ['Алексей', ''],
        'status': ['Отказ', 'Взяли'],
        'note': ['Примечание 1', 'Примечание 2'],
    })


@pytest.fixture
def direction_python(db):
    """Создаёт направление Python для тестов сервиса импорта."""
    return Direction.objects.create(name='Python')


@pytest.fixture
def test_intern(db, direction_python):
    """Создаёт студента «Иван Иванов» для тестов сервиса импорта."""
    return Intern.objects.create(
        full_name='Иван Иванов',
        direction=direction_python,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR1',
        type_of_training='internal'
    )


@pytest.fixture
def test_intern2(db, direction_python):
    """Создаёт студента «Петр Петров» для тестов сервиса импорта."""
    return Intern.objects.create(
        full_name='Петр Петров',
        direction=direction_python,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR2',
        type_of_training='internal'
    )


# ---------------------------------------------------------------------------
# Фикстуры для тестов сортировки во вью
# ---------------------------------------------------------------------------

@pytest.fixture
def two_ordered_sad_interns(db, direction):
    """
    Два грустящих студента с разным days_waiting для проверки сортировки.

    Возвращает (sad_longer, sad_shorter), где sad_longer ждёт дольше (25 дней),
    sad_shorter — меньше (10 дней). При сортировке desc sad_longer должен быть первым.
    """
    from django.utils import timezone

    today = timezone.now().date()

    intern1 = Intern.objects.create(
        full_name='Первый Студент',
        direction=direction,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR1',
        type_of_training='internal',
        real_interview_date=today - timedelta(days=10),
    )
    intern2 = Intern.objects.create(
        full_name='Второй Студент',
        direction=direction,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR2',
        type_of_training='internal',
        real_interview_date=today - timedelta(days=25),
    )

    Interview.objects.create(
        intern=intern1,
        direction=direction,
        manager_email='admin@example.com',
        interview_type='tech',
        date=today - timedelta(days=5),
    )
    Interview.objects.create(
        intern=intern2,
        direction=direction,
        manager_email='admin@example.com',
        interview_type='tech',
        date=today - timedelta(days=5),
    )

    sad_shorter = SadIntern.objects.create(
        intern=intern1,
        waiting_since=today - timedelta(days=10),
    )
    sad_longer = SadIntern.objects.create(
        intern=intern2,
        waiting_since=today - timedelta(days=25),
    )

    return sad_longer, sad_shorter


# ---------------------------------------------------------------------------
# Фикстуры для тестов analytics_views
# ---------------------------------------------------------------------------

@pytest.fixture
def sad_intern_on_project(db, intern_other, direction):
    """Создаёт SadIntern со статусом 'on_project' для intern_other.

    Без Offer/Debt/недавних собеседований — нужна для проверки,
    что аналитика исключает on_project из подсчёта.
    """
    return SadIntern.objects.create(
        intern=intern_other,
        waiting_since=date(2025, 10, 1),
        manager_email='manager2@example.com',
        status='on_project',
    )
