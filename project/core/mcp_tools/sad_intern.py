"""MCP-тулы: «Грустят»."""
from __future__ import annotations

from typing import Any

from sad_intern.drf_list_query import apply_list_filters, sad_intern_role_scoped_qs
from sad_intern.models import SadIntern
from sad_intern.serializers import SadInternCreateUpdateSerializer, SadInternDetailSerializer, SadInternListSerializer

from core.mcp_tools._common import (
    MAX_PAGE_SIZE,
    can_interview_write,
    deny,
    is_admin_user,
    is_hr_or_outstaff,
    page_bounds,
    tool_text,
    validation_error,
)


def tool_list_sad_interns(request, arguments: dict[str, Any]) -> dict[str, Any]:
    qs = sad_intern_role_scoped_qs(request.user)
    qs = apply_list_filters(
        qs,
        arguments,
        waiting=True,
        allow_manager_email_filter=is_admin_user(request.user) or is_hr_or_outstaff(request.user),
    )
    start, page_size = page_bounds(arguments)
    total = qs.count()
    rows = SadInternListSerializer(qs[start:start + page_size], many=True).data
    return tool_text({'count': total, 'results': rows})


def tool_get_sad_intern(request, arguments: dict[str, Any]) -> dict[str, Any]:
    pk = arguments.get('id')
    if pk is None:
        return tool_text({'error': 'Нужен id записи'}, is_error=True)
    obj = sad_intern_role_scoped_qs(request.user).filter(pk=pk).first()
    if obj is None:
        return tool_text({'error': 'Запись не найдена или недоступна'}, is_error=True)
    return tool_text(SadInternDetailSerializer(obj, context={'request': request}).data)


def tool_create_sad_intern(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if is_hr_or_outstaff(request.user) and not is_admin_user(request.user):
        return deny('HR и outstaff могут только просматривать')
    if not can_interview_write(request.user) and not is_admin_user(request.user):
        return deny('Недостаточно прав для создания')
    serializer = SadInternCreateUpdateSerializer(data=arguments, context={'request': request})
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    obj = serializer.save()
    return tool_text(SadInternDetailSerializer(obj, context={'request': request}).data)


def tool_update_sad_intern(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if is_hr_or_outstaff(request.user) and not is_admin_user(request.user):
        return deny('HR и outstaff могут только просматривать')
    pk = arguments.get('id')
    if pk is None:
        return tool_text({'error': 'Нужен id записи'}, is_error=True)
    obj = sad_intern_role_scoped_qs(request.user).filter(pk=pk).first()
    if obj is None:
        return tool_text({'error': 'Запись не найдена или недоступна'}, is_error=True)
    user = request.user
    if not is_admin_user(user) and obj.manager_email != getattr(user, 'email', None):
        return deny('Нет прав для редактирования этой записи')
    data = {k: v for k, v in arguments.items() if k != 'id'}
    serializer = SadInternCreateUpdateSerializer(
        obj, data=data, partial=True, context={'request': request},
    )
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    obj = serializer.save()
    return tool_text(SadInternDetailSerializer(obj, context={'request': request}).data)


def tool_delete_sad_intern(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('Удаление доступно только администраторам')
    pk = arguments.get('id')
    if pk is None:
        return tool_text({'error': 'Нужен id записи'}, is_error=True)
    obj = SadIntern.objects.filter(pk=pk).first()
    if obj is None:
        return tool_text({'error': 'Запись не найдена'}, is_error=True)
    deleted_id = obj.pk
    obj.delete()
    return tool_text({'deleted': True, 'id': deleted_id})


TOOLS: dict[str, dict[str, Any]] = {
    'list_sad_interns': {
        'description': 'Список «Грустят» в области видимости пользователя.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'q': {'type': 'string'},
                'status': {'type': 'string'},
                'page': {'type': 'integer', 'minimum': 1},
                'page_size': {'type': 'integer', 'minimum': 1, 'maximum': MAX_PAGE_SIZE},
            },
        },
        'handler': tool_list_sad_interns,
    },
    'get_sad_intern': {
        'description': 'Карточка записи «Грустят».',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_get_sad_intern,
    },
    'create_sad_intern': {
        'description': 'Создать запись «Грустят» (менеджер/админ).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'intern': {'type': 'integer'},
                'status': {'type': 'string'},
                'note': {'type': 'string'},
                'telegram_username': {'type': 'string'},
            },
            'required': ['intern'],
        },
        'handler': tool_create_sad_intern,
    },
    'update_sad_intern': {
        'description': 'Изменить запись «Грустят» (менеджер — свою; админ — любую).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'status': {'type': 'string'},
                'note': {'type': 'string'},
                'telegram_username': {'type': 'string'},
            },
            'required': ['id'],
        },
        'handler': tool_update_sad_intern,
    },
    'delete_sad_intern': {
        'description': 'Удалить запись «Грустят» (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_delete_sad_intern,
    },
}
