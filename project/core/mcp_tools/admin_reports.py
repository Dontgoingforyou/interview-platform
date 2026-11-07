"""MCP-тулы: админ-отчёты KPI и разработчики у менеджеров."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from core.intern_utils import transliterate_name_to_cyrillic
from employees.services import get_developer_count_data, get_kpi_report_data

from core.mcp_tools._common import deny, is_admin_user, tool_text


def _serialize_manager(manager) -> dict:
    raw = manager.full_name or ''
    return {
        'full_name': transliterate_name_to_cyrillic(raw) or raw,
        'email': manager.email,
        'is_active': manager.is_active,
    }


def _serialize_intern(intern) -> dict:
    return {
        'id': intern.id,
        'full_name': intern.full_name,
        'group': intern.group or '',
        'manager_email': intern.manager_email or '',
    }


def tool_get_managers_kpi(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('KPI в MCP доступен только администраторам')
    date_from_str = arguments.get('date_from') or ''
    date_to_str = arguments.get('date_to') or ''
    if not date_from_str or not date_to_str:
        return tool_text({'error': 'Укажите date_from и date_to (YYYY-MM-DD)'}, is_error=True)
    try:
        date_from = datetime.strptime(str(date_from_str), '%Y-%m-%d').date()
        date_to = datetime.strptime(str(date_to_str), '%Y-%m-%d').date()
        min_kpi = float(arguments.get('min_kpi') or 3)
    except ValueError:
        return tool_text({'error': 'Некорректный формат даты или порога KPI'}, is_error=True)
    data = get_kpi_report_data(date_from, date_to, min_kpi)
    if 'error' in data:
        return tool_text({'error': data['error']}, is_error=True)
    results = []
    for item in data['results']:
        results.append({
            'manager': _serialize_manager(item['manager']),
            'qualifying_weeks_count': item['qualifying_weeks_count'],
            'qualifying_weeks': item['qualifying_weeks'],
            'total_active_devs': item['total_active_devs'],
        })
    return tool_text({
        'date_from': date_from_str,
        'date_to': date_to_str,
        'min_kpi': min_kpi,
        'results': results,
    })


def tool_get_admin_developers(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('Отчёт доступен только администраторам')
    show_hidden = str(arguments.get('show_hidden', '')).lower() in ('1', 'true', 'yes')
    data = get_developer_count_data(show_hidden)
    results = [
        {
            'manager': _serialize_manager(item['manager']),
            'active_count': item['active_count'],
            'interns': [_serialize_intern(i) for i in item['interns']],
        }
        for item in data['results']
    ]
    hidden_results = [
        {
            'manager': _serialize_manager(item['manager']),
            'active_count': item['active_count'],
            'interns': [_serialize_intern(i) for i in item['interns']],
        }
        for item in data['hidden_results']
    ]
    return tool_text({
        'results': results,
        'hidden_results': hidden_results,
        'total_active': data['total_active'],
        'hidden_count': data['hidden_count'],
    })


TOOLS: dict[str, dict[str, Any]] = {
    'get_managers_kpi': {
        'description': 'Отчёт KPI менеджеров за период (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'date_from': {'type': 'string'},
                'date_to': {'type': 'string'},
                'min_kpi': {'type': 'number'},
            },
            'required': ['date_from', 'date_to'],
        },
        'handler': tool_get_managers_kpi,
    },
    'get_admin_developers': {
        'description': 'Количество разработчиков у менеджеров (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'show_hidden': {'type': 'boolean'}},
        },
        'handler': tool_get_admin_developers,
    },
}
