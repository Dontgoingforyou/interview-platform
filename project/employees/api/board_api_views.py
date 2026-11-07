from urllib.parse import unquote

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsManagerOrAdmin
from core.intern_utils import transliterate_name_to_cyrillic
from managers.models import Manager

from ..board_serialization import serialize_manager_board
from ..services import ManagerDetailService, get_managers_for_employees_list


def _manager_to_list_item(manager) -> dict:
    raw = manager.full_name or ''
    display_name = transliterate_name_to_cyrillic(raw) or raw
    return {
        'email': manager.email,
        'full_name': display_name,
    }


class EmployeeManagersListAPIView(APIView):
    """Список активных менеджеров с менеджерскими группами Keycloak."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    @extend_schema(
        summary='Менеджеры для раздела «Сотрудники»',
        description=(
            'Список активных менеджеров, у которых есть хотя бы одна группа из KEYCLOAK_MANAGER_GROUPS. '
            'Аналог страницы списка сотрудников в Django.'
        ),
        tags=['Менеджеры'],
    )
    def get(self, request):
        managers = get_managers_for_employees_list()
        return Response([_manager_to_list_item(m) for m in managers])


class ManagerBoardAPIView(APIView):
    """Полные данные таблицы сотрудников менеджера (52 недели, коэффициенты, месяцы)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    @extend_schema(
        summary='Доска менеджера (студенты и недели)',
        description=(
            'Возвращает сериализованный контекст ManagerDetailService для отображения в React. '
            'Email в пути — один сегмент (рекомендуется URL-encoding, например user%40domain.com).'
        ),
        tags=['Менеджеры'],
    )
    def get(self, request, email: str):
        decoded = unquote(email)
        manager = get_object_or_404(
            Manager.objects.filter(is_active=True),
            email=decoded,
        )
        context = ManagerDetailService().get_context(manager)
        return Response(serialize_manager_board(manager, context))
