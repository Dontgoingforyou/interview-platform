"""
Тесты для core/views.py.

Покрывает:
- GetInternDataView: без intern_id (400), несуществующий id (404), без авторизации (401),
  валидный запрос (200) с корректными данными в ответе
- ImportTaskStatusView: все состояния Celery (PENDING, PROGRESS, SUCCESS, FAILURE, ValueError)
- /help/: отдаётся SPA (shell)
- ProtectedSwaggerView, ProtectedRedocView, ProtectedSchemaView: при DEBUG=False — 404;
  при DEBUG=True — редирект или 401 без SSO, 200 у менеджера, 403 у студента
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from django.test import override_settings


def _get_api_docs(client, url, *, debug):
    """GET документации API при заданном DEBUG."""
    with override_settings(DEBUG=debug):
        return client.get(url)


@pytest.mark.django_db(databases=['default'])
class TestGetInternDataView:
    """Тесты для GetInternDataView (/get-intern-data/)."""

    URL = '/api/intern-data/'

    def test_no_intern_id_returns_400(self, logged_in_manager):
        """Запрос без intern_id → 400."""
        response = logged_in_manager.get(self.URL)
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    def test_nonexistent_intern_id_returns_404(self, logged_in_manager):
        """Несуществующий intern_id → 404."""
        response = logged_in_manager.get(self.URL, {'intern_id': 99999})
        assert response.status_code == 404
        data = json.loads(response.content)
        assert 'error' in data

    def test_unauthenticated_returns_401(self, client):
        """Запрос без SSO-сессии → 401."""
        response = client.get(self.URL, {'intern_id': 1})
        assert response.status_code == 401

    def test_valid_request_returns_intern_data(self, logged_in_manager, intern, direction):
        """Валидный запрос → 200, JSON содержит ожидаемые поля."""
        response = logged_in_manager.get(self.URL, {'intern_id': intern.id})
        assert response.status_code == 200

        data = json.loads(response.content)
        assert data['direction_id'] == direction.id
        assert data['email'] == intern.email
        assert data['manager_email'] == intern.manager_email

    def test_response_contains_all_required_fields(self, logged_in_manager, intern):
        """Ответ содержит все обязательные поля."""
        response = logged_in_manager.get(self.URL, {'intern_id': intern.id})
        data = json.loads(response.content)

        required_fields = {'direction_id', 'direction_name', 'telegram_username',
                           'email', 'manager_email', 'manager_name', 'real_interview_date'}
        assert required_fields.issubset(data.keys())

    def test_intern_without_direction_returns_none(self, logged_in_manager, intern):
        """Студент без направления → direction_id=None, direction_name=None (через мок)."""
        mock_intern = MagicMock()
        mock_intern.id = intern.id
        mock_intern.direction = None
        mock_intern.direction_id = None
        mock_intern.email = 'test@example.com'
        mock_intern.manager_email = 'manager@example.com'
        mock_intern.telegram_username = None
        mock_intern.real_interview_date = None

        # Патчим get_object_or_404, т.к. вид использует его вместо .get() — так в ответ не попадёт MagicMock
        with patch('core.views.get_object_or_404', return_value=mock_intern):
            response = logged_in_manager.get(self.URL, {'intern_id': intern.id})

        data = json.loads(response.content)
        assert data['direction_id'] is None
        assert data['direction_name'] is None

    def test_real_interview_date_formatted_as_yyyy_mm_dd(self, logged_in_manager, intern):
        """real_interview_date форматируется как YYYY-MM-DD."""
        from datetime import date
        intern.real_interview_date = date(2025, 6, 15)
        intern.save()
        response = logged_in_manager.get(self.URL, {'intern_id': intern.id})
        data = json.loads(response.content)
        assert data['real_interview_date'] == '2025-06-15'


@pytest.mark.django_db(databases=['default'])
class TestImportTaskStatusView:
    """Тесты для ImportTaskStatusView (/import/status/<task_id>/)."""

    def _url(self, task_id='test-task-id'):
        return f'/import/status/{task_id}/'

    def _mock_task(self, state, info=None, result=None):
        """Создаёт мок AsyncResult с заданным состоянием."""
        task = MagicMock()
        task.state = state
        task.info = info
        task.result = result
        return task

    def test_pending_state(self, logged_in_manager):
        """Состояние PENDING → current=0, total=100, state='PENDING'."""
        task = self._mock_task('PENDING')
        with patch('core.views.AsyncResult', return_value=task):
            response = logged_in_manager.get(self._url())

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['state'] == 'PENDING'
        assert data['current'] == 0
        assert data['total'] == 100

    def test_progress_state_returns_task_info(self, logged_in_manager):
        """Состояние PROGRESS → current и total берутся из task.info."""
        task = self._mock_task('PROGRESS', info={'current': 42, 'total': 100, 'status': 'Импорт...'})
        with patch('core.views.AsyncResult', return_value=task):
            response = logged_in_manager.get(self._url())

        data = json.loads(response.content)
        assert data['state'] == 'PROGRESS'
        assert data['current'] == 42
        assert data['total'] == 100
        assert data['status'] == 'Импорт...'

    def test_success_state_returns_100_percent(self, logged_in_manager):
        """Состояние SUCCESS → current=100, total=100, наличие result."""
        task = self._mock_task('SUCCESS', result={'created': 10, 'errors': 0})
        with patch('core.views.AsyncResult', return_value=task):
            response = logged_in_manager.get(self._url())

        data = json.loads(response.content)
        assert data['state'] == 'SUCCESS'
        assert data['current'] == 100
        assert data['total'] == 100
        assert 'result' in data

    def test_failure_state_returns_error_status(self, logged_in_manager):
        """Состояние FAILURE → state='FAILURE', status содержит описание ошибки."""
        task = self._mock_task('FAILURE', info=Exception('Что-то пошло не так'))
        with patch('core.views.AsyncResult', return_value=task):
            response = logged_in_manager.get(self._url())

        data = json.loads(response.content)
        assert data['state'] == 'FAILURE'
        assert data['current'] == 0
        assert 'Что-то пошло не так' in data['status']

    def test_value_error_on_state_returns_failure(self, logged_in_manager):
        """ValueError при получении task.state → state='FAILURE' со специальным статусом."""
        task = MagicMock()
        type(task).state = property(lambda self: (_ for _ in ()).throw(ValueError('bad format')))
        with patch('core.views.AsyncResult', return_value=task):
            response = logged_in_manager.get(self._url())

        data = json.loads(response.content)
        assert data['state'] == 'FAILURE'
        assert data['current'] == 0
        assert 'импорт заново' in data['status'].lower()

    def test_unknown_state_returns_generic_response(self, logged_in_manager):
        """Неизвестное состояние → state сохраняется, current=0."""
        task = self._mock_task('REVOKED', info=None)
        with patch('core.views.AsyncResult', return_value=task):
            response = logged_in_manager.get(self._url())

        data = json.loads(response.content)
        assert data['state'] == 'REVOKED'
        assert data['current'] == 0

    def test_unauthenticated_redirects(self, client):
        """Без авторизации → редирект на логин."""
        task = self._mock_task('PENDING')
        with patch('core.views.AsyncResult', return_value=task):
            response = client.get(self._url())

        assert response.status_code == 302


@pytest.mark.django_db(databases=['default'])
class TestHelpSpaShell:
    """Справка в React: Django отдаёт только оболочку SPA."""

    URL = '/help/'

    def test_authenticated_user_gets_spa_shell(self, logged_in_manager):
        """С SSO → 200, в ответе шаблон SPA с #root."""
        response = logged_in_manager.get(self.URL)
        assert response.status_code == 200
        assert b'id="root"' in response.content


