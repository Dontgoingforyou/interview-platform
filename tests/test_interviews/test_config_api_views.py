"""Тесты interviews.api.config_views."""
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDeepgramBalanceAPI:
    def test_manager_forbidden(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        assert api_client.get(reverse('deepgram_balance_api')).status_code == 403

    @patch('interviews.api.config_views.TranscriptionService.get_balance')
    def test_admin_balance(self, mock_balance, api_client, api_admin_user):
        mock_balance.return_value = {'amount': 10.5}
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse('deepgram_balance_api'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['amount'] == 10.5

    @patch('interviews.api.config_views.TranscriptionService.get_balance')
    def test_admin_balance_error(self, mock_balance, api_client, api_admin_user):
        mock_balance.side_effect = RuntimeError('api down')
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse('deepgram_balance_api'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['amount'] is None
        assert 'error' in response.data
