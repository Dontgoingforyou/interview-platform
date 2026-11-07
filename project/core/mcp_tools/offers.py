"""MCP-тулы: офферы (только admin на уровне visibility)."""
from __future__ import annotations

from typing import Any

from offers.drf_list_query import apply_offer_list_filters, apply_offer_ordering
from offers.models import Offer
from offers.serializers import (
    OfferCreateUpdateSerializer,
    OfferDetailSerializer,
    OfferListSerializer,
)

from core.mcp_tools._common import MAX_PAGE_SIZE, deny, is_admin_user, page_bounds, tool_text, validation_error


def _require_admin(request) -> dict[str, Any] | None:
    if not is_admin_user(request.user):
        return deny('Офферы в MCP доступны только администраторам')
    return None


def tool_list_offers(request, arguments: dict[str, Any]) -> dict[str, Any]:
    err = _require_admin(request)
    if err:
        return err
    qs = Offer.objects.select_related('intern', 'direction')
    qs = apply_offer_list_filters(qs, arguments)
    qs = apply_offer_ordering(qs, arguments)
    start, page_size = page_bounds(arguments)
    total = qs.count()
    rows = OfferListSerializer(qs[start:start + page_size], many=True).data
    return tool_text({'count': total, 'results': rows})


def tool_get_offer(request, arguments: dict[str, Any]) -> dict[str, Any]:
    err = _require_admin(request)
    if err:
        return err
    pk = arguments.get('id')
    if pk is None:
        return tool_text({'error': 'Нужен id оффера'}, is_error=True)
    obj = Offer.objects.select_related('intern', 'direction').filter(pk=pk).first()
    if obj is None:
        return tool_text({'error': 'Оффер не найден'}, is_error=True)
    return tool_text(OfferDetailSerializer(obj).data)


def tool_create_offer(request, arguments: dict[str, Any]) -> dict[str, Any]:
    err = _require_admin(request)
    if err:
        return err
    serializer = OfferCreateUpdateSerializer(data=arguments)
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    obj = serializer.save()
    return tool_text(OfferDetailSerializer(obj).data)


def tool_update_offer(request, arguments: dict[str, Any]) -> dict[str, Any]:
    err = _require_admin(request)
    if err:
        return err
    pk = arguments.get('id')
    if pk is None:
        return tool_text({'error': 'Нужен id оффера'}, is_error=True)
    obj = Offer.objects.filter(pk=pk).first()
    if obj is None:
        return tool_text({'error': 'Оффер не найден'}, is_error=True)
    data = {k: v for k, v in arguments.items() if k != 'id'}
    serializer = OfferCreateUpdateSerializer(obj, data=data, partial=True)
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    obj = serializer.save()
    return tool_text(OfferDetailSerializer(obj).data)


def tool_delete_offer(request, arguments: dict[str, Any]) -> dict[str, Any]:
    err = _require_admin(request)
    if err:
        return err
    pk = arguments.get('id')
    if pk is None:
        return tool_text({'error': 'Нужен id оффера'}, is_error=True)
    obj = Offer.objects.filter(pk=pk).first()
    if obj is None:
        return tool_text({'error': 'Оффер не найден'}, is_error=True)
    deleted_id = obj.pk
    obj.delete()
    return tool_text({'deleted': True, 'id': deleted_id})


TOOLS: dict[str, dict[str, Any]] = {
    'list_offers': {
        'description': 'Список офферов (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'q': {'type': 'string'},
                'page': {'type': 'integer', 'minimum': 1},
                'page_size': {'type': 'integer', 'minimum': 1, 'maximum': MAX_PAGE_SIZE},
            },
        },
        'handler': tool_list_offers,
    },
    'get_offer': {
        'description': 'Карточка оффера (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_get_offer,
    },
    'create_offer': {
        'description': 'Создать оффер (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'intern': {'type': 'integer'},
                'direction_id': {'type': 'integer'},
                'company': {'type': 'string'},
                'amount': {'type': 'number'},
                'month': {'type': 'integer'},
                'year': {'type': 'integer'},
            },
            'required': ['intern', 'direction_id'],
        },
        'handler': tool_create_offer,
    },
    'update_offer': {
        'description': 'Изменить оффер (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_update_offer,
    },
    'delete_offer': {
        'description': 'Удалить оффер (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_delete_offer,
    },
}
