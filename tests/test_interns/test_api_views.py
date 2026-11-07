"""
Тесты для API-эндпоинтов приложения interns.

Покрывают InternViewSet:
    GET    /api/interns/                   — список студентов
    POST   /api/interns/                   — создание (admin / менеджер на себя)
    GET    /api/interns/{id}/              — детали студента
    PATCH  /api/interns/{id}/              — частичное обновление (только admin)
    DELETE /api/interns/{id}/              — удаление студента (только admin)
    PATCH  /api/interns/{id}/manual-status/     — смена manual_status (менеджеры и админы)

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.api       - для группировки API-тестов
"""
import pytest
from datetime import date

from interns.models import Intern
from tests.helpers import get_api_results


# ============================================================================
# InternViewSet — аутентификация и базовый доступ
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternViewSetAuth:
    """Тесты аутентификации и прав доступа к /api/interns/."""

    def test_unauthenticated_returns_403(self, api_client):
        """Неаутентифицированный запрос получает 401 или 403."""
        response = api_client.get('/api/interns/')
        assert response.status_code in (401, 403)

    def test_manager_can_access_list(self, api_client, api_manager_user):
        """Менеджер имеет доступ к списку студентов."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/interns/')
        assert response.status_code == 200

    def test_admin_can_access_list(self, api_client, api_admin_user):
        """Администратор имеет доступ к списку студентов."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/')
        assert response.status_code == 200

    def test_user_without_groups_gets_403(self, api_client, api_anon_user):
        """Пользователь без групп получает 403."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get('/api/interns/')
        assert response.status_code == 403

    def test_response_content_type_is_json(self, api_client, api_admin_user):
        """Ответ возвращается в формате JSON."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/')
        assert 'application/json' in response['Content-Type']


