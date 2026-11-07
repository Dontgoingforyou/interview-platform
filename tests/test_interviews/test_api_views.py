"""
Тесты для API-эндпоинтов приложения interviews.

Покрывают InterviewViewSet:
    GET    /api/interviews/                         — список собеседований
    POST   /api/interviews/                         — создание (admin и менеджер)
    GET    /api/interviews/{id}/                    — детали собеседования
    PATCH  /api/interviews/{id}/                    — частичное обновление (admin и менеджер в scope)
    DELETE /api/interviews/{id}/                    — удаление (admin и менеджер в scope)
    GET    /api/interviews/{id}/transcription-status/ — статус (менеджер — свои; admin, HR, outstaff)
    GET    /api/interviews/{id}/transcription-text/ — текст при completed (те же правила)

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.api       - для группировки API-тестов
"""
import pytest
from datetime import date

from interviews.models import Interview
from transcriptions.models import InterviewTranscription, TranscriptionStatus
from tests.helpers import get_api_results


# ============================================================================
# InterviewViewSet — аутентификация и базовый доступ
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewViewSetAuth:
    """Тесты аутентификации и прав доступа к /api/interviews/."""

    def test_unauthenticated_returns_403(self, api_client):
        """Неаутентифицированный запрос возвращает 401 или 403."""
        response = api_client.get('/api/interviews/')
        assert response.status_code in (401, 403)

    def test_manager_can_access_list(self, api_client, api_manager_user):
        """Менеджер имеет доступ к списку собеседований."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 200

    def test_admin_can_access_list(self, api_client, api_admin_user):
        """Администратор имеет доступ к списку собеседований."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 200

    def test_user_without_groups_gets_403(self, api_client, api_anon_user):
        """Пользователь без групп получает 403."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 403

    def test_response_content_type_is_json(self, api_client, api_admin_user):
        """Ответ возвращается в формате JSON."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/')
        assert 'application/json' in response['Content-Type']


