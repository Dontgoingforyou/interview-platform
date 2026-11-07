import pytest
from datetime import date

from employees.models import InternWeeklyStatus
from managers.models import Manager


@pytest.fixture
def weekly_status(db, intern):
    """Создаёт запись недельного статуса студента."""
    return InternWeeklyStatus.objects.create(
        intern=intern,
        week_start=date(2025, 1, 6),
        manual_interview_count=3,
    )


@pytest.fixture
def inactive_manager(db):
    """Неактивный менеджер с менеджерской группой Keycloak."""
    return Manager.objects.create(
        email='inactive@example.com',
        full_name='Неактивный Менеджер',
        username='inactive',
        groups=['employment-managers'],
        is_active=False,
    )


@pytest.fixture
def weekly_status_other(db, intern_other):
    """Создаёт запись недельного статуса второго студента."""
    return InternWeeklyStatus.objects.create(
        intern=intern_other,
        week_start=date(2025, 1, 6),
        absence_status='болеет',
    )
