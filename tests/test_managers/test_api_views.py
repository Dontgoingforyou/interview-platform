"""
Тесты для API-эндпоинтов приложения managers.

Покрывают:
- ManagerViewSet GET  /api/managers/               — список (только admin)
- ManagerViewSet GET  /api/managers/{email}/        — детали (только admin)
- ManagerViewSet GET  /api/managers/me/             — профиль текущего пользователя
- ManagerViewSet PATCH /api/managers/{email}/update/ — обновление (только admin)

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.api       - для группировки API-тестов
"""
import pytest
from django.db import connection

from tests.helpers import make_keycloak_user, get_api_results

requires_postgres = pytest.mark.skipif(
    connection.vendor != 'postgresql',
    reason="JSONField __contains поддерживается только на PostgreSQL"
)


# ============================================================================
# Аутентификация и права доступа
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestManagerViewSetAuth:
    """Тесты аутентификации и прав доступа к /api/managers/."""

    def test_unauthenticated_list_returns_401_or_403(self, api_client):
        """Неаутентифицированный запрос получает 401/403."""
        response = api_client.get('/api/managers/')
        assert response.status_code in (401, 403)

    def test_unauthenticated_retrieve_returns_401_or_403(self, api_client, manager):
        """Неаутентифицированный запрос на retrieve получает 401/403."""
        response = api_client.get(f'/api/managers/{manager.email}/')
        assert response.status_code in (401, 403)

    def test_regular_manager_cannot_access_list(self, api_client, api_manager_user):
        """Обычный менеджер не может получить список (только admin)."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/managers/')
        assert response.status_code == 403

    def test_regular_manager_cannot_access_retrieve(self, api_client, api_manager_user, manager):
        """Обычный менеджер не может получить детали менеджера (только admin)."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/managers/{manager.email}/')
        assert response.status_code == 403

    def test_admin_can_access_list(self, api_client, api_admin_user):
        """Администратор имеет доступ к списку менеджеров."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/')
        assert response.status_code == 200

    def test_admin_can_access_retrieve(self, api_client, api_admin_user, manager):
        """Администратор имеет доступ к деталям менеджера."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/managers/{manager.email}/')
        assert response.status_code == 200

    def test_user_without_groups_cannot_access_list(self, api_client, api_anon_user):
        """Пользователь без групп получает 403."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get('/api/managers/')
        assert response.status_code == 403

    def test_response_content_type_is_json(self, api_client, api_admin_user):
        """Ответ возвращается в формате JSON."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/')
        assert 'application/json' in response['Content-Type']


