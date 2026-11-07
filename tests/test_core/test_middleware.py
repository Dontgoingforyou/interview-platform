"""
Тесты для core/middleware.py.

Тестируются вспомогательные методы через прямой вызов, без запуска middleware-цепочки:
- RequestLoggingMiddleware.get_client_ip
- RequestLoggingMiddleware.process_request: установка _start_time
- RequestLoggingMiddleware.process_response: статика пропускается, уровень по статусу
- ApiAccessLoggingMiddleware._get_client_ip
- ApiAccessLoggingMiddleware._get_request_body (маскировка sensitive-полей)
- ApiAccessLoggingMiddleware._get_user_info
- ApiAccessLoggingMiddleware._get_query_params
- ApiAccessLoggingMiddleware._log_api_access: уровень, метод/путь, body/params
- UserActivityLoggingMiddleware: POST/PUT/PATCH/DELETE логируются, GET нет
- StudentRedirectMiddleware: студент редиректится на портал с менеджерских URL
"""
import json
import logging
import time as time_module
import pytest
from unittest.mock import MagicMock, patch

from django.urls import reverse

from core.constants import KEYCLOAK_GROUP_ADMIN
from core.middleware import (
    ApiAccessLoggingMiddleware,
    HROutstaffRedirectMiddleware,
    RequestLoggingMiddleware,
    SessionRoleRepairMiddleware,
    SQLQueryLoggingMiddleware,
    StudentRedirectMiddleware,
    UserActivityLoggingMiddleware,
)


def make_middleware():
    """Создаёт экземпляры middleware без вызова цепочки Django."""
    get_response = MagicMock(return_value=MagicMock(status_code=200))
    return RequestLoggingMiddleware(get_response), ApiAccessLoggingMiddleware(get_response)


class TestRequestLoggingGetClientIp:
    """Тесты для RequestLoggingMiddleware.get_client_ip."""

    def setup_method(self):
        request_mw, _ = make_middleware()
        self.mw = request_mw

    def _request(self, meta):
        req = MagicMock()
        req.META = meta
        return req

    def test_x_forwarded_for_single_ip(self):
        """Один IP в X-Forwarded-For → берётся как есть."""
        req = self._request({'HTTP_X_FORWARDED_FOR': '1.2.3.4'})
        assert self.mw.get_client_ip(req) == '1.2.3.4'

    def test_x_forwarded_for_multiple_ips_first_taken(self):
        """Несколько IP через запятую → берётся первый."""
        req = self._request({'HTTP_X_FORWARDED_FOR': '10.0.0.1, 192.168.0.1, 172.16.0.1'})
        assert self.mw.get_client_ip(req) == '10.0.0.1'

    def test_x_forwarded_for_with_spaces(self):
        """IP с пробелами вокруг запятой → strip применяется."""
        req = self._request({'HTTP_X_FORWARDED_FOR': '  5.5.5.5  , 6.6.6.6'})
        assert self.mw.get_client_ip(req) == '5.5.5.5'

    def test_remote_addr_used_when_no_forwarded_for(self):
        """Нет X-Forwarded-For → берётся REMOTE_ADDR."""
        req = self._request({'REMOTE_ADDR': '9.9.9.9'})
        assert self.mw.get_client_ip(req) == '9.9.9.9'

    def test_unknown_when_both_missing(self):
        """Ни X-Forwarded-For, ни REMOTE_ADDR → 'Unknown'."""
        req = self._request({})
        assert self.mw.get_client_ip(req) == 'Unknown'


class TestApiMiddlewareGetClientIp:
    """Тесты для ApiAccessLoggingMiddleware._get_client_ip."""

    def setup_method(self):
        _, api_mw = make_middleware()
        self.mw = api_mw

    def _request(self, meta):
        req = MagicMock()
        req.META = meta
        return req

    def test_x_forwarded_for_multiple_returns_first(self):
        """Несколько IP → берётся первый (без пробелов)."""
        req = self._request({'HTTP_X_FORWARDED_FOR': '1.1.1.1, 2.2.2.2'})
        assert self.mw._get_client_ip(req) == '1.1.1.1'

    def test_remote_addr_fallback(self):
        """Нет X-Forwarded-For → REMOTE_ADDR."""
        req = self._request({'REMOTE_ADDR': '8.8.8.8'})
        assert self.mw._get_client_ip(req) == '8.8.8.8'

    def test_unknown_default(self):
        """Ни заголовка, ни REMOTE_ADDR → 'unknown'."""
        req = self._request({})
        assert self.mw._get_client_ip(req) == 'unknown'