# ============================================================================
# GET /api/interviews/ — список собеседований и фильтрация
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewViewSetList:
    """Тесты GET /api/interviews/ — список и фильтрация."""

    def test_admin_sees_all_interviews(
        self, api_client, api_admin_user, interview, interview_other
    ):
        """Администратор видит все собеседования."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview.id in ids
        assert interview_other.id in ids

    def test_manager_sees_only_own_interviews(
        self, api_client, api_manager_user, interview, interview_other
    ):
        """Менеджер видит только свои собеседования (manager_email=manager@example.com)."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview.id in ids
        assert interview_other.id not in ids

    def test_manager2_does_not_see_foreign_interviews(
        self, api_client, api_manager2_user, interview, interview_other
    ):
        """Второй менеджер видит только свои собеседования."""
        api_client.force_authenticate(user=api_manager2_user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview_other.id in ids
        assert interview.id not in ids

    @pytest.mark.parametrize('hr_like_user', ['api_hr_user', 'api_outstaff_user'])
    def test_hr_like_sees_all_interviews_in_list(
        self, request, api_client, hr_like_user, interview, interview_other
    ):
        """HR и outstaff видят все собеседования в списке API."""
        user = request.getfixturevalue(hr_like_user)
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview.id in ids
        assert interview_other.id in ids

    def test_manager_sees_interview_without_manager_email_via_intern(
        self, api_client, api_manager_user, intern, direction
    ):
        """Менеджер видит собеседования со своим студентом, у которых manager_email не заполнен."""
        interview_no_email = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=None,
            interview_type='tech',
            date=date(2025, 12, 5),
        )
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview_no_email.id in ids

    def test_manager_does_not_see_null_email_interview_of_foreign_intern(
        self, api_client, api_manager_user, intern_other, direction
    ):
        """Менеджер НЕ видит собеседования с NULL-email чужого студента."""
        foreign_interview_no_email = Interview.objects.create(
            intern=intern_other,
            direction=direction,
            manager_email=None,
            interview_type='hr',
            date=date(2025, 12, 6),
        )
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert foreign_interview_no_email.id not in ids

    def test_empty_list_when_no_data(self, api_client, api_admin_user):
        """Пустой список при отсутствии собеседований."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert results == []

    @pytest.mark.parametrize('field', [
        'id', 'intern', 'intern_name', 'direction_id', 'company_id',
        'manager_email', 'manager_display_name', 'interview_type', 'interview_type_display',
        'interview_format', 'interview_format_display',
        'date', 'time', 'link', 'vacancy_link', 'interview_link', 'video_link',
        'has_video',
        'transcription_media_url', 'transcription_status', 'transcription_error_message',
        'hr_name', 'hr_contacts', 'created_at', 'updated_at',
    ])
    def test_list_response_has_required_fields(self, api_client, api_admin_user, interview, field):
        """Элемент списка содержит обязательные поля."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        item = results[0]
        assert field in item, f'Поле {field!r} отсутствует в ответе'

    def test_filter_no_link_true(self, api_client, api_admin_user, interview, intern, direction):
        """Фильтр no_link=true возвращает только собеседования без ссылки."""
        interview_with_link = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='admin@example.com',
            interview_type='tech',
            date=date(2025, 12, 10),
            link='https://example.com/meet',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'no_link': 'true'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview.id in ids
        assert interview_with_link.id not in ids

    def test_filter_no_link_false_returns_all(
        self, api_client, api_admin_user, interview, intern, direction
    ):
        """Фильтр no_link=false возвращает все собеседования."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'no_link': 'false'})
        assert response.status_code == 200

    def test_filter_has_video_true(
        self, api_client, api_admin_user, interview, interview_other
    ):
        """Фильтр has_video=true возвращает только собеседования с непустым video_link."""
        Interview.objects.filter(pk=interview_other.pk).update(
            video_link='https://disk.yandex.ru/i/only-this-has-video',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'has_video': 'true'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview_other.id in ids
        assert interview.id not in ids

    def test_filter_has_video_false(
        self, api_client, api_admin_user, interview, interview_other
    ):
        """Фильтр has_video=false возвращает только собеседования без загруженной записи."""
        Interview.objects.filter(pk=interview_other.pk).update(
            video_link='https://disk.yandex.ru/i/other-recording',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'has_video': 'false'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview.id in ids
        assert interview_other.id not in ids

    def test_filter_date_from(self, api_client, api_admin_user, interview, interview_other):
        """Фильтр date_from возвращает собеседования начиная с указанной даты."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'date_from': '2025-12-02'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview_other.id in ids
        assert interview.id not in ids

    def test_filter_date_to(self, api_client, api_admin_user, interview, interview_other):
        """Фильтр date_to возвращает собеседования до указанной даты включительно."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'date_to': '2025-12-01'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview.id in ids
        assert interview_other.id not in ids

    def test_filter_date_range(self, api_client, api_admin_user, interview, interview_other):
        """Фильтр date_from + date_to работает вместе."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {
            'date_from': '2025-12-01',
            'date_to': '2025-12-01',
        })
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview.id in ids
        assert interview_other.id not in ids

    def test_filter_intern_id(self, api_client, api_admin_user, interview, interview_other):
        """Фильтр intern_id возвращает только собеседования указанного студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'intern_id': interview.intern.id})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview.id in ids
        assert interview_other.id not in ids

    def test_filter_intern_id_invalid_ignored(self, api_client, api_admin_user, interview):
        """Невалидный intern_id (строка) игнорируется."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'intern_id': 'abc'})
        assert response.status_code == 200

    def test_filter_interview_type(
        self, api_client, api_admin_user, interview, interview_other
    ):
        """Фильтр interview_type возвращает только нужный тип собеседования."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'interview_type': 'screening'})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert interview.id in ids
        assert interview_other.id not in ids

    def test_filter_direction_id(self, api_client, api_admin_user, interview, direction):
        """Фильтр direction_id возвращает собеседования по направлению."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'direction_id': direction.id})
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        assert results[0]['direction_id'] == direction.id

    def test_filter_direction_id_invalid_ignored(self, api_client, api_admin_user, interview):
        """Невалидный direction_id (строка) игнорируется."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'direction_id': 'xyz'})
        assert response.status_code == 200

    def test_filter_direction_id_nonexistent_returns_empty(
        self, api_client, api_admin_user, interview
    ):
        """Фильтр по несуществующему direction_id возвращает пустой список."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/', {'direction_id': 99999})
        assert response.status_code == 200
        results = get_api_results(response)
        assert results == []


