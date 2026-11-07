"""Тесты interns.api.import_views."""
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternImportAPI:
    def test_unauthenticated(self, api_client):
        url = reverse('intern_import_api')
        assert api_client.post(url, {}).status_code in (401, 403)

    def test_manager_forbidden(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        assert api_client.post(reverse('intern_import_api'), {}).status_code == 403

    def test_admin_no_file_400(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        assert api_client.post(reverse('intern_import_api'), {}).status_code == 400

    @patch('interns.api.import_views.async_import_from_file.delay')
    def test_admin_upload_started(self, mock_delay, api_client, api_admin_user):
        mock_delay.return_value = MagicMock(id='task-intern-1')
        api_client.force_authenticate(user=api_admin_user)
        upload = SimpleUploadedFile('interns.csv', b'full_name\nIvan')
        response = api_client.post(
            reverse('intern_import_api'),
            {'file': upload},
            format='multipart',
        )
        assert response.status_code == 200
        assert response.data['task_id'] == 'task-intern-1'


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternSyncImportAPI:
    def test_unauthenticated(self, api_client):
        url = reverse('intern_sync_import_api')
        assert api_client.post(url, {}).status_code in (401, 403)

    def test_manager_forbidden(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        assert api_client.post(reverse('intern_sync_import_api'), {}).status_code == 403

    def test_admin_no_file_400(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        assert api_client.post(reverse('intern_sync_import_api'), {}).status_code == 400

    @patch('interns.api.import_views.async_import_from_file.delay')
    def test_admin_upload_started(self, mock_delay, api_client, api_admin_user):
        mock_delay.return_value = MagicMock(id='task-intern-sync-1')
        api_client.force_authenticate(user=api_admin_user)
        upload = SimpleUploadedFile('interns.csv', b'full_name\nIvan')
        response = api_client.post(
            reverse('intern_sync_import_api'),
            {'file': upload},
            format='multipart',
        )
        assert response.status_code == 200
        assert response.data['task_id'] == 'task-intern-sync-1'


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternImportDatesAPI:
    @patch('interns.api.import_views.async_import_from_file.delay')
    def test_admin_dates_import(self, mock_delay, api_client, api_admin_user):
        mock_delay.return_value = MagicMock(id='task-dates-1')
        api_client.force_authenticate(user=api_admin_user)
        upload = SimpleUploadedFile(
            'dates.csv',
            'ФИ,Дата\nIvan,01.01.2025'.encode('utf-8'),
        )
        response = api_client.post(
            reverse('intern_import_dates_api'),
            {'file': upload},
            format='multipart',
        )
        assert response.status_code == 200
        assert response.data['status'] == 'started'
