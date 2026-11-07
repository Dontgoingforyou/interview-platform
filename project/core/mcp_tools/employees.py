"""MCP-тулы: сотрудники / доска менеджера."""
from __future__ import annotations

from typing import Any
from urllib.parse import unquote

from core.intern_utils import transliterate_name_to_cyrillic
from employees.board_serialization import serialize_manager_board
from employees.services import ManagerDetailService, get_managers_for_employees_list
from managers.models import Manager

from core.mcp_tools._common import tool_text


def tool_list_employees_managers(request, arguments: dict[str, Any]) -> dict[str, Any]:
    managers = get_managers_for_employees_list()
    rows = []
    for manager in managers:
        raw = manager.full_name or ''
        rows.append({
            'email': manager.email,
            'full_name': transliterate_name_to_cyrillic(raw) or raw,
        })
    return tool_text({'count': len(rows), 'results': rows})


def tool_get_manager_board(request, arguments: dict[str, Any]) -> dict[str, Any]:
    email = arguments.get('email')
    if not email:
        return tool_text({'error': 'Нужен email менеджера'}, is_error=True)
    decoded = unquote(str(email))
    manager = Manager.objects.filter(is_active=True, email=decoded).first()
    if manager is None:
        return tool_text({'error': 'Менеджер не найден'}, is_error=True)
    context = ManagerDetailService().get_context(manager)
    return tool_text(serialize_manager_board(manager, context))


TOOLS: dict[str, dict[str, Any]] = {
    'list_employees_managers': {
        'description': 'Список менеджеров для раздела «Сотрудники».',
        'inputSchema': {'type': 'object', 'properties': {}},
        'handler': tool_list_employees_managers,
    },
    'get_manager_board': {
        'description': 'Доска сотрудников менеджера (недели, статусы).',
        'inputSchema': {
            'type': 'object',
            'properties': {'email': {'type': 'string'}},
            'required': ['email'],
        },
        'handler': tool_get_manager_board,
    },
}
