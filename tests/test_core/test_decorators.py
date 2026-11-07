"""
Тесты для core/decorators.py.

Покрывает:
- manager_required_api: 401 без SSO-сессии, проход с SSO, сохранение имени функции
- login_required_custom: редирект без SSO, проход с SSO, сохранение имени функции
"""
import json
from unittest.mock import patch

from django.test import RequestFactory
from django.urls import reverse

from core.decorators import manager_required_api, login_required_custom


def _make_request(*, has_sso=True):
    """Создаёт GET-запрос с нужными параметрами SSO-сессии."""
    request = RequestFactory().get('/')
    session = {}
    if has_sso:
        session['keycloak_user'] = True
        session['keycloak_id'] = 'test-keycloak-id'
    request.session = session
    return request


def _attach_messages(request):
    """Подключает messages storage к request (нужен для messages.warning)."""
    from django.contrib.messages.storage.fallback import FallbackStorage
    setattr(request, '_messages', FallbackStorage(request))
    return request


class TestManagerRequiredApiDecorator:
    """Тесты для декоратора manager_required_api."""

    def _make_view(self):
        @manager_required_api
        def my_api_view(request, *args, **kwargs):
            return 'success'

        return my_api_view

    def test_without_sso_returns_401(self):
        """Без SSO-сессии → JsonResponse 401 с полем error."""
        view = self._make_view()
        response = view(_make_request(has_sso=False))
        assert response.status_code == 401
        data = json.loads(response.content)
        assert 'error' in data

    def test_with_sso_calls_original_view(self):
        """С SSO-сессией → исходная функция вызывается и возвращает результат."""
        view = self._make_view()
        result = view(_make_request(has_sso=True))
        assert result == 'success'

    def test_preserves_function_name_via_wraps(self):
        """@wraps сохраняет имя исходной функции."""
        @manager_required_api
        def named_view(request):
            pass

        assert named_view.__name__ == 'named_view'

    def test_passes_args_and_kwargs_to_view(self):
        """Позиционные и именованные аргументы передаются во view."""
        @manager_required_api
        def view_with_args(request, pk, *args, extra=None):
            return (pk, extra)

        result = view_with_args(_make_request(has_sso=True), 42, extra='val')
        assert result == (42, 'val')


class TestLoginRequiredCustomDecorator:
    """Тесты для декоратора login_required_custom."""

    def _make_view(self):
        @login_required_custom
        def my_view(request, *args, **kwargs):
            return 'ok'

        return my_view

    def test_without_sso_redirects_to_login(self):
        """Без SSO-сессии → 302 редирект на страницу login."""
        view = self._make_view()
        request = _attach_messages(_make_request(has_sso=False))
        response = view(request)
        assert response.status_code == 302
        assert response['Location'] == reverse('login')

    def test_with_sso_calls_original_view(self):
        """С SSO-сессией → исходная функция вызывается и возвращает результат."""
        view = self._make_view()
        result = view(_make_request(has_sso=True))
        assert result == 'ok'

    def test_preserves_function_name_via_wraps(self):
        """@wraps сохраняет имя исходной функции."""
        @login_required_custom
        def my_page_view(request):
            pass

        assert my_page_view.__name__ == 'my_page_view'

    def test_without_sso_sets_warning_message(self):
        """Без SSO → сообщение об ошибке добавляется в messages."""
        from django.contrib.messages import get_messages

        view = self._make_view()
        request = _attach_messages(_make_request(has_sso=False))
        view(request)
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert str(messages[0]) == 'Для доступа к этой странице необходима авторизация'


class TestAnalyticsCacheHelpers:
    def test_get_analytics_cache_key_stable(self):
        from core.decorators import get_analytics_cache_key

        k1 = get_analytics_cache_key('view', {'a': '1', 'b': '2'})
        k2 = get_analytics_cache_key('view', {'b': '2', 'a': '1'})
        assert k1 == k2
        assert k1.startswith('analytics:')

    def test_cache_analytics_returns_cached(self):
        from core.decorators import cache_analytics
        from django.http import JsonResponse

        @cache_analytics(timeout=60)
        def view(request):
            return JsonResponse({'live': True})

        request = _make_request(has_sso=True)
        with patch('core.decorators.cache.get', return_value={'cached': 1}):
            response = view(request)
        assert json.loads(response.content) == {'cached': 1}
