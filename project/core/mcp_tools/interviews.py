"""MCP-тулы: собеседования, база, транскрипции."""
from __future__ import annotations

from typing import Any

from interviews.interview_list import (
    INTERVIEW_ORDER_FIELD_MAP,
    apply_interview_api_scope,
    apply_interview_list_filters,
    apply_interview_ordering,
    build_interviews_database_api_queryset,
)
from interviews.models import Interview
from interviews.serializers import (
    InterviewCreateUpdateSerializer,
    InterviewFullSerializer,
    InterviewListSerializer,
)
from transcriptions.interview_transcription_handlers import (
    transcribe_interview_payload,
    transcription_status_payload,
    transcription_text_payload,
)

from core.mcp_tools._common import (
    MAX_PAGE_SIZE,
    can_interview_write,
    can_transcribe,
    deny,
    is_admin_user,
    page_bounds,
    tool_text,
    validation_error,
)


def tool_list_interviews(request, arguments: dict[str, Any]) -> dict[str, Any]:
    qs = Interview.objects.select_related('intern', 'company', 'direction')
    qs = apply_interview_api_scope(qs, request.user, view_action='list')
    qs = apply_interview_list_filters(qs, arguments)
    qs = apply_interview_ordering(
        qs,
        arguments.get('order_by', 'id'),
        arguments.get('order_dir', 'desc'),
        valid_fields=INTERVIEW_ORDER_FIELD_MAP,
        default_field='date',
    )
    start, page_size = page_bounds(arguments)
    total = qs.count()
    rows = InterviewListSerializer(qs[start:start + page_size], many=True).data
    return tool_text({'count': total, 'results': rows})


def tool_get_interview(request, arguments: dict[str, Any]) -> dict[str, Any]:
    interview_id = arguments.get('id')
    if interview_id is None:
        return tool_text({'error': 'Нужен id собеседования'}, is_error=True)
    qs = apply_interview_api_scope(
        Interview.objects.select_related('intern', 'company', 'direction'),
        request.user,
        view_action='retrieve',
    )
    obj = qs.filter(pk=interview_id).first()
    if obj is None:
        return tool_text({'error': 'Собеседование не найдено или недоступно'}, is_error=True)
    return tool_text(InterviewFullSerializer(obj, context={'request': request}).data)


