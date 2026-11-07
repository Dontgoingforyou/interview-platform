from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import ListAPIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsManagerOrAdmin
from core.pagination import ListPagination
from interviews.interview_list import (
    INTERVIEW_ORDER_FIELD_MAP,
    apply_interview_ordering,
    build_interviews_database_api_queryset,
    query_params_from_request,
)
from interviews.serializers import InterviewFullSerializer


@extend_schema(
    summary='Список базы собеседований',
    description=(
        'Собеседования с записью созвона (непустой `link`), загруженным видео (`video_link`) '
        'или активной загрузкой (`upload_task_id`). '
        'Все менеджеры видят все записи (без ограничения по своему email); '
        'доступ ограничен ролью (IsManagerOrAdmin).'
    ),
    parameters=[
        OpenApiParameter('page', OpenApiTypes.INT, description='Номер страницы'),
        OpenApiParameter('page_size', OpenApiTypes.INT, description='Размер страницы (по умолчанию 20)'),
        OpenApiParameter('q', OpenApiTypes.STR, description='Поиск: ФИО, HR, подстрока в ссылках записи'),
        OpenApiParameter('company', OpenApiTypes.INT, description='ID компании'),
        OpenApiParameter('direction', OpenApiTypes.INT, description='ID направления'),
        OpenApiParameter('direction_id', OpenApiTypes.INT, description='Алиас direction'),
        OpenApiParameter('manager', OpenApiTypes.STR, description='Email менеджера'),
        OpenApiParameter('interview_type', OpenApiTypes.STR, description='Тип собеседования'),
        OpenApiParameter(
            'transcription',
            OpenApiTypes.STR,
            description=(
                'Фильтр по транскрипции: completed — готовый текст; failed — ошибка; '
                'in_progress — ожидает или в процессе'
            ),
        ),
        OpenApiParameter('order_by', OpenApiTypes.STR, description='Поле сортировки (id, full_name, company_name, …)'),
        OpenApiParameter('order_dir', OpenApiTypes.STR, description='asc или desc'),
    ],
    tags=['База собеседований'],
)
class InterviewsDatabaseListAPIView(ListAPIView):
    """GET — пагинированный список для React и внешних клиентов."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    serializer_class = InterviewFullSerializer
    permission_classes = [IsManagerOrAdmin]
    pagination_class = ListPagination

    def get_queryset(self):
        qs = build_interviews_database_api_queryset(self.request)
        params = query_params_from_request(self.request)
        order_by = params.get('order_by', 'date')
        order_dir = params.get('order_dir', 'desc')
        return apply_interview_ordering(
            qs,
            str(order_by),
            str(order_dir).lower(),
            valid_fields=INTERVIEW_ORDER_FIELD_MAP,
            default_field='date',
        )
