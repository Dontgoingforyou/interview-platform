"""MCP-тулы: направления и метрики."""
from __future__ import annotations

from typing import Any

from directions.analytics_views import compute_direction_metrics
from directions.models import Direction
from directions.serializers import DirectionSerializer

from core.mcp_tools._common import MAX_PAGE_SIZE, page_bounds, tool_text


def tool_list_directions(request, arguments: dict[str, Any]) -> dict[str, Any]:
    qs = Direction.objects.all().order_by('name')
    q = arguments.get('q')
    if q and str(q).strip():
        qs = qs.filter(name__icontains=str(q).strip())
    start, page_size = page_bounds(arguments)
    total = qs.count()
    rows = DirectionSerializer(qs[start:start + page_size], many=True).data
    return tool_text({'count': total, 'results': rows})


def tool_get_direction(request, arguments: dict[str, Any]) -> dict[str, Any]:
    direction_id = arguments.get('id')
    if direction_id is None:
        return tool_text({'error': 'Нужен id направления'}, is_error=True)
    obj = Direction.objects.filter(pk=direction_id).first()
    if obj is None:
        return tool_text({'error': 'Направление не найдено'}, is_error=True)
    return tool_text(DirectionSerializer(obj).data)


def tool_get_directions_metrics(request, arguments: dict[str, Any]) -> dict[str, Any]:
    params = {k: v for k, v in arguments.items() if v is not None}
    data = compute_direction_metrics(params)
    return tool_text(data)


TOOLS: dict[str, dict[str, Any]] = {
    'list_directions': {
        'description': 'Список направлений.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'q': {'type': 'string'},
                'page': {'type': 'integer', 'minimum': 1},
                'page_size': {'type': 'integer', 'minimum': 1, 'maximum': MAX_PAGE_SIZE},
            },
        },
        'handler': tool_list_directions,
    },
    'get_direction': {
        'description': 'Карточка направления по id.',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_get_direction,
    },
    'get_directions_metrics': {
        'description': 'Метрики по направлениям / собесам (аналитика).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'date_filter': {'type': 'string'},
                'direction': {'type': 'integer'},
                'min_conversion': {'type': 'number'},
            },
        },
        'handler': tool_get_directions_metrics,
    },
}
