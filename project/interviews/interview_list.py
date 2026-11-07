"""
Общая логика фильтрации и сортировки списка собеседований (Django list + DRF API).
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Mapping, MutableMapping

from django.contrib import messages
from django.db.models import F, Q, QuerySet

from core.constants import INTERVIEW_FORMAT_CHOICES
from interviews.models import Interview
from transcriptions.models import TranscriptionStatus

logger = logging.getLogger(__name__)

VALID_INTERVIEW_FORMAT_FILTER = frozenset(code for code, _ in INTERVIEW_FORMAT_CHOICES)

# GET «База собеседований»: фильтр по статусу транскрипции (related transcription).
INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER = frozenset({'completed', 'failed', 'in_progress'})

# Ключ: имя в order_by из URL; значение: поле ORM для Interview
INTERVIEW_ORDER_FIELD_MAP: dict[str, str] = {
    'id': 'id',
    'full_name': 'intern__full_name',
    'direction_name': 'direction_id',
    'company_name': 'company_id',
    'interview_type': 'interview_type',
    'date': 'date',
    'time': 'time',
    'manager_name': 'manager_email',
    'hr_name': 'hr_name',
}


def apply_interview_api_scope(qs: QuerySet, user: Any, *, view_action: str | None = None) -> QuerySet:
    """
    Ограничение выборки по роли (как InterviewViewSet на develop).
    Админ и суперпользователь — все записи.
    HR/outstaff/mentor — полный доступ на чтение: list, retrieve, transcription-status, transcription-text.
    Остальные — только «свои» собеседования по email.
    """
    is_admin = getattr(user, 'is_admin', False) or getattr(user, 'is_superuser', False)
    if is_admin:
        return qs
    hr_outstaff_read_all = (
        view_action in (
            'list',
            'retrieve',
            'transcription_status',
            'transcription_text',
            'transcribe',
        )
        and (
            getattr(user, 'is_hr', False)
            or getattr(user, 'is_outstaff', False)
            or getattr(user, 'is_mentor', False)
        )
    )
    if hr_outstaff_read_all:
        return qs
    email = getattr(user, 'email', None)
    if email:
        return qs.filter(
            Q(manager_email=email) | Q(manager_email__isnull=True, intern__manager_email=email),
        )
    return qs


def _apply_common_filters(qs: QuerySet, params: Mapping[str, Any]) -> QuerySet:
    """Менеджер, направление, компания — фильтры списка собеседований в API."""
    manager_email = params.get('manager')
    if manager_email and '@' in str(manager_email):
        qs = qs.filter(manager_email=manager_email)

    direction_id = params.get('direction') or params.get('direction_id')
    if direction_id:
        try:
            qs = qs.filter(direction_id=int(direction_id))
        except (ValueError, TypeError):
            logger.warning('Неверный формат direction_id в фильтре: %s', direction_id)

    company_id = params.get('company')
    if company_id:
        try:
            qs = qs.filter(company_id=int(company_id))
        except (ValueError, TypeError):
            logger.warning('Неверный формат company_id в фильтре: %s', company_id)

    return qs


def _apply_custom_interview_filters(
    qs: QuerySet,
    params: Mapping[str, Any],
    *,
    request: Any | None = None,
) -> QuerySet:
    """Специфичные фильтры InterviewListView.apply_custom_filters (даты, формат)."""
    date_filter = params.get('date_filter')
    date_from = params.get('date_from')
    date_to = params.get('date_to')

    if date_filter == 'today':
        qs = qs.filter(date=date.today())
    elif date_filter == 'tomorrow':
        tomorrow = date.today() + timedelta(days=1)
        qs = qs.filter(date=tomorrow)
    elif date_from and date_to:
        qs = qs.filter(date__gte=date_from, date__lte=date_to)
    elif date_from:
        qs = qs.filter(date__gte=date_from)
    elif date_to:
        qs = qs.filter(date__lte=date_to)

    interview_format = params.get('interview_format')
    if interview_format:
        if interview_format in VALID_INTERVIEW_FORMAT_FILTER:
            qs = qs.filter(interview_format=interview_format)
        else:
            logger.warning('Невалидное значение interview_format в фильтре: %s', interview_format)
            if request is not None:
                messages.warning(
                    request,
                    f'Невалидное значение фильтра по формату: {interview_format}',
                )

    return qs


def _apply_q_search(qs: QuerySet, q: str | None) -> QuerySet:
    if not q:
        return qs
    return qs.filter(
        Q(intern__full_name__icontains=q) | Q(hr_name__icontains=q) | Q(vacancy_link__icontains=q),
    )


def apply_interview_list_filters(
    qs: QuerySet,
    params: Mapping[str, Any],
    *,
    request: Any | None = None,
) -> QuerySet:
    """
    Полный набор фильтров списка: общие + специфичные + поиск q + no_link (API).
    """
    qs = _apply_common_filters(qs, params)
    qs = _apply_custom_interview_filters(qs, params, request=request)
    qs = _apply_q_search(qs, params.get('q'))

    no_link = str(params.get('no_link', '')).lower()
    if no_link in ('true', '1', 'yes'):
        qs = qs.filter(Q(link__isnull=True) | Q(link=''))

    has_video = str(params.get('has_video', '')).lower()
    if has_video in ('true', '1', 'yes'):
        qs = qs.filter(Q(video_link__isnull=False) & ~Q(video_link=''))
    elif has_video in ('false', '0', 'no'):
        qs = qs.filter(Q(video_link__isnull=True) | Q(video_link=''))

    interview_type = params.get('interview_type')
    if interview_type:
        qs = qs.filter(interview_type=interview_type)

    intern_id = params.get('intern_id')
    if intern_id:
        try:
            qs = qs.filter(intern_id=int(intern_id))
        except (ValueError, TypeError):
            pass

    return qs


def apply_interview_ordering(
    qs: QuerySet,
    order_by: str,
    order_dir: str,
    *,
    valid_fields: Mapping[str, str] | None = None,
    default_field: str = 'date',
    use_f_ordering: bool = True,
) -> QuerySet:
    """Сортировка списка собеседований в API."""
    valid_order_fields = valid_fields or INTERVIEW_ORDER_FIELD_MAP
    if order_by in valid_order_fields:
        field_name = valid_order_fields[order_by]
    else:
        field_name = default_field

    if use_f_ordering:
        if order_dir == 'desc':
            return qs.order_by(F(field_name).desc(nulls_last=True))
        return qs.order_by(F(field_name).asc(nulls_last=True))

    order_string = f'-{field_name}' if order_dir == 'desc' else field_name
    return qs.order_by(order_string)


def interview_type_statistics_payload(qs: QuerySet) -> dict[str, Any]:
    """Статистика по типам для текущего queryset (как InterviewListView.get_interview_type_statistics)."""
    from django.db.models import Count

    stats = qs.values('interview_type').annotate(count=Count('id')).order_by('-count')
    interview_type_dict = dict(Interview.INTERVIEW_TYPES)
    result: list[dict[str, Any]] = []
    total = 0
    for row in stats:
        itype = row['interview_type']
        count = row['count']
        total += count
        result.append({
            'type': itype,
            'label': interview_type_dict.get(itype, itype),
            'count': count,
        })
    return {'items': result, 'total': total}


def query_params_from_request(request: Any) -> MutableMapping[str, Any]:
    """GET для Django или query_params для DRF Request."""
    if hasattr(request, 'query_params'):
        return request.query_params
    return request.GET


def build_interview_api_list_queryset(request: Any, *, view_action: str | None = None) -> QuerySet:
    """
    Базовый queryset для API списка: scope по роли + фильтры (без сортировки).
    Используется в InterviewViewSet и в аналитике type-breakdown.
    """
    action = view_action if view_action is not None else 'list'
    qs = Interview.objects.select_related('intern', 'company', 'direction').prefetch_related('transcription')
    qs = apply_interview_api_scope(qs, request.user, view_action=action)
    return apply_interview_list_filters(qs, query_params_from_request(request))


def filter_interviews_with_any_recording(qs: QuerySet) -> QuerySet:
    """Собеседования с непустым link, video_link или upload_task_id."""
    has_link = Q(link__isnull=False) & ~Q(link='')
    has_video = Q(video_link__isnull=False) & ~Q(video_link='')
    has_upload = Q(upload_task_id__isnull=False) & ~Q(upload_task_id='')
    return qs.filter(has_link | has_video | has_upload)


def apply_interviews_database_transcription_filter(qs: QuerySet, raw: Any) -> QuerySet:
    """Оставить собеседования с InterviewTranscription в заданном состоянии."""
    if not raw:
        return qs
    v = str(raw).strip().lower()
    if v not in INTERVIEWS_DATABASE_TRANSCRIPTION_FILTER:
        logger.warning('Невалидное значение transcription в фильтре базы собеседований: %s', raw)
        return qs
    if v == 'completed':
        return qs.filter(transcription__status=TranscriptionStatus.COMPLETED)
    if v == 'failed':
        return qs.filter(transcription__status=TranscriptionStatus.FAILED)
    return qs.filter(
        transcription__status__in=(TranscriptionStatus.PENDING, TranscriptionStatus.PROCESSING),
    )


def apply_interviews_database_search(qs: QuerySet, q: str | None) -> QuerySet:
    """Поиск для базы собеседований: ФИО, HR, подстрока в link и video_link."""
    if not q:
        return qs
    text = str(q).strip()
    if not text:
        return qs
    return qs.filter(
        Q(intern__full_name__icontains=text)
        | Q(hr_name__icontains=text)
        | Q(link__icontains=text)
        | Q(video_link__icontains=text),
    )


def build_interviews_database_api_queryset(request: Any, *, view_action: str | None = None) -> QuerySet:
    """
    API «База собеседований»: только с записью, общие фильтры,
    тип собеседования, поиск q (без дат и фильтров списка интервью no_link/has_video).
    Все менеджеры видят все записи — без ограничения по email.
    Доступ ограничен на уровне permission_classes (IsManagerOrAdmin).
    """
    params = query_params_from_request(request)
    qs = Interview.objects.select_related('intern', 'company', 'direction').prefetch_related('transcription')
    qs = filter_interviews_with_any_recording(qs)
    qs = _apply_common_filters(qs, params)
    interview_type = params.get('interview_type')
    if interview_type:
        qs = qs.filter(interview_type=interview_type)
    qs = apply_interviews_database_transcription_filter(qs, params.get('transcription'))
    qs = apply_interviews_database_search(qs, params.get('q'))
    return qs