# ============================================================================
# GET /api/interviews/{id}/ — детали собеседования
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewViewSetRetrieve:
    """Тесты GET /api/interviews/{id}/ — детали собеседования."""

    def test_admin_can_retrieve_any_interview(self, api_client, api_admin_user, interview):
        """Администратор может получить любое собеседование."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interviews/{interview.id}/')
        assert response.status_code == 200
        assert response.data['id'] == interview.id

    def test_manager_can_retrieve_own_interview(
        self, api_client, api_manager_user, interview
    ):
        """Менеджер может получить своё собеседование."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/interviews/{interview.id}/')
        assert response.status_code == 200
        assert response.data['id'] == interview.id

    def test_manager_cannot_retrieve_foreign_interview(
        self, api_client, api_manager_user, interview_other
    ):
        """Менеджер не может получить чужое собеседование — возвращает 404."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/interviews/{interview_other.id}/')
        assert response.status_code == 404

    @pytest.mark.parametrize('hr_like_user', ['api_hr_user', 'api_outstaff_user'])
    def test_hr_like_can_retrieve_foreign_interview(
        self, request, api_client, hr_like_user, interview_other
    ):
        """HR и outstaff получают детали любого собеседования по id."""
        user = request.getfixturevalue(hr_like_user)
        api_client.force_authenticate(user=user)
        response = api_client.get(f'/api/interviews/{interview_other.id}/')
        assert response.status_code == 200
        assert response.data['id'] == interview_other.id

    def test_retrieve_nonexistent_returns_404(self, api_client, api_admin_user):
        """Запрос несуществующего собеседования возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/interviews/99999/')
        assert response.status_code == 404

    @pytest.mark.parametrize('field', [
        'id', 'intern', 'intern_name', 'direction_id', 'company_id',
        'manager_email', 'manager_display_name', 'interview_type', 'interview_type_display',
        'interview_format', 'interview_format_display',
        'date', 'time', 'link', 'vacancy_link', 'interview_link', 'video_link',
        'has_video',
        'transcription_media_url', 'transcription_status', 'transcription_error_message',
        'hr_name', 'hr_contacts', 'created_at', 'updated_at',
    ])
    def test_retrieve_response_has_detail_fields(self, api_client, api_admin_user, interview, field):
        """Ответ содержит все поля детального сериализатора."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interviews/{interview.id}/')
        assert response.status_code == 200
        assert field in response.data, f'Поле {field!r} отсутствует в ответе'

    def test_retrieve_correct_field_values(self, api_client, api_admin_user, interview):
        """Детальный ответ содержит корректные значения полей."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interviews/{interview.id}/')
        assert response.status_code == 200
        assert response.data['id'] == interview.id
        assert response.data['interview_type'] == interview.interview_type
        assert response.data['manager_email'] == interview.manager_email

    def test_retrieve_intern_name_populated(self, api_client, api_admin_user, interview):
        """Поле intern_name заполнено именем студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interviews/{interview.id}/')
        assert response.status_code == 200
        assert response.data['intern_name'] == interview.intern.full_name

    def test_retrieve_interview_type_display(self, api_client, api_admin_user, interview):
        """Поле interview_type_display содержит человекочитаемое название типа."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interviews/{interview.id}/')
        assert response.status_code == 200
        assert response.data['interview_type_display'] == interview.get_interview_type_display()

    def test_unauthenticated_cannot_retrieve(self, api_client, interview):
        """Неаутентифицированный пользователь не может получить детали."""
        response = api_client.get(f'/api/interviews/{interview.id}/')
        assert response.status_code in (401, 403)


