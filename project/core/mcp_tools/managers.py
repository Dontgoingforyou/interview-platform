"""MCP-тулы: менеджеры и аналитика."""
from __future__ import annotations

from typing import Any

from managers.analytics_views import compute_managers_analytics
from managers.models import Manager
from managers.serializers import ManagerForFilterSerializer

from core.mcp_tools._common import MAX_PAGE_SIZE, page_bounds, tool_text


def tool_list_managers(request, arguments: dict[str, Any]) -> dict[str, Any]:
    qs = Manager.objects.filter(is_active=True).order_by('full_name')
    q = arguments.get('q')
    if q and str(q).strip():
        qs = qs.filter(full_name__icontains=str(q).strip())
    start, page_size = page_bounds(arguments)
    total = qs.count()
    rows = ManagerForFilterSerializer(qs[start:start + page_size], many=True).data
    return tool_text({'count': total, 'results': rows})


def tool_get_managers_analytics(request, arguments: dict[str, Any]) -> dict[str, Any]:
    return tool_text(compute_managers_analytics())


TOOLS: dict[str, dict[str, Any]] = {
    'list_managers': {
        'description': 'Список активных менеджеров (для фильтров и раздела «Менеджеры»).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'q': {'type': 'string'},
                'page': {'type': 'integer', 'minimum': 1},
                'page_size': {'type': 'integer', 'minimum': 1, 'maximum': MAX_PAGE_SIZE},
            },
        },
        'handler': tool_list_managers,
    },
    'get_managers_analytics': {
        'description': 'Аналитика по менеджерам.',
        'inputSchema': {'type': 'object', 'properties': {}},
        'handler': tool_get_managers_analytics,
    },
}