# ============================================================================
# GET /api/managers/ — список менеджеров
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestManagerViewSetList:
    """Тесты GET /api/managers/ — список менеджеров."""

    def test_admin_sees_all_managers(self, api_client, api_admin_user, manager, manager2, admin_manager):
        """Администратор видит всех менеджеров в системе."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/')
        assert response.status_code == 200
        results = get_api_results(response)
        emails = [r['email'] for r in results]
        assert manager.email in emails
        assert manager2.email in emails
        assert admin_manager.email in emails

    def test_empty_list_when_no_managers(self, api_client, api_admin_user):
        """Пустой список при отсутствии менеджеров в системе."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert results == []

    def test_response_has_required_fields(self, api_client, api_admin_user, manager):
        """Ответ содержит все обязательные поля."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/')
        results = get_api_results(response)
        assert len(results) >= 1
        item = results[0]
        expected_fields = {
            'email', 'full_name', 'username', 'groups', 'is_active',
            'is_admin', 'is_employment_manager', 'is_cv_manager',
            'is_education_manager', 'created_at', 'updated_at',
        }
        assert expected_fields.issubset(set(item.keys()))

    def test_filter_active_managers(self, api_client, api_admin_user, manager, manager2):
        """Фильтр is_active=true возвращает только активных менеджеров."""
        manager2.is_active = False
        manager2.save()
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/', {'is_active': 'true'})
        assert response.status_code == 200
        results = get_api_results(response)
        assert all(item['is_active'] is True for item in results)

    def test_filter_inactive_managers(self, api_client, api_admin_user, manager, manager2):
        """Фильтр is_active=false возвращает только неактивных менеджеров."""
        manager2.is_active = False
        manager2.save()
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/', {'is_active': 'false'})
        assert response.status_code == 200
        results = get_api_results(response)
        assert all(item['is_active'] is False for item in results)

    @pytest.mark.parametrize('val', ['true', '1', 'yes'])
    def test_filter_active_true_variants(self, api_client, api_admin_user, manager, manager2, val):
        """Фильтр is_active принимает значения 'true', '1', 'yes'."""
        manager2.is_active = False
        manager2.save()
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/', {'is_active': val})
        assert response.status_code == 200
        results = get_api_results(response)
        assert all(item['is_active'] is True for item in results)

    def test_unknown_filter_param_does_not_break_list(self, api_client, api_admin_user, manager):
        """Неизвестные query-параметры не ломают список менеджеров."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/', {'unknown_param': 'value'})
        assert response.status_code == 200

    def test_no_filter_returns_all(self, api_client, api_admin_user, manager, manager2):
        """Без фильтров возвращаются все менеджеры."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) >= 2

    def test_active_field_value_is_true_for_active_manager(self, api_client, api_admin_user, manager):
        """Поле is_active в ответе — True для активного менеджера."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/')
        results = get_api_results(response)
        assert len(results) == 1
        assert results[0]['is_active'] is True

    def test_groups_field_matches_manager_groups(self, api_client, api_admin_user, manager):
        """Поле groups в ответе совпадает с группами менеджера из БД."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/')
        results = get_api_results(response)
        assert len(results) == 1
        assert results[0]['groups'] == manager.groups

    @requires_postgres
    def test_filter_by_group_returns_matching_managers(
        self, api_client, api_admin_user, manager, admin_manager
    ):
        """Фильтр group=employment-managers возвращает только менеджеров с этой группой."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/', {'group': 'employment-managers'})
        assert response.status_code == 200
        results = get_api_results(response)
        assert all('employment-managers' in item['groups'] for item in results)

    @requires_postgres
    def test_filter_by_group_excludes_non_matching_managers(
        self, api_client, api_admin_user, manager, pure_admin_manager
    ):
        """Фильтр group=employment-managers не включает менеджеров без этой группы.

        pure_admin_manager имеет только группу role_admin
        и не должен попасть в результаты.
        """
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/', {'group': 'employment-managers'})
        assert response.status_code == 200
        results = get_api_results(response)
        emails = [item['email'] for item in results]
        assert pure_admin_manager.email not in emails
        assert manager.email in emails

    @requires_postgres
    def test_filter_by_exact_group_not_substring(
        self, api_client, api_admin_user
    ):
        """Фильтр по группе ищет точное вхождение в JSONField, а не подстроку.

        Менеджер с группой 'cv-managers' не должен попасть в результаты
        при фильтре group=managers.
        """
        from managers.models import Manager
        cv_manager = Manager.objects.create(
            email='cv@test.com',
            full_name='CV Менеджер',
            username='cv_manager',
            groups=['cv-managers'],
        )
        api_client.force_authenticate(user=api_admin_user)
        # Фильтр по 'managers' — подстрока 'cv-managers', но не отдельная группа
        response = api_client.get('/api/managers/', {'group': 'managers'})
        assert response.status_code == 200
        results = get_api_results(response)
        emails = [item['email'] for item in results]
        assert cv_manager.email not in emails


