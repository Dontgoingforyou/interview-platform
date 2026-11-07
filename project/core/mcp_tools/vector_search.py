"""MCP-тулы: семантический поиск."""
from __future__ import annotations

from typing import Any

from vector_search.api.views import (
    _manager_role_for_vector_api,
    _vector_search_unrestricted_by_manager_email,
    _vector_user_label,
)
from vector_search.models import SearchLog
from vector_search.serializers import SemanticSearchRequestSerializer
from vector_search.services import EmbeddingService
from vector_search.utils import ENTITY_KB_ARTICLE

from core.mcp_tools._common import tool_text, validation_error


def tool_vector_search(request, arguments: dict[str, Any]) -> dict[str, Any]:
    serializer = SemanticSearchRequestSerializer(data=arguments)
    if not serializer.is_valid():
        return validation_error(serializer.errors)

    data = serializer.validated_data
    query = data['query']
    entity_type = data.get('entity_type')
    top_k = data.get('top_k')
    min_score = data.get('min_score')

    manager_role = _manager_role_for_vector_api(request)
    manager_email = getattr(request.user, 'email', None)

    filters = {}
    for key in ['direction_id', 'manager_email', 'interview_type', 'status']:
        if key in data and data[key]:
            filters[key] = data[key]

    if (
        entity_type != ENTITY_KB_ARTICLE
        and not _vector_search_unrestricted_by_manager_email(manager_role)
        and manager_email
    ):
        if 'manager_email' in filters and filters['manager_email'] != manager_email:
            return tool_text(
                {'error': 'Доступ запрещен', 'details': 'Вы можете искать только свои данные'},
                is_error=True,
            )
        filters['manager_email'] = manager_email

    try:
        results, search_time = EmbeddingService.semantic_search(
            query=query,
            entity_type=entity_type,
            filters=filters if filters else None,
            top_k=top_k,
            min_score=min_score,
        )
        if entity_type == ENTITY_KB_ARTICLE:
            results = EmbeddingService.enrich_kb_article_semantic_results(results)
        SearchLog.objects.create(
            query=query,
            entity_type=entity_type,
            results_count=len(results),
            search_time_ms=search_time,
            user_email=manager_email or '',
            filters=filters,
        )
    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            'Ошибка семантического поиска MCP user=%s', _vector_user_label(request),
        )
        return tool_text({'error': 'Ошибка выполнения поиска'}, is_error=True)

    return tool_text({
        'query': query,
        'results': results,
        'total_found': len(results),
        'search_time_ms': search_time,
    })


TOOLS: dict[str, dict[str, Any]] = {
    'vector_search': {
        'description': 'Семантический поиск по доступным данным.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string'},
                'entity_type': {'type': 'string'},
                'top_k': {'type': 'integer'},
                'min_score': {'type': 'number'},
                'direction_id': {'type': 'integer'},
            },
            'required': ['query'],
        },
        'handler': tool_vector_search,
    },
}
