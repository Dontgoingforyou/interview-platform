import json
import logging
import time
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from core.constants import (
    HR_ALLOWED_REACT_PATH_PREFIXES,
    HR_OUTSTAFF_ALLOWED_PATH_PREFIXES,
    HR_OUTSTAFF_ALLOWED_URL_NAMES,
    HR_OUTSTAFF_BLOCKED_SPA_PATH_PREFIXES,
    KEYCLOAK_GROUP_STUDENTS,
    KEYCLOAK_MANAGER_GROUPS,
    KEYCLOAK_ROLE_ADMIN,
    KEYCLOAK_ROLE_HR,
    KEYCLOAK_ROLE_MENTOR,
    KEYCLOAK_ROLE_OUTSTAFF,
    MENTOR_ALLOWED_PATH_PREFIXES,
    MENTOR_ALLOWED_REACT_PATH_PREFIXES,
    MENTOR_ALLOWED_URL_NAMES,
)
logger = logging.getLogger('django.request')
api_access_logger = logging.getLogger('api_access')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware для логирования всех HTTP запросов.
    Логирует:
    - Метод и путь запроса
    - Пользователя (если авторизован)
    - IP адрес клиента
    - Время выполнения запроса
    - Статус ответа
    """

    def process_request(self, request):
        """Сохраняет время начала обработки запроса."""
        request._start_time = time.time()
        return None

    def process_response(self, request, response):
        """Логирует информацию о запросе и ответе."""
        # Пропускаем логирование статики и media файлов
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return response

        # Вычисляем время выполнения
        duration = 0
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time

        # Получаем информацию о пользователе
        user_info = 'Anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = f"{request.user.username} (ID: {request.user.id})"
        elif hasattr(request, 'session') and request.session.get('manager_name'):
            user_info = request.session.get('manager_name', 'Unknown')

        # Получаем IP адрес
        ip_address = self.get_client_ip(request)

        # Определяем уровень логирования в зависимости от статус кода
        status_code = response.status_code
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        # Логируем запрос
        logger.log(
            log_level,
            f"{request.method} {request.path} | "
            f"Status: {status_code} | "
            f"User: {user_info} | "
            f"IP: {ip_address} | "
            f"Duration: {duration:.3f}s"
        )

        return response

    def get_client_ip(self, request):
        """Получает IP адрес клиента из запроса."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip


# Префиксы путей, на которые студента не редиректим
_STUDENT_REDIRECT_ALLOWED_PREFIXES = (
    '/interns-portal',
    '/login',  # старт PKCE в SPA (иначе цикл: нет токена в zustand → /login → редирект на портал)
    '/auth/',  # OAuth callback React (/auth/callback) — иначе 302 на портал до обмена code на токены
    '/no-access',
    '/accounts/',
    '/admin/',
    '/static/',
    '/media/',
    '/api/',
    '/import/',
)


class StudentRedirectMiddleware(MiddlewareMixin):
    """
    Редирект пользователя «только студент» (SSO + группа students, без admin/manager)
    на портал студентов при заходе на любую страницу вне белого списка.
    После закрытия вкладки и перезахода студент по умолчанию попадает на «Мои собеседования».
    """

    def process_request(self, request):
        if request.method != 'GET':
            return None
        session = getattr(request, 'session', None)
        if not session:
            return None
        if not session.get('keycloak_user'):
            return None
        groups = session.get('manager_groups') or []
        if KEYCLOAK_GROUP_STUDENTS not in groups:
            return None
        if session.get('manager_role') == KEYCLOAK_ROLE_ADMIN:
            return None
        if session.get('manager_role') == KEYCLOAK_ROLE_MENTOR:
            return None
        if set(groups) & KEYCLOAK_MANAGER_GROUPS:
            return None
        path = request.path
        if path != '/' and not path.startswith('/interns-portal'):
            if any(path.startswith(p) for p in _STUDENT_REDIRECT_ALLOWED_PREFIXES):
                return None
        elif path.startswith('/interns-portal'):
            return None
        return redirect('/interns-portal/')


class SessionRoleRepairMiddleware(MiddlewareMixin):
    """
    Синхронизирует manager_role в сессии с compute_manager_role(manager_groups).

    Покрывает: hrs + employment-managers (должна быть роль manager), появление группы admin
    до повторного полного логина, прочий рассинхрон поля роли и списка групп.
    """

    def process_request(self, request):
        session = getattr(request, 'session', None)
        if not session or not session.get('keycloak_user'):
            return None
        groups = session.get('manager_groups') or []
        if not groups:
            return None
        from accounts.sso_user import compute_manager_role

        canonical_role, _, _, _, _, _ = compute_manager_role(groups)
        if session.get('manager_role') != canonical_role:
            session['manager_role'] = canonical_role
        return None


