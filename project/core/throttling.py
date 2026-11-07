"""DRF throttling для security-sensitive эндпоинтов."""

import logging

from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle

logger = logging.getLogger(__name__)


class _RedisFallbackMixin:
    """
    Если Redis недоступен — пропускаем запрос с предупреждением вместо 500.

    DRF's SimpleRateThrottle.allow_request() не ловит ошибки кэша,
    поэтому redis.exceptions.ConnectionError / RedisError прорывается наружу,
    проходит мимо DRF handle_exception (не APIException) и вызывает 500 без логов.
    """

    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as exc:
            logger.warning(
                'Throttle: ошибка кэша Redis (%s), пропускаем throttle для %s %s: %s',
                self.__class__.__name__,
                request.method,
                request.path,
                exc,
            )
            return True


def _throttle_ident(request) -> str:
    """Идентификатор для rate limit: пользователь сессии или IP."""
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        return str(
            getattr(user, 'pk', None)
            or getattr(user, 'email', None)
            or 'auth-user',
        )
    return AnonRateThrottle().get_ident(request)


class PortalUploadThrottle(_RedisFallbackMixin, UserRateThrottle):
    """Лимит загрузки видео на портале студента."""

    scope = 'portal_upload'

    def get_cache_key(self, request, view):
        if request.user and getattr(request.user, 'is_authenticated', False):
            return self.cache_format % {'scope': self.scope, 'ident': _throttle_ident(request)}
        return super().get_cache_key(request, view)


class ApiUserRateThrottle(_RedisFallbackMixin, UserRateThrottle):
    """Общий лимит для аутентифицированных API-запросов (Keycloak)."""

    scope = 'api_user'

    def get_cache_key(self, request, view):
        if request.user and getattr(request.user, 'is_authenticated', False):
            return self.cache_format % {'scope': self.scope, 'ident': _throttle_ident(request)}
        return super().get_cache_key(request, view)


class SpaAuthThrottle(_RedisFallbackMixin, SimpleRateThrottle):
    """Лимит для публичных SSO/PKCE эндпоинтов."""

    scope = 'spa_auth'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}
