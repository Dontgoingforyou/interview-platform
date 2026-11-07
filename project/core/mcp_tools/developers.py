"""MCP-тулы: разработчики (период)."""
from __future__ import annotations

from typing import Any

from developers.api.views import _build_developer_rows, _resolve_direction_filter

from core.mcp_tools._common import MAX_PAGE_SIZE, page_bounds, tool_text


def tool_get_developers_stats(request, arguments: dict[str, Any]) -> dict[str, Any]:
    direction_id = _resolve_direction_filter(arguments)
    rows = _build_developer_rows(
        direction_id,
        arguments.get('q'),
        arguments.get('order_by') or 'full_name',
        arguments.get('order_dir') or 'asc',
    )
    start, page_size = page_bounds(arguments)
    page = rows[start:start + page_size]
    return tool_text({'count': len(rows), 'results': page})


TOOLS: dict[str, dict[str, Any]] = {
    'get_developers_stats': {
        'description': 'Статистика по разработчикам за период (список с агрегатами).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'direction_id': {'type': 'integer'},
                'q': {'type': 'string'},
                'order_by': {'type': 'string'},
                'order_dir': {'type': 'string'},
                'page': {'type': 'integer', 'minimum': 1},
                'page_size': {'type': 'integer', 'minimum': 1, 'maximum': MAX_PAGE_SIZE},
            },
        },
        'handler': tool_get_developers_stats,
    },
}