class TestGetRequestBody:
    """Тесты для ApiAccessLoggingMiddleware._get_request_body."""

    def setup_method(self):
        _, api_mw = make_middleware()
        self.mw = api_mw

    def _request(self, method, body_bytes=b''):
        req = MagicMock()
        req.method = method
        req.body = body_bytes
        return req

    @pytest.mark.parametrize('method', ['GET', 'DELETE', 'HEAD'])
    def test_non_mutating_methods_return_empty(self, method):
        """GET, DELETE, HEAD → {}."""
        req = self._request(method, b'{"key": "val"}')
        assert self.mw._get_request_body(req) == {}

    def test_post_with_valid_json_returns_dict(self):
        """POST с валидным JSON-словарём → возвращает словарь."""
        body = json.dumps({'name': 'Иван', 'age': 30}).encode()
        req = self._request('POST', body)
        result = self.mw._get_request_body(req)
        assert result == {'name': 'Иван', 'age': 30}

    @pytest.mark.parametrize('sensitive_key', ['password', 'token', 'secret', 'key', 'authorization'])
    def test_sensitive_fields_are_masked(self, sensitive_key):
        """Чувствительные поля заменяются значением '***'."""
        body = json.dumps({sensitive_key: 'supersecret', 'name': 'visible'}).encode()
        req = self._request('PUT', body)
        result = self.mw._get_request_body(req)
        assert result[sensitive_key] == '***'
        assert result['name'] == 'visible'

    def test_sensitive_field_case_insensitive(self):
        """Ключ PASSWORD (верхний регистр) тоже маскируется."""
        body = json.dumps({'PASSWORD': 'secret'}).encode()
        req = self._request('POST', body)
        result = self.mw._get_request_body(req)
        assert result['PASSWORD'] == '***'

    def test_invalid_json_returns_empty(self):
        """Невалидный JSON → {}."""
        req = self._request('POST', b'not-json')
        assert self.mw._get_request_body(req) == {}

    def test_json_list_returns_raw(self):
        """JSON-список (не словарь) → {'raw': ...}."""
        body = json.dumps([1, 2, 3]).encode()
        req = self._request('PATCH', body)
        result = self.mw._get_request_body(req)
        assert 'raw' in result

    def test_empty_body_returns_empty(self):
        """Пустое тело → {}."""
        req = self._request('POST', b'')
        assert self.mw._get_request_body(req) == {}


class TestApiMiddlewareGetUserInfo:
    """Тесты для ApiAccessLoggingMiddleware._get_user_info."""

    def setup_method(self):
        _, api_mw = make_middleware()
        self.mw = api_mw

    def test_authenticated_user_returns_full_info(self):
        """Аутентифицированный пользователь → словарь с email, full_name, role."""
        user = MagicMock()
        user.is_authenticated = True
        user.email = 'boss@example.com'
        user.full_name = 'Иван Иванов'
        user.role = 'admin'
        user.groups = MagicMock()
        user.groups.all = MagicMock(return_value=[])
        # Имитируем values_list
        user.groups.values_list = MagicMock(return_value=['managers'])

        req = MagicMock()
        req.user = user
        result = self.mw._get_user_info(req)

        assert result['email'] == 'boss@example.com'
        assert result['full_name'] == 'Иван Иванов'
        assert result['role'] == 'admin'

    def test_session_manager_returns_role_manager(self):
        """Сессия с manager_email → role='manager'."""
        req = MagicMock()
        req.user = None  # нет user
        req.session = {
            'manager_email': 'mgr@example.com',
            'manager_name': 'Петр Петров',
        }
        result = self.mw._get_user_info(req)
        assert result['email'] == 'mgr@example.com'
        assert result['full_name'] == 'Петр Петров'
        assert result['role'] == 'manager'

    def test_anonymous_returns_anonymous_email(self):
        """Нет ни user, ни сессии → email='anonymous'."""
        req = MagicMock()
        req.user = None
        req.session = {}
        result = self.mw._get_user_info(req)
        assert result['email'] == 'anonymous'
        assert result['role'] == ''


class TestGetQueryParams:
    """Тесты для ApiAccessLoggingMiddleware._get_query_params."""

    def setup_method(self):
        _, api_mw = make_middleware()
        self.mw = api_mw

    def _request_with_get(self, params: dict):
        req = MagicMock()
        req.GET = params
        return req

    def test_empty_params_returns_empty_dict(self):
        """Пустые параметры → {}."""
        req = self._request_with_get({})
        assert self.mw._get_query_params(req) == {}

    def test_single_value_param_returns_string(self):
        """Один параметр с одним значением → строка (не список)."""
        req = self._request_with_get({'page': ['2']})
        result = self.mw._get_query_params(req)
        assert result['page'] == '2'

    def test_multi_value_param_returns_list(self):
        """Один ключ с несколькими значениями → список."""
        req = self._request_with_get({'tag': ['python', 'django']})
        result = self.mw._get_query_params(req)
        assert result['tag'] == ['python', 'django']


# ---------------------------------------------------------------------------
# RequestLoggingMiddleware.process_request / process_response
# ---------------------------------------------------------------------------

class TestRequestLoggingProcessRequest:
    """Тесты для RequestLoggingMiddleware.process_request."""

    def test_sets_start_time_as_float_on_request(self):
        """process_request добавляет _start_time (float) на объект request."""
        mw, _ = make_middleware()

        class Req:
            pass

        req = Req()
        result = mw.process_request(req)
        assert hasattr(req, '_start_time')
        assert isinstance(req._start_time, float)
        assert result is None


