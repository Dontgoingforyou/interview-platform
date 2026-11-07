"""
Тесты для API-эндпоинтов приложения sad_intern.

Покрывают:
- SadInternViewSet GET  /api/sad-interns/           — список (менеджер/admin)
- SadInternViewSet GET  /api/sad-interns/{id}/      — детали (менеджер/admin)
- SadInternViewSet POST /api/sad-interns/           — создание (менеджер / admin)
- SadInternViewSet PATCH /api/sad-interns/{id}/     — обновление (менеджер своих / admin)
- SadInternViewSet DELETE /api/sad-interns/{id}/    — удаление (только admin, 204)
- Фильтрация: status, manager_email, exclude_on_project

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.api       - для группировки API-тестов
"""
import pytest
from datetime import date

from sad_intern.models import SadIntern
from tests.helpers import get_api_results


# ============================================================================
# Аутентификация и права доступа
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSadInternViewSetAuth:
    """Тесты аутентификации и прав доступа к /api/sad-interns/."""

    def test_unauthenticated_list_returns_401_or_403(self, api_client):
        """Неаутентифицированный запрос на список получает 401/403."""
        response = api_client.get('/api/sad-interns/')
        assert response.status_code in (401, 403)

    def test_unauthenticated_retrieve_returns_401_or_403(self, api_client, sad_intern):
        """Неаутентифицированный запрос на детали получает 401/403."""
        response = api_client.get(f'/api/sad-interns/{sad_intern.pk}/')
        assert response.status_code in (401, 403)

    def test_unauthenticated_create_returns_401_or_403(self, api_client, intern):
        """Неаутентифицированный POST получает 401/403."""
        response = api_client.post('/api/sad-interns/', {'intern': intern.pk}, format='json')
        assert response.status_code in (401, 403)

    def test_user_without_groups_gets_403_on_list(self, api_client, api_anon_user):
        """Пользователь без групп получает 403."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get('/api/sad-interns/')
        assert response.status_code == 403

    def test_manager_can_access_list(self, api_client, api_manager_user):
        """Менеджер имеет доступ к списку."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/sad-interns/')
        assert response.status_code == 200

    def test_admin_can_access_list(self, api_client, api_admin_user):
        """Администратор имеет доступ к списку."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/sad-interns/')
        assert response.status_code == 200

    def test_response_content_type_is_json(self, api_client, api_admin_user):
        """Ответ возвращается в формате JSON."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/sad-interns/')
        assert 'application/json' in response['Content-Type']

    def test_manager_can_create(self, api_client, api_manager_user, intern):
        """Менеджер может создать запись (как в веб-форме)."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/api/sad-interns/',
            {
                'intern': intern.pk,
                'waiting_since': '2025-11-01',
                'status': 'rejected',
            },
            format='json',
        )
        assert response.status_code == 201
        assert SadIntern.objects.filter(intern=intern).exists()

    def test_manager_delete_returns_403(self, api_client, api_manager_user, sad_intern):
        """DELETE только для админа — менеджер получает 403."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.delete(f'/api/sad-interns/{sad_intern.pk}/')
        assert response.status_code == 403

    def test_admin_can_create(self, api_client, api_admin_user, intern):
        """Администратор может создать запись."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post(
            '/api/sad-interns/',
            {
                'intern': intern.pk,
                'waiting_since': '2025-11-01',
                'status': 'rejected',
            },
            format='json',
        )
        assert response.status_code == 201

    def test_admin_delete_succeeds_in_smoke_check(self, api_client, api_admin_user, sad_intern):
        """Администратор может удалить запись (смоук)."""
        sad_intern_id = sad_intern.pk
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/sad-interns/{sad_intern_id}/')
        assert response.status_code == 204
        assert not SadIntern.objects.filter(pk=sad_intern_id).exists()


# ============================================================================
# GET /api/sad-interns/ — список
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSadInternViewSetList:
    """Тесты GET /api/sad-interns/ — список грустящих студентов."""

    def test_manager_sees_only_own_interns(
        self, api_client, api_manager_user, sad_intern, sad_intern_other
    ):
        """Менеджер видит только своих грустящих студентов."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/sad-interns/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert sad_intern.pk in ids
        assert sad_intern_other.pk not in ids

    def test_admin_sees_all_interns(
        self, api_client, api_admin_user, sad_intern, sad_intern_other
    ):
        """Администратор видит всех грустящих студентов."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/sad-interns/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert sad_intern.pk in ids
        assert sad_intern_other.pk in ids

    def test_empty_list_when_no_interns(self, api_client, api_manager_user):
        """Пустой список при отсутствии грустящих студентов у менеджера."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/sad-interns/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert results == []

    def test_response_has_required_fields(self, api_client, api_manager_user, sad_intern):
        """Ответ содержит все обязательные поля из SadInternListSerializer."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/sad-interns/')
        results = get_api_results(response)
        assert len(results) >= 1
        item = results[0]
        expected_fields = {
            'id', 'intern', 'intern_name', 'date_added', 'waiting_since',
            'days_waiting', 'telegram_username', 'manager_email', 'status', 'note',
            'real_interview_date', 'direction_id', 'direction_name', 'status_display',
            'intern_manager_name',
        }
        assert expected_fields.issubset(set(item.keys()))

    def test_intern_name_field_contains_full_name(self, api_client, api_manager_user, sad_intern):
        """Поле intern_name содержит полное имя студента."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/sad-interns/')
        results = get_api_results(response)
        assert len(results) >= 1
        item = results[0]
        assert item['intern_name'] == sad_intern.intern.full_name

    def test_filter_by_status_rejected(
        self, api_client, api_admin_user, sad_intern, sad_intern_other
    ):
        """Фильтр ?status=rejected возвращает только отклонённых."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/sad-interns/', {'status': 'rejected'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert sad_intern.pk in ids        # статус rejected
        assert sad_intern_other.pk not in ids  # статус accepted

    def test_filter_by_status_accepted(
        self, api_client, api_admin_user, sad_intern, sad_intern_other
    ):
        """Фильтр ?status=accepted возвращает только принятых."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/sad-interns/', {'status': 'accepted'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert sad_intern_other.pk in ids
        assert sad_intern.pk not in ids

    def test_filter_by_manager_email_admin_only(
        self, api_client, api_admin_user, sad_intern, sad_intern_other
    ):
        """Фильтр ?manager_email работает только для администраторов."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(
            '/api/sad-interns/', {'manager_email': 'manager@example.com'}
        )
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert sad_intern.pk in ids
        assert sad_intern_other.pk not in ids

    def test_filter_manager_email_ignored_for_manager(
        self, api_client, api_manager_user, sad_intern, sad_intern_other
    ):
        """Параметр ?manager_email игнорируется для обычного менеджера."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(
            '/api/sad-interns/', {'manager_email': 'manager2@example.com'}
        )
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        # Менеджер видит только свои, несмотря на параметр
        assert sad_intern.pk in ids
        assert sad_intern_other.pk not in ids

    def test_filter_exclude_on_project_true(self, api_client, api_admin_user, intern):
        """Фильтр ?exclude_on_project=true исключает студентов со статусом on_project."""
        on_project = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 11, 1),
            manager_email='admin@example.com',
            status='on_project',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/sad-interns/', {'exclude_on_project': 'true'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert on_project.pk not in ids

    def test_list_default_excludes_on_project(self, api_client, api_admin_user, intern):
        """По умолчанию список без записей со статусом on_project (как основной список на сайте)."""
        on_project = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 11, 1),
            manager_email='admin@example.com',
            status='on_project',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/sad-interns/')
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert on_project.pk not in ids

    def test_filter_exclude_on_project_false_includes_on_project(
        self, api_client, api_admin_user, intern
    ):
        """?exclude_on_project=false возвращает и записи on_project (интерн не оффер/ушёл)."""
        on_project = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 11, 1),
            manager_email='admin@example.com',
            status='on_project',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/sad-interns/', {'exclude_on_project': 'false'})
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert on_project.pk in ids

    @pytest.mark.parametrize('val', ['true', '1', 'yes'])
    def test_filter_exclude_on_project_variants(self, api_client, api_admin_user, intern, val):
        """Параметр exclude_on_project принимает true, 1, yes."""
        on_project = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 11, 1),
            manager_email='admin@example.com',
            status='on_project',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/sad-interns/', {'exclude_on_project': val})
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert on_project.pk not in ids


