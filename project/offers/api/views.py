from django.db.models import Count
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsManagerOrAdmin, IsAdminRole
from core.logging_mixins import ApiCRUDLoggingMixin
from core.pagination import ListPagination

from ..drf_list_query import apply_offer_list_filters, apply_offer_ordering
from ..models import Offer
from ..serializers import OfferListSerializer, OfferDetailSerializer, OfferCreateUpdateSerializer


class OfferViewSet(ApiCRUDLoggingMixin, viewsets.ModelViewSet):
    """
    ViewSet для управления офферами студентов.

    Администратор видит все офферы.
    Менеджер видит офферы своих студентов (через intern.manager_email).
    """

    api_logger_name = 'offers.offer'
    pagination_class = ListPagination

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [IsManagerOrAdmin()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OfferDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return OfferCreateUpdateSerializer
        return OfferListSerializer

    def _role_scoped_base_qs(self):
        qs = Offer.objects.select_related('intern', 'direction')
        user = self.request.user
        if not getattr(user, 'is_admin', False):
            email = getattr(user, 'email', None)
            if email:
                qs = qs.filter(intern__manager_email=email)
        return qs

    def get_queryset(self):
        qs = self._role_scoped_base_qs()

        if self.action == 'retrieve':
            return qs

        if self.action == 'month_groups':
            return apply_offer_list_filters(qs, self.request.query_params)

        if self.action == 'list':
            qs = apply_offer_list_filters(qs, self.request.query_params)
            return apply_offer_ordering(qs, self.request.query_params)

        return qs

    @extend_schema(
        summary='Список офферов',
        description=(
            'Возвращает список офферов студентов.\n\n'
            'Менеджер видит офферы только своих студентов.\n\n'
            '**Фильтры:**\n'
            '- `search` / `q` — поиск по ФИО студента и названию компании\n'
            '- `intern_id` — ID студента\n'
            '- `direction_id` — ID направления\n'
            '- `year` — год оффера\n'
            '- `month` — месяц оффера (1–12)\n'
            '- `order_by`, `order_dir` — сортировка (asc/desc)\n\n'
            'Пагинация: `page`, `page_size` (до 100).'
        ),
        tags=['Офферы'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Группы офферов по месяцам',
        description=(
            'Уникальные пары (год, месяц) с количеством офферов, по убыванию периода.\n\n'
            'Те же фильтры, что у списка (`search`/`q`, `intern_id`, `direction_id`, `year`, `month`).\n'
            'Пагинация окон: `offset` (по умолчанию 0), `limit` (по умолчанию 3, макс. 50).'
        ),
        parameters=[
            OpenApiParameter('offset', int, required=False),
            OpenApiParameter('limit', int, required=False),
            OpenApiParameter('search', str, required=False),
            OpenApiParameter('q', str, required=False),
            OpenApiParameter('intern_id', int, required=False),
            OpenApiParameter('direction_id', int, required=False),
            OpenApiParameter('year', int, required=False),
            OpenApiParameter('month', int, required=False),
        ],
        tags=['Офферы'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'groups': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'year': {'type': 'integer'},
                                'month': {'type': 'integer'},
                                'total_count': {'type': 'integer'},
                            },
                        },
                    },
                    'offset': {'type': 'integer'},
                    'limit': {'type': 'integer'},
                    'has_more': {'type': 'boolean'},
                    'next_offset': {'type': 'integer', 'nullable': True},
                },
            }
        },
    )
    @action(detail=False, methods=['get'], url_path='month-groups')
    def month_groups(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        aggregated = (
            qs.values('year', 'month')
            .annotate(total_count=Count('id'))
            .order_by('-year', '-month')
        )

        try:
            offset = int(request.query_params.get('offset', 0) or 0)
        except (ValueError, TypeError):
            offset = 0
        offset = max(offset, 0)

        try:
            limit = int(request.query_params.get('limit', 3) or 3)
        except (ValueError, TypeError):
            limit = 3
        limit = min(max(limit, 1), 50)

        total_groups = aggregated.count()
        rows = aggregated[offset : offset + limit]
        groups = [
            {'year': row['year'], 'month': row['month'], 'total_count': row['total_count']}
            for row in rows
        ]
        next_offset = offset + limit if offset + limit < total_groups else None
        return Response(
            {
                'groups': groups,
                'offset': offset,
                'limit': limit,
                'has_more': next_offset is not None,
                'next_offset': next_offset,
            }
        )

    @extend_schema(
        summary='Детали оффера',
        description='Возвращает полную информацию об оффере по ID.',
        tags=['Офферы'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Создать оффер',
        description='Создаёт новый оффер для студента. Только для администраторов.',
        tags=['Офферы'],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Обновить оффер (PUT)',
        description='Полное обновление оффера. Только для администраторов.',
        tags=['Офферы'],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Обновить оффер (PATCH)',
        description='Частичное обновление оффера. Только для администраторов.',
        tags=['Офферы'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Удалить оффер',
        description='Удаляет оффер по ID. Доступно только администраторам (как удаление в классическом интерфейсе).',
        tags=['Офферы'],
        responses={204: None},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