class TestRequestLoggingProcessResponse:
    """Тесты для RequestLoggingMiddleware.process_response.

    Для проверки уровней логирования используем patch('core.middleware.logger'),
    так как 'django.request' настроен с propagate=False и caplog его не захватывает.
    """

    def _make_request(self, path, method='GET', with_start_time=True):
        """Создаёт простой объект запроса (не MagicMock, чтобы hasattr работал правильно)."""
        class Req:
            pass

        req = Req()
        req.path = path
        req.method = method
        req.META = {'REMOTE_ADDR': '127.0.0.1'}
        req.session = {}
        user = MagicMock()
        user.is_authenticated = False
        req.user = user
        if with_start_time:
            req._start_time = time_module.time()
        return req

    def test_static_path_returns_response_without_logging(self):
        """Запрос к /static/ → response возвращается, логгер НЕ вызывается."""
        from unittest.mock import patch
        mw, _ = make_middleware()
        req = self._make_request('/static/css/main.css')
        resp = MagicMock()
        resp.status_code = 200
        with patch('core.middleware.logger') as mock_logger:
            returned = mw.process_response(req, resp)
        assert returned is resp
        mock_logger.log.assert_not_called()

    def test_media_path_returns_response_without_logging(self):
        """Запрос к /media/ → response возвращается, логгер НЕ вызывается."""
        from unittest.mock import patch
        mw, _ = make_middleware()
        req = self._make_request('/media/file.jpg')
        resp = MagicMock()
        resp.status_code = 200
        with patch('core.middleware.logger') as mock_logger:
            mw.process_response(req, resp)
        mock_logger.log.assert_not_called()

    @pytest.mark.parametrize('status_code, expected_level', [
        (200, logging.INFO),
        (302, logging.INFO),
        (400, logging.WARNING),
        (404, logging.WARNING),
        (500, logging.ERROR),
        (503, logging.ERROR),
    ])
    def test_log_level_matches_status_code(self, status_code, expected_level):
        """Уровень лога зависит от статус-кода: 2xx/3xx=INFO, 4xx=WARNING, 5xx=ERROR."""
        from unittest.mock import patch
        mw, _ = make_middleware()
        req = self._make_request('/api/test/')
        resp = MagicMock()
        resp.status_code = status_code
        with patch('core.middleware.logger') as mock_logger:
            mw.process_response(req, resp)
        mock_logger.log.assert_called_once()
        actual_level = mock_logger.log.call_args[0][0]
        assert actual_level == expected_level

    def test_without_start_time_duration_is_zero_in_message(self):
        """Без _start_time duration в сообщении = 0.000s."""
        from unittest.mock import patch
        mw, _ = make_middleware()
        req = self._make_request('/api/test/', with_start_time=False)
        resp = MagicMock()
        resp.status_code = 200
        with patch('core.middleware.logger') as mock_logger:
            mw.process_response(req, resp)
        message = mock_logger.log.call_args[0][1]
        assert '0.000s' in message

    def test_log_contains_method_path_and_status(self):
        """Лог содержит метод, путь и статус-код."""
        from unittest.mock import patch
        mw, _ = make_middleware()
        req = self._make_request('/api/interns/', method='POST')
        resp = MagicMock()
        resp.status_code = 201
        with patch('core.middleware.logger') as mock_logger:
            mw.process_response(req, resp)
        message = mock_logger.log.call_args[0][1]
        assert 'POST' in message
        assert '/api/interns/' in message
        assert '201' in message

    def test_log_user_info_from_session_when_user_not_authenticated(self):
        """При неаутентифицированном user и manager_name в сессии лог содержит только имя (без email)."""
        from unittest.mock import patch
        mw, _ = make_middleware()
        req = self._make_request('/api/test/')
        req.user.is_authenticated = False
        req.session = {'manager_email': 'mgr@test.com', 'manager_name': 'Менеджер Тест'}
        resp = MagicMock()
        resp.status_code = 200
        with patch('core.middleware.logger') as mock_logger:
            mw.process_response(req, resp)
        message = mock_logger.log.call_args[0][1]
        assert 'Менеджер Тест' in message
        assert 'mgr@test.com' not in message


# ---------------------------------------------------------------------------
# UserActivityLoggingMiddleware
# ---------------------------------------------------------------------------