# ============================================================================
# POST /api/interviews/ — создание собеседования
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewViewSetCreate:
    """Тесты POST /api/interviews/ — создание собеседования."""

    def _interview_payload(self, intern_id, direction_id):
        return {
            'intern': intern_id,
            'direction_id': direction_id,
            'interview_type': 'screening',
            'date': '2025-12-15',
            'time': '10:00:00',
            'manager_email': 'admin@example.com',
        }

    def test_admin_can_create_interview(self, api_client, api_admin_user, intern, direction):
        """Администратор может создать собеседование."""
        api_client.force_authenticate(user=api_admin_user)
        payload = self._interview_payload(intern.id, direction.id)
        response = api_client.post('/api/interviews/', payload, format='json')
        assert response.status_code == 201
        assert Interview.objects.filter(
            intern=intern,
            interview_type='screening',
        ).exists()

    def test_manager_can_create_interview(
        self, api_client, api_manager_user, intern, direction
    ):
        """Менеджер может создать собеседование — 201."""
        api_client.force_authenticate(user=api_manager_user)
        payload = self._interview_payload(intern.id, direction.id)
        response = api_client.post('/api/interviews/', payload, format='json')
        assert response.status_code == 201

    def test_hr_cannot_create_interview(self, api_client, api_hr_user, intern, direction):
        """HR не может создать собеседование — 403."""
        api_client.force_authenticate(user=api_hr_user)
        payload = self._interview_payload(intern.id, direction.id)
        response = api_client.post('/api/interviews/', payload, format='json')
        assert response.status_code == 403

    def test_unauthenticated_cannot_create(self, api_client, intern, direction):
        """Неаутентифицированный пользователь не может создать собеседование."""
        payload = self._interview_payload(intern.id, direction.id)
        response = api_client.post('/api/interviews/', payload, format='json')
        assert response.status_code in (401, 403)

    def test_create_returns_201_with_id(self, api_client, api_admin_user, intern, direction):
        """Успешное создание возвращает 201 и id записи."""
        api_client.force_authenticate(user=api_admin_user)
        payload = self._interview_payload(intern.id, direction.id)
        response = api_client.post('/api/interviews/', payload, format='json')
        assert response.status_code == 201

    def test_create_with_all_optional_fields(
        self, api_client, api_admin_user, intern, direction
    ):
        """Создание собеседования со всеми опциональными полями."""
        api_client.force_authenticate(user=api_admin_user)
        payload = {
            'intern': intern.id,
            'direction_id': direction.id,
            'interview_type': 'tech',
            'date': '2025-12-20',
            'time': '14:30:00',
            'manager_email': 'admin@example.com',
            'link': 'https://meet.example.com/abc',
            'vacancy_link': 'https://hh.ru/vacancy/123',
            'interview_link': 'https://example.com/interview',
            'hr_name': 'Анна HR',
            'hr_contacts': 'anna@hr.com',
        }
        response = api_client.post('/api/interviews/', payload, format='json')
        assert response.status_code == 201
        interview = Interview.objects.get(intern=intern, interview_type='tech')
        assert interview.hr_name == 'Анна HR'
        assert interview.hr_contacts == 'anna@hr.com'
        assert interview.link == 'https://meet.example.com/abc'

    def test_create_without_required_field_returns_400(
        self, api_client, api_admin_user, direction
    ):
        """Создание без обязательного поля intern возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        payload = {
            'direction_id': direction.id,
            'interview_type': 'screening',
        }
        response = api_client.post('/api/interviews/', payload, format='json')
        assert response.status_code == 400

    def test_create_with_invalid_interview_type_returns_400(
        self, api_client, api_admin_user, intern, direction
    ):
        """Создание с невалидным типом собеседования возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        payload = self._interview_payload(intern.id, direction.id)
        payload['interview_type'] = 'invalid_type'
        response = api_client.post('/api/interviews/', payload, format='json')
        assert response.status_code == 400