API_DOCS_URLS = ('/api/docs/', '/api/redoc/', '/api/schema/')


@pytest.mark.django_db(databases=['default'])
class TestApiDocsHiddenWithoutDebug:
    """Вне DEBUG документация API не отдаётся ни анониму, ни менеджеру."""

    @pytest.mark.parametrize('url', API_DOCS_URLS)
    def test_anonymous_gets_404(self, client, url):
        response = _get_api_docs(client, url, debug=False)
        assert response.status_code == 404

    @pytest.mark.parametrize('url', API_DOCS_URLS)
    def test_manager_gets_404(self, logged_in_manager, url):
        response = _get_api_docs(logged_in_manager, url, debug=False)
        assert response.status_code == 404


@pytest.mark.django_db(databases=['default'])
class TestProtectedSchemaView:
    """Тесты для ProtectedSchemaView (/api/schema/)."""

    URL = '/api/schema/'

    def test_without_sso_returns_401(self, client):
        """Без SSO-сессии → 401 JSON-ответ."""
        response = _get_api_docs(client, self.URL, debug=True)
        assert response.status_code == 401
        import json
        data = json.loads(response.content)
        assert 'error' in data

    def test_with_sso_returns_200(self, logged_in_manager):
        """С SSO-сессией менеджера → 200 (OpenAPI-схема)."""
        response = _get_api_docs(logged_in_manager, self.URL, debug=True)
        assert response.status_code == 200

    def test_student_gets_403(self, logged_in_student):
        """Студент (только группа students) → 403."""
        response = _get_api_docs(logged_in_student, self.URL, debug=True)
        assert response.status_code == 403


@pytest.mark.django_db(databases=['default'])
class TestProtectedSwaggerView:
    """Тесты для ProtectedSwaggerView (/api/docs/)."""

    URL = '/api/docs/'

    def test_without_sso_redirects_to_login(self, client):
        """Без сессии → 302 на страницу входа портала."""
        response = _get_api_docs(client, self.URL, debug=True)
        assert response.status_code == 302
        assert response['Location'].startswith('/login?next=')

    def test_with_sso_returns_200(self, logged_in_manager):
        """С SSO-сессией менеджера → 200 (Swagger UI)."""
        response = _get_api_docs(logged_in_manager, self.URL, debug=True)
        assert response.status_code == 200

    def test_student_gets_403(self, logged_in_student):
        """Студент (только группа students) → 403."""
        response = _get_api_docs(logged_in_student, self.URL, debug=True)
        assert response.status_code == 403


@pytest.mark.django_db(databases=['default'])
class TestProtectedRedocView:
    """Тесты для ProtectedRedocView (/api/redoc/)."""

    URL = '/api/redoc/'

    def test_without_sso_redirects_to_login(self, client):
        """Без сессии → 302 на страницу входа портала."""
        response = _get_api_docs(client, self.URL, debug=True)
        assert response.status_code == 302
        assert response['Location'].startswith('/login?next=')

    def test_with_sso_returns_200(self, logged_in_manager):
        """С SSO-сессией менеджера → 200 (ReDoc)."""
        response = _get_api_docs(logged_in_manager, self.URL, debug=True)
        assert response.status_code == 200

    def test_student_gets_403(self, logged_in_student):
        """Студент (только группа students) → 403."""
        response = _get_api_docs(logged_in_student, self.URL, debug=True)
        assert response.status_code == 403
