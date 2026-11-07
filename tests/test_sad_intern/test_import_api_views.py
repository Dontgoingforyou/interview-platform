"""Тесты sad_intern.api.import_views."""
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSadInternImportAPI:
    def test_unauthenticated(self, api_client):
        assert api_client.post(reverse('api_sad_intern_import'), {}).status_code in (401, 403)

    def test_manager_forbidden(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        assert api_client.post(reverse('api_sad_intern_import'), {}).status_code == 403

    @patch('sad_intern.api.import_views.async_import_from_file.delay')
    def test_admin_upload(self, mock_delay, api_client, api_admin_user):
        mock_delay.return_value = MagicMock(id='sad-import-1')
        api_client.force_authenticate(user=api_admin_user)
        upload = SimpleUploadedFile('sad.xlsx', b'x')
        response = api_client.post(
            reverse('api_sad_intern_import'),
            {'file': upload},
            format='multipart',
        )
        assert response.status_code == 200
        assert response.data['task_id'] == 'sad-import-1'