# ============================================================================
# GET /api/interns/ — список студентов
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternViewSetList:
    """Тесты GET /api/interns/ — список и фильтрация."""

    def test_admin_sees_all_interns(self, api_client, api_admin_user, intern, intern_other):
        """Администратор видит всех студентов."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert intern.id in ids
        assert intern_other.id in ids

    def test_manager_sees_only_own_interns(
        self, api_client, api_manager_user, intern, intern_other
    ):
        """Менеджер видит только своих студентов (manager_email=manager@example.com)."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/interns/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert intern.id in ids
        assert intern_other.id not in ids

    def test_manager_does_not_see_foreign_interns(
        self, api_client, api_manager2_user, intern, intern_other
    ):
        """Второй менеджер видит только своих студентов."""
        api_client.force_authenticate(user=api_manager2_user)
        response = api_client.get('/api/interns/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert intern_other.id in ids
        assert intern.id not in ids

    @pytest.mark.parametrize('hr_like_user', ['api_hr_user', 'api_outstaff_user'])
    def test_hr_like_sees_all_interns_in_list(
        self, request, api_client, hr_like_user, intern, intern_other
    ):
        """HR и outstaff видят всех студентов в списке API."""
        user = request.getfixturevalue(hr_like_user)
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/interns/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert intern.id in ids
        assert intern_other.id in ids

    def test_empty_list_when_no_data(self, api_client, api_admin_user):
        """Пустой список при отсутствии студентов."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert results == []

    def test_list_response_has_required_fields(self, api_client, api_admin_user, intern):
        """Элемент списка содержит обязательные поля."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        item = results[0]
        required_fields = {
            'id',
            'full_name',
            'email',
            'telegram_username',
            'direction_id',
            'direction_name',
            'group',
            'city',
            'type_of_training',
            'type_of_training_display',
            'status',
            'status_display',
            'manual_status',
            'manager_email',
            'manager_display_name',
            'date_of_receipt',
            'date_of_birth',
            'hiring_hr',
            'responsible_hr',
            'real_interview_date',
            'cv',
            'legend',
        }
        assert required_fields == set(item.keys())

    def test_filter_by_status(self, api_client, api_admin_user, intern, direction):
        """Фильтр по статусу возвращает только студентов с нужным статусом."""
        intern_left = Intern.objects.create(
            full_name='Ушедший Студент',
            email='left@example.com',
            manager_email='admin@example.com',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            manual_status='ушел',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/', {'status': 'ушел'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert intern_left.id in ids
        assert intern.id not in ids

    def test_filter_by_group(self, api_client, api_admin_user, intern, intern_other):
        """Фильтр по группе возвращает только студентов из нужной группы."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/', {'group': 'GR1'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert intern.id in ids
        assert intern_other.id not in ids

    def test_filter_by_group_partial_match(self, api_client, api_admin_user, intern):
        """Фильтр по группе поддерживает частичное совпадение (icontains)."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/', {'group': 'gr'})
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1

    def test_filter_by_q_full_name(self, api_client, api_admin_user, intern, intern_other):
        """Параметр q ищет по ФИО (и др. полям)."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/', {'q': 'Петр'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert intern_other.id in ids
        assert intern.id not in ids

    def test_filter_by_direction_id(
        self, api_client, api_admin_user, intern, direction
    ):
        """Фильтр по direction_id возвращает только студентов нужного направления."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/', {'direction_id': direction.id})
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        assert all(item['direction_id'] == direction.id for item in results)

    def test_filter_by_invalid_direction_id_ignored(
        self, api_client, api_admin_user, intern
    ):
        """Невалидный direction_id (строка) игнорируется."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/', {'direction_id': 'invalid'})
        assert response.status_code == 200

    def test_filter_by_nonexistent_direction_returns_empty(
        self, api_client, api_admin_user, intern
    ):
        """Фильтр по несуществующему direction_id возвращает пустой список."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/', {'direction_id': 99999})
        assert response.status_code == 200
        results = get_api_results(response)
        assert results == []

    def test_multiple_filters_combined(
        self, api_client, api_admin_user, intern, intern_other, direction
    ):
        """Несколько фильтров применяются одновременно."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/', {
            'direction_id': direction.id,
            'group': 'GR1',
        })
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert intern.id in ids
        assert intern_other.id not in ids

    def test_status_default_is_active(self, api_client, api_admin_user, intern):
        """Студент без manual_status отображается со статусом 'активный'."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/')
        results = get_api_results(response)
        item = next(i for i in results if i['id'] == intern.id)
        assert item['status'] == 'активный'
        assert item['status_display'] == 'Активный'


# ============================================================================
# GET /api/interns/{id}/ — детали студента
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternViewSetRetrieve:
    """Тесты GET /api/interns/{id}/ — детали студента."""

    def test_admin_can_retrieve_any_intern(self, api_client, api_admin_user, intern):
        """Администратор может получить данные любого студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interns/{intern.id}/')
        assert response.status_code == 200
        assert response.data['id'] == intern.id

    def test_manager_can_retrieve_own_intern(
        self, api_client, api_manager_user, intern
    ):
        """Менеджер может получить данные своего студента."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/interns/{intern.id}/')
        assert response.status_code == 200
        assert response.data['id'] == intern.id

    def test_manager_cannot_retrieve_foreign_intern(
        self, api_client, api_manager_user, intern_other
    ):
        """Менеджер не может получить данные чужого студента — возвращает 404."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/interns/{intern_other.id}/')
        assert response.status_code == 404

    @pytest.mark.parametrize('hr_like_user', ['api_hr_user', 'api_outstaff_user'])
    def test_hr_like_can_retrieve_foreign_intern(
        self, request, api_client, hr_like_user, intern_other
    ):
        """HR и outstaff получают детали любого студента по id."""
        user = request.getfixturevalue(hr_like_user)
        api_client.force_authenticate(user=user)
        response = api_client.get(f'/api/interns/{intern_other.id}/')
        assert response.status_code == 200
        assert response.data['id'] == intern_other.id

    def test_retrieve_nonexistent_returns_404(self, api_client, api_admin_user):
        """Запрос несуществующего студента возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/99999/')
        assert response.status_code == 404

    def test_retrieve_response_has_detail_fields(
        self, api_client, api_admin_user, intern
    ):
        """Ответ содержит все поля детального сериализатора."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interns/{intern.id}/')
        assert response.status_code == 200
        expected_fields = {
            'id', 'full_name', 'email', 'telegram_username',
            'direction_id', 'direction_name', 'city', 'cv', 'date_of_receipt', 'date_of_birth',
            'hiring_hr', 'responsible_hr', 'group', 'type_of_training',
            'legend', 'hr_feedback', 'mentor_feedback', 'real_interview_date',
            'manual_status', 'status', 'status_display',
            'manager_email',
        }
        assert expected_fields == set(response.data.keys())

    def test_retrieve_detail_fields_values(
        self, api_client, api_admin_user, intern
    ):
        """Детальный ответ содержит корректные значения полей."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interns/{intern.id}/')
        assert response.status_code == 200
        assert response.data['full_name'] == intern.full_name
        assert response.data['email'] == intern.email
        assert response.data['manager_email'] == intern.manager_email
        assert response.data['direction_id'] == intern.direction_id

# ============================================================================
# POST /api/interns/ — создание студента
# ============================================================================


def _intern_payload(direction_id):
    return {
        'full_name': 'Новый Студент',
        'email': 'new_intern@example.com',
        'telegram_username': '@new_intern',
        'direction_id': direction_id,
        'date_of_receipt': '2025-03-01',
        'date_of_birth': '2001-05-15',
        'hiring_hr': 'HR Петрова',
        'responsible_hr': 'HR Сидорова',
        'group': 'Python-01',
        'type_of_training': 'internal',
        'manager_email': 'manager@example.com',
    }


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternViewSetCreate:
    """Тесты POST /api/interns/ — создание студента."""

    def test_admin_can_create_intern(self, api_client, api_admin_user, direction, manager):
        """Администратор может создать студента."""
        api_client.force_authenticate(user=api_admin_user)
        payload = _intern_payload(direction.id)
        response = api_client.post('/api/interns/', payload, format='json')
        assert response.status_code == 201
        assert Intern.objects.filter(email='new_intern@example.com').exists()

    def test_manager_can_create_intern_assigned_to_self(
        self, api_client, api_manager_user, direction, manager
    ):
        """Менеджер создаёт студента; назначение — на его email (даже если в теле другой менеджер)."""
        api_client.force_authenticate(user=api_manager_user)
        payload = _intern_payload(direction.id)
        payload['manager_email'] = 'other@example.com'
        payload['email'] = 'self_created@example.com'
        response = api_client.post('/api/interns/', payload, format='json')
        assert response.status_code == 201, response.data
        intern = Intern.objects.get(email='self_created@example.com')
        assert intern.manager_email == 'manager@example.com'

    def test_hr_cannot_create_intern(self, api_client, api_hr_user, direction, manager):
        """HR не создаёт студентов — 403."""
        api_client.force_authenticate(user=api_hr_user)
        payload = _intern_payload(direction.id)
        response = api_client.post('/api/interns/', payload, format='json')
        assert response.status_code == 403

    def test_unauthenticated_cannot_create(self, api_client, direction):
        """Неаутентифицированный пользователь не может создать студента."""
        payload = _intern_payload(direction.id)
        response = api_client.post('/api/interns/', payload, format='json')
        assert response.status_code in (401, 403)

    def test_create_returns_201_with_fields(self, api_client, api_admin_user, direction, manager):
        """Успешное создание возвращает 201 с данными студента."""
        api_client.force_authenticate(user=api_admin_user)
        payload = _intern_payload(direction.id)
        response = api_client.post('/api/interns/', payload, format='json')
        assert response.status_code == 201
        assert response.data['full_name'] == payload['full_name']
        assert response.data['email'] == payload['email']

    def test_create_saves_all_fields(self, api_client, api_admin_user, direction, manager):
        """Созданный студент содержит все переданные поля."""
        api_client.force_authenticate(user=api_admin_user)
        payload = _intern_payload(direction.id)
        response = api_client.post('/api/interns/', payload, format='json')
        assert response.status_code == 201
        intern = Intern.objects.get(email='new_intern@example.com')
        assert intern.full_name == payload['full_name']
        assert intern.email == payload['email']
        assert intern.group == payload['group']
        assert intern.direction_id == direction.id

    def test_create_with_optional_fields(self, api_client, api_admin_user, direction, manager):
        """Создание студента с необязательными полями."""
        api_client.force_authenticate(user=api_admin_user)
        payload = _intern_payload(direction.id)
        payload['hr_feedback'] = 'Отличный кандидат'
        payload['mentor_feedback'] = 'Хорошо справляется'
        payload['legend'] = 'https://example.com/legend'
        payload['cv'] = 'https://example.com/cv'
        response = api_client.post('/api/interns/', payload, format='json')
        assert response.status_code == 201
        intern = Intern.objects.get(email='new_intern@example.com')
        assert intern.hr_feedback == 'Отличный кандидат'
        assert intern.mentor_feedback == 'Хорошо справляется'

    def test_create_with_manual_status(self, api_client, api_admin_user, direction, manager):
        """Создание студента с ручным статусом."""
        api_client.force_authenticate(user=api_admin_user)
        payload = _intern_payload(direction.id)
        payload['manual_status'] = 'оффер'
        payload['email'] = 'offer_intern@example.com'
        response = api_client.post('/api/interns/', payload, format='json')
        assert response.status_code == 201
        intern = Intern.objects.get(email='offer_intern@example.com')
        assert intern.manual_status == 'оффер'
        assert intern.status == 'оффер'

    def test_create_without_required_field_returns_400(
        self, api_client, api_admin_user, direction
    ):
        """Создание без обязательного поля full_name возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        payload = _intern_payload(direction.id)
        del payload['full_name']
        response = api_client.post('/api/interns/', payload, format='json')
        assert response.status_code == 400


# ============================================================================
# PATCH /api/interns/{id}/ — частичное обновление
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternViewSetPartialUpdate:
    """Тесты PATCH /api/interns/{id}/ — частичное обновление студента."""

    def test_admin_can_patch_intern(self, api_client, api_admin_user, intern):
        """Администратор может обновить поля студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/interns/{intern.id}/',
            {'full_name': 'Обновлённое Имя'},
            format='json',
        )
        assert response.status_code == 200
        intern.refresh_from_db()
        assert intern.full_name == 'Обновлённое Имя'

    def test_manager_cannot_patch_intern(self, api_client, api_manager_user, intern):
        """Обычный менеджер не может обновить студента — 403."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/interns/{intern.id}/',
            {'full_name': 'Новое Имя'},
            format='json',
        )
        assert response.status_code == 403

    def test_unauthenticated_cannot_patch(self, api_client, intern):
        """Неаутентифицированный пользователь не может обновить студента."""
        response = api_client.patch(
            f'/api/interns/{intern.id}/',
            {'full_name': 'Новое Имя'},
            format='json',
        )
        assert response.status_code in (401, 403)

    def test_patch_nonexistent_returns_404(self, api_client, api_admin_user):
        """Обновление несуществующего студента возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            '/api/interns/99999/',
            {'full_name': 'Неважно'},
            format='json',
        )
        assert response.status_code == 404

    def test_patch_updates_only_specified_fields(
        self, api_client, api_admin_user, intern
    ):
        """PATCH обновляет только переданные поля, остальные не меняются."""
        original_email = intern.email
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/interns/{intern.id}/',
            {'group': 'NewGroup'},
            format='json',
        )
        assert response.status_code == 200
        intern.refresh_from_db()
        assert intern.group == 'NewGroup'
        assert intern.email == original_email

    def test_patch_manual_status(self, api_client, api_admin_user, intern):
        """Администратор может обновить ручной статус студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/interns/{intern.id}/',
            {'manual_status': 'ушел'},
            format='json',
        )
        assert response.status_code == 200
        intern.refresh_from_db()
        assert intern.manual_status == 'ушел'
        assert intern.status == 'ушел'

    def test_patch_real_interview_date(self, api_client, api_admin_user, intern):
        """Администратор может установить дату реального собеседования."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/interns/{intern.id}/',
            {'real_interview_date': '2025-06-01'},
            format='json',
        )
        assert response.status_code == 200
        intern.refresh_from_db()
        assert str(intern.real_interview_date) == '2025-06-01'

    def test_admin_can_patch_any_intern(
        self, api_client, api_admin_user, intern_other
    ):
        """Администратор может обновить любого студента, не только своего."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/interns/{intern_other.id}/',
            {'group': 'UpdatedGroup'},
            format='json',
        )
        assert response.status_code == 200
        intern_other.refresh_from_db()
        assert intern_other.group == 'UpdatedGroup'


# ============================================================================
# PATCH /api/interns/{id}/manual-status/ — раздел «Сотрудники»
# ============================================================================


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternPatchManualStatusAction:
    """Тесты PATCH /api/interns/{id}/manual-status/."""

    def test_unauthenticated_returns_401_or_403(self, api_client, intern):
        response = api_client.patch(
            f'/api/interns/{intern.id}/manual-status/',
            {'manual_status': 'ушел'},
            format='json',
        )
        assert response.status_code in (401, 403)

    def test_manager_cannot_change_status_of_other_managers_intern(
        self, api_client, api_manager_user, intern_other
    ):
        """Менеджер не может менять статус чужого студента (scope + проверка manager_email)."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/interns/{intern_other.id}/manual-status/',
            {'manual_status': 'оффер'},
            format='json',
        )
        assert response.status_code in (403, 404)

    def test_invalid_manual_status_returns_400(self, api_client, api_manager_user, intern):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/interns/{intern.id}/manual-status/',
            {'manual_status': 'недопустимо'},
            format='json',
        )
        assert response.status_code == 400

    @pytest.mark.parametrize('hr_like_user', ['api_hr_user', 'api_outstaff_user'])
    def test_hr_cannot_patch_manual_status(
        self, api_client, hr_like_user, intern, request,
    ):
        """HR и outstaff — только чтение; PATCH manual-status запрещён."""
        api_client.force_authenticate(user=request.getfixturevalue(hr_like_user))
        response = api_client.patch(
            f'/api/interns/{intern.id}/manual-status/',
            {'manual_status': 'активный'},
            format='json',
        )
        assert response.status_code == 403


