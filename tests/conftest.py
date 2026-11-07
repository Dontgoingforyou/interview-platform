import glob
import os
import pytest
from datetime import date, time
from pathlib import Path
from rest_framework.test import APIClient

from directions.models import Direction
from interviews.models import Interview
from companies.models import Company
from managers.models import Manager
from interns.models import Intern
from sad_intern.models import SadIntern
from tests.helpers import make_keycloak_user


def pytest_configure():
    """Настраивает окружение pytest."""
    from django.conf import settings

    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    settings.CELERY_BROKER_URL = 'memory://'
    settings.CELERY_RESULT_BACKEND = 'cache+memory://'

    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

    settings.COMPRESS_OFFLINE = False
    settings.COMPRESS_ENABLED = False

    settings.S3_ENDPOINT_URL = 'https://s3.test.example'
    settings.S3_REGION = 'ru-central1'
    settings.S3_ACCESS_KEY_ID = 'test-access-key'
    settings.S3_SECRET_ACCESS_KEY = 'test-secret-key'
    settings.S3_VIDEO_BUCKET = 'interview-videos'
    settings.S3_VIDEO_PREFIX = ''
    settings.S3_PRESIGNED_EXPIRES = 86400

    settings.LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'null': {
                'class': 'logging.NullHandler',
            },
        },
        'root': {
            'handlers': ['null'],
        },
    }


@pytest.fixture
def set_session(client):
    """Фикстура для установки сессии менеджера или админа с SSO авторизацией."""

    def _set_session(
            manager_email='manager@example.com',
            role='manager',
            manager_name='Тестовый Менеджер',
            keycloak_id=None,
            manager_groups=None):
        session = client.session
        session['manager_email'] = manager_email
        session['manager_name'] = manager_name
        session['manager_role'] = role
        session['keycloak_user'] = True
        session['keycloak_id'] = keycloak_id or f'test-keycloak-id-{manager_email}'
        if manager_groups is not None:
            session['manager_groups'] = manager_groups
        else:
            # По умолчанию — группы, при которых пользователь считается менеджером/админом
            session['manager_groups'] = (
                ['role_admin'] if role == 'admin' else ['employment-managers']
            )
        session.save()
        return session
    return _set_session


# --- Фикстуры для API-тестов (DRF APIClient) ---

@pytest.fixture
def api_client():
    """Возвращает DRF APIClient."""
    return APIClient()


@pytest.fixture(autouse=True)
def disable_throttling(settings):
    """Отключает DRF rate-throttling и заменяет Redis-кэш на LocMem для API-тестов."""
    from django.core.cache import cache

    rf = dict(settings.REST_FRAMEWORK)
    rf['DEFAULT_THROTTLE_CLASSES'] = []
    settings.REST_FRAMEWORK = rf
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    cache.clear()


# --- Keycloak-пользователи для DRF API-тестов ---

@pytest.fixture
def api_admin_user():
    """KeycloakUser с правами администратора."""
    return make_keycloak_user(email='admin@example.com', is_admin=True)


@pytest.fixture
def api_manager_user():
    """KeycloakUser — менеджер (manager@example.com)."""
    return make_keycloak_user(email='manager@example.com', is_admin=False)


@pytest.fixture
def api_manager2_user():
    """KeycloakUser — второй менеджер (manager2@example.com)."""
    return make_keycloak_user(email='manager2@example.com', is_admin=False)


@pytest.fixture
def api_anon_user():
    """KeycloakUser без групп — нет прав доступа."""
    return make_keycloak_user(email='anon@example.com', groups=[])


@pytest.fixture
def api_outstaff_user():
    """KeycloakUser с группой outstaff (без админских прав)."""
    return make_keycloak_user(email='outstaff@example.com', groups=['outstaff'])


@pytest.fixture
def api_bot_user(db):
    """Django User для Basic Auth (Telegram-бот / RAG) в security-тестах."""
    from django.contrib.auth.models import User

    return User.objects.create_user(
        username='tg_bot_test',
        password='bot-test-password',
        is_superuser=True,
    )


@pytest.fixture
def api_student_user():
    """KeycloakUser — студент портала (только группа students)."""
    return make_keycloak_user(
        email='student@example.com',
        groups=['students'],
        full_name='Студент Тест',
    )


@pytest.fixture
def api_hr_user():
    """KeycloakUser с группой hrs (только просмотр по политике приложения)."""
    return make_keycloak_user(email='hr@example.com', groups=['hrs'])


@pytest.fixture
def api_mentor_user():
    """KeycloakUser с группой mentors (только «База собеседований»)."""
    return make_keycloak_user(email='mentor@example.com', groups=['mentors'])


@pytest.fixture
def api_cv_manager_user():
    """KeycloakUser из группы cv-managers."""
    return make_keycloak_user(email='cv_manager@example.com', groups=['cv-managers'])


@pytest.fixture
def cv_api_manager_user():
    """KeycloakUser из группы cv-managers (псевдоним api_cv_manager_user для обратной совместимости)."""
    return make_keycloak_user(email='cv_manager@example.com', groups=['cv-managers'])


# --- Фикстуры для создания тестовых данных ---

@pytest.fixture
def direction(db):
    """ Создаёт тестовое направление. """
    return Direction.objects.create(name='Backend')


@pytest.fixture
def company(db):
    """ Создаёт тестовую компанию. """
    return Company.objects.create(name='Google', is_bigtech=True)