class TestUserActivityLoggingMiddleware:
    """Тесты для UserActivityLoggingMiddleware.__call__."""

    def _make_middleware(self, response_status=200):
        get_response = MagicMock(return_value=MagicMock(status_code=response_status))
        return UserActivityLoggingMiddleware(get_response)

    def _make_request(self, method, path='/test/', authenticated=False):
        req = MagicMock()
        req.method = method
        req.path = path
        user = MagicMock()
        user.is_authenticated = authenticated
        user.username = 'tester'
        user.id = 1
        req.user = user
        req.session = {}
        return req

    @pytest.mark.parametrize('method', ['POST', 'PUT', 'PATCH', 'DELETE'])
    def test_mutating_methods_produce_two_log_records(self, caplog, method):
        """POST/PUT/PATCH/DELETE → два лог-сообщения (до и после обработки)."""
        mw = self._make_middleware()
        req = self._make_request(method)
        with caplog.at_level(logging.INFO, logger='user_activity'):
            mw(req)
        assert len(caplog.records) == 2

    def test_get_method_not_logged(self, caplog):
        """GET-запрос → лог не пишется."""
        mw = self._make_middleware()
        req = self._make_request('GET')
        with caplog.at_level(logging.DEBUG, logger='user_activity'):
            mw(req)
        assert not caplog.records

    @pytest.mark.parametrize('excluded_path', [
        '/static/css/main.css',
        '/media/file.jpg',
        '/admin/jsi18n/',
    ])
    def test_excluded_paths_not_logged(self, caplog, excluded_path):
        """Запросы к исключённым путям (/static/, /media/, /admin/jsi18n/) не логируются."""
        mw = self._make_middleware()
        req = self._make_request('POST', path=excluded_path)
        with caplog.at_level(logging.DEBUG, logger='user_activity'):
            mw(req)
        assert not caplog.records

    def test_error_response_logs_at_warning_level(self, caplog):
        """Ответ >= 400 → хотя бы одна запись уровня WARNING."""
        mw = self._make_middleware(response_status=404)
        req = self._make_request('POST')
        with caplog.at_level(logging.DEBUG, logger='user_activity'):
            mw(req)
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    def test_success_response_logs_at_info_level(self, caplog):
        """Ответ 200 → записи уровня INFO."""
        mw = self._make_middleware(response_status=200)
        req = self._make_request('DELETE')
        with caplog.at_level(logging.INFO, logger='user_activity'):
            mw(req)
        assert any(r.levelno == logging.INFO for r in caplog.records)

    def test_user_info_from_session_when_user_not_authenticated(self, caplog):
        """При неаутентифицированном user и manager_name в сессии в логе — только имя (без email)."""
        mw = self._make_middleware()
        req = self._make_request('POST', path='/some/form/', authenticated=False)
        req.session = {'manager_email': 'sess@test.com', 'manager_name': 'Сессионный Менеджер'}
        with caplog.at_level(logging.INFO, logger='user_activity'):
            mw(req)
        assert any('Сессионный Менеджер' in r.message and 'sess@test.com' not in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# ApiAccessLoggingMiddleware._log_api_access
# ---------------------------------------------------------------------------

class TestApiMiddlewareLogApiAccess:
    """Тесты для ApiAccessLoggingMiddleware._log_api_access.

    Используем patch('core.middleware.api_access_logger'), так как 'api_access'
    логгер может быть настроен с propagate=False.
    """

    def _make_middleware(self):
        _, api_mw = make_middleware()
        return api_mw

    def _make_request(self, path='/api/test/', method='GET', params=None):
        req = MagicMock()
        req.path = path
        req.method = method
        req.META = {'REMOTE_ADDR': '127.0.0.1'}
        req.GET = params or {}
        user = MagicMock()
        user.is_authenticated = True
        user.email = 'user@test.com'
        user.full_name = 'Test User'
        user.role = 'manager'
        user.groups = MagicMock()
        user.groups.values_list = MagicMock(return_value=[])
        req.user = user
        return req

    @pytest.mark.parametrize('status_code, log_method', [
        (200, 'info'),
        (201, 'info'),
        (400, 'warning'),
        (404, 'warning'),
        (500, 'error'),
    ])
    def test_log_level_matches_status_code(self, status_code, log_method):
        """Уровень лога _log_api_access зависит от статус-кода ответа."""
        from unittest.mock import patch
        mw = self._make_middleware()
        req = self._make_request()
        response = MagicMock()
        response.status_code = status_code
        with patch('core.middleware.api_access_logger') as mock_logger:
            mw._log_api_access(req, response, 0.1, {})
        getattr(mock_logger, log_method).assert_called_once()

    def test_log_contains_method_and_path(self):
        """Лог содержит метод и путь запроса."""
        from unittest.mock import patch
        mw = self._make_middleware()
        req = self._make_request('/api/interns/', method='POST')
        response = MagicMock()
        response.status_code = 201
        with patch('core.middleware.api_access_logger') as mock_logger:
            mw._log_api_access(req, response, 0.05, {'name': 'Иван'})
        message = mock_logger.info.call_args[0][0]
        assert 'POST' in message
        assert '/api/interns/' in message

    def test_log_includes_body_when_present(self):
        """Если body непустой, в лог добавляется 'body='."""
        from unittest.mock import patch
        mw = self._make_middleware()
        req = self._make_request()
        response = MagicMock()
        response.status_code = 200
        with patch('core.middleware.api_access_logger') as mock_logger:
            mw._log_api_access(req, response, 0.1, {'field': 'value'})
        message = mock_logger.info.call_args[0][0]
        assert 'body=' in message

    def test_log_excludes_body_when_empty(self):
        """Если body пустой, 'body=' не добавляется в лог."""
        from unittest.mock import patch
        mw = self._make_middleware()
        req = self._make_request()
        response = MagicMock()
        response.status_code = 200
        with patch('core.middleware.api_access_logger') as mock_logger:
            mw._log_api_access(req, response, 0.1, {})
        message = mock_logger.info.call_args[0][0]
        assert 'body=' not in message

    def test_log_includes_params_when_present(self):
        """Query params в логе появляются как 'params='."""
        from unittest.mock import patch
        mw = self._make_middleware()
        req = self._make_request(params={'page': ['2']})
        response = MagicMock()
        response.status_code = 200
        with patch('core.middleware.api_access_logger') as mock_logger:
            mw._log_api_access(req, response, 0.1, {})
        message = mock_logger.info.call_args[0][0]
        assert 'params=' in message


# ---------------------------------------------------------------------------
# SQLQueryLoggingMiddleware
# ---------------------------------------------------------------------------

class TestSQLQueryLoggingMiddleware:
    """Тесты для SQLQueryLoggingMiddleware.__call__."""

    def _make_middleware(self):
        get_response = MagicMock(return_value=MagicMock(status_code=200))
        return SQLQueryLoggingMiddleware(get_response)

    def _make_request(self, path='/test/'):
        req = MagicMock()
        req.path = path
        return req

    def test_debug_false_returns_response_directly(self):
        """При DEBUG=False __call__ возвращает результат get_response без логирования."""
        from django.conf import settings
        mw = self._make_middleware()
        req = self._make_request()
        mock_response = MagicMock()
        mw.get_response = MagicMock(return_value=mock_response)
        mock_logger = MagicMock()
        with patch.object(mw, 'logger', mock_logger):
            with patch.object(settings, 'DEBUG', False):
                result = mw(req)
        assert result is mock_response
        mw.get_response.assert_called_once_with(req)
        mock_logger.warning.assert_not_called()
        mock_logger.info.assert_not_called()

    def test_debug_true_few_queries_no_logging(self):
        """При DEBUG=True и ≤20 запросах логер не вызывается."""
        from django.conf import settings
        mw = self._make_middleware()
        req = self._make_request()
        mock_response = MagicMock()
        mw.get_response = MagicMock(return_value=mock_response)
        fake_queries = [{'time': '0.001'} for _ in range(10)]
        mock_connection = MagicMock()
        mock_connection.queries = fake_queries
        mock_connection.queries_log = MagicMock()
        mock_logger = MagicMock()
        with patch.object(mw, 'logger', mock_logger):
            with patch.object(settings, 'DEBUG', True):
                with patch('django.db.connection', mock_connection):
                    result = mw(req)
        assert result is mock_response
        mock_logger.warning.assert_not_called()
        mock_logger.info.assert_not_called()

    def test_debug_true_many_queries_calls_warning(self):
        """При DEBUG=True и >50 запросов вызывается logger.warning с текстом про N+1."""
        from django.conf import settings
        mw = self._make_middleware()
        req = self._make_request('/some/view/')
        mock_response = MagicMock()
        mw.get_response = MagicMock(return_value=mock_response)
        fake_queries = [{'time': '0.001'} for _ in range(51)]
        mock_connection = MagicMock()
        mock_connection.queries = fake_queries
        mock_connection.queries_log = MagicMock()
        mock_logger = MagicMock()
        with patch.object(mw, 'logger', mock_logger):
            with patch.object(settings, 'DEBUG', True):
                with patch('django.db.connection', mock_connection):
                    result = mw(req)
        assert result is mock_response
        mock_logger.warning.assert_called_once()
        call_msg = mock_logger.warning.call_args[0][0]
        assert '51' in call_msg
        assert 'N+1' in call_msg
        assert '/some/view/' in call_msg

    def test_debug_true_medium_queries_calls_info(self):
        """При DEBUG=True и >20 запросов (≤50) вызывается logger.info."""
        from django.conf import settings
        mw = self._make_middleware()
        req = self._make_request('/other/')
        mock_response = MagicMock()
        mw.get_response = MagicMock(return_value=mock_response)
        fake_queries = [{'time': '0.002'} for _ in range(25)]
        mock_connection = MagicMock()
        mock_connection.queries = fake_queries
        mock_connection.queries_log = MagicMock()
        mock_logger = MagicMock()
        with patch.object(mw, 'logger', mock_logger):
            with patch.object(settings, 'DEBUG', True):
                with patch('django.db.connection', mock_connection):
                    result = mw(req)
        assert result is mock_response
        mock_logger.info.assert_called_once()
        call_msg = mock_logger.info.call_args[0][0]
        assert '25' in call_msg
        assert '/other/' in call_msg


class TestStudentRedirectMiddleware:
    """Тесты для StudentRedirectMiddleware: редирект «только студент» на портал."""

    def _make_middleware(self):
        get_response = MagicMock(return_value=MagicMock(status_code=200))
        return StudentRedirectMiddleware(get_response)

    def _request(self, path='/', method='GET', session_data=None):
        req = MagicMock()
        req.method = method
        req.path = path
        req.session = session_data if session_data is not None else {}
        return req

    def test_student_get_root_redirects_to_interns_portal(self):
        """Студент GET / редиректится на портал студентов."""
        session = {
            'keycloak_id': 'uuid-student',
            'keycloak_user': True,
            'manager_groups': ['students'],
            'manager_role': 'manager',
        }
        mw = self._make_middleware()
        result = mw.process_request(self._request('/', session_data=session))
        assert result is not None
        assert result.status_code == 302
        assert result.url == '/interns-portal/'

    def test_student_get_interns_portal_no_redirect(self):
        """Студент GET /interns-portal/ не редиректится."""
        session = {
            'keycloak_id': 'uuid-student',
            'keycloak_user': True,
            'manager_groups': ['students'],
            'manager_role': 'manager',
        }
        mw = self._make_middleware()
        result = mw.process_request(
            self._request('/interns-portal/', session_data=session)
        )
        assert result is None

    def test_student_get_auth_callback_no_redirect(self):
        """Студент GET /auth/callback — не редиректить до обмена code на токены в SPA."""
        session = {
            'keycloak_id': 'uuid-student',
            'keycloak_user': True,
            'manager_groups': ['students'],
            'manager_role': 'student',
        }
        mw = self._make_middleware()
        result = mw.process_request(
            self._request('/auth/callback', session_data=session)
        )
        assert result is None

    def test_student_get_login_no_redirect(self):
        """Студент GET /login — разрешить старт PKCE (zustand может быть пуст при живой Django-сессии)."""
        session = {
            'keycloak_id': 'uuid-student',
            'keycloak_user': True,
            'manager_groups': ['students'],
            'manager_role': 'student',
        }
        mw = self._make_middleware()
        result = mw.process_request(self._request('/login', session_data=session))
        assert result is None

    def test_student_get_no_access_no_redirect(self):
        """Студент GET /no-access — страница «нет доступа» не должна уводить на портал."""
        session = {
            'keycloak_id': 'uuid-student',
            'keycloak_user': True,
            'manager_groups': ['students'],
            'manager_role': 'student',
        }
        mw = self._make_middleware()
        result = mw.process_request(self._request('/no-access', session_data=session))
        assert result is None

    def test_student_get_debts_redirects_to_interns_portal(self):
        """Студент GET /debts/ редиректится на портал."""
        session = {
            'keycloak_id': 'uuid-student',
            'keycloak_user': True,
            'manager_groups': ['students'],
            'manager_role': 'manager',
        }
        mw = self._make_middleware()
        result = mw.process_request(self._request('/debts/', session_data=session))
        assert result is not None
        assert result.status_code == 302
        assert result.url == '/interns-portal/'

    def test_manager_get_root_no_redirect(self):
        """Менеджер GET / не редиректится."""
        session = {
            'keycloak_id': 'uuid-mgr',
            'keycloak_user': True,
            'manager_groups': ['students', 'employment-managers'],
            'manager_role': 'manager',
        }
        mw = self._make_middleware()
        result = mw.process_request(self._request('/', session_data=session))
        assert result is None

    def test_admin_get_root_no_redirect(self):
        """Админ GET / не редиректится."""
        session = {
            'keycloak_id': 'uuid-admin',
            'keycloak_user': True,
            'manager_groups': ['students', 'role_admin'],
            'manager_role': 'admin',
        }
        mw = self._make_middleware()
        result = mw.process_request(self._request('/', session_data=session))
        assert result is None

    def test_no_session_no_redirect(self):
        """Без сессии GET / не редиректится (дальше вью запросит логин)."""
        mw = self._make_middleware()
        result = mw.process_request(self._request('/', session_data={}))
        assert result is None

    def test_no_sso_no_redirect(self):
        """Без keycloak_id в сессии GET / не редиректится."""
        session = {
            'manager_groups': ['students'],
        }
        mw = self._make_middleware()
        result = mw.process_request(self._request('/', session_data=session))
        assert result is None

    def test_post_root_no_redirect(self):
        """POST / не редиректится (только GET)."""
        session = {
            'keycloak_id': 'uuid-student',
            'keycloak_user': True,
            'manager_groups': ['students'],
            'manager_role': 'manager',
        }
        mw = self._make_middleware()
        result = mw.process_request(
            self._request('/', method='POST', session_data=session)
        )
        assert result is None

    def test_student_get_accounts_no_redirect(self):
        """Студент GET /accounts/login/ не редиректится."""
        session = {
            'keycloak_id': 'uuid-student',
            'keycloak_user': True,
            'manager_groups': ['students'],
            'manager_role': 'manager',
        }
        mw = self._make_middleware()
        result = mw.process_request(
            self._request('/accounts/login/', session_data=session)
        )
        assert result is None

    def test_student_get_import_status_no_redirect(self):
        """Студент GET /import/status/<task_id>/ не редиректится (опрос прогресса загрузки видео)."""
        session = {
            'keycloak_id': 'uuid-student',
            'keycloak_user': True,
            'manager_groups': ['students'],
            'manager_role': 'manager',
        }
        mw = self._make_middleware()
        result = mw.process_request(
            self._request('/import/status/abc-123/', session_data=session)
        )
        assert result is None


class TestSessionRoleRepairMiddleware:
    """Тесты SessionRoleRepairMiddleware: синхронизация manager_role с compute_manager_role(groups)."""

    def _make_middleware(self):
        get_response = MagicMock(return_value=MagicMock(status_code=200))
        return SessionRoleRepairMiddleware(get_response)

    def test_hr_and_employment_managers_upgrades_to_manager(self):
        """Сессия с manager_role=hr и группами hrs+employment-managers после middleware получает manager_role=manager."""
        mw = self._make_middleware()
        session = {
            'keycloak_user': True,
            'manager_role': 'hr',
            'manager_groups': ['hrs', 'employment-managers'],
        }
        req = MagicMock()
        req.session = session
        result = mw.process_request(req)
        assert result is None
        assert req.session['manager_role'] == 'manager'

    def test_hr_only_unchanged(self):
        """Сессия только с hrs — роль hr не меняется."""
        mw = self._make_middleware()
        session = {'keycloak_user': True, 'manager_role': 'hr', 'manager_groups': ['hrs']}
        req = MagicMock()
        req.session = session
        mw.process_request(req)
        assert req.session['manager_role'] == 'hr'

    def test_manager_unchanged(self):
        """Сессия с ролью manager не меняется."""
        mw = self._make_middleware()
        session = {'keycloak_user': True, 'manager_role': 'manager', 'manager_groups': ['employment-managers']}
        req = MagicMock()
        req.session = session
        mw.process_request(req)
        assert req.session['manager_role'] == 'manager'

    def test_stale_hr_with_admin_group_becomes_admin(self):
        """Устаревшая роль hr при наличии группы админа в сессии приводится к admin."""
        mw = self._make_middleware()
        session = {
            'keycloak_user': True,
            'manager_role': 'hr',
            'manager_groups': [KEYCLOAK_GROUP_ADMIN, 'hrs'],
        }
        req = MagicMock()
        req.session = session
        mw.process_request(req)
        assert req.session['manager_role'] == 'admin'

    def test_no_keycloak_user_returns_none(self):
        """Без keycloak_user middleware ничего не меняет."""
        mw = self._make_middleware()
        session = {'manager_role': 'hr', 'manager_groups': ['hrs', 'employment-managers']}
        req = MagicMock()
        req.session = session
        mw.process_request(req)
        assert req.session.get('manager_role') == 'hr'


class TestHROutstaffRedirectMiddleware:
    """Тесты HROutstaffRedirectMiddleware: HR и outstaff — только разрешённые URL, иначе редирект на interview_list."""

    def _make_middleware(self):
        get_response = MagicMock(return_value=MagicMock(status_code=200))
        return HROutstaffRedirectMiddleware(get_response)

    def _request(self, path='/', session_data=None, url_name=None):
        req = MagicMock()
        req.path = path
        req.session = session_data if session_data is not None else {}
        req.resolver_match = MagicMock()
        req.resolver_match.url_name = url_name
        return req

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_interview_list_returns_none(self, role):
        """HR/outstaff на interview_list — доступ разрешён (process_view возвращает None)."""
        mw = self._make_middleware()
        req = self._request(path='/', session_data={'manager_role': role}, url_name='interview_list')
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_interviews_database_list_returns_none(self, role):
        """HR/outstaff на маршруте SPA «База собеседований» — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(
            path='/interviews-database',
            session_data={'manager_role': role},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_directions_list_returns_none(self, role):
        """HR/outstaff на маршруте SPA directions — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(
            path='/directions',
            session_data={'manager_role': role},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_sad_intern_list_returns_none(self, role):
        """HR/outstaff на маршруте SPA sad-intern — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(
            path='/sad-intern',
            session_data={'manager_role': role},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_developer_list_returns_none(self, role):
        """HR/outstaff на маршруте SPA developers — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(
            path='/developers',
            session_data={'manager_role': role},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_intern_list_returns_none(self, role):
        """HR/outstaff на маршруте SPA interns — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(
            path='/interns',
            session_data={'manager_role': role},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_managers_list_returns_none(self, role):
        """HR/outstaff на маршруте SPA managers — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(
            path='/managers',
            session_data={'manager_role': role},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_employees_list_returns_none(self, role):
        """HR/outstaff на маршруте SPA employees — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(
            path='/employees',
            session_data={'manager_role': role},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_company_list_returns_none(self, role):
        """HR/outstaff на маршруте SPA companies — доступ разрешён (только просмотр в UI)."""
        mw = self._make_middleware()
        req = self._request(
            path='/companies',
            session_data={'manager_role': role},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_forbidden_company_merge_redirects(self, role):
        """HR/outstaff на company_merge — редирект (merge только менеджеры/админ)."""
        mw = self._make_middleware()
        req = self._request(
            path='/companies/merge',
            session_data={'manager_role': role},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is not None
        assert result.status_code == 302
        assert result.url == reverse('interview_list')

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_path_prefix_accounts_allowed(self, role):
        """HR/outstaff на /accounts/ — разрешено по префиксу (редирект не возвращается)."""
        mw = self._make_middleware()
        req = self._request(
            path='/accounts/logout/',
            session_data={'manager_role': role},
            url_name='logout',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    def test_manager_role_not_hr_like_no_redirect(self):
        """Пользователь с ролью manager — middleware не срабатывает (None)."""
        mw = self._make_middleware()
        req = self._request(
            path='/interns',
            session_data={'manager_role': 'manager'},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_forbidden_interview_create_redirects(self, role):
        """HR/outstaff на interview_create — редирект (только просмотр, без создания)."""
        mw = self._make_middleware()
        req = self._request(
            path='/interviews/new',
            session_data={'manager_role': role},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is not None
        assert result.status_code == 302
        assert result.url == reverse('interview_list')

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_transcription_status(self, role):
        """HR/outstaff на interview_transcription_status — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(
            path='/api/interviews/1/transcription-status/',
            session_data={'manager_role': role},
            url_name='interview-transcription-status',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_transcribe(self, role):
        """HR/outstaff на interview_transcribe — доступ разрешён (запуск транскрипции)."""
        mw = self._make_middleware()
        req = self._request(
            path='/api/interviews/1/transcribe/',
            session_data={'manager_role': role},
            url_name='interview-transcribe',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('url_name', [
        'intern_autocomplete',
        'company_autocomplete',
        'direction_autocomplete',
        'manager_autocomplete',
    ])
    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_autocomplete(self, url_name, role):
        """HR/outstaff на autocomplete — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(session_data={'manager_role': role}, url_name=url_name)
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_api_direction_list(self, role):
        """HR/outstaff на DRF direction-list — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(
            path='/api/directions/',
            session_data={'manager_role': role},
            url_name='direction-list',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('path', [
        '/interviews',
        '/interns',
        '/companies',
        '/managers',
        '/employees',
        '/login',
    ])
    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_react_spa_path_prefix(self, path, role):
        """HR/outstaff на префиксах React SPA из HR_ALLOWED_REACT_PATH_PREFIXES — без редиректа."""
        mw = self._make_middleware()
        req = self._request(path=path, session_data={'manager_role': role}, url_name='not_in_whitelist')
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_api_interviews_database_list(self, role):
        """HR/outstaff на DRF api_interviews_database_list — доступ разрешён (React «База собеседований»)."""
        mw = self._make_middleware()
        req = self._request(
            path='/api/interviews-database/',
            session_data={'manager_role': role},
            url_name='api_interviews_database_list',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('url_name', [
        'employees-managers-list',
        'employees-manager-board',
        'weekly-status-list',
        'weekly-status-detail',
    ])
    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_employees_api(self, url_name, role):
        """HR/outstaff на DRF-эндпоинтах раздела «Сотрудники» — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(
            path='/api/employees/',
            session_data={'manager_role': role},
            url_name=url_name,
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('url_name', [
        'sad-intern-list',
        'sad-intern-detail',
        'sad-intern-grouped',
        'sad-intern-on-project',
        'api_sad_intern_analytics',
    ])
    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_sad_intern_api(self, url_name, role):
        """HR/outstaff на DRF-эндпоинтах раздела «Грустят» — доступ разрешён."""
        mw = self._make_middleware()
        req = self._request(
            path='/api/sad-interns/',
            session_data={'manager_role': role},
            url_name=url_name,
        )
        result = mw.process_view(req, None, (), {})
        assert result is None

    @pytest.mark.parametrize('role', ['hr', 'outstaff'])
    def test_hr_like_allowed_api_developer_stats(self, role):
        """HR/outstaff на DRF api-developer-stats — доступ разрешён (React «Разработчики»)."""
        mw = self._make_middleware()
        req = self._request(
            path='/api/developers/',
            session_data={'manager_role': role},
            url_name='api-developer-stats',
        )
        result = mw.process_view(req, None, (), {})
        assert result is None


class TestMentorRedirectMiddleware:
    """Тесты MentorRedirectMiddleware: mentor — только «База собеседований» и whitelist API."""

    def _make_middleware(self):
        from core.middleware import MentorRedirectMiddleware

        get_response = MagicMock(return_value=MagicMock(status_code=200))
        return MentorRedirectMiddleware(get_response)

    def _request(self, path='/', session_data=None, url_name=None):
        req = MagicMock()
        req.path = path
        req.session = session_data if session_data is not None else {}
        req.resolver_match = MagicMock()
        req.resolver_match.url_name = url_name
        return req

    def test_mentor_allowed_interviews_database_spa_returns_none(self):
        mw = self._make_middleware()
        req = self._request(
            path='/interviews-database',
            session_data={'manager_role': 'mentor'},
            url_name='react_spa_catchall',
        )
        assert mw.process_view(req, None, (), {}) is None

    def test_mentor_allowed_api_interviews_database_list(self):
        mw = self._make_middleware()
        req = self._request(
            path='/api/interviews-database/',
            session_data={'manager_role': 'mentor'},
            url_name='api_interviews_database_list',
        )
        assert mw.process_view(req, None, (), {}) is None

    def test_mentor_blocked_interviews_spa_redirects(self):
        mw = self._make_middleware()
        req = self._request(
            path='/interviews',
            session_data={'manager_role': 'mentor'},
            url_name='react_spa_catchall',
        )
        result = mw.process_view(req, None, (), {})
        assert result is not None
        assert result['Location'] == '/interviews-database/'

    def test_mentor_blocked_api_interns_redirects(self):
        mw = self._make_middleware()
        req = self._request(
            path='/api/interns/',
            session_data={'manager_role': 'mentor'},
            url_name='intern-list',
        )
        result = mw.process_view(req, None, (), {})
        assert result is not None
        assert result['Location'] == '/interviews-database/'

    def test_mentor_allowed_api_transcribe(self):
        mw = self._make_middleware()
        req = self._request(
            path='/api/interviews/1/transcribe/',
            session_data={'manager_role': 'mentor'},
            url_name='interview-transcribe',
        )
        assert mw.process_view(req, None, (), {}) is None

    def test_manager_role_not_affected(self):
        mw = self._make_middleware()
        req = self._request(
            path='/interviews',
            session_data={'manager_role': 'manager'},
            url_name='react_spa_catchall',
        )
        assert mw.process_view(req, None, (), {}) is None