# ============================================================================
# DELETE /api/interns/{id}/ — удаление студента
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternViewSetDelete:
    """Тесты DELETE /api/interns/{id}/ — удаление только администратором."""

    def test_admin_delete_removes_intern(self, api_client, api_admin_user, intern):
        """Администратор удаляет студента — 204, запись удалена."""
        intern_id = intern.id
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/interns/{intern_id}/')
        assert response.status_code == 204
        assert not Intern.objects.filter(id=intern_id).exists()

    def test_manager_delete_returns_403(self, api_client, api_manager_user, intern):
        """Менеджер при DELETE получает 403."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.delete(f'/api/interns/{intern.id}/')
        assert response.status_code == 403
        assert Intern.objects.filter(id=intern.id).exists()

    def test_unauthenticated_cannot_delete(self, api_client, intern):
        """Неаутентифицированный пользователь не может удалить студента."""
        response = api_client.delete(f'/api/interns/{intern.id}/')
        assert response.status_code in (401, 403)
        assert Intern.objects.filter(id=intern.id).exists()

    def test_delete_nonexistent_returns_404(self, api_client, api_admin_user):
        """Удаление несуществующего студента возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete('/api/interns/99999/')
        assert response.status_code == 404

    def test_admin_can_delete_other_managers_intern(
        self, api_client, api_admin_user, intern_other
    ):
        """Администратор удаляет студента другого менеджера."""
        intern_id = intern_other.id
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/interns/{intern_id}/')
        assert response.status_code == 204
        assert not Intern.objects.filter(id=intern_id).exists()