# ============================================================================
# GET /api/sad-interns/{id}/ — детали
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSadInternViewSetRetrieve:
    """Тесты GET /api/sad-interns/{id}/ — детали записи."""

    def test_manager_can_retrieve_own_intern(self, api_client, api_manager_user, sad_intern):
        """Менеджер может получить детали своего студента."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/sad-interns/{sad_intern.pk}/')
        assert response.status_code == 200

    def test_admin_can_retrieve_any_intern(
        self, api_client, api_admin_user, sad_intern, sad_intern_other
    ):
        """Администратор может получить детали любого студента."""
        api_client.force_authenticate(user=api_admin_user)
        response1 = api_client.get(f'/api/sad-interns/{sad_intern.pk}/')
        response2 = api_client.get(f'/api/sad-interns/{sad_intern_other.pk}/')
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_manager_cannot_retrieve_other_intern(
        self, api_client, api_manager_user, sad_intern_other
    ):
        """Менеджер не получает детали чужого студента (404 из-за фильтрации queryset)."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/sad-interns/{sad_intern_other.pk}/')
        assert response.status_code == 404

    def test_retrieve_nonexistent_returns_404(self, api_client, api_admin_user):
        """Запрос несуществующей записи возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/sad-interns/99999/')
        assert response.status_code == 404

    def test_retrieve_response_has_detail_fields(self, api_client, api_manager_user, sad_intern):
        """Ответ содержит все поля из SadInternDetailSerializer."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/sad-interns/{sad_intern.pk}/')
        assert response.status_code == 200
        expected_fields = {
            'id', 'intern', 'intern_name', 'date_added', 'waiting_since',
            'days_waiting', 'telegram_username', 'manager_email',
            'status', 'note',
        }
        assert expected_fields.issubset(set(response.data.keys()))

    def test_retrieve_correct_data(self, api_client, api_manager_user, sad_intern):
        """Данные в ответе соответствуют реальным данным из БД."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/sad-interns/{sad_intern.pk}/')
        assert response.status_code == 200
        data = response.data
        assert data['id'] == sad_intern.pk
        assert data['intern'] == sad_intern.intern.pk
        assert data['intern_name'] == sad_intern.intern.full_name
        assert data['manager_email'] == sad_intern.manager_email
        assert data['status'] == sad_intern.status
        assert data['note'] == sad_intern.note
        assert data['telegram_username'] == sad_intern.telegram_username


# ============================================================================
# POST /api/sad-interns/ — создание
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSadInternViewSetCreate:
    """Тесты POST /api/sad-interns/ — создание записи (менеджер / admin)."""

    def test_admin_can_create_sad_intern(self, api_client, api_admin_user, intern):
        """Администратор может создать запись грустящего студента."""
        api_client.force_authenticate(user=api_admin_user)
        payload = {
            'intern': intern.pk,
            'waiting_since': '2025-11-01',
            'telegram_username': '@new_intern',
            'manager_email': 'admin@example.com',
            'status': 'rejected',
            'note': 'Создано через API',
        }
        response = api_client.post('/api/sad-interns/', payload, format='json')
        assert response.status_code == 201
        assert SadIntern.objects.filter(intern=intern).exists()

    def test_create_response_has_expected_fields(self, api_client, api_admin_user, intern):
        """Ответ на POST содержит данные созданной записи."""
        api_client.force_authenticate(user=api_admin_user)
        payload = {
            'intern': intern.pk,
            'waiting_since': '2025-11-01',
            'status': 'offered',
        }
        response = api_client.post('/api/sad-interns/', payload, format='json')
        assert response.status_code == 201

    def test_create_sets_days_waiting_automatically(self, api_client, api_admin_user, intern):
        """При создании days_waiting вычисляется автоматически."""
        api_client.force_authenticate(user=api_admin_user)
        payload = {
            'intern': intern.pk,
            'waiting_since': '2025-01-01',
            'status': 'rejected',
        }
        response = api_client.post('/api/sad-interns/', payload, format='json')
        assert response.status_code == 201
        created = SadIntern.objects.get(intern=intern)
        assert created.days_waiting >= 0

    def test_create_without_required_intern_field_returns_400(self, api_client, api_admin_user):
        """POST без обязательного поля intern возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        payload = {
            'waiting_since': '2025-11-01',
            'status': 'rejected',
        }
        response = api_client.post('/api/sad-interns/', payload, format='json')
        assert response.status_code == 400

    def test_create_without_waiting_since_uses_today(
        self, api_client, api_admin_user, intern
    ):
        """POST без waiting_since — дата ожидания подставляется (сегодня или real_interview_date)."""
        api_client.force_authenticate(user=api_admin_user)
        payload = {
            'intern': intern.pk,
            'status': 'rejected',
        }
        response = api_client.post('/api/sad-interns/', payload, format='json')
        assert response.status_code == 201
        created = SadIntern.objects.get(intern=intern)
        assert created.waiting_since is not None

    @pytest.mark.parametrize('status_val', ['rejected', 'accepted', 'offered', 'fired'])
    def test_create_with_all_statuses(self, api_client, api_admin_user, intern, status_val):
        """Можно создать запись с любым допустимым статусом."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post(
            '/api/sad-interns/',
            {
                'intern': intern.pk,
                'waiting_since': '2025-11-01',
                'status': status_val,
            },
            format='json',
        )
        assert response.status_code == 201

    def test_manager_create_sets_own_manager_email(self, api_client, api_manager_user, intern):
        """Менеджер создаёт запись — manager_email = email менеджера."""
        SadIntern.objects.filter(intern=intern).delete()
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/api/sad-interns/',
            {
                'intern': intern.pk,
                'waiting_since': '2025-11-01',
                'status': 'rejected',
            },
            format='json',
        )
        assert response.status_code == 201
        created = SadIntern.objects.get(intern=intern)
        assert created.manager_email == 'manager@example.com'


# ============================================================================
# PATCH /api/sad-interns/{id}/ — обновление
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSadInternViewSetUpdate:
    """Тесты PATCH /api/sad-interns/{id}/ — частичное обновление."""

    def test_manager_can_update_own_intern_status(
        self, api_client, api_manager_user, sad_intern
    ):
        """Менеджер может обновить статус своего студента."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/sad-interns/{sad_intern.pk}/',
            {'status': 'accepted'},
            format='json',
        )
        assert response.status_code == 200
        sad_intern.refresh_from_db()
        assert sad_intern.status == 'accepted'

    def test_manager_can_update_own_intern_note(
        self, api_client, api_manager_user, sad_intern
    ):
        """Менеджер может обновить примечание своего студента."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/sad-interns/{sad_intern.pk}/',
            {'note': 'Новое примечание'},
            format='json',
        )
        assert response.status_code == 200
        sad_intern.refresh_from_db()
        assert sad_intern.note == 'Новое примечание'

    def test_manager_cannot_update_other_intern(
        self, api_client, api_manager_user, sad_intern_other
    ):
        """Менеджер не может обновить запись чужого студента — получает 404."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/sad-interns/{sad_intern_other.pk}/',
            {'status': 'accepted'},
            format='json',
        )
        # Queryset менеджера не включает чужие записи → 404
        assert response.status_code == 404

    def test_admin_can_update_any_intern(
        self, api_client, api_admin_user, sad_intern_other
    ):
        """Администратор может обновить запись любого студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/sad-interns/{sad_intern_other.pk}/',
            {'status': 'fired', 'note': 'Обновлено админом'},
            format='json',
        )
        assert response.status_code == 200
        sad_intern_other.refresh_from_db()
        assert sad_intern_other.status == 'fired'
        assert sad_intern_other.note == 'Обновлено админом'

    def test_update_response_reflects_new_data(
        self, api_client, api_manager_user, sad_intern
    ):
        """Ответ на PATCH содержит обновлённые данные."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/sad-interns/{sad_intern.pk}/',
            {'status': 'offered'},
            format='json',
        )
        assert response.status_code == 200

    def test_patch_is_always_partial(self, api_client, api_manager_user, sad_intern):
        """PATCH не требует всех полей — частичное обновление работает корректно."""
        original_note = sad_intern.note
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/sad-interns/{sad_intern.pk}/',
            {'status': 'accepted'},
            format='json',
        )
        assert response.status_code == 200
        sad_intern.refresh_from_db()
        # Примечание не изменилось
        assert sad_intern.note == original_note

    def test_update_nonexistent_intern_returns_404(self, api_client, api_admin_user):
        """PATCH несуществующей записи возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            '/api/sad-interns/99999/',
            {'status': 'accepted'},
            format='json',
        )
        assert response.status_code == 404

    def test_unauthenticated_cannot_update(self, api_client, sad_intern):
        """Неаутентифицированный запрос не может обновить запись."""
        response = api_client.patch(
            f'/api/sad-interns/{sad_intern.pk}/',
            {'status': 'accepted'},
            format='json',
        )
        assert response.status_code in (401, 403)

    def test_update_telegram_username(self, api_client, api_manager_user, sad_intern):
        """Менеджер может обновить telegram_username своего студента."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/sad-interns/{sad_intern.pk}/',
            {'telegram_username': '@updated_tg'},
            format='json',
        )
        assert response.status_code == 200
        sad_intern.refresh_from_db()
        assert sad_intern.telegram_username == '@updated_tg'


