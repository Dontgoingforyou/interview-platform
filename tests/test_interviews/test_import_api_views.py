"""Тесты interviews.api.import_views."""
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewImportAPI:
    def test_unauthenticated(self, api_client):
        url = reverse('interview_import_api')
        assert api_client.post(url, {}).status_code in (401, 403)

    def test_manager_forbidden(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        assert api_client.post(reverse('interview_import_api'), {}).status_code == 403

    @patch('interviews.api.import_views.async_import_from_file.delay')
    def test_admin_upload(self, mock_delay, api_client, api_admin_user):
        mock_delay.return_value = MagicMock(id='iv-import-1')
        api_client.force_authenticate(user=api_admin_user)
        upload = SimpleUploadedFile('iv.csv', b'a,b\n1,2')
        response = api_client.post(
            reverse('interview_import_api'),
            {'file': upload},
            format='multipart',
        )
        assert response.status_code == 200
        assert response.data['task_id'] == 'iv-import-1'


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestImportTaskStatusAPI:
    @patch('interviews.api.import_views.celery_task_status_payload')
    def test_returns_payload(self, mock_payload, api_client, api_manager_user):
        mock_payload.return_value = {'state': 'PENDING', 'status': 'wait', 'current': 0, 'total': 100}
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('api_import_status', kwargs={'task_id': 'tid-1'})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data['state'] == 'PENDING'
