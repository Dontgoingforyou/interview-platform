"""
Фикстуры для тестов приложения interviews.

Содержит фикстуры, специфичные для тестов импорта/сервисов,
которые требуют отдельного направления (name='Python') и компании (name='Google'),
а также фикстуры для тестов аналитики.
"""
import pytest
import pandas as pd
from datetime import date, timedelta

from django.utils import timezone

from directions.models import Direction
from companies.models import Company
from interns.models import Intern
from interviews.models import Interview


@pytest.fixture
def sample_df():
    """Тестовый DataFrame для ImportService."""
    return pd.DataFrame({
        'full_name': ['Иван Иванов', 'Петр Петров'],
        'direction_name': ['Backend', 'Frontend'],
        'interview_type_label': ['Скрининг', 'Техническое собеседование'],
        'date_str': ['2025-12-01', '2025-12-02'],
        'time_str': ['10:00', '14:00'],
        'company_name': ['Google', ''],
        'manager_name': ['Алексей', ''],
    })


@pytest.fixture
def direction_python(db):
    """Направление 'Python' — DIRECTION_MAPPING преобразует 'Backend' → 'Python'."""
    return Direction.objects.create(name='Python')


@pytest.fixture
def company_google(db):
    """Компания Google для тестов сервиса импорта."""
    return Company.objects.create(name='Google')


@pytest.fixture
def services_intern(db, direction_python):
    """Студент 'Иван Иванов', привязанный к направлению Python."""
    return Intern.objects.create(
        full_name='Иван Иванов',
        email='ivan@example.com',
        manager_email='manager@example.com',
        direction=direction_python,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR1',
        type_of_training='internal',
    )


# ===== Фикстуры для тестов аналитики =====

@pytest.fixture
def interview_last_30(db, intern, direction, company):
    """Скрининг с компанией, дата — 10 дней назад (в рамках последних 30 дней)."""
    today = timezone.now().date()
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        company=company,
        manager_email='manager@example.com',
        interview_type='screening',
        date=today - timedelta(days=10),
    )


@pytest.fixture
def interview_old(db, intern, direction, company):
    """Скрининг с компанией, дата — 40 дней назад (за пределами последних 30 дней)."""
    today = timezone.now().date()
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        company=company,
        manager_email='manager@example.com',
        interview_type='screening',
        date=today - timedelta(days=40),
    )


@pytest.fixture
def interview_upcoming(db, intern, direction, company):
    """Интервью с будущей датой (+5 дней), попадает в upcoming."""
    today = timezone.now().date()
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        company=company,
        manager_email='manager@example.com',
        interview_type='screening',
        date=today + timedelta(days=5),
    )


@pytest.fixture
def interview_cancelled_30(db, intern, direction):
    """Отменённое интервью в рамках последних 30 дней (без компании)."""
    today = timezone.now().date()
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        manager_email='manager@example.com',
        interview_type='cancelled',
        date=today - timedelta(days=5),
    )


@pytest.fixture
def interview_this_week(db, intern, direction, company):
    """Интервью на текущей неделе (сегодня)."""
    today = timezone.now().date()
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        company=company,
        manager_email='manager@example.com',
        interview_type='screening',
        date=today,
    )


@pytest.fixture
def interview_last_week(db, intern, direction, company):
    """Интервью на прошлой неделе (среда прошлой недели)."""
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    last_week_wednesday = start_of_week - timedelta(days=4)
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        company=company,
        manager_email='manager@example.com',
        interview_type='screening',
        date=last_week_wednesday,
    )


@pytest.fixture
def interview_tech_after(db, intern, direction, company):
    """Tech-интервью в той же компании у того же студента — для расчёта success_rate.

    Дата (today - 5 дней) позже, чем у interview_last_30 (today - 10 дней).
    """
    today = timezone.now().date()
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        company=company,
        manager_email='manager@example.com',
        interview_type='tech',
        date=today - timedelta(days=5),
    )


@pytest.fixture
def interview_unknown_manager(db, intern, direction, company):
    """Интервью с неизвестным email менеджера (нет записи в таблице Manager)."""
    today = timezone.now().date()
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        company=company,
        manager_email='unknown@example.com',
        interview_type='screening',
        date=today - timedelta(days=7),
    )


@pytest.fixture
def interview_with_video(db, interview):
    """Собеседование с video_link для API транскрипции."""
    Interview.objects.filter(pk=interview.pk).update(
        video_link='https://disk.yandex.ru/i/test-video-link',
    )
    interview.refresh_from_db()
    return interview