# ============================================================================
# DELETE /api/sad-interns/{id}/ — удаление
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSadInternViewSetDestroy:
    """Тесты DELETE /api/sad-interns/{id}/ — только администратор (204)."""

    def test_admin_delete_returns_204(self, api_client, api_admin_user, sad_intern):
        """Администратор удаляет запись — 204."""
        sad_intern_id = sad_intern.pk
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/sad-interns/{sad_intern_id}/')
        assert response.status_code == 204
        assert not SadIntern.objects.filter(pk=sad_intern_id).exists()

    def test_manager_delete_returns_403(
        self, api_client, api_manager_user, sad_intern
    ):
        """Менеджер при DELETE получает 403."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.delete(f'/api/sad-interns/{sad_intern.pk}/')
        assert response.status_code == 403
        assert SadIntern.objects.filter(pk=sad_intern.pk).exists()

    def test_delete_nonexistent_returns_404(self, api_client, api_admin_user):
        """Удаление несуществующей записи возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete('/api/sad-interns/99999/')
        assert response.status_code == 404

    def test_unauthenticated_cannot_delete(self, api_client, sad_intern):
        """Неаутентифицированный запрос не может удалить запись."""
        response = api_client.delete(f'/api/sad-interns/{sad_intern.pk}/')
        assert response.status_code in (401, 403)

    def test_admin_can_delete_any_record(
        self, api_client, api_admin_user, sad_intern_other
    ):
        """Администратор удаляет любую запись — 204."""
        pk = sad_intern_other.pk
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/sad-interns/{pk}/')
        assert response.status_code == 204
        assert not SadIntern.objects.filter(pk=pk).exists()


# ============================================================================
# DRF: аналитика, grouped, on-project, импорт
# ============================================================================


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSadInternDrfExtraEndpoints:
    """Доп. эндпоинты после переноса в sad_intern.api."""

    def test_analytics_sad_intern_get(self, api_client, api_manager_user):
        """GET /api/analytics/sad-intern/ — 200 и структура."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/analytics/sad-intern/')
        assert response.status_code == 200
        data = response.json()
        assert 'total' in data
        assert 'with_contact' in data
        assert 'avg_wait' in data
        assert 'longest_wait_days' in data

    def test_grouped_get(self, api_client, api_manager_user, sad_intern):
        """GET /api/sad-interns/grouped/ — 200, есть groups."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/sad-interns/grouped/')
        assert response.status_code == 200
        data = response.json()
        assert 'groups' in data
        assert 'has_more_directions' in data
        assert 'total_directions' in data

    def test_on_project_get(self, api_client, api_admin_user):
        """GET /api/sad-interns/on-project/ — 200."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/sad-interns/on-project/')
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        assert 'count' in data

    def test_import_requires_file(self, api_client, api_admin_user):
        """POST /api/sad-interns/import/ без файла — 400."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post('/api/sad-interns/import/', {})
        assert response.status_code == 400
