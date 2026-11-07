"""MCP-тулы: студенты."""
from __future__ import annotations

from typing import Any

from interns.list_filters import apply_intern_list_ordering, apply_intern_text_search
from interns.models import Intern
from interns.serializers import (
    InternCreateUpdateSerializer,
    InternDetailSerializer,
    InternListSerializer,
)

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


def _intern_scope(user: Any):
    qs = Intern.objects.select_related('direction')
    if is_admin_user(user):
        return qs
    if is_hr_or_outstaff(user):
        return qs
    email = getattr(user, 'email', None)
    if email:
        return qs.filter(manager_email=email)
    return qs.none()


def tool_list_interns(request, arguments: dict[str, Any]) -> dict[str, Any]:
    qs = _intern_scope(request.user)
    qs = apply_intern_text_search(qs, arguments.get('q'))
    qs = apply_intern_list_ordering(
        qs,
        arguments.get('order_by', 'id'),
        arguments.get('order_dir', 'desc'),
    )
    start, page_size = page_bounds(arguments)
    total = qs.count()
    rows = InternListSerializer(qs[start:start + page_size], many=True).data
    return tool_text({'count': total, 'results': rows})


def tool_get_intern(request, arguments: dict[str, Any]) -> dict[str, Any]:
    intern_id = arguments.get('id')
    if intern_id is None:
        return tool_text({'error': 'Нужен id студента'}, is_error=True)
    obj = _intern_scope(request.user).filter(pk=intern_id).first()
    if obj is None:
        return tool_text({'error': 'Студент не найден или недоступен'}, is_error=True)
    return tool_text(InternDetailSerializer(
        obj,
        context={'request': request},
    ).data)


def tool_create_intern(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not can_interview_write(request.user):
        return deny('Создание студентов доступно менеджерам и администраторам')
    serializer = InternCreateUpdateSerializer(data=arguments, context={'request': request})
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    user = request.user
    if not is_admin_user(user):
        email = getattr(user, 'email', None)
        if not email:
            return deny('Не удалось определить email пользователя')
        obj = serializer.save(manager_email=email)
    else:
        obj = serializer.save()
    return tool_text(InternDetailSerializer(obj, context={'request': request}).data)


def tool_update_intern(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('Изменение студента доступно только администраторам')
    intern_id = arguments.get('id')
    if intern_id is None:
        return tool_text({'error': 'Нужен id студента'}, is_error=True)
    obj = Intern.objects.filter(pk=intern_id).select_related('direction').first()
    if obj is None:
        return tool_text({'error': 'Студент не найден'}, is_error=True)
    data = {k: v for k, v in arguments.items() if k != 'id'}
    serializer = InternCreateUpdateSerializer(
        obj, data=data, partial=True, context={'request': request},
    )
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    obj = serializer.save()
    return tool_text(InternDetailSerializer(obj, context={'request': request}).data)


def tool_delete_intern(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('Удаление студента доступно только администраторам')
    intern_id = arguments.get('id')
    if intern_id is None:
        return tool_text({'error': 'Нужен id студента'}, is_error=True)
    obj = Intern.objects.filter(pk=intern_id).first()
    if obj is None:
        return tool_text({'error': 'Студент не найден'}, is_error=True)
    pk = obj.pk
    obj.delete()
    return tool_text({'deleted': True, 'id': pk})


TOOLS: dict[str, dict[str, Any]] = {
    'list_interns': {
        'description': 'Список студентов в области видимости текущего SSO-пользователя.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'q': {'type': 'string', 'description': 'Поиск по ФИО, email, группе, городу'},
                'page': {'type': 'integer', 'minimum': 1},
                'page_size': {'type': 'integer', 'minimum': 1, 'maximum': MAX_PAGE_SIZE},
            },
        },
        'handler': tool_list_interns,
    },
    'get_intern': {
        'description': 'Карточка студента по id, если запись доступна роли.',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_get_intern,
    },
    'create_intern': {
        'description': 'Создать студента (менеджер/админ). Для менеджера manager_email подставляется сам.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'full_name': {'type': 'string'},
                'email': {'type': 'string'},
                'telegram_username': {'type': 'string'},
                'direction_id': {'type': 'integer'},
                'city': {'type': 'string'},
                'group': {'type': 'string'},
            },
            'required': ['full_name', 'direction_id'],
        },
        'handler': tool_create_intern,
    },
    'update_intern': {
        'description': 'Изменить студента (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'full_name': {'type': 'string'},
                'email': {'type': 'string'},
                'direction_id': {'type': 'integer'},
            },
            'required': ['id'],
        },
        'handler': tool_update_intern,
    },
    'delete_intern': {
        'description': 'Удалить студента (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_delete_intern,
    },
}