def tool_create_interview(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not can_interview_write(request.user):
        return deny('Создание собеседований доступно менеджерам и администраторам')
    serializer = InterviewCreateUpdateSerializer(data=arguments, context={'request': request})
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    user = request.user
    if not is_admin_user(user):
        obj = serializer.save(manager_email=user.email)
    else:
        obj = serializer.save()
    return tool_text(InterviewFullSerializer(obj, context={'request': request}).data)


def tool_update_interview(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not can_interview_write(request.user):
        return deny('Изменение собеседований доступно менеджерам и администраторам')
    interview_id = arguments.get('id')
    if interview_id is None:
        return tool_text({'error': 'Нужен id собеседования'}, is_error=True)
    qs = apply_interview_api_scope(
        Interview.objects.select_related('intern', 'company', 'direction'),
        request.user,
        view_action='partial_update',
    )
    obj = qs.filter(pk=interview_id).first()
    if obj is None:
        return tool_text({'error': 'Собеседование не найдено или недоступно'}, is_error=True)
    data = {k: v for k, v in arguments.items() if k != 'id'}
    serializer = InterviewCreateUpdateSerializer(
        obj, data=data, partial=True, context={'request': request},
    )
    if not serializer.is_valid():
        return validation_error(serializer.errors)
    obj = serializer.save()
    return tool_text(InterviewFullSerializer(obj, context={'request': request}).data)


def tool_list_interviews_database(request, arguments: dict[str, Any]) -> dict[str, Any]:
    class _Req:
        user = request.user
        query_params = arguments

    qs = build_interviews_database_api_queryset(_Req())
    qs = apply_interview_ordering(
        qs,
        arguments.get('order_by', 'date'),
        str(arguments.get('order_dir', 'desc')).lower(),
        valid_fields=INTERVIEW_ORDER_FIELD_MAP,
        default_field='date',
    )
    start, page_size = page_bounds(arguments)
    total = qs.count()
    rows = InterviewFullSerializer(
        qs[start:start + page_size], many=True, context={'request': request},
    ).data
    return tool_text({'count': total, 'results': rows})


def _scoped_interview_for_transcription(request, interview_id: Any):
    if interview_id is None:
        return None, tool_text({'error': 'Нужен id собеседования'}, is_error=True)
    qs = apply_interview_api_scope(
        Interview.objects.all(),
        request.user,
        view_action='transcription_status',
    )
    obj = qs.filter(pk=interview_id).first()
    if obj is None:
        return None, tool_text({'error': 'Собеседование не найдено или недоступно'}, is_error=True)
    return obj, None


def tool_get_transcription_status(request, arguments: dict[str, Any]) -> dict[str, Any]:
    obj, err = _scoped_interview_for_transcription(request, arguments.get('id'))
    if err:
        return err
    payload, _code = transcription_status_payload(obj.pk)
    return tool_text(payload)


def tool_get_transcription_text(request, arguments: dict[str, Any]) -> dict[str, Any]:
    obj, err = _scoped_interview_for_transcription(request, arguments.get('id'))
    if err:
        return err
    payload, code = transcription_text_payload(obj.pk)
    if code >= 400:
        return tool_text(payload, is_error=True)
    return tool_text(payload)


def tool_start_transcription(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not can_transcribe(request.user):
        return deny('Запуск транскрипции доступен администраторам и менторам')
    interview_id = arguments.get('id')
    if interview_id is None:
        return tool_text({'error': 'Нужен id собеседования'}, is_error=True)
    from core.logging_mixins import get_user_label_for_log

    payload, code = transcribe_interview_payload(
        int(interview_id),
        log_user_label=get_user_label_for_log(request),
    )
    if code >= 400:
        return tool_text(payload, is_error=True)
    return tool_text(payload)


TOOLS: dict[str, dict[str, Any]] = {
    'list_interviews': {
        'description': 'Список собеседований в области видимости текущего SSO-пользователя.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'q': {'type': 'string', 'description': 'Поиск'},
                'page': {'type': 'integer', 'minimum': 1},
                'page_size': {'type': 'integer', 'minimum': 1, 'maximum': MAX_PAGE_SIZE},
                'manager': {'type': 'string'},
                'direction_id': {'type': 'integer'},
            },
        },
        'handler': tool_list_interviews,
    },
    'get_interview': {
        'description': 'Карточка собеседования по id, если запись доступна роли.',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_get_interview,
    },
    'create_interview': {
        'description': 'Создать собеседование (менеджер/админ). Для менеджера manager_email подставляется сам.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'intern': {'type': 'integer'},
                'direction_id': {'type': 'integer'},
                'company_id': {'type': 'integer'},
                'company_name': {'type': 'string'},
                'interview_type': {'type': 'string'},
                'interview_format': {'type': 'string'},
                'date': {'type': 'string'},
                'time': {'type': 'string'},
                'link': {'type': 'string'},
                'vacancy_link': {'type': 'string'},
                'interview_link': {'type': 'string'},
                'hr_name': {'type': 'string'},
                'hr_contacts': {'type': 'string'},
            },
            'required': ['intern', 'direction_id'],
        },
        'handler': tool_create_interview,
    },
    'update_interview': {
        'description': 'Частично обновить собеседование (менеджер — своё; админ — любое).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'intern': {'type': 'integer'},
                'direction_id': {'type': 'integer'},
                'company_id': {'type': 'integer'},
                'company_name': {'type': 'string'},
                'interview_type': {'type': 'string'},
                'interview_format': {'type': 'string'},
                'date': {'type': 'string'},
                'time': {'type': 'string'},
                'link': {'type': 'string'},
                'vacancy_link': {'type': 'string'},
                'interview_link': {'type': 'string'},
                'hr_name': {'type': 'string'},
                'hr_contacts': {'type': 'string'},
            },
            'required': ['id'],
        },
        'handler': tool_update_interview,
    },
    'list_interviews_database': {
        'description': 'База собеседований (записи с link/video_link/upload). Видимость как у API базы.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'q': {'type': 'string'},
                'page': {'type': 'integer', 'minimum': 1},
                'page_size': {'type': 'integer', 'minimum': 1, 'maximum': MAX_PAGE_SIZE},
                'company': {'type': 'integer'},
                'direction_id': {'type': 'integer'},
                'manager': {'type': 'string'},
                'interview_type': {'type': 'string'},
                'transcription': {'type': 'string'},
            },
        },
        'handler': tool_list_interviews_database,
    },
    'get_transcription_status': {
        'description': 'Статус транскрипции собеседования.',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_get_transcription_status,
    },
    'get_transcription_text': {
        'description': 'Текст транскрипции (если готов).',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_get_transcription_text,
    },
    'start_transcription': {
        'description': 'Запустить транскрипцию (админ или ментор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}},
            'required': ['id'],
        },
        'handler': tool_start_transcription,
    },
}