# ============================================================================
# GET /api/managers/{email}/ — детали менеджера
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestManagerViewSetRetrieve:
    """Тесты GET /api/managers/{email}/ — детали менеджера."""

    def test_admin_can_retrieve_manager(self, api_client, api_admin_user, manager):
        """Администратор может получить детали менеджера по email."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/managers/{manager.email}/')
        assert response.status_code == 200
        assert response.data['email'] == manager.email

    def test_retrieve_nonexistent_returns_404(self, api_client, api_admin_user):
        """Запрос несуществующего менеджера возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/nonexistent@example.com/')
        assert response.status_code == 404

    def test_retrieve_response_has_required_fields(self, api_client, api_admin_user, manager):
        """Ответ содержит все обязательные поля."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/managers/{manager.email}/')
        assert response.status_code == 200
        expected_fields = {
            'email', 'full_name', 'username', 'groups', 'is_active',
            'is_admin', 'is_employment_manager', 'is_cv_manager',
            'is_education_manager', 'created_at', 'updated_at',
        }
        assert expected_fields.issubset(set(response.data.keys()))

    def test_retrieve_correct_manager_data(self, api_client, api_admin_user, manager):
        """Данные в ответе соответствуют реальным данным менеджера из БД."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/managers/{manager.email}/')
        assert response.status_code == 200
        assert response.data['full_name'] == manager.full_name
        assert response.data['username'] == manager.username
        assert response.data['is_active'] == manager.is_active

    def test_retrieve_admin_shows_is_admin_true(self, api_client, api_admin_user, admin_manager):
        """Для admin_manager поле is_admin=True."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/managers/{admin_manager.email}/')
        assert response.status_code == 200
        assert response.data['is_admin'] is True

    def test_retrieve_regular_manager_shows_is_admin_false(self, api_client, api_admin_user, manager):
        """Для обычного менеджера поле is_admin=False."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/managers/{manager.email}/')
        assert response.status_code == 200
        assert response.data['is_admin'] is False

    def test_retrieve_employment_manager_shows_is_employment_manager_true(
        self, api_client, api_admin_user, manager
    ):
        """Для employment-менеджера поле is_employment_manager=True."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/managers/{manager.email}/')
        assert response.status_code == 200
        assert response.data['is_employment_manager'] is True

    def test_retrieve_groups_matches_db(self, api_client, api_admin_user, manager):
        """Поле groups соответствует данным в БД."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/managers/{manager.email}/')
        assert response.status_code == 200
        assert response.data['groups'] == manager.groups


