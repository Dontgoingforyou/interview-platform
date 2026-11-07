"""
Фикстуры для тестов приложения interns_portal.
"""
import pytest
from datetime import date, time, timedelta

STUDENT_CORPORATE_EMAIL = 'student@example.com'
STUDENT_FULL_NAME = 'Студент Загружайло'


@pytest.fixture
def student_intern(db, direction):
    """Студент с почтой входа (имитирует повторный вход)."""
    from interns.models import Intern

    return Intern.objects.create(
        full_name=STUDENT_FULL_NAME,
        email='student_personal@yandex.ru',
        corporate_email=STUDENT_CORPORATE_EMAIL,
        telegram_username='@student_tg',
        manager_email='manager@example.com',
        direction=direction,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR1',
        type_of_training='internal',
    )


@pytest.fixture
def student_intern_unlinked(db, direction):
    """Студент без corporate_email (имитирует первый вход, связка по ФИО)."""
    from interns.models import Intern

    return Intern.objects.create(
        full_name=STUDENT_FULL_NAME,
        email='student_personal@yandex.ru',
        telegram_username='@student_tg',
        manager_email='manager@example.com',
        direction=direction,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR1',
        type_of_training='internal',
    )


@pytest.fixture
def student_interview(db, student_intern, direction):
    """Собеседование студента без видео."""
    from interviews.models import Interview

    return Interview.objects.create(
        intern=student_intern,
        direction=direction,
        manager_email='manager@example.com',
        interview_type='screening',
        date=date(2025, 12, 1),
        time=time(10, 0),
    )


@pytest.fixture
def student_interview_with_video(db, student_intern, direction):
    """Собеседование студента с уже загруженным видео."""
    from interviews.models import Interview

    return Interview.objects.create(
        intern=student_intern,
        direction=direction,
        manager_email='manager@example.com',
        interview_type='tech',
        date=date(2025, 12, 2),
        time=time(14, 0),
        video_link='https://disk.yandex.ru/i/example-link',
    )


@pytest.fixture
def student_interview_with_link_from_bot(db, student_intern, direction):
    """Собеседование студента: в записи уже есть video_link."""
    from interviews.models import Interview

    return Interview.objects.create(
        intern=student_intern,
        direction=direction,
        manager_email='manager@example.com',
        interview_type='final',
        date=date(2025, 12, 3),
        time=time(16, 0),
        video_link='https://disk.yandex.ru/i/bot-uploaded-link',
    )


@pytest.fixture
def student_interview_test_type(db, student_intern, direction):
    """Собеседование студента с типом «Тестовое задание» — не показывается на портале."""
    from interviews.models import Interview

    return Interview.objects.create(
        intern=student_intern,
        direction=direction,
        manager_email='manager@example.com',
        interview_type='test',
        date=date(2025, 12, 5),
        time=time(12, 0),
    )


@pytest.fixture
def student_interview_tech_questionnaire_type(db, student_intern, direction):
    """Собеседование студента с типом «Анкета с большим кол-вом технички» — не показывается на портале."""
    from interviews.models import Interview

    return Interview.objects.create(
        intern=student_intern,
        direction=direction,
        manager_email='manager@example.com',
        interview_type='tech_questionnaire',
        date=date(2025, 12, 6),
        time=time(13, 0),
    )


@pytest.fixture
def student_twenty_one_interviews(db, student_intern, direction):
    """21 собеседование студента для тестов пагинации (2 страницы по 20)."""
    from interviews.models import Interview

    for i in range(21):
        Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            date=date(2025, 12, 1) + timedelta(days=i),
            time=time(10 + i % 12, i % 60),
        )


@pytest.fixture
def logged_in_student(client):
    """Клиент с сессией студента (группа students)."""
    session = client.session
    session['manager_email'] = 'student@example.com'
    session['manager_username'] = 'student_tg'
    session['manager_name'] = STUDENT_FULL_NAME
    session['manager_role'] = 'student'
    session['manager_groups'] = ['students']
    session['keycloak_user'] = True
    session.save()
    return client


@pytest.fixture
def logged_in_student_unlinked(client):
    """Клиент с сессией студента, но студент не привязан (нет в БД по email и по ФИО)."""
    session = client.session
    session['manager_email'] = 'student@example.com'
    session['manager_name'] = 'Несуществующий Студент'
    session['manager_role'] = 'student'
    session['manager_groups'] = ['students']
    session['keycloak_user'] = True
    session.save()
    return client