# ============================================================================
# PATCH /api/interviews/{id}/ — частичное обновление
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewViewSetPartialUpdate:
    """Тесты PATCH /api/interviews/{id}/ — частичное обновление собеседования."""

    def test_admin_can_patch_interview(self, api_client, api_admin_user, interview):
        """Администратор может обновить поля собеседования."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/interviews/{interview.id}/',
            {'interview_type': 'tech'},
            format='json',
        )
        assert response.status_code == 200
        interview.refresh_from_db()
        assert interview.interview_type == 'tech'

    def test_manager_can_patch_own_interview(self, api_client, api_manager_user, interview):
        """Менеджер может обновить своё собеседование."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/interviews/{interview.id}/',
            {'interview_type': 'tech'},
            format='json',
        )
        assert response.status_code == 200
        interview.refresh_from_db()
        assert interview.interview_type == 'tech'

    def test_manager_cannot_patch_other_managers_interview(
        self, api_client, api_manager_user, interview_other
    ):
        """Менеджер не видит чужое собеседование в queryset — PATCH даёт 404."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/interviews/{interview_other.id}/',
            {'interview_type': 'final'},
            format='json',
        )
        assert response.status_code == 404

    def test_unauthenticated_cannot_patch(self, api_client, interview):
        """Неаутентифицированный пользователь не может обновить собеседование."""
        response = api_client.patch(
            f'/api/interviews/{interview.id}/',
            {'interview_type': 'tech'},
            format='json',
        )
        assert response.status_code in (401, 403)

    def test_patch_nonexistent_returns_404(self, api_client, api_admin_user):
        """Обновление несуществующего собеседования возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            '/api/interviews/99999/',
            {'interview_type': 'tech'},
            format='json',
        )
        assert response.status_code == 404

    def test_patch_updates_only_specified_fields(
        self, api_client, api_admin_user, interview
    ):
        """PATCH обновляет только переданные поля, остальные не меняются."""
        original_type = interview.interview_type
        original_date = interview.date
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/interviews/{interview.id}/',
            {'hr_name': 'Новый HR'},
            format='json',
        )
        assert response.status_code == 200
        interview.refresh_from_db()
        assert interview.hr_name == 'Новый HR'
        assert interview.interview_type == original_type
        assert interview.date == original_date

    def test_patch_hr_contacts(self, api_client, api_admin_user, interview):
        """Администратор может обновить контакты HR."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/interviews/{interview.id}/',
            {'hr_contacts': 'newhr@example.com'},
            format='json',
        )
        assert response.status_code == 200
        interview.refresh_from_db()
        assert interview.hr_contacts == 'newhr@example.com'

    def test_patch_date(self, api_client, api_admin_user, interview):
        """Администратор может обновить дату собеседования."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/interviews/{interview.id}/',
            {'date': '2026-01-15'},
            format='json',
        )
        assert response.status_code == 200
        interview.refresh_from_db()
        assert str(interview.date) == '2026-01-15'

    def test_admin_can_patch_any_interview(
        self, api_client, api_admin_user, interview_other
    ):
        """Администратор может обновить любое собеседование."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/interviews/{interview_other.id}/',
            {'interview_type': 'final'},
            format='json',
        )
        assert response.status_code == 200
        interview_other.refresh_from_db()
        assert interview_other.interview_type == 'final'


# ============================================================================
# DELETE /api/interviews/{id}/ — удаление собеседования
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewViewSetDelete:
    """Тесты DELETE /api/interviews/{id}/ — администратор или менеджер (свои записи)."""

    def test_admin_delete_returns_204(self, api_client, api_admin_user, interview):
        """Администратор удаляет собеседование — 204."""
        pk = interview.pk
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/interviews/{pk}/')
        assert response.status_code == 204
        assert not Interview.objects.filter(id=pk).exists()

    def test_manager_can_delete_own_interview(self, api_client, api_manager_user, interview):
        """Менеджер удаляет своё собеседование — 204."""
        pk = interview.pk
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.delete(f'/api/interviews/{pk}/')
        assert response.status_code == 204
        assert not Interview.objects.filter(id=pk).exists()

    def test_manager_delete_other_interview_returns_404(
        self, api_client, api_manager_user, interview_other
    ):
        """Чужое собеседование в queryset недоступно — 404."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.delete(f'/api/interviews/{interview_other.id}/')
        assert response.status_code == 404
        assert Interview.objects.filter(id=interview_other.id).exists()

    def test_unauthenticated_cannot_delete(self, api_client, interview):
        """Неаутентифицированный пользователь не может удалить собеседование."""
        response = api_client.delete(f'/api/interviews/{interview.id}/')
        assert response.status_code in (401, 403)
        assert Interview.objects.filter(id=interview.id).exists()

    def test_delete_nonexistent_returns_404(self, api_client, api_admin_user):
        """Удаление несуществующего собеседования возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete('/api/interviews/99999/')
        assert response.status_code == 404

    def test_admin_delete_any_interview(
        self, api_client, api_admin_user, interview_other
    ):
        """Администратор удаляет любое собеседование."""
        interview_id = interview_other.id
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/interviews/{interview_id}/')
        assert response.status_code == 204
        assert not Interview.objects.filter(id=interview_id).exists()


# ============================================================================
# POST transcribe — только администратор
# ============================================================================


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewViewSetTranscription:
    """POST транскрипции на InterviewViewSet."""

    def test_transcribe_manager_forbidden(self, api_client, api_manager_user, interview):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(f'/api/interviews/{interview.id}/transcribe/')
        assert response.status_code == 403

    def test_transcribe_admin_no_video_400(self, api_client, api_admin_user, interview):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post(f'/api/interviews/{interview.id}/transcribe/')
        assert response.status_code == 400
        assert 'error' in response.data

    def test_transcribe_admin_ok(
        self, api_client, api_admin_user, interview_with_video, mocker
    ):
        mocker.patch('transcriptions.tasks.transcribe_interview.delay')
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post(f'/api/interviews/{interview_with_video.id}/transcribe/')
        assert response.status_code == 200
        assert response.data.get('status') == 'pending'

    def test_transcribe_mentor_ok(
        self, api_client, api_mentor_user, interview_with_video, mocker,
    ):
        """Ментор может запустить транскрипцию для любого собеседования в базе."""
        mocker.patch('transcriptions.tasks.transcribe_interview.delay')
        api_client.force_authenticate(user=api_mentor_user)
        response = api_client.post(f'/api/interviews/{interview_with_video.id}/transcribe/')
        assert response.status_code == 200
        assert response.data.get('status') == 'pending'


# ============================================================================
# GET /api/interviews/{id}/transcription-status/ — статус транскрипции
# ============================================================================


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewViewSetTranscriptionStatus:
    """Тесты GET /api/interviews/{id}/transcription-status/."""

    def test_transcription_status_admin_no_record(self, api_client, api_admin_user, interview):
        """Администратор получает status=none, если записи транскрипции нет."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interviews/{interview.id}/transcription-status/')
        assert response.status_code == 200
        assert response.data['status'] == 'none'
        assert response.data['error_message'] == ''

    def test_transcription_status_outstaff_no_record(
        self, api_client, api_outstaff_user, interview
    ):
        """Outstaff получает status=none при отсутствии транскрипции."""
        api_client.force_authenticate(user=api_outstaff_user)
        response = api_client.get(f'/api/interviews/{interview.id}/transcription-status/')
        assert response.status_code == 200
        assert response.data['status'] == 'none'

    def test_transcription_status_hr_no_record(self, api_client, api_hr_user, interview):
        """HR получает status=none при отсутствии транскрипции."""
        api_client.force_authenticate(user=api_hr_user)
        response = api_client.get(f'/api/interviews/{interview.id}/transcription-status/')
        assert response.status_code == 200
        assert response.data['status'] == 'none'

    def test_transcription_status_mentor_no_record(self, api_client, api_mentor_user, interview):
        """Ментор получает status=none при отсутствии транскрипции (read-only, как HR)."""
        api_client.force_authenticate(user=api_mentor_user)
        response = api_client.get(f'/api/interviews/{interview.id}/transcription-status/')
        assert response.status_code == 200
        assert response.data['status'] == 'none'

    def test_transcription_status_with_pending(
        self, api_client, api_admin_user, interview
    ):
        """Возвращается статус из InterviewTranscription."""
        InterviewTranscription.objects.create(
            interview=interview,
            status=TranscriptionStatus.PENDING,
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interviews/{interview.id}/transcription-status/')
        assert response.status_code == 200
        assert response.data['status'] == TranscriptionStatus.PENDING

    def test_transcription_status_unauthenticated(self, api_client, interview):
        """Без аутентификации — 401 или 403."""
        response = api_client.get(f'/api/interviews/{interview.id}/transcription-status/')
        assert response.status_code in (401, 403)

    def test_transcription_status_manager_own_interview(
        self, api_client, api_manager_user, interview
    ):
        """Менеджер получает status=none для своего собеседования."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/interviews/{interview.id}/transcription-status/')
        assert response.status_code == 200
        assert response.data['status'] == 'none'

    def test_transcription_status_manager_foreign_interview_404(
        self, api_client, api_manager_user, interview_other
    ):
        """Менеджер не видит статус транскрипции чужого собеседования."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/interviews/{interview_other.id}/transcription-status/')
        assert response.status_code == 404


# ============================================================================
# GET /api/interviews/{id}/transcription-text/ — текст транскрипции
# ============================================================================


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewViewSetTranscriptionText:
    """Тесты GET /api/interviews/{id}/transcription-text/."""

    def test_transcription_text_admin_no_text_404(self, api_client, api_admin_user, interview):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/interviews/{interview.id}/transcription-text/')
        assert response.status_code == 404

    def test_transcription_text_manager_completed(
        self, api_client, api_manager_user, interview
    ):
        """Менеджер получает текст для своего собеседования со статусом completed."""
        InterviewTranscription.objects.create(
            interview=interview,
            status=TranscriptionStatus.COMPLETED,
            text='Привет, это тестовая транскрипция.',
        )
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/interviews/{interview.id}/transcription-text/')
        assert response.status_code == 200
        assert response.data['text'] == 'Привет, это тестовая транскрипция.'
        assert response.data['filename'] == 'Иван Иванов_Скрининг_01.12.2025.txt'

    def test_transcription_text_manager_foreign_404(
        self, api_client, api_manager_user, interview_other
    ):
        """Менеджер не получает текст транскрипции чужого собеседования."""
        InterviewTranscription.objects.create(
            interview=interview_other,
            status=TranscriptionStatus.COMPLETED,
            text='Секретный текст',
        )
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/interviews/{interview_other.id}/transcription-text/')
        assert response.status_code == 404

    def test_transcription_text_hr_any_interview(
        self, api_client, api_hr_user, interview
    ):
        """HR может запросить текст по любому интервью при completed."""
        InterviewTranscription.objects.create(
            interview=interview,
            status=TranscriptionStatus.COMPLETED,
            text='Текст для HR',
        )
        api_client.force_authenticate(user=api_hr_user)
        response = api_client.get(f'/api/interviews/{interview.id}/transcription-text/')
        assert response.status_code == 200
        assert response.data['text'] == 'Текст для HR'
        assert response.data['filename'].endswith('.txt')
