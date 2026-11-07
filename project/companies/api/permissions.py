from rest_framework.permissions import BasePermission

from accounts.permissions import IsAdminRole, IsManagerOrAdmin
from core.constants import KEYCLOAK_MANAGER_GROUPS


class IsCompanyEditor(BasePermission):
    """
    Создание, изменение и объединение: менеджеры из KEYCLOAK_MANAGER_GROUPS и администраторы.
    HR и outstaff — только просмотр (как в шаблонах с can_write).
    """

    message = 'Редактирование компаний доступно только менеджерам и администраторам.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_admin', False):
            return True
        if getattr(user, 'is_hr', False) or getattr(user, 'is_outstaff', False):
            return False
        user_groups = set(getattr(user, 'groups', []))
        return bool(user_groups & KEYCLOAK_MANAGER_GROUPS)


class CompanyViewSetPermissionMixin:
    """Композиция прав: чтение — IsManagerOrAdmin; запись — IsCompanyEditor; удаление — IsAdminRole."""

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'head', 'options'):
            return [IsManagerOrAdmin()]
        if self.action == 'destroy':
            return [IsAdminRole()]
        return [IsCompanyEditor()]
