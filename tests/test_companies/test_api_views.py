"""
Тесты для API-эндпоинтов приложения companies.

Покрывают:
- CompanyViewSet — список, детали, CRUD, сортировка, interviews_count
- GET /api/companies/stats/
- POST /api/companies/merge/

Доступ: чтение — IsManagerOrAdmin; запись — менеджеры (не HR/outstaff); удаление — админ.
"""
import pytest

from tests.helpers import get_api_results


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestCompanyViewSetAuth:
    """Тесты аутентификации и прав доступа к /api/companies/."""

    def test_unauthenticated_list_returns_401_or_403(self, api_client):
        """Неаутентифицированный запрос к списку получает 401/403."""
        response = api_client.get('/api/companies/')
        assert response.status_code in (401, 403)

    def test_unauthenticated_retrieve_returns_401_or_403(self, api_client, company_a):
        """Неаутентифицированный запрос к деталям получает 401/403."""
        response = api_client.get(f'/api/companies/{company_a.id}/')
        assert response.status_code in (401, 403)

    def test_manager_can_access_list(self, api_client, api_manager_user):
        """Менеджер имеет доступ к списку компаний."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/companies/')
        assert response.status_code == 200

    def test_manager_can_access_retrieve(self, api_client, api_manager_user, company_a):
        """Менеджер имеет доступ к деталям компании."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/companies/{company_a.id}/')
        assert response.status_code == 200

    def test_admin_can_access_list(self, api_client, api_admin_user):
        """Администратор имеет доступ к списку компаний."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/companies/')
        assert response.status_code == 200

    def test_admin_can_access_retrieve(self, api_client, api_admin_user, company_a):
        """Администратор имеет доступ к деталям компании."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/companies/{company_a.id}/')
        assert response.status_code == 200

    def test_user_without_groups_cannot_access_list(self, api_client, api_anon_user):
        """Пользователь без групп получает 403."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get('/api/companies/')
        assert response.status_code == 403

    def test_user_without_groups_cannot_access_retrieve(self, api_client, api_anon_user, company_a):
        """Пользователь без групп не может получить детали компании."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get(f'/api/companies/{company_a.id}/')
        assert response.status_code == 403

    def test_response_content_type_is_json(self, api_client, api_manager_user):
        """Ответ возвращается в формате JSON."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/companies/')
        assert 'application/json' in response['Content-Type']


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestCompanyViewSetList:
    """Тесты списка компаний."""

    def test_list_returns_companies(self, api_client, api_manager_user, company_a, company_c):
        """Список возвращает все компании с ожидаемыми полями."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/companies/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 2
        by_id = {r['id']: r for r in results}
        assert company_a.id in by_id
        assert company_c.id in by_id
        a = by_id[company_a.id]
        assert a['name'] == 'Яндекс'
        assert a['is_bigtech'] is True
        assert 'Yandex' in a.get('aliases', '')
        assert 'aliases_list' in a
        assert 'Yandex' in a['aliases_list']
        assert 'interviews_count' in a
        assert a['interviews_count'] == 0

    def test_list_includes_interviews_count(
        self,
        api_client,
        api_manager_user,
        company_a,
        company_c,
        interview_for_company,
    ):
        """Список содержит число собеседований по компании."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/companies/')
        assert response.status_code == 200
        results = get_api_results(response)
        by_id = {r['id']: r for r in results}
        assert by_id[company_a.id]['interviews_count'] == 1
        assert by_id[company_c.id]['interviews_count'] == 0

    def test_list_filter_by_q(self, api_client, api_manager_user, company_a, company_c):
        """Фильтр q ищет по названию и псевдонимам."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/companies/', {'q': 'Яндекс'})
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        assert results[0]['name'] == 'Яндекс'

    def test_list_filter_by_is_bigtech_true(self, api_client, api_manager_user, company_a, company_c):
        """Фильтр is_bigtech=true возвращает только бигтех."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/companies/', {'is_bigtech': 'true'})
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        assert results[0]['is_bigtech'] is True

    def test_list_filter_by_is_bigtech_false(self, api_client, api_manager_user, company_a, company_c):
        """Фильтр is_bigtech=false возвращает только не бигтех."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/companies/', {'is_bigtech': 'false'})
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        assert results[0]['is_bigtech'] is False


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestCompanyViewSetRetrieve:
    """Тесты деталей компании."""

    def test_retrieve_returns_company(self, api_client, api_manager_user, company_a):
        """Retrieve возвращает компанию с полями id, name, is_bigtech, aliases, aliases_list."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/companies/{company_a.id}/')
        assert response.status_code == 200
        data = response.data
        assert data['id'] == company_a.id
        assert data['name'] == 'Яндекс'
        assert data['is_bigtech'] is True
        assert 'Yandex' in data['aliases_list']

    def test_retrieve_404_for_invalid_id(self, api_client, api_manager_user):
        """Retrieve для несуществующего id возвращает 404."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/companies/99999/')
        assert response.status_code == 404


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestCompanyStatsAPI:
    """GET /api/companies/stats/."""

    def test_stats_requires_auth(self, api_client):
        response = api_client.get('/api/companies/stats/')
        assert response.status_code in (401, 403)

    def test_stats_returns_counts(self, api_client, api_manager_user, company_a, company_c, interview_for_company):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/companies/stats/')
        assert response.status_code == 200
        assert response.data['total_count'] == 2
        assert response.data['bigtech_count'] == 1
        assert response.data['with_interviews_count'] == 1
        assert response.data['without_interviews_count'] == 1


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestCompanyWriteAPI:
    """Создание и изменение компаний."""

    def test_manager_can_create(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/api/companies/',
            {'name': 'Новая компания API', 'is_bigtech': False, 'aliases': 'Alias1'},
            format='json',
        )
        assert response.status_code == 201
        assert response.data['name'] == 'Новая компания API'
        assert response.data['interviews_count'] == 0

    def test_hr_cannot_create(self, api_client, api_hr_user):
        api_client.force_authenticate(user=api_hr_user)
        response = api_client.post(
            '/api/companies/',
            {'name': 'HR попытка', 'is_bigtech': False, 'aliases': ''},
            format='json',
        )
        assert response.status_code == 403

    def test_manager_can_patch(self, api_client, api_manager_user, company_c):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/companies/{company_c.id}/',
            {'is_bigtech': True},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['is_bigtech'] is True

    def test_hr_cannot_patch(self, api_client, api_hr_user, company_c):
        api_client.force_authenticate(user=api_hr_user)
        response = api_client.patch(
            f'/api/companies/{company_c.id}/',
            {'name': 'X'},
            format='json',
        )
        assert response.status_code == 403


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestCompanyDeleteAPI:
    """Удаление компании (только админ)."""

    def test_manager_cannot_delete(self, api_client, api_manager_user, company_c):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.delete(f'/api/companies/{company_c.id}/')
        assert response.status_code == 403

    def test_admin_deletes_without_interviews(self, api_client, api_admin_user, company_c):
        pk = company_c.id
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/companies/{pk}/')
        assert response.status_code == 204

    def test_admin_delete_protected_when_interviews_exist(
        self,
        api_client,
        api_admin_user,
        company_a,
        interview_for_company,
    ):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/companies/{company_a.id}/')
        assert response.status_code == 409
        assert 'собеседования' in response.data['detail']


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestCompanyMergeAPI:
    """POST /api/companies/merge/."""

    def test_merge_requires_auth(self, api_client):
        response = api_client.post(
            '/api/companies/merge/',
            {'primary_id': 1, 'duplicate_ids': [2]},
            format='json',
        )
        assert response.status_code in (401, 403)

    def test_hr_cannot_merge(self, api_client, api_hr_user, company_a, company_b):
        api_client.force_authenticate(user=api_hr_user)
        response = api_client.post(
            '/api/companies/merge/',
            {'primary_id': company_a.id, 'duplicate_ids': [company_b.id]},
            format='json',
        )
        assert response.status_code == 403

    def test_merge_success(self, api_client, api_manager_user, company_a, company_b):
        dup_id = company_b.id
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/api/companies/merge/',
            {'primary_id': company_a.id, 'duplicate_ids': [company_b.id]},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['primary_id'] == company_a.id
        assert dup_id in response.data['removed_ids']

    def test_merge_rejects_primary_in_duplicates(self, api_client, api_manager_user, company_a):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/api/companies/merge/',
            {'primary_id': company_a.id, 'duplicate_ids': [company_a.id]},
            format='json',
        )
        assert response.status_code == 400


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestCompanyHrRead:
    """HR может только читать список и детали."""

    def test_hr_can_list(self, api_client, api_hr_user, company_a):
        api_client.force_authenticate(user=api_hr_user)
        response = api_client.get('/api/companies/')
        assert response.status_code == 200

    def test_hr_can_retrieve(self, api_client, api_hr_user, company_a):
        api_client.force_authenticate(user=api_hr_user)
        response = api_client.get(f'/api/companies/{company_a.id}/')
        assert response.status_code == 200

    def test_hr_can_stats(self, api_client, api_hr_user, company_a):
        api_client.force_authenticate(user=api_hr_user)
        response = api_client.get('/api/companies/stats/')
        assert response.status_code == 200
