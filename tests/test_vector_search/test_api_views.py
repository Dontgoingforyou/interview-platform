"""Тесты vector_search.api.views."""
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from vector_search.models import VectorEmbedding


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSemanticSearchAPI:
    def test_unauthenticated(self, api_client):
        url = reverse('vector_search:semantic_search')
        response = api_client.post(url, {'query': 'test'}, format='json')
        assert response.status_code in (401, 403)

    @patch('vector_search.api.views.EmbeddingService.semantic_search')
    def test_manager_search_applies_email_filter(self, mock_search, api_client, api_manager_user):
        mock_search.return_value = ([], 12.5)
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            reverse('vector_search:semantic_search'),
            {'query': 'студенты', 'top_k': 5},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs['filters']['manager_email'] == api_manager_user.email

    @patch('vector_search.api.views.EmbeddingService.semantic_search')
    def test_admin_no_manager_filter(self, mock_search, api_client, api_admin_user):
        mock_search.return_value = ([], 5.0)
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post(
            reverse('vector_search:semantic_search'),
            {'query': 'все'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        filters = mock_search.call_args[1].get('filters')
        assert not filters or 'manager_email' not in filters

    def test_invalid_payload_400(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(reverse('vector_search:semantic_search'), {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('vector_search.api.views.EmbeddingService.semantic_search')
    def test_manager_foreign_email_filter_403(self, mock_search, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            reverse('vector_search:semantic_search'),
            {
                'query': 'x',
                'manager_email': 'other@example.com',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_search.assert_not_called()


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSimilarEntitiesAPI:
    def test_not_found_embedding(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('vector_search:similar_entities')
        response = api_client.post(
            url,
            {'entity_type': 'intern', 'entity_id': '99999'},
            format='json',
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('vector_search.api.views.EmbeddingService.get_similar_entities')
    def test_success(self, mock_similar, api_client, api_admin_user, intern):
        VectorEmbedding.objects.create(
            entity_type='intern',
            entity_id=str(intern.pk),
            text_content='test',
            embedding=[0.1] * 8,
            metadata={'manager_email': 'admin@example.com'},
        )
        mock_similar.return_value = []
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post(
            reverse('vector_search:similar_entities'),
            {'entity_type': 'intern', 'entity_id': str(intern.pk)},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestVectorStatsAPI:
    def test_stats_authenticated(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('vector_search:vector_stats')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
