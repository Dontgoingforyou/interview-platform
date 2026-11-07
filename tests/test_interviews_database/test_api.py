from datetime import date

import pytest
from django.urls import reverse

from interviews.models import Interview
from tests.helpers import get_api_results
from transcriptions.models import InterviewTranscription, TranscriptionStatus


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewsDatabaseAPIAuth:
    """Аутентификация и права."""

    def test_unauthenticated_returns_401_or_403(self, api_client):
        response = api_client.get(reverse('api_interviews_database_list'))
        assert response.status_code in (401, 403)

    def test_manager_can_list(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(reverse('api_interviews_database_list'))
        assert response.status_code == 200

    def test_admin_can_list(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse('api_interviews_database_list'))
        assert response.status_code == 200

    def test_mentor_can_list(self, api_client, api_mentor_user):
        api_client.force_authenticate(user=api_mentor_user)
        response = api_client.get(reverse('api_interviews_database_list'))
        assert response.status_code == 200

    def test_user_without_groups_gets_403(self, api_client, api_anon_user):
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get(reverse('api_interviews_database_list'))
        assert response.status_code == 403


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewsDatabaseAPIList:
    """Фильтрация «есть запись» и область видимости."""

    def test_includes_interview_with_link(
        self, api_client, api_manager_user, interview_with_link
    ):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(reverse('api_interviews_database_list'))
        assert response.status_code == 200
        ids = {row['id'] for row in get_api_results(response)}
        assert interview_with_link.id in ids

    def test_excludes_interview_without_link(
        self, api_client, api_admin_user, interview_without_link
    ):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse('api_interviews_database_list'))
        assert response.status_code == 200
        ids = {row['id'] for row in get_api_results(response)}
        assert interview_without_link.id not in ids

    def test_manager_sees_other_manager_recording(
        self, api_client, api_manager_user, interview_other_with_link
    ):
        """В базе собеседований все менеджеры видят все записи, а не только свои."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(reverse('api_interviews_database_list'))
        assert response.status_code == 200
        ids = {row['id'] for row in get_api_results(response)}
        assert interview_other_with_link.id in ids

    def test_search_by_link_substring(
        self, api_client, api_admin_user, interview_with_link, interview_with_link_and_company
    ):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(
            reverse('api_interviews_database_list'),
            {'q': 'zoom.us/rec/abc123'},
        )
        assert response.status_code == 200
        ids = {row['id'] for row in get_api_results(response)}
        assert interview_with_link.id in ids
        assert interview_with_link_and_company.id not in ids

    def test_filter_by_company(
        self, api_client, api_admin_user, interview_with_link_and_company, company
    ):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(
            reverse('api_interviews_database_list'),
            {'company': company.pk},
        )
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) >= 1
        assert all(row['company_id'] == company.pk for row in results)

    def test_filter_by_interview_type(
        self, api_client, api_admin_user, interview_with_link
    ):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(
            reverse('api_interviews_database_list'),
            {'interview_type': 'tech'},
        )
        assert response.status_code == 200
        for row in get_api_results(response):
            assert row['interview_type'] == 'tech'

    def test_response_includes_upload_task_id_field(
        self, api_client, api_admin_user, db, intern, direction
    ):
        row = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            upload_task_id='task-uuid-123',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse('api_interviews_database_list'))
        assert response.status_code == 200
        by_id = {r['id']: r for r in get_api_results(response)}
        assert by_id[row.id]['upload_task_id'] == 'task-uuid-123'

    def test_default_page_size_matches_list_pagination(self, api_client, api_admin_user, db, intern, direction):
        for i in range(25):
            Interview.objects.create(
                intern=intern,
                direction=direction,
                manager_email='manager@example.com',
                interview_type='screening',
                link=f'https://example.com/rec/{i}',
            )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse('api_interviews_database_list'))
        assert response.status_code == 200
        assert len(get_api_results(response)) == 20
        assert response.data['count'] >= 25

    def test_filter_transcription_completed(
        self, api_client, api_admin_user, intern, direction, db
    ):
        a = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            date=date(2025, 3, 1),
            link='https://example.com/rec-a',
        )
        b = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            date=date(2025, 3, 2),
            link='https://example.com/rec-b',
        )
        InterviewTranscription.objects.create(
            interview=a,
            status=TranscriptionStatus.COMPLETED,
            text='готово',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(
            reverse('api_interviews_database_list'),
            {'transcription': 'completed'},
        )
        assert response.status_code == 200
        ids = {row['id'] for row in get_api_results(response)}
        assert a.id in ids
        assert b.id not in ids

    def test_filter_transcription_failed(
        self, api_client, api_admin_user, intern, direction, db
    ):
        a = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            date=date(2025, 3, 3),
            link='https://example.com/rec-fail',
        )
        b = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            date=date(2025, 3, 4),
            link='https://example.com/rec-ok',
        )
        InterviewTranscription.objects.create(
            interview=a,
            status=TranscriptionStatus.FAILED,
            error_message='ошибка',
        )
        InterviewTranscription.objects.create(
            interview=b,
            status=TranscriptionStatus.COMPLETED,
            text='ok',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(
            reverse('api_interviews_database_list'),
            {'transcription': 'failed'},
        )
        assert response.status_code == 200
        ids = {row['id'] for row in get_api_results(response)}
        assert a.id in ids
        assert b.id not in ids

    def test_filter_transcription_in_progress(
        self, api_client, api_admin_user, intern, direction, db
    ):
        a = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            date=date(2025, 3, 5),
            link='https://example.com/rec-pend',
        )
        b = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            date=date(2025, 3, 6),
            link='https://example.com/rec-proc',
        )
        c = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            date=date(2025, 3, 7),
            link='https://example.com/rec-done',
        )
        InterviewTranscription.objects.create(
            interview=a,
            status=TranscriptionStatus.PENDING,
        )
        InterviewTranscription.objects.create(
            interview=b,
            status=TranscriptionStatus.PROCESSING,
        )
        InterviewTranscription.objects.create(
            interview=c,
            status=TranscriptionStatus.COMPLETED,
            text='x',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(
            reverse('api_interviews_database_list'),
            {'transcription': 'in_progress'},
        )
        assert response.status_code == 200
        ids = {row['id'] for row in get_api_results(response)}
        assert a.id in ids
        assert b.id in ids
        assert c.id not in ids
