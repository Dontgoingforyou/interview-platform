import hashlib
import json
import logging
from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages

logger = logging.getLogger(__name__)

ANALYTICS_CACHE_TIMEOUT = 60 * 15  # 15 минут


def get_analytics_cache_key(view_name: str, params: dict | None = None) -> str:
    """Возвращает ключ Redis-кэша для аналитического endpoint'а."""
    params_str = json.dumps(sorted((params or {}).items()), ensure_ascii=False)
    key_raw = f"analytics:{view_name}:{params_str}"
    return "analytics:" + hashlib.md5(key_raw.encode()).hexdigest()


def cache_analytics(timeout=ANALYTICS_CACHE_TIMEOUT):
    """
    Кэширует JSON-ответ аналитического endpoint'а в Redis.
    Ключ кэша строится из имени функции + GET-параметров запроса.
    Применять ПОСЛЕ @manager_required_api.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            params_str = json.dumps(sorted(request.GET.items()), ensure_ascii=False)
            key_raw = f"analytics:{view_func.__name__}:{params_str}"
            cache_key = "analytics:" + hashlib.md5(key_raw.encode()).hexdigest()

            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return JsonResponse(cached_data, safe=False)

            response = view_func(request, *args, **kwargs)

            if response.status_code == 200:
                cache.set(cache_key, json.loads(response.content), timeout)

            return response
        return wrapper
    return decorator


def manager_required_api(view_func):
    """Декоратор для функций-представлений API, требующих SSO авторизации."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Проверяем наличие SSO авторизации
        has_sso_auth = request.session.get('keycloak_user')

        if not has_sso_auth:
            return JsonResponse({'error': 'Требуется авторизация'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def login_required_custom(view_func):
    """
    Декоратор для защиты views, требующих SSO авторизации.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Проверяем наличие SSO авторизации
        has_sso_auth = request.session.get('keycloak_user')

        if not has_sso_auth:
            messages.warning(request, 'Для доступа к этой странице необходима авторизация')
            return redirect('login')

        return view_func(request, *args, **kwargs)
    return wrapper
