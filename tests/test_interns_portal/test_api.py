import pytest
from datetime import date, time
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from core.constants import INTERVIEW_FORMAT_ONLINE
from interviews.models import Interview
from tests.helpers import get_api_results, make_keycloak_user

from .conftest import STUDENT_CORPORATE_EMAIL, STUDENT_FULL_NAME


def _student_api_user():
    return make_keycloak_user(
        email=STUDENT_CORPORATE_EMAIL,
        groups=['students'],
        full_name=STUDENT_FULL_NAME,
    )


@pytest.mark.django_db
class TestInternPortalInterviewListAPI:
    def test_list_requires_auth(self, api_client):
        url = reverse('api_intern_portal_interviews')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_forbidden_for_manager(self, api_client, api_manager_user, student_intern):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('api_intern_portal_interviews')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_returns_only_own_interviews(self, api_client, student_intern, direction):
        from interns.models import Intern

        other = Intern.objects.create(
            full_name='Другой Студент',
            email='other@example.com',
            manager_email='manager2@example.com',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
        )
        Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            date=date(2025, 12, 1),
            time=time(10, 0),
        )
        Interview.objects.create(
            intern=other,
            direction=direction,
            manager_email='manager2@example.com',
            interview_type='screening',
            date=date(2025, 12, 2),
            time=time(11, 0),
        )

        api_client.force_authenticate(user=_student_api_user())
        response = api_client.get(reverse('api_intern_portal_interviews'))
        assert response.status_code == status.HTTP_200_OK
        results = get_api_results(response)
        assert len(results) == 1
        own_iv = Interview.objects.get(intern=student_intern)
        assert results[0]['id'] == own_iv.pk

    def test_list_excludes_hidden_types(
        self, api_client, student_intern, student_interview_test_type, direction
    ):
        api_client.force_authenticate(user=_student_api_user())
        response = api_client.get(reverse('api_intern_portal_interviews'))
        assert response.status_code == status.HTTP_200_OK
        ids = {row['id'] for row in get_api_results(response)}
        assert student_interview_test_type.pk not in ids

    def test_list_pagination_twenty(self, api_client, student_twenty_one_interviews):
        api_client.force_authenticate(user=_student_api_user())
        response = api_client.get(reverse('api_intern_portal_interviews'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 21
        assert len(response.data['results']) == 20
        page2 = api_client.get(reverse('api_intern_portal_interviews'), {'page': 2})
        assert len(page2.data['results']) == 1


@pytest.mark.django_db
class TestInternPortalUploadAPI:
    def test_upload_requires_auth(self, api_client, student_interview):
        url = reverse('api_intern_portal_upload', kwargs={'interview_id': student_interview.pk})
        response = api_client.post(url, {}, format='multipart')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('interns_portal.api.views.upload_video_to_s3.delay')
    def test_upload_starts_task(self, mock_delay, api_client, student_intern, direction, settings, tmp_path):
        settings.MEDIA_ROOT = str(tmp_path)
        mock_delay.return_value = type('T', (), {'id': 'celery-task-abc'})()
        iv = Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            interview_format=INTERVIEW_FORMAT_ONLINE,
            date=date(2025, 12, 1),
            time=time(10, 0),
        )
        api_client.force_authenticate(user=_student_api_user())
        url = reverse('api_intern_portal_upload', kwargs={'interview_id': iv.pk})
        response = api_client.post(url, {'video': TestInternPortalUploadAPI._video_file()}, format='multipart')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['task_id'] == 'celery-task-abc'
        iv.refresh_from_db()
        assert iv.upload_task_id == 'celery-task-abc'

    @staticmethod
    def _video_file():
        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile('test.mp4', b'\x00\x00\x00\x18ftypmp42', content_type='video/mp4')


@pytest.mark.django_db
class TestInternPortalUploadTaskStatusAPI:
    def test_status_404_for_foreign_task(self, api_client, student_intern, direction):
        iv = Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            date=date(2025, 12, 1),
            time=time(10, 0),
            upload_task_id='my-task',
        )
        api_client.force_authenticate(user=_student_api_user())
        url = reverse('api_intern_portal_upload_task', kwargs={'task_id': 'other-task'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        # sanity: own task would not 404 without celery mock — use wrong id
        assert iv.upload_task_id == 'my-task'

    @patch('core.celery_task_status.AsyncResult')
    def test_status_returns_payload_for_own_task(self, mock_ar, api_client, student_intern, direction):
        mock_inst = mock_ar.return_value
        mock_inst.state = 'PROGRESS'
        mock_inst.info = {'status': 'Загрузка...', 'current': 50, 'total': 100}

        Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            date=date(2025, 12, 1),
            time=time(10, 0),
            upload_task_id='owned-task-id',
        )
        api_client.force_authenticate(user=_student_api_user())
        url = reverse('api_intern_portal_upload_task', kwargs={'task_id': 'owned-task-id'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['state'] == 'PROGRESS'
        assert response.data['current'] == 50
