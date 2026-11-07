from rest_framework.permissions import BasePermission

from accounts.authentication import KeycloakUser
from accounts.sso_user import compute_manager_role
from core.constants import (
    KEYCLOAK_GROUP_STUDENTS,
    KEYCLOAK_MANAGER_GROUPS,
    KEYCLOAK_ROLE_ADMIN,
    KEYCLOAK_ROLE_HR,
    KEYCLOAK_ROLE_MENTOR,
    KEYCLOAK_ROLE_NO_ACCESS,
    KEYCLOAK_ROLE_OUTSTAFF,
    KEYCLOAK_ROLE_STUDENT,
)


class IsKeycloakAuthenticated(BasePermission):
    """Пользователь вошёл локальной сессией (любая роль)."""

    message = 'Требуется вход.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and hasattr(request.user, 'is_authenticated')
            and request.user.is_authenticated
        )


class IsAdminRole(BasePermission):
    """Только администраторы (группа role_admin) или Django-суперпользователи."""

    message = 'Доступ разрешён только администраторам.'

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return False
        if getattr(request.user, 'is_superuser', False):
            return True
        return bool(getattr(request.user, 'is_admin', False))


class IsAdminOrMentorRole(BasePermission):
    """Администраторы или менторы (запуск транскрипции на «База собеседований»)."""

    message = 'Запуск транскрипции доступен администраторам и менторам.'

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return False
        if getattr(request.user, 'is_superuser', False):
            return True
        if getattr(request.user, 'is_admin', False):
            return True
        return bool(getattr(request.user, 'is_mentor', False))


class IsInterviewWriteRole(BasePermission):
    """
    Создание, изменение и удаление собеседований: admin и manager.
    Как core.context_processors.can_write для шаблонов (не HR/outstaff-only).
    """

    message = 'Создание и редактирование собеседований доступны только администраторам и менеджерам.'

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return False
        if getattr(request.user, 'is_superuser', False):
            return True
        groups = list(getattr(request.user, 'groups', None) or [])
        role, _, _, _, _, _ = compute_manager_role(groups)
        if role in (
            KEYCLOAK_ROLE_HR,
            KEYCLOAK_ROLE_OUTSTAFF,
            KEYCLOAK_ROLE_MENTOR,
            KEYCLOAK_ROLE_STUDENT,
            KEYCLOAK_ROLE_NO_ACCESS,
        ):
            return False
        return role in (KEYCLOAK_ROLE_ADMIN, 'manager')


class IsManagerOrAdmin(BasePermission):
    """Менеджеры любой группы, HR, outstaff, менторы, администраторы или Django-суперпользователи."""

    message = 'Доступ разрешён только менеджерам, HR, outstaff, менторам и администраторам.'

    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_authenticated'):
            return False
        if not request.user.is_authenticated:
            return False

        # Django-суперпользователь
        if getattr(request.user, 'is_superuser', False):
            return True

        # Keycloak-администратор всегда имеет доступ
        if getattr(request.user, 'is_admin', False):
            return True

        # HR (группа hrs) — доступ к read-only API (ограничение URL в middleware для веб)
        if getattr(request.user, 'is_hr', False):
            return True

        # Outstaff — те же права на API, что у HR
        if getattr(request.user, 'is_outstaff', False):
            return True

        # Менторы — read-only API в рамках whitelist middleware
        if getattr(request.user, 'is_mentor', False):
            return True

        # Любой менеджер из известных групп
        user_groups = set(getattr(request.user, 'groups', []))
        return bool(user_groups & KEYCLOAK_MANAGER_GROUPS)


class IsEmploymentManager(BasePermission):
    """Менеджеры по найму (employment-managers) или администраторы."""

    message = 'Доступ разрешён только employment-managers и администраторам.'

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return False
        if getattr(request.user, 'is_admin', False):
            return True
        return getattr(request.user, 'is_employment_manager', False)


class IsCVManager(BasePermission):
    """CV-менеджеры (cv-managers) или администраторы."""

    message = 'Доступ разрешён только cv-managers и администраторам.'

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return False
        if getattr(request.user, 'is_admin', False):
            return True
        return getattr(request.user, 'is_cv_manager', False)


class IsEducationManager(BasePermission):
    """Менеджеры обучения (education) или администраторы."""

    message = 'Доступ разрешён только education-менеджерам и администраторам.'

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return False
        if getattr(request.user, 'is_admin', False):
            return True
        return getattr(request.user, 'is_education_manager', False)


class IsReadOnlyHROutstaff(BasePermission):
    """
    HR, outstaff и mentor — только безопасные методы (GET, HEAD, OPTIONS).
    Для выравнивания API с can_write=False на вебе.
    """

    message = 'HR, outstaff и менторы могут только просматривать данные.'

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        user = request.user
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        if isinstance(user, KeycloakUser):
            if getattr(user, 'is_hr', False) or getattr(user, 'is_outstaff', False):
                if not getattr(user, 'is_admin', False):
                    return False
            if getattr(user, 'is_mentor', False):
                if not getattr(user, 'is_admin', False):
                    return False
        return True


class IsInternPortalStudent(BasePermission):
    """
    Только «чистый» студент портала: группа students, без админских и менеджерских групп.
    """

    message = 'Доступ разрешён только студентам портала.'

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return False
        groups = set(getattr(request.user, 'groups', []) or [])
        if KEYCLOAK_GROUP_STUDENTS not in groups:
            return False
        if getattr(request.user, 'is_admin', False):
            return False
        if groups & KEYCLOAK_MANAGER_GROUPS:
            return False
        return True
