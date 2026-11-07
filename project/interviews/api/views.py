from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from accounts.permissions import IsAdminOrMentorRole, IsInterviewWriteRole, IsManagerOrAdmin
from core.logging_mixins import ApiCRUDLoggingMixin
from interviews import interview_list
from interviews.pagination import InterviewListPagination
from interviews.serializers import (
    InterviewFullSerializer,
    InterviewCreateUpdateSerializer,
)
from transcriptions.interview_transcription_handlers import (
    transcribe_interview_payload,
    transcription_status_payload,
    transcription_text_payload,
)


class InterviewViewSet(ApiCRUDLoggingMixin, viewsets.ModelViewSet):
    """
    ViewSet для полного управления собеседованиями.

    GET /api/interviews/       — список собеседований с фильтрацией (в т.ч. has_video)
    POST /api/interviews/      — создать собеседование (admin и менеджер; HR/outstaff — нет)
    GET /api/interviews/{id}/  — детали собеседования
    PATCH /api/interviews/{id}/ — обновить (admin и менеджер по scope queryset; HR/outstaff — нет)
    GET /api/interviews/{id}/transcription-status/ — статус транскрипции (менеджер — только свои; admin, HR, outstaff — любые)
    GET /api/interviews/{id}/transcription-text/ — текст транскрипции (то же ограничение)

    Менеджер видит только свои собеседования.
    HR и outstaff — все собеседования на чтение (list, retrieve, транскрипция).
    Администратор видит все.
    """

    api_logger_name = 'interviews'
    pagination_class = InterviewListPagination

    def get_permissions(self):
        action = getattr(self, 'action', None)
        if action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsInterviewWriteRole()]
        if action == 'transcribe':
            return [IsAdminOrMentorRole()]
        return [IsManagerOrAdmin()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InterviewFullSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return InterviewCreateUpdateSerializer
        return InterviewFullSerializer

    def get_queryset(self):
        qs = interview_list.build_interview_api_list_queryset(
            self.request,
            view_action=self.action,
        )
        order_by = self.request.query_params.get('order_by', 'id')
        order_dir = self.request.query_params.get('order_dir', 'desc')
        return interview_list.apply_interview_ordering(
            qs,
            order_by,
            order_dir,
            valid_fields=interview_list.INTERVIEW_ORDER_FIELD_MAP,
            default_field='date',
        )

    @extend_schema(
        summary='Список собеседований',
        description=(
            'Возвращает список собеседований.\n\n'
            'Менеджер видит только свои собеседования. HR и outstaff — все.\n\n'
            '**Фильтры:**\n'
            '- `no_link` — только без ссылки (true/false)\n'
            '- `has_video` — только с загруженной записью (true) или без (false)\n'
            '- `date_from` — начало периода (YYYY-MM-DD)\n'
            '- `date_to` — конец периода (YYYY-MM-DD)\n'
            '- `intern_id` — ID студента\n'
            '- `interview_type` — тип: screening / tech / hr / final / mock / test / tech_questionnaire / cancelled\n'
            '- `direction_id` — ID направления'
        ),
        parameters=[
            OpenApiParameter('no_link', OpenApiTypes.BOOL, description='Только без ссылки'),
            OpenApiParameter(
                'has_video',
                OpenApiTypes.BOOL,
                description='true — только с непустым video_link; false — без загруженной записи',
            ),
            OpenApiParameter('date_from', OpenApiTypes.DATE, description='Дата от (YYYY-MM-DD)'),
            OpenApiParameter('date_to', OpenApiTypes.DATE, description='Дата до (YYYY-MM-DD)'),
            OpenApiParameter('intern_id', OpenApiTypes.INT, description='ID студента'),
            OpenApiParameter('interview_type', OpenApiTypes.STR, description='Тип собеседования'),
            OpenApiParameter('direction_id', OpenApiTypes.INT, description='ID направления'),
        ],
        tags=['Интервью'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Детали собеседования',
        description='Возвращает полную информацию о собеседовании.',
        tags=['Интервью'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        if not getattr(user, 'is_admin', False) and not getattr(user, 'is_superuser', False):
            serializer.save(manager_email=user.email)
        else:
            serializer.save()

    @extend_schema(
        summary='Создать собеседование',
        description='Создаёт новое собеседование. Только для администраторов.',
        tags=['Интервью'],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Обновить собеседование (PUT)',
        description='Полное обновление собеседования. Только для администраторов.',
        tags=['Интервью'],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Обновить собеседование',
        description='Частичное обновление собеседования. Только для администраторов.',
        tags=['Интервью'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Удалить собеседование',
        description='Удаление записи. Только администратор.',
        tags=['Интервью'],
        responses={204: {'description': 'Удалено'}},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary='Запустить транскрипцию видео',
        description='Ставит задачу транскрипции в очередь. Администратор или ментор.',
        tags=['Интервью'],
        responses={200: {'description': 'Очередь / уже выполняется'}, 400: {'description': 'Нет URL медиа'}},
    )
    @action(detail=True, methods=['post'], url_path='transcribe', permission_classes=[IsAdminOrMentorRole])
    def transcribe(self, request, pk=None):
        from core.logging_mixins import get_user_label_for_log  # noqa: PLC0415

        payload, code = transcribe_interview_payload(
            int(pk), log_user_label=get_user_label_for_log(request),
        )
        return Response(payload, status=code)

    @extend_schema(
        summary='Статус транскрипции',
        description=(
            'Поллинг статуса транскрипции. '
            'Менеджер — только по своим собеседованиям; администратор, HR, outstaff и mentor — по любому id.'
        ),
        tags=['Интервью'],
        responses={200: {'description': 'Статус и сообщение об ошибке (если есть)'}},
    )
    @action(
        detail=True,
        methods=['get'],
        url_path='transcription-status',
        permission_classes=[IsManagerOrAdmin],
    )
    def transcription_status(self, request, pk=None):
        interview = self.get_object()
        payload, code = transcription_status_payload(interview.pk)
        return Response(payload, status=code)

    @extend_schema(
        summary='Текст транскрипции',
        description=(
            'Готовый текст при статусе completed. '
            'Менеджер — только свои собеседования; администратор, HR, outstaff и mentor — любой id.'
        ),
        tags=['Интервью'],
        responses={200: {'description': 'Текст'}, 404: {'description': 'Не готово'}},
    )
    @action(
        detail=True,
        methods=['get'],
        url_path='transcription-text',
        permission_classes=[IsManagerOrAdmin],
    )
    def transcription_text(self, request, pk=None):
        interview = self.get_object()
        payload, code = transcription_text_payload(interview.pk)
        return Response(payload, status=code)
