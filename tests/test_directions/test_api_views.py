"""
Тесты для API-эндпоинтов приложения directions.

Покрывают:
- DirectionViewSet GET /api/directions/        — список
- DirectionViewSet GET /api/directions/<id>/   — детали
- DirectionViewSet POST /api/directions/       — создание (только админ)

Доступ: IsManagerOrAdmin (менеджеры и администраторы); POST — IsAdminRole.
"""
from unittest.mock import patch

import pytest

from core.decorators import get_analytics_cache_key
from directions.models import Direction
from tests.helpers import get_api_results


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDirectionViewSetAuth:
    """Тесты аутентификации и прав доступа к /api/directions/."""

    def test_unauthenticated_list_returns_401_or_403(self, api_client):
        """Неаутентифицированный запрос к списку получает 401/403."""
        response = api_client.get('/api/directions/')
        assert response.status_code in (401, 403)

    def test_unauthenticated_retrieve_returns_401_or_403(self, api_client, direction):
        """Неаутентифицированный запрос к деталям получает 401/403."""
        response = api_client.get(f'/api/directions/{direction.id}/')
        assert response.status_code in (401, 403)

    def test_manager_can_access_list(self, api_client, api_manager_user):
        """Менеджер имеет доступ к списку направлений."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/directions/')
        assert response.status_code == 200

    def test_manager_can_access_retrieve(self, api_client, api_manager_user, direction):
        """Менеджер имеет доступ к деталям направления."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/directions/{direction.id}/')
        assert response.status_code == 200

    def test_admin_can_access_list(self, api_client, api_admin_user):
        """Администратор имеет доступ к списку направлений."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/directions/')
        assert response.status_code == 200

    def test_admin_can_access_retrieve(self, api_client, api_admin_user, direction):
        """Администратор имеет доступ к деталям направления."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/directions/{direction.id}/')
        assert response.status_code == 200

    def test_user_without_groups_cannot_access_list(self, api_client, api_anon_user):
        """Пользователь без групп получает 403."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get('/api/directions/')
        assert response.status_code == 403

    def test_user_without_groups_cannot_access_retrieve(self, api_client, api_anon_user, direction):
        """Пользователь без групп не может получить детали направления."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get(f'/api/directions/{direction.id}/')
        assert response.status_code == 403

    def test_response_content_type_is_json(self, api_client, api_manager_user):
        """Ответ возвращается в формате JSON."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/directions/')
        assert 'application/json' in response['Content-Type']


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDirectionViewSetList:
    """Тесты списка направлений."""

    def test_list_returns_directions(self, api_client, api_manager_user, direction):
        """Список возвращает направления с полями id, name."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/directions/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) >= 1
        by_id = {r['id']: r for r in results}
        assert direction.id in by_id
        assert by_id[direction.id]['name'] == direction.name
        assert 'id' in by_id[direction.id]
        assert 'name' in by_id[direction.id]

    def test_list_filter_by_q(self, api_client, api_manager_user, direction):
        """Фильтр q ищет по названию."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/directions/', {'q': direction.name})
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        assert results[0]['name'] == direction.name


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDirectionViewSetRetrieve:
    """Тесты деталей направления."""

    def test_retrieve_returns_direction(self, api_client, api_manager_user, direction):
        """Retrieve возвращает направление с полями id, name."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/directions/{direction.id}/')
        assert response.status_code == 200
        data = response.data
        assert data['id'] == direction.id
        assert data['name'] == direction.name

    def test_retrieve_404_for_invalid_id(self, api_client, api_manager_user):
        """Retrieve для несуществующего id возвращает 404."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/directions/99999/')
        assert response.status_code == 404


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDirectionViewSetCreate:
    """Тесты создания направления POST /api/directions/."""

    def test_unauthenticated_create_returns_401_or_403(self, api_client):
        """Неаутентифицированный POST получает 401/403."""
        response = api_client.post('/api/directions/', {'name': 'Новое направление'}, format='json')
        assert response.status_code in (401, 403)

    def test_manager_cannot_create(self, api_client, api_manager_user):
        """Менеджер не может создать направление."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post('/api/directions/', {'name': 'Только админ'}, format='json')
        assert response.status_code == 403

    def test_admin_creates_direction(self, api_client, api_admin_user):
        """Администратор создаёт направление, ответ 201."""
        api_client.force_authenticate(user=api_admin_user)
        name = 'Направление из API-теста'
        response = api_client.post('/api/directions/', {'name': name}, format='json')
        assert response.status_code == 201
        assert response.data['name'] == name
        created = Direction.objects.get(id=response.data['id'])
        assert created.name == name

    @patch('directions.api.views.cache')
    def test_admin_create_invalidates_metrics_cache(self, mock_cache, api_client, api_admin_user):
        """После создания сбрасывается кэш метрик и наблюдений."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post('/api/directions/', {'name': 'Кэш сброс'}, format='json')
        assert response.status_code == 201
        mock_cache.delete.assert_any_call(get_analytics_cache_key('direction_metrics_api', {}))
        mock_cache.delete.assert_any_call(get_analytics_cache_key('directions_observations_api', {}))