class HROutstaffRedirectMiddleware(MiddlewareMixin):
    """
    Ограничивает доступ ролей HR и outstaff только разрешёнными разделами (см. HR_OUTSTAFF_ALLOWED_*).
    Создание, редактирование, удаление и импорт скрываются через can_write в шаблонах.
    Редирект на список собеседований при заходе на запрещённый URL.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        role = request.session.get('manager_role')
        if role not in (KEYCLOAK_ROLE_HR, KEYCLOAK_ROLE_OUTSTAFF):
            return None
        path = request.path
        if any(path.startswith(blocked) for blocked in HR_OUTSTAFF_BLOCKED_SPA_PATH_PREFIXES):
            return redirect(reverse('interview_list'))
        if any(path.startswith(prefix) for prefix in HR_ALLOWED_REACT_PATH_PREFIXES):
            return None
        if any(path.startswith(prefix) for prefix in HR_OUTSTAFF_ALLOWED_PATH_PREFIXES):
            return None
        resolver_match = getattr(request, 'resolver_match', None)
        if resolver_match and resolver_match.url_name in HR_OUTSTAFF_ALLOWED_URL_NAMES:
            return None
        return redirect(reverse('interview_list'))


class MentorRedirectMiddleware(MiddlewareMixin):
    """
    Ограничивает доступ роли mentor только «База собеседований» и связанными read-only API.
    Иначе редирект на /interviews-database/.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        role = request.session.get('manager_role')
        if role != KEYCLOAK_ROLE_MENTOR:
            return None
        path = request.path
        if any(path.startswith(prefix) for prefix in MENTOR_ALLOWED_REACT_PATH_PREFIXES):
            return None
        if any(path.startswith(prefix) for prefix in MENTOR_ALLOWED_PATH_PREFIXES):
            return None
        resolver_match = getattr(request, 'resolver_match', None)
        if resolver_match and resolver_match.url_name in MENTOR_ALLOWED_URL_NAMES:
            return None
        return redirect('/interviews-database/')