# ============================================================================
# Тесты сериализаторов через API
# ============================================================================

def _get_intern_item(api_client, user, intern):
    """Находит запись студента в списке GET /api/interns/."""
    api_client.force_authenticate(user=user)
    response = api_client.get('/api/interns/')
    results = get_api_results(response)
    return next(i for i in results if i['id'] == intern.id)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternListSerializer:
    """Тесты сериализации данных в GET /api/interns/ (InternListSerializer)."""

    def test_id_is_integer(self, api_client, api_admin_user, intern):
        """id совпадает с id студента."""
        item = _get_intern_item(api_client, api_admin_user, intern)
        assert item['id'] == intern.id

    def test_full_name_is_string(self, api_client, api_admin_user, intern):
        """full_name корректно возвращается."""
        item = _get_intern_item(api_client, api_admin_user, intern)
        assert item['full_name'] == intern.full_name

    def test_direction_id_is_integer(self, api_client, api_admin_user, intern):
        """direction_id совпадает с direction студента."""
        item = _get_intern_item(api_client, api_admin_user, intern)
        assert item['direction_id'] == intern.direction_id

    def test_status_field_present_and_not_empty(self, api_client, api_admin_user, intern):
        """Поле status присутствует и содержит ожидаемое значение по умолчанию."""
        item = _get_intern_item(api_client, api_admin_user, intern)
        assert 'status' in item
        assert item['status'] == 'активный'

    def test_status_display_is_capitalized(self, api_client, api_admin_user, intern):
        """status_display возвращает человекочитаемое название."""
        item = _get_intern_item(api_client, api_admin_user, intern)
        assert item['status_display'] == 'Активный'

    def test_list_has_cv_legend_not_hr_feedback(self, api_client, api_admin_user, intern):
        """В списке есть cv/legend для таблицы; длинные текстовые поля — только в деталях."""
        item = _get_intern_item(api_client, api_admin_user, intern)
        assert 'cv' in item
        assert 'legend' in item
        assert 'hr_feedback' not in item
        assert 'mentor_feedback' not in item
        assert 'date_of_birth' in item


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternDetailSerializer:
    """Тесты сериализации данных в GET /api/interns/{id}/ (InternDetailSerializer)."""

    @pytest.mark.parametrize('field', ['cv', 'hr_feedback', 'mentor_feedback'])
    def test_detail_contains_extra_field(self, api_client, api_admin_user, intern, field):
        """Детальный ответ содержит поля, отсутствующие в списке."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interns/{intern.id}/')
        assert field in response.data

    def test_detail_contains_date_of_birth(self, api_client, api_admin_user, intern):
        """Детальный ответ содержит поле date_of_birth с корректным значением."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interns/{intern.id}/')
        assert 'date_of_birth' in response.data
        assert str(response.data['date_of_birth']) == str(intern.date_of_birth)

    def test_detail_status_and_status_display(self, api_client, api_admin_user, intern):
        """Детальный ответ содержит status и status_display."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interns/{intern.id}/')
        assert response.data['status'] == 'активный'
        assert response.data['status_display'] == 'Активный'

    def test_detail_status_reflects_manual_status(
        self, api_client, api_admin_user, intern
    ):
        """Детальный ответ отражает ручной статус студента."""
        intern.manual_status = 'оффер'
        intern.save()
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interns/{intern.id}/')
        assert response.data['status'] == 'оффер'
        assert response.data['status_display'] == 'Оффер'

    def test_detail_nullable_fields_are_null(self, api_client, api_admin_user, intern):
        """Пустые nullable поля возвращаются как null."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interns/{intern.id}/')
        # intern из фикстуры не имеет cv, legend, hr_feedback и т.д.
        assert response.data['cv'] is None
        assert response.data['legend'] is None
        assert response.data['real_interview_date'] is None


