"""Тесты interviews.api.interview_analytics."""
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewAnalyticsAPI:
    def test_unauthenticated(self, api_client):
        assert api_client.get(reverse('interview_analytics_api')).status_code in (401, 403)

    @patch('interviews.api.interview_analytics.compute_interview_analytics')
    def test_manager_gets_analytics(self, mock_compute, api_client, api_manager_user):
        mock_compute.return_value = {'total': 1}
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(reverse('interview_analytics_api'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 1


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewTypeBreakdownAPI:
    @patch('interviews.api.interview_analytics.interview_list.interview_type_statistics_payload')
    @patch('interviews.api.interview_analytics.interview_list.build_interview_api_list_queryset')
    def test_breakdown(self, mock_qs, mock_payload, api_client, api_manager_user):
        mock_qs.return_value = []
        mock_payload.return_value = {'types': []}
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(reverse('interview_type_breakdown_api'))
        assert response.status_code == status.HTTP_200_OK