class UserActivityLoggingMiddleware:
    """
    Middleware для логирования активности пользователей.
    Логирует только модифицирующие операции (POST, PUT, PATCH, DELETE).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('user_activity')

    def __call__(self, request):
        # Логируем до обработки запроса (если это модифицирующий метод)
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            self.log_user_activity(request, 'before')

        response = self.get_response(request)

        # Логируем после обработки запроса
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            self.log_user_activity(request, 'after', response)

        return response

    def log_user_activity(self, request, stage, response=None):
        """Логирует активность пользователя."""
        # Пропускаем логирование для некоторых путей
        excluded_paths = ['/static/', '/media/', '/admin/jsi18n/']
        if any(request.path.startswith(path) for path in excluded_paths):
            return

        # Получаем информацию о пользователе
        user_info = 'Anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = f"{request.user.username} (ID: {request.user.id})"
        elif hasattr(request, 'session') and request.session.get('manager_name'):
            user_info = request.session.get('manager_name', 'Unknown')

        # Формируем сообщение
        if stage == 'before':
            message = f"[{request.method}] {user_info} запросил {request.path}"
        else:
            status_code = response.status_code if response else 'Unknown'
            message = f"[{request.method}] {user_info} завершил {request.path} с кодом {status_code}"

        # Определяем уровень логирования
        if response and response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        self.logger.log(log_level, message)


class ApiAccessLoggingMiddleware:
    """
    Middleware для детального логирования обращений к API.

    Логирует все запросы к /api/ — кто (пользователь, IP), что (метод, путь, параметры),
    как (тело запроса для мутирующих операций), результат (статус, время).

    Особенно полезен для отслеживания активности MCP-сервера и внешних интеграций.
    """

    # Поля, которые не логируем в теле запроса
    SENSITIVE_FIELDS = {'password', 'token', 'secret', 'key', 'authorization'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/api/'):
            return self.get_response(request)

        start_time = time.time()
        request_body = self._get_request_body(request)
        response = None

        try:
            response = self.get_response(request)
            return response
        except Exception:
            raise
        finally:
            duration = time.time() - start_time
            if response is not None:
                self._log_api_access(request, response, duration, request_body)
            else:
                # Необработанное исключение: логируем как 500 без тела ответа
                self._log_api_access_error(request, duration, request_body)

    def _get_user_info(self, request) -> dict:
        """Извлекает информацию о пользователе из запроса (Keycloak или сессия)."""
        user = getattr(request, 'user', None)

        if user and getattr(user, 'is_authenticated', False):
            email = getattr(user, 'email', '') or getattr(user, 'username', '')
            full_name = getattr(user, 'full_name', '') or getattr(user, 'get_full_name', lambda: '')()
            role = getattr(user, 'role', '')
            groups = getattr(user, 'groups', [])
            if hasattr(groups, 'all'):
                groups = list(groups.values_list('name', flat=True))  # type: ignore[union-attr]
            return {
                'email': email,
                'full_name': full_name,
                'role': role,
                'groups': groups,
            }

        session = getattr(request, 'session', None)
        if session:
            manager_email = session.get('manager_email')
            if manager_email:
                return {
                    'email': manager_email,
                    'full_name': session.get('manager_name', ''),
                    'role': 'manager',
                    'groups': [],
                }

        return {'email': 'anonymous', 'full_name': '', 'role': '', 'groups': []}

    def _get_client_ip(self, request) -> str:
        """Возвращает IP-адрес клиента с учётом прокси."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')

    def _get_request_body(self, request) -> dict:
        """Безопасно читает и фильтрует тело запроса (только JSON)."""
        if request.method not in ('POST', 'PUT', 'PATCH'):
            return {}

        # Multipart-запросы (загрузка файлов) — не читаем: тело большое,
        # файл бинарный, и чтение request.body здесь конкурирует с DRF MultiPartParser.
        content_type = request.META.get('CONTENT_TYPE', '')
        if 'multipart/form-data' in content_type:
            return {}

        try:
            body = request.body
            if not body:
                return {}
            data = json.loads(body)
            if isinstance(data, dict):
                return {
                    k: '***' if k.lower() in self.SENSITIVE_FIELDS else v
                    for k, v in data.items()
                }
            return {'raw': str(data)[:200]}
        except (json.JSONDecodeError, Exception):
            return {}

    def _get_query_params(self, request) -> dict:
        """Возвращает query-параметры запроса."""
        params = dict(request.GET)
        return {k: v[0] if len(v) == 1 else v for k, v in params.items()}

    def _log_api_access(self, request, response, duration: float, request_body: dict):
        """Формирует и записывает лог API-запроса."""
        user_info = self._get_user_info(request)
        ip = self._get_client_ip(request)
        status_code = response.status_code
        query_params = self._get_query_params(request)

        user_str = user_info['email']
        if user_info.get('full_name'):
            user_str = f"{user_info['full_name']} ({user_info['email']})"
        if user_info.get('role'):
            user_str += f" [{user_info['role']}]"

        parts = [
            f"[API] {request.method} {request.path}",
            f"user={user_str}",
            f"ip={ip}",
            f"status={status_code}",
            f"time={duration:.3f}s",
        ]

        if query_params:
            parts.append(f"params={query_params}")

        if request_body:
            parts.append(f"body={request_body}")

        message = ' | '.join(parts)

        if status_code >= 500:
            api_access_logger.error(message)
        elif status_code >= 400:
            api_access_logger.warning(message)
        else:
            api_access_logger.info(message)

    def _log_api_access_error(self, request, duration: float, request_body: dict):
        """Логирует API-запрос завершившийся необработанным исключением (нет объекта response)."""
        user_info = self._get_user_info(request)
        ip = self._get_client_ip(request)
        parts = [
            f"[API] {request.method} {request.path}",
            f"user={user_info['email']}",
            f"ip={ip}",
            'status=500_UNHANDLED_EXCEPTION',
            f"time={duration:.3f}s",
        ]
        if request_body:
            parts.append(f"body={request_body}")
        api_access_logger.error(' | '.join(parts))


class SQLQueryLoggingMiddleware(MiddlewareMixin):
    """
    Middleware для логирования SQL запросов (только в DEBUG режиме).
    Внимание: использовать только в development, может существенно замедлить приложение.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django.db.backends')

    def __call__(self, request):
        from django.conf import settings
        from django.db import connection

        # Включаем только в DEBUG режиме
        if not settings.DEBUG:
            return self.get_response(request)

        # Сбрасываем счетчик запросов
        connection.queries_log.clear() if hasattr(connection, 'queries_log') else None

        response = self.get_response(request)

        # Логируем количество SQL запросов
        if hasattr(connection, 'queries'):
            query_count = len(connection.queries)
            total_time = sum(float(q['time']) for q in connection.queries)

            if query_count > 50:  # Предупреждение о большом количестве запросов
                self.logger.warning(
                    f"{request.path} выполнил {query_count} SQL запросов "
                    f"за {total_time:.3f}s (возможна N+1 проблема)"
                )
            elif query_count > 20:
                self.logger.info(
                    f"{request.path} выполнил {query_count} SQL запросов "
                    f"за {total_time:.3f}s"
                )

        return response
