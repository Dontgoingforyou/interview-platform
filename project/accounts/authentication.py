"""Сессионная аутентификация по демо-входу.

Пользователь API — KeycloakUser, собранный из полей сессии.
Внешний SSO не используется.
"""
import logging

from rest_framework.authentication import BaseAuthentication

from .sso_user import compute_manager_role, normalize_keycloak_groups
from core.constants import (
    KEYCLOAK_GROUP_ADMIN,
    KEYCLOAK_GROUP_CV,
    KEYCLOAK_GROUP_EDUCATION,
    KEYCLOAK_GROUP_EMPLOYMENT,
    KEYCLOAK_GROUP_HR,
    KEYCLOAK_GROUP_MENTORS,
    KEYCLOAK_GROUP_OUTSTAFF,
    KEYCLOAK_GROUP_STUDENTS,
)

logger = logging.getLogger(__name__)


class KeycloakUser:
    """
    Объект пользователя для DRF, собранный из сессии локального входа.

    Используется вместо стандартного Django User: демо-учётки не лежат в таблице auth_user.
    """

    def __init__(self, user_info: dict):
        self.email = user_info.get('email', '')
        self.username = user_info.get('username', '')
        self.full_name = user_info.get('full_name', '')
        self.groups = normalize_keycloak_groups(user_info.get('groups', []))
        self.role, _, _, _, _, _ = compute_manager_role(self.groups)

        # DRF UserRateThrottle и совместимость с Django User API
        self.pk = self.email or self.username or 'keycloak-user'
        self.is_superuser = False

        # Производные флаги доступа
        self.is_admin = KEYCLOAK_GROUP_ADMIN in self.groups
        self.is_employment_manager = KEYCLOAK_GROUP_EMPLOYMENT in self.groups
        self.is_cv_manager = KEYCLOAK_GROUP_CV in self.groups
        self.is_education_manager = KEYCLOAK_GROUP_EDUCATION in self.groups
        self.is_student = KEYCLOAK_GROUP_STUDENTS in self.groups
        self.is_hr = KEYCLOAK_GROUP_HR in self.groups
        self.is_outstaff = KEYCLOAK_GROUP_OUTSTAFF in self.groups
        self.is_mentor = KEYCLOAK_GROUP_MENTORS in self.groups

        # Совместимость с DRF
        self.is_authenticated = True
        self.is_active = True

    def __str__(self):
        return f'{self.full_name} ({self.email})'


class KeycloakSessionAuthentication(BaseAuthentication):
    """Пользователь из сессии, которую заполнил локальный вход."""

    def authenticate(self, request):
        if not request.session.get('keycloak_user'):
            return None
        email = request.session.get('manager_email')
        if not email:
            return None
        user_info = {
            'email': email,
            'username': request.session.get('manager_username') or email,
            'full_name': request.session.get('manager_name', ''),
            'groups': list(request.session.get('manager_groups') or []),
        }
        user = KeycloakUser(user_info)
        return (user, None)

    def authenticate_header(self, request):
        return 'Session'


API_VIEW_AUTHENTICATION_CLASSES = (
    KeycloakSessionAuthentication,
)
