"""MCP-тулы: компании."""
from __future__ import annotations

from typing import Any

from django.db.models import Count

from companies.models import Company
from companies.serializers import CompanySerializer

from core.mcp_tools._common import (
    MAX_PAGE_SIZE,
    can_company_edit,
    deny,
    is_admin_user,
    page_bounds,
    tool_text,
    validation_error,
)


def tool_list_companies(request, arguments: dict[str, Any]) -> dict[str, Any]:
    qs = Company.objects.annotate(interviews_count=Count('interview')).order_by('name')
    q = arguments.get('q')
    if q and str(q).strip():
        qs = qs.filter(name__icontains=str(q).strip())
    start, page_size = page_bounds(arguments)
    total = qs.count()
    rows = CompanySerializer(qs[start:start + page_size], many=True).data
    return tool_text({'count': total, 'results': rows})


def tool_get_company(request, arguments: dict[str, Any]) -> dict[str, Any]:
    company_id = arguments.get('id')
    if company_id is None:
        return tool_text({'error': 'Нужен id компании'}, is_error=True)
    obj = Company.objects.annotate(interviews_count=Count('interview')).filter(pk=company_id).first()
    if obj is None:
        return tool_text({'error': 'Компания не найдена'}, is_error=True)
    return tool_text(CompanySerializer(obj).data)


def tool_create_company(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not can_company_edit(request.user):
        return deny('Редактирование компаний доступно менеджерам и администраторам')
    serializer = CompanySerializer(data=arguments)
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    obj = serializer.save()
    obj = Company.objects.annotate(interviews_count=Count('interview')).get(pk=obj.pk)
    return tool_text(CompanySerializer(obj).data)


def tool_update_company(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not can_company_edit(request.user):
        return deny('Редактирование компаний доступно менеджерам и администраторам')
    company_id = arguments.get('id')
    if company_id is None:
        return tool_text({'error': 'Нужен id компании'}, is_error=True)
    obj = Company.objects.filter(pk=company_id).first()
    if obj is None:
        return tool_text({'error': 'Компания не найдена'}, is_error=True)
    data = {k: v for k, v in arguments.items() if k != 'id'}
    serializer = CompanySerializer(obj, data=data, partial=True)
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    obj = serializer.save()
    obj = Company.objects.annotate(interviews_count=Count('interview')).get(pk=obj.pk)
    return tool_text(CompanySerializer(obj).data)


def tool_delete_company(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('Удаление компаний доступно только администраторам')
    company_id = arguments.get('id')
    if company_id is None:
        return tool_text({'error': 'Нужен id компании'}, is_error=True)
    obj = Company.objects.filter(pk=company_id).first()
    if obj is None:
        return tool_text({'error': 'Компания не найдена'}, is_error=True)
    pk = obj.pk
    obj.delete()
    return tool_text({'deleted': True, 'id': pk})


TOOLS: dict[str, dict[str, Any]] = {
    'list_companies': {
        'description': 'Список компаний.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'q': {'type': 'string'},
                'page': {'type': 'integer', 'minimum': 1},
                'page_size': {'type': 'integer', 'minimum': 1, 'maximum': MAX_PAGE_SIZE},
            },
        },
        'handler': tool_list_companies,
    },
    'get_company': {
        'description': 'Карточка компании по id.',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_get_company,
    },
    'create_company': {
        'description': 'Создать компанию (менеджер/админ).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'is_bigtech': {'type': 'boolean'},
                'aliases': {'type': 'string'},
            },
            'required': ['name'],
        },
        'handler': tool_create_company,
    },
    'update_company': {
        'description': 'Изменить компанию (менеджер/админ).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
                'is_bigtech': {'type': 'boolean'},
                'aliases': {'type': 'string'},
            },
            'required': ['id'],
        },
        'handler': tool_update_company,
    },
    'delete_company': {
        'description': 'Удалить компанию (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_delete_company,
    },
}