# ============================================================================
# GET /api/managers/me/ — профиль текущего пользователя
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestManagerViewSetMe:
    """Тесты GET /api/managers/me/ — профиль текущего пользователя."""

    def test_unauthenticated_returns_401_or_403(self, api_client):
        """Неаутентифицированный запрос получает 401/403."""
        response = api_client.get('/api/managers/me/')
        assert response.status_code in (401, 403)

    def test_manager_can_access_me(self, api_client, api_manager_user, manager):
        """Обычный менеджер может получить свой профиль."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/managers/me/')
        assert response.status_code == 200

    def test_admin_can_access_me(self, api_client, api_admin_user, admin_manager):
        """Администратор может получить свой профиль."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/me/')
        assert response.status_code == 200

    def test_me_returns_correct_manager_from_db(self, api_client, api_manager_user, manager):
        """Возвращает данные из БД для текущего пользователя."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/managers/me/')
        assert response.status_code == 200
        assert response.data['email'] == manager.email
        assert response.data['full_name'] == manager.full_name

    def test_me_includes_role_fields(self, api_client, api_manager_user, manager):
        """Ответ /me/ содержит поля ролей."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/managers/me/')
        assert response.status_code == 200
        assert 'is_admin' in response.data
        assert 'is_employment_manager' in response.data
        assert 'is_cv_manager' in response.data
        assert 'is_education_manager' in response.data

    def test_me_returns_token_data_if_manager_not_in_db(self, api_client):
        """Если менеджер не найден в БД, возвращаются данные из токена и поле note."""
        unknown_user = make_keycloak_user(email='unknown@example.com', groups=['employment-managers'])
        api_client.force_authenticate(user=unknown_user)
        response = api_client.get('/api/managers/me/')
        assert response.status_code == 200
        assert response.data['email'] == 'unknown@example.com'
        assert 'note' in response.data

    def test_user_without_groups_cannot_access_me(self, api_client, api_anon_user):
        """Пользователь без групп получает 403 при обращении к /me/."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get('/api/managers/me/')
        assert response.status_code == 403

    def test_cv_manager_can_access_me(self, api_client, cv_api_manager_user):
        """CV-менеджер (без записи в БД) может получить данные /me/ из токена."""
        api_client.force_authenticate(user=cv_api_manager_user)
        response = api_client.get('/api/managers/me/')
        assert response.status_code == 200

    def test_me_employment_manager_is_employment_manager_true(
        self, api_client, api_manager_user, manager
    ):
        """Для employment-менеджера /me/ возвращает is_employment_manager=True."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/managers/me/')
        assert response.status_code == 200
        assert response.data['is_employment_manager'] is True

    def test_me_admin_is_admin_true(self, api_client, api_admin_user, admin_manager):
        """Для администратора /me/ возвращает is_admin=True."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/managers/me/')
        assert response.status_code == 200
        assert response.data['is_admin'] is True


# ============================================================================
# PATCH /api/managers/{email}/update/ — обновление менеджера
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestManagerViewSetUpdate:
    """Тесты PATCH /api/managers/{email}/update/ — обновление менеджера."""

    def test_unauthenticated_cannot_update(self, api_client, manager):
        """Неаутентифицированный запрос не может обновить менеджера."""
        response = api_client.patch(
            f'/api/managers/{manager.email}/update/',
            {'full_name': 'Новое Имя'},
            format='json',
        )
        assert response.status_code in (401, 403)

    def test_regular_manager_cannot_update(self, api_client, api_manager_user, manager):
        """Обычный менеджер не может обновить данные (только admin)."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/managers/{manager.email}/update/',
            {'full_name': 'Новое Имя'},
            format='json',
        )
        assert response.status_code == 403

    def test_admin_can_update_full_name(self, api_client, api_admin_user, manager):
        """Администратор может обновить полное имя менеджера."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/managers/{manager.email}/update/',
            {'full_name': 'Обновлённое Имя'},
            format='json',
        )
        assert response.status_code == 200
        manager.refresh_from_db()
        assert manager.full_name == 'Обновлённое Имя'

    def test_admin_can_deactivate_manager(self, api_client, api_admin_user, manager):
        """Администратор может деактивировать менеджера."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/managers/{manager.email}/update/',
            {'is_active': False},
            format='json',
        )
        assert response.status_code == 200
        manager.refresh_from_db()
        assert manager.is_active is False

    def test_admin_can_activate_manager(self, api_client, api_admin_user, manager):
        """Администратор может активировать менеджера."""
        manager.is_active = False
        manager.save()
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/managers/{manager.email}/update/',
            {'is_active': True},
            format='json',
        )
        assert response.status_code == 200
        manager.refresh_from_db()
        assert manager.is_active is True

    def test_admin_can_update_username(self, api_client, api_admin_user, manager):
        """Администратор может обновить username менеджера."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/managers/{manager.email}/update/',
            {'username': 'new_username'},
            format='json',
        )
        assert response.status_code == 200
        manager.refresh_from_db()
        assert manager.username == 'new_username'

    def test_update_returns_full_manager_data(self, api_client, api_admin_user, manager):
        """Ответ на PATCH содержит полные данные менеджера (ManagerListSerializer)."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/managers/{manager.email}/update/',
            {'full_name': 'Новое Имя'},
            format='json',
        )
        assert response.status_code == 200
        expected_fields = {
            'email', 'full_name', 'username', 'groups', 'is_active',
            'is_admin', 'is_employment_manager', 'is_cv_manager',
            'is_education_manager', 'created_at', 'updated_at',
        }
        assert expected_fields.issubset(set(response.data.keys()))

    def test_update_nonexistent_manager_returns_404(self, api_client, api_admin_user):
        """Обновление несуществующего менеджера возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            '/api/managers/nonexistent@example.com/update/',
            {'full_name': 'Новое Имя'},
            format='json',
        )
        assert response.status_code == 404

    def test_partial_update_does_not_change_other_fields(self, api_client, api_admin_user, manager):
        """PATCH обновляет только переданные поля, остальные не изменяются."""
        original_username = manager.username
        api_client.force_authenticate(user=api_admin_user)
        api_client.patch(
            f'/api/managers/{manager.email}/update/',
            {'full_name': 'Только Имя'},
            format='json',
        )
        manager.refresh_from_db()
        assert manager.username == original_username

    def test_email_is_readonly_cannot_be_changed(self, api_client, api_admin_user, manager):
        """Поле email нельзя изменить через PATCH (оно является read-only)."""
        original_email = manager.email
        api_client.force_authenticate(user=api_admin_user)
        api_client.patch(
            f'/api/managers/{manager.email}/update/',
            {'email': 'changed@example.com'},
            format='json',
        )
        manager.refresh_from_db()
        assert manager.email == original_email

    def test_update_response_reflects_new_data(self, api_client, api_admin_user, manager):
        """Ответ на PATCH отражает обновлённые данные."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/managers/{manager.email}/update/',
            {'full_name': 'Отражённое Имя'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['email'] == manager.email

    def test_update_with_invalid_data_returns_400(self, api_client, api_admin_user, manager):
        """PATCH с невалидными данными возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/managers/{manager.email}/update/',
            {'is_active': 'не_булево'},
            format='json',
        )
        assert response.status_code == 400