# ============================================================================
# Тесты queryset логики (фильтрация по менеджеру)
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternViewSetQueryset:
    """Тесты логики фильтрации queryset в InternViewSet."""

    def test_manager_with_no_interns_gets_empty_list(
        self, api_client, api_manager2_user
    ):
        """Менеджер без студентов получает пустой список."""
        api_client.force_authenticate(user=api_manager2_user)
        response = api_client.get('/api/interns/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert results == []

    def test_admin_filter_status_ofer(
        self, api_client, api_admin_user, intern, direction
    ):
        """Администратор фильтрует по статусу 'оффер'."""
        intern_offer = Intern.objects.create(
            full_name='Студент Оффер',
            email='offer@example.com',
            manager_email='admin@example.com',
            direction=direction,
            date_of_receipt=date(2025, 2, 1),
            date_of_birth=date(2001, 1, 1),
            hiring_hr='HR',
            responsible_hr='HR',
            group='GRO',
            type_of_training='outstaff',
            manual_status='оффер',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interns/', {'status': 'оффер'})
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert intern_offer.id in ids
        assert intern.id not in ids

    def test_manager_filter_respects_manager_scope(
        self, api_client, api_manager_user, intern, intern_other, direction
    ):
        """Фильтр по группе у менеджера работает только в пределах его студентов."""
        # intern принадлежит api_manager_user (GR1), intern_other — другому менеджеру (GR2)
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/interns/', {'group': 'GR2'})
        results = get_api_results(response)
        # api_manager_user не должен видеть intern_other даже при совпадении фильтра
        ids = [item['id'] for item in results]
        assert intern_other.id not in ids

    def test_filter_status_with_manager_scope(
        self, api_client, api_manager_user, intern, direction
    ):
        """Фильтр по статусу у менеджера работает только для его студентов."""
        intern2 = Intern.objects.create(
            full_name='Второй своего менеджера',
            email='intern2@example.com',
            manager_email='manager@example.com',
            direction=direction,
            date_of_receipt=date(2025, 3, 1),
            date_of_birth=date(2001, 1, 1),
            hiring_hr='HR',
            responsible_hr='HR',
            group='GR1',
            type_of_training='internal',
            manual_status='ушел',
        )
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/interns/', {'status': 'ушел'})
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert intern2.id in ids
        assert intern.id not in ids  # intern без manual_status = активный


# ============================================================================
@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternPatchManualStatusActionExtended:
    """Дополнительные сценарии manual-status."""

    def test_manager_can_patch_own_intern_manual_status(
        self, api_client, api_manager_user, intern,
    ):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/interns/{intern.id}/manual-status/',
            {'manual_status': 'оффер'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['success'] is True
        assert response.data['manual_status'] == 'оффер'
        intern.refresh_from_db()
        assert intern.manual_status == 'оффер'

    def test_empty_manual_status_returns_400(self, api_client, api_admin_user, intern):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/interns/{intern.id}/manual-status/',
            {'manual_status': ''},
            format='json',
        )
        assert response.status_code == 400