@pytest.fixture
def manager(db):
    """ Создаёт тестового менеджера в локальной таблице managers. """
    return Manager.objects.create(
        email='manager@example.com',
        full_name='Алексей Менеджеров',
        username='aleksey',
        groups=['employment-managers'],
        is_active=True
    )


@pytest.fixture
def manager2(db):
    """ Создаёт второго тестового менеджера в локальной таблице managers. """
    return Manager.objects.create(
        email='manager2@example.com',
        full_name='Петр Управляющий',
        username='petr',
        groups=['employment-managers'],
        is_active=True
    )


@pytest.fixture
def admin_manager(db):
    """ Создаёт тестового менеджера с правами админа И менеджера (обе группы). """
    return Manager.objects.create(
        email='admin@example.com',
        full_name='Администратор Админов',
        username='admin',
        groups=['role_admin', 'employment-managers'],
        is_active=True
    )


@pytest.fixture
def pure_admin_manager(db):
    """ Создаёт тестового менеджера только с правами администратора (без менеджерских групп). """
    return Manager.objects.create(
        email='pure_admin@example.com',
        full_name='Чистый Администратор',
        username='pure_admin',
        groups=['role_admin'],
        is_active=True
    )


@pytest.fixture
def intern(db, direction):
    """ Создаёт тестового студента. """
    return Intern.objects.create(
        full_name='Иван Иванов',
        email='ivan@example.com',
        manager_email='manager@example.com',
        direction=direction,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR1',
        type_of_training='internal'
    )


@pytest.fixture
def intern_other(db, direction):
    """ Создаёт другого тестового студента. """
    return Intern.objects.create(
        full_name='Петр Петров',
        email='petr@example.com',
        manager_email='manager2@example.com',
        direction=direction,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR2',
        type_of_training='outstaff'
    )


@pytest.fixture
def interview(db, intern, direction):
    """ Создаёт собеседование, принадлежащее менеджеру 1. """
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        manager_email='manager@example.com',
        company=None,
        interview_type='screening',
        date=date(2025, 12, 1),
        time=time(10, 0)
    )


@pytest.fixture
def interview_other(db, intern_other, direction):
    """ Создаёт собеседование, принадлежащее другому менеджеру 2. """
    return Interview.objects.create(
        intern=intern_other,
        direction=direction,
        manager_email='manager2@example.com',
        company=None,
        interview_type='tech',
        date=date(2025, 12, 2),
        time=time(14, 0)
    )


@pytest.fixture
def sad_intern(db, intern, direction):
    """Создаёт тестового грустящего студента (менеджер manager@example.com, статус rejected)."""
    from datetime import timedelta
    from django.utils import timezone

    today = timezone.now().date()
    intern.real_interview_date = today - timedelta(days=10)
    intern.save()

    return SadIntern.objects.create(
        intern=intern,
        waiting_since=date(2025, 11, 1),
        telegram_username='@ivan_tg',
        manager_email='manager@example.com',
        status='rejected',
        note='Тестовое примечание'
    )


@pytest.fixture
def interview_with_company(db, intern, direction, company):
    """ Создаёт собеседование с компанией. """
    return Interview.objects.create(
        intern=intern,
        direction=direction,
        company=company,
        manager_email='manager@example.com',
        interview_type='hr',
        date=date(2025, 12, 3),
        time=time(15, 0),
        hr_name='Анна HR',
        hr_contacts='anna@company.com'
    )


# --- Фикстуры сессий для Django-клиентных тестов ---

@pytest.fixture
def logged_in_manager(client, set_session):
    """ Логинит менеджера и возвращает клиента. """
    set_session(
        manager_email='manager@example.com',
        role='manager',
        manager_name='Тестовый Менеджер',
        keycloak_id='test-keycloak-id-1',
    )
    return client


@pytest.fixture
def logged_in_admin(client, set_session):
    """Логинит админа и возвращает клиента."""
    set_session(
        manager_email='admin@example.com',
        role='admin',
        manager_name='Администратор',
        keycloak_id='test-keycloak-admin-id',
    )
    return client


@pytest.fixture
def logged_in_student(client, set_session):
    """Логинит студента (SSO + группа students, без групп менеджеров) и возвращает клиента."""
    set_session(
        manager_email='student@example.com',
        role='student',
        manager_name='Студент',
        keycloak_id='test-keycloak-student-id',
        manager_groups=['students'],
    )
    return client


@pytest.fixture(autouse=True, scope='function')
def cleanup_import_files():
    """Автоматически очищает временные файлы импорта после каждого теста."""
    yield
    from django.conf import settings

    media_root = getattr(settings, 'MEDIA_ROOT', None)
    if not media_root:
        media_root = Path(settings.BASE_DIR) / 'media'

    import_dir = Path(media_root) / 'imports'

    if import_dir.exists():
        patterns = [
            'offers_*.csv', 'offers_*.xlsx', 'offers_*.xls',
            'interns_*.csv', 'interns_*.xlsx', 'interns_*.xls',
            'interviews_*.csv', 'interviews_*.xlsx', 'interviews_*.xls',
            'debts_*.csv', 'debts_*.xlsx', 'debts_*.xls',
            'sad_intern_*.csv', 'sad_intern_*.xlsx', 'sad_intern_*.xls',
        ]
        for pattern in patterns:
            files = glob.glob(str(import_dir / pattern))
            for file_path in files:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
