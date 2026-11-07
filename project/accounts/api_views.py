"""Локальный вход для React SPA."""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .demo_users import authenticate_demo
from .sso_user import complete_local_login_session, spa_path_after_pkce_login

logger = logging.getLogger(__name__)


class SpaAuthThrottle(AnonRateThrottle):
    """Лимит по IP для входа (30 запросов/мин)."""

    scope = 'spa_auth'


class LoginView(APIView):
    """POST: логин и пароль демо-учётки, сессия Django."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [SpaAuthThrottle]
    parser_classes = [JSONParser]

    @extend_schema(
        summary='Локальный вход',
        tags=['Авторизация'],
    )
    def post(self, request, *args, **kwargs):
        username = request.data.get('username') or ''
        password = request.data.get('password') or ''
        account = authenticate_demo(username, password)
        if account is None:
            return Response(
                {'detail': 'Неверный логин или пароль'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user_payload = complete_local_login_session(request, account)
        return Response(
            {
                'expires_in': 60 * 60 * 12,
                'user': user_payload,
                'redirect_after_login': spa_path_after_pkce_login(user_payload['groups']),
            },
            status=status.HTTP_200_OK,
        )
