"""MCP-тулы: долги (только admin на уровне visibility)."""
from __future__ import annotations

from typing import Any

from debts.drf_list_query import apply_debt_list_filters, apply_debt_list_ordering
from debts.models import Debt
from debts.serializers import (
    DebtCreateUpdateSerializer,
    DebtDetailSerializer,
    DebtListSerializer,
    PaymentHistoryCreateSerializer,
)

from core.mcp_tools._common import MAX_PAGE_SIZE, deny, is_admin_user, page_bounds, tool_text, validation_error


def _require_admin(request) -> dict[str, Any] | None:
    if not is_admin_user(request.user):
        return deny('Долги в MCP доступны только администраторам')
    return None


def tool_list_debts(request, arguments: dict[str, Any]) -> dict[str, Any]:
    err = _require_admin(request)
    if err:
        return err
    qs = Debt.objects.select_related('intern', 'direction')
    qs = apply_debt_list_filters(qs, arguments)
    qs = apply_debt_list_ordering(qs, arguments)
    start, page_size = page_bounds(arguments)
    total = qs.count()
    rows = DebtListSerializer(qs[start:start + page_size], many=True).data
    return tool_text({'count': total, 'results': rows})


def tool_get_debt(request, arguments: dict[str, Any]) -> dict[str, Any]:
    err = _require_admin(request)
    if err:
        return err
    pk = arguments.get('id')
    if pk is None:
        return tool_text({'error': 'Нужен id долга'}, is_error=True)
    obj = Debt.objects.select_related('intern', 'direction').filter(pk=pk).first()
    if obj is None:
        return tool_text({'error': 'Долг не найден'}, is_error=True)
    return tool_text(DebtDetailSerializer(obj).data)


def tool_create_debt(request, arguments: dict[str, Any]) -> dict[str, Any]:
    err = _require_admin(request)
    if err:
        return err
    serializer = DebtCreateUpdateSerializer(data=arguments)
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    obj = serializer.save()
    return tool_text(DebtDetailSerializer(obj).data)


def tool_update_debt(request, arguments: dict[str, Any]) -> dict[str, Any]:
    err = _require_admin(request)
    if err:
        return err
    pk = arguments.get('id')
    if pk is None:
        return tool_text({'error': 'Нужен id долга'}, is_error=True)
    obj = Debt.objects.filter(pk=pk).first()
    if obj is None:
        return tool_text({'error': 'Долг не найден'}, is_error=True)
    data = {k: v for k, v in arguments.items() if k != 'id'}
    serializer = DebtCreateUpdateSerializer(obj, data=data, partial=True)
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    obj = serializer.save()
    return tool_text(DebtDetailSerializer(obj).data)


def tool_delete_debt(request, arguments: dict[str, Any]) -> dict[str, Any]:
    err = _require_admin(request)
    if err:
        return err
    pk = arguments.get('id')
    if pk is None:
        return tool_text({'error': 'Нужен id долга'}, is_error=True)
    obj = Debt.objects.filter(pk=pk).first()
    if obj is None:
        return tool_text({'error': 'Долг не найден'}, is_error=True)
    deleted_id = obj.pk
    obj.delete()
    return tool_text({'deleted': True, 'id': deleted_id})


def tool_add_debt_payment(request, arguments: dict[str, Any]) -> dict[str, Any]:
    err = _require_admin(request)
    if err:
        return err
    debt_id = arguments.get('id')
    if debt_id is None:
        return tool_text({'error': 'Нужен id долга'}, is_error=True)
    debt = Debt.objects.filter(pk=debt_id).first()
    if debt is None:
        return tool_text({'error': 'Долг не найден'}, is_error=True)
    data = {k: v for k, v in arguments.items() if k != 'id'}
    serializer = PaymentHistoryCreateSerializer(data=data)
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    payment = serializer.save(debt=debt)
    return tool_text({
        'id': payment.pk,
        'debt_id': debt.pk,
        'amount': str(payment.amount),
        'month': payment.month,
        'year': payment.year,
    })


TOOLS: dict[str, dict[str, Any]] = {
    'list_debts': {
        'description': 'Список долгов (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'q': {'type': 'string'},
                'page': {'type': 'integer', 'minimum': 1},
                'page_size': {'type': 'integer', 'minimum': 1, 'maximum': MAX_PAGE_SIZE},
            },
        },
        'handler': tool_list_debts,
    },
    'get_debt': {
        'description': 'Карточка долга (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_get_debt,
    },
    'create_debt': {
        'description': 'Создать долг (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'intern': {'type': 'integer'},
                'total_amount': {'type': 'number'},
            },
            'required': ['intern'],
        },
        'handler': tool_create_debt,
    },
    'update_debt': {
        'description': 'Изменить долг (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_update_debt,
    },
    'delete_debt': {
        'description': 'Удалить долг (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_delete_debt,
    },
    'add_debt_payment': {
        'description': 'Добавить платёж по долгу (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer', 'description': 'ID долга'},
                'amount': {'type': 'number'},
                'month': {'type': 'integer'},
                'year': {'type': 'integer'},
            },
            'required': ['id', 'amount', 'month', 'year'],
        },
        'handler': tool_add_debt_payment,
    },
}
