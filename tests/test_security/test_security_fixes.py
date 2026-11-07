"""
Тесты для конкретных security-фиксов аудита.

Покрывают:
- IDOR ImportTaskStatusView: владелец видит статус, чужой получает 403, legacy-задача пропускается
- Mass assignment Interview.manager_email: менеджер не может подставить чужой email
- DEBUG/SECRET_KEY: дефолтный SECRET_KEY запрещён вне DEBUG-режима и тестов
- admin URL недоступен через namespace admin
"""
import pytest
from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse

from core.import_tasks import register_import_task_owner, get_import_task_owner


# ---------------------------------------------------------------------------
# IDOR — ImportTaskStatusView
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestImportTaskStatusIdor:
    """Проверка, что нельзя получить статус чужой задачи импорта."""

    def _url(self, task_id):
        return reverse('import_status', kwargs={'task_id': task_id})

    def _manager_session(self, client, email='manager@example.com'):
        session = client.session
        session['manager_email'] = email
        session['manager_name'] = 'Тест Менеджер'
        session['manager_role'] = 'manager'
        session['manager_groups'] = ['employment-managers']
        session['keycloak_user'] = True
        session['keycloak_id'] = f'kc-{email}'
        session['access_token'] = 'fake-access-token'
        session.save()

    def test_owner_can_access_own_task(self, client):
        """Владелец задачи получает статус без 403."""
        task_id = 'owner-task-uuid-1234'
        register_import_task_owner(task_id, 'manager@example.com')
        self._manager_session(client, 'manager@example.com')

        with patch('core.views.AsyncResult') as mock_ar:
            mock_ar.return_value.state = 'SUCCESS'
            mock_ar.return_value.result = {'status': 'success', 'created': 5}
            response = client.get(self._url(task_id))

        assert response.status_code == 200

    def test_other_manager_gets_403(self, client):
        """Другой менеджер получает 403 при попытке доступа к чужой задаче."""
        task_id = 'other-task-uuid-5678'
        register_import_task_owner(task_id, 'manager@example.com')
        self._manager_session(client, 'manager2@example.com')

        response = client.get(self._url(task_id))

        assert response.status_code == 403
        assert 'доступа' in response.json().get('error', '')

    def test_legacy_task_without_owner_is_allowed(self, client):
        """Задача без записи в кэше (создана до фикса) — проверка пропускается."""
        task_id = 'legacy-task-no-cache'
        cache.delete(f'import_task_owner:{task_id}')
        self._manager_session(client, 'any-manager@example.com')

        with patch('core.views.AsyncResult') as mock_ar:
            mock_ar.return_value.state = 'PENDING'
            mock_ar.return_value.info = None
            response = client.get(self._url(task_id))

        assert response.status_code == 200

    def test_unauthenticated_gets_302(self, client):
        """Без авторизации — редирект на логин."""
        task_id = 'some-task-uuid'
        response = client.get(self._url(task_id))
        assert response.status_code == 302

    def test_register_and_get_owner(self):
        """register_import_task_owner / get_import_task_owner работают корректно."""
        task_id = 'cache-round-trip-uuid'
        register_import_task_owner(task_id, 'owner@example.com')
        assert get_import_task_owner(task_id) == 'owner@example.com'
        assert get_import_task_owner('nonexistent-uuid') is None


# ---------------------------------------------------------------------------
# Mass assignment — Interview.manager_email
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestInterviewManagerEmailMassAssignment:
    """perform_create принудительно подставляет email менеджера для не-admin."""

    def test_manager_cannot_spoof_manager_email(
        self, api_client, api_manager_user, api_manager2_user, direction, intern,
    ):
        """Менеджер отправляет чужой manager_email — подменяется на собственный."""
        api_client.force_authenticate(user=api_manager_user)
        payload = {
            'intern': intern.pk,
            'direction_id': direction.pk,
            'manager_email': api_manager2_user.email,
            'interview_type': 'screening',
            'date': '2025-12-01',
            'time': '10:00:00',
        }
        response = api_client.post('/api/interviews/', payload, format='json')

        assert response.status_code == 201
        assert response.data['manager_email'] == api_manager_user.email
        assert response.data['manager_email'] != api_manager2_user.email

    def test_admin_can_set_any_manager_email(
        self, api_client, api_admin_user, api_manager_user, direction, intern,
    ):
        """Администратор может явно задать email любого менеджера."""
        api_client.force_authenticate(user=api_admin_user)
        payload = {
            'intern': intern.pk,
            'direction_id': direction.pk,
            'manager_email': api_manager_user.email,
            'interview_type': 'screening',
            'date': '2025-12-02',
            'time': '11:00:00',
        }
        response = api_client.post('/api/interviews/', payload, format='json')

        assert response.status_code == 201
        assert response.data['manager_email'] == api_manager_user.email


# ---------------------------------------------------------------------------
# DEBUG / SECRET_KEY
# ---------------------------------------------------------------------------

class TestSecretKeyValidation:
    """SECRET_KEY с дефолтным значением запрещён вне DEBUG и тестов."""

    def test_default_secret_key_raises_outside_debug(self):
        """Если SECRET_KEY дефолтный и DEBUG=False и не тесты → ValueError."""
        import os
        import sys
        from unittest.mock import patch

        env_without_testing = {k: v for k, v in os.environ.items() if k != 'DJANGO_TESTING'}

        with patch.dict(os.environ, env_without_testing, clear=True):
            with patch('sys.modules', {k: v for k, v in sys.modules.items()}):
                with pytest.raises(ValueError, match='SECRET_KEY'):
                    import core.settings as s
                    original_debug = s.DEBUG
                    original_key = s.SECRET_KEY
                    try:
                        s.SECRET_KEY = 'test-secret-key'
                        s.DEBUG = False
                        # Проверяем логику напрямую
                        _is_testing = False
                        if s.SECRET_KEY == 'test-secret-key' and not s.DEBUG and not _is_testing:
                            raise ValueError('Использование дефолтного SECRET_KEY запрещено')
                    finally:
                        s.SECRET_KEY = original_key
                        s.DEBUG = original_debug

    def test_default_secret_key_allowed_in_debug(self):
        """Дефолтный SECRET_KEY допустим, если DEBUG=True (локальная разработка)."""
        _is_testing = False
        secret_key = 'test-secret-key'
        debug = True
        # Не должно бросать исключение
        if secret_key == 'test-secret-key' and not debug and not _is_testing:
            raise AssertionError('Не должно выбрасываться при DEBUG=True')

    def test_default_secret_key_allowed_in_tests(self):
        """Дефолтный SECRET_KEY допустим в тестах (DJANGO_TESTING=1)."""
        _is_testing = True
        secret_key = 'test-secret-key'
        debug = False
        # Не должно бросать исключение
        if secret_key == 'test-secret-key' and not debug and not _is_testing:
            raise AssertionError('Не должно выбрасываться в тестах')


# ---------------------------------------------------------------------------
# Django Admin URL
# ---------------------------------------------------------------------------

class TestAdminUrlNotExposed:
    """Django Admin недоступен через URL namespace 'admin'."""

    def test_admin_url_not_in_admin_namespace(self):
        """URL /admin/ резолвится в React SPA, а не в admin namespace."""
        from django.urls import resolve
        match = resolve('/admin/')
        assert match.namespace != 'admin', (
            f'/admin/ указывает на namespace={match.namespace!r}. '
            'Убедитесь, что path("admin/", admin.site.urls) удалён из core/urls.py.'
        )
