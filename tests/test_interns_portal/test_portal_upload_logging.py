"""Тесты структурированного логирования [PORTAL_UPLOAD]."""

from datetime import date, time
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from core.constants import INTERVIEW_FORMAT_ONLINE
from interviews.models import Interview
from tests.helpers import make_keycloak_user

from .conftest import STUDENT_CORPORATE_EMAIL, STUDENT_FULL_NAME


def _student_user():
    return make_keycloak_user(
        email=STUDENT_CORPORATE_EMAIL,
        groups=['students'],
        full_name=STUDENT_FULL_NAME,
    )


def _mp4_file():
    return SimpleUploadedFile('test.mp4', b'\x00\x00\x00\x18ftypmp42', content_type='video/mp4')


def _logged_phases(mock_log) -> list[str]:
    return [call.args[1] for call in mock_log.call_args_list]


@pytest.mark.django_db
class TestPortalUploadLogging:
    """Вызовы portal_upload_log на ключевых этапах API."""

    @patch('interns_portal.api.views.portal_upload_log')
    @patch('interns_portal.api.views.upload_video_to_s3.delay')
    def test_success_logs_celery_dispatched_without_email(
        self, mock_delay, mock_log, api_client, student_intern, direction, settings, tmp_path
    ):
        mock_delay.return_value = MagicMock(id='task-log-1')
        settings.PRIVATE_UPLOAD_ROOT = tmp_path

        iv = Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            interview_format=INTERVIEW_FORMAT_ONLINE,
            date=date(2025, 12, 1),
            time=time(10, 0),
        )
        api_client.force_authenticate(user=_student_user())
        url = reverse('api_intern_portal_upload', kwargs={'interview_id': iv.pk})
        response = api_client.post(url, {'video': _mp4_file()}, format='multipart')

        assert response.status_code == status.HTTP_200_OK
        phases = _logged_phases(mock_log)
        assert 'request_start' in phases
        assert 'celery_dispatched' in phases
        for call in mock_log.call_args_list:
            assert 'student@example.com' not in str(call)

    @patch('interns_portal.api.views.portal_upload_log')
    def test_validation_failed_logs_and_clears_slot(self, mock_log, api_client, student_intern, direction):
        iv = Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            interview_format=INTERVIEW_FORMAT_ONLINE,
            date=date(2025, 12, 1),
            time=time(10, 0),
        )
        api_client.force_authenticate(user=_student_user())
        url = reverse('api_intern_portal_upload', kwargs={'interview_id': iv.pk})
        bad = SimpleUploadedFile('x.mp4', b'bad', content_type='video/mp4')
        response = api_client.post(url, {'video': bad}, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        iv.refresh_from_db()
        assert iv.upload_task_id == ''
        phases = _logged_phases(mock_log)
        assert 'validation_failed' in phases
        assert 'slot_cleared' in phases
