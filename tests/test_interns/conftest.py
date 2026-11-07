"""
Локальные фикстуры для тестов приложения interns.

Фикстуры, специфичные только для interns-тестов (не нужные в других приложениях).
"""
import pandas as pd
import pytest
from datetime import date

from directions.models import Direction
from interns.models import Intern


@pytest.fixture
def sample_df():
    """Создаёт тестовый DataFrame для импорта студентов."""
    return pd.DataFrame({
        'full_name': ['Иван Иванов', 'Петр Петров'],
        'direction_name': ['Backend', 'Frontend'],
        'manager_name': ['Алексей', ''],
        'type_of_training_label': ['outstaff', 'во вне'],
        'date_of_birth_str': ['01.01.2000', '02.02.2001'],
        'date_of_receipt_str': ['01.01.2025', '02.02.2025'],
        'telegram_username': ['@ivan', '@petr'],
        'group': ['GR1', 'GR2'],
        'hiring_hr': ['HR1', 'HR2'],
        'responsible_hr': ['HR3', 'HR4'],
        'cv': ['https://example.com/cv1', ''],
        'legend': ['https://example.com/legend1', ''],
        'hr_feedback': ['Отличный кандидат', ''],
        'additional_contacts_str': ['email@example.com', ''],
    })


@pytest.fixture
def direction_python(db):
    """Создаёт тестовое направление Python.

    DIRECTION_MAPPING преобразует 'Backend' из sample_df в 'Python',
    поэтому создаём направление именно с таким именем.
    """
    return Direction.objects.create(name='Python')


@pytest.fixture
def direction_frontend(db):
    """Создаёт тестовое направление Frontend."""
    return Direction.objects.create(name='Frontend')


@pytest.fixture
def intern_for_date_import(db, direction_python):
    """Создаёт студента без real_interview_date для тестов RealInterviewDateImportService."""
    return Intern.objects.create(
        full_name='Тест Студентов',
        direction=direction_python,
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR',
        responsible_hr='HR2',
        group='GR1',
        type_of_training='internal',
    )


@pytest.fixture
def real_date_df(intern_for_date_import):
    """DataFrame для импорта дат выхода на реальные собеседования."""
    return pd.DataFrame({
        'ФИ': [intern_for_date_import.full_name],
        'Дата': ['15.03.2025'],
    })


@pytest.fixture
def intern_api_request(api_admin_user):
    """POST-запрос с админом для сериализаторов interns."""
    from rest_framework.test import APIRequestFactory

    req = APIRequestFactory().post('/api/interns/')
    req.user = api_admin_user
    return req


@pytest.fixture
def intern_api_request_manager(api_manager_user):
    """PATCH-запрос с менеджером для сериализаторов interns."""
    from rest_framework.test import APIRequestFactory

    req = APIRequestFactory().patch('/api/interns/1/')
    req.user = api_manager_user
    return req
