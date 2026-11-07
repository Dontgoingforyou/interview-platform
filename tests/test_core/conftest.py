"""
Фикстуры для тестов модуля core.

Содержит дополнительных студентов для тестирования алгоритма поиска find_intern_by_name.
Глобальные фикстуры (intern, direction) используются из tests/conftest.py.
"""
import pytest
from datetime import date

from interns.models import Intern


@pytest.fixture
def intern_petrov(db, direction):
    """Студент 'Петр Петров' — для тестов поиска по другому имени."""
    return Intern.objects.create(
        full_name='Петр Петров',
        email='petrov@example.com',
        manager_email='manager@example.com',
        direction=direction,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2001, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR1',
        type_of_training='internal',
    )


@pytest.fixture
def intern_ivanov_sergey(db, direction):
    """Студент 'Сергей Иванов' — для тестов с несколькими кандидатами (одинаковая фамилия)."""
    return Intern.objects.create(
        full_name='Сергей Иванов',
        email='sivanov@example.com',
        manager_email='manager@example.com',
        direction=direction,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2002, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR1',
        type_of_training='internal',
    )


@pytest.fixture
def intern_sidorov(db, direction):
    """Студент 'Алексей Сидоров' — для тестов подстрочного поиска."""
    return Intern.objects.create(
        full_name='Алексей Сидоров',
        email='sidorov@example.com',
        manager_email='manager@example.com',
        direction=direction,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2003, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR1',
        type_of_training='internal',
    )
