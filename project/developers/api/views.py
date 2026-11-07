from django.core.cache import cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsManagerOrAdmin
from core.decorators import ANALYTICS_CACHE_TIMEOUT, get_analytics_cache_key
from core.pagination import ListPagination

from ..analytics_views import (
    apply_developers_ordering,
    get_developer_analytics_data,
    get_developers_stats,
)
from ..serializers import DeveloperStatSerializer

_VALID_ORDER_FIELDS = frozenset({'full_name', 'direction_name', 'last_activity', 'interview_count'})


def _resolve_direction_filter(query_params):
    """direction_id или direction (как в HTML-форме списка)."""
    v = query_params.get('direction_id')
    if v is not None and str(v).strip() != '':
        return v
    v = query_params.get('direction')
    if v is not None and str(v).strip() != '':
        return v
    return None


def _build_developer_rows(direction_id, search_query, order_by, order_dir):
    raw = get_developers_stats(direction_id=direction_id, search_query=search_query)
    apply_developers_ordering(raw, order_by=order_by, order_dir=order_dir)
    return [
        {
            'intern_id': item['intern_id'],
            'intern_name': item['intern'].full_name,
            'direction_id': item['direction_id'],
            'direction_name': item.get('direction_name'),
            'interview_count': item['interview_count'],
            'first_interview_date': item['first_interview_date'],
            'last_interview_date': item['last_interview_date'],
            'id': item['intern_id'],
            'full_name': item['intern'].full_name,
            'email': getattr(item['intern'], 'email', None) or None,
        }
        for item in raw
    ]


class DeveloperStatsAPIView(APIView):
    """
    Пагинированный список разработчиков со статистикой по собеседованиям
    (интервью + офферы).
    """

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]
    pagination_class = ListPagination

    @extend_schema(
        summary='Статистика по разработчикам',
        description=(
            'Пагинированный список специалистов с агрегированной статистикой.\n\n'
            '**Фильтры:** `direction_id` или `direction`, `q` (ФИО).\n'
            '**Сортировка:** `order_by`, `order_dir` (asc|desc).'
        ),
        parameters=[
            OpenApiParameter('direction_id', OpenApiTypes.INT, description='Фильтр по направлению'),
            OpenApiParameter('direction', OpenApiTypes.INT, description='Синоним direction_id'),
            OpenApiParameter('q', OpenApiTypes.STR, description='Поиск по ФИО'),
            OpenApiParameter('order_by', OpenApiTypes.STR, description='Поле сортировки'),
            OpenApiParameter('order_dir', OpenApiTypes.STR, description='asc или desc'),
            OpenApiParameter('page', OpenApiTypes.INT, description='Номер страницы'),
        ],
        responses={200: DeveloperStatSerializer(many=True)},
        tags=['Разработчики'],
    )
    def get(self, request):
        direction_id = _resolve_direction_filter(request.query_params)
        search_query = request.query_params.get('q', '').strip() or None
        order_by = request.query_params.get('order_by', 'full_name')
        order_dir = request.query_params.get('order_dir', 'desc')
        if order_by not in _VALID_ORDER_FIELDS:
            order_by = 'full_name'

        result = _build_developer_rows(direction_id, search_query, order_by, order_dir)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(result, request, view=self)
        serializer = DeveloperStatSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class DeveloperAnalyticsAPIView(APIView):
    """Аналитика по разработчикам (метрики, график по месяцам, подсказки)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            raise NotAuthenticated()

    @extend_schema(
        summary='Аналитика по разработчикам',
        tags=['Аналитика'],
    )
    def get(self, request):
        cache_key = get_analytics_cache_key('developer_analytics_api')
        data = cache.get(cache_key)
        if data is None:
            data = get_developer_analytics_data()
            cache.set(cache_key, data, ANALYTICS_CACHE_TIMEOUT)
        return Response(data)
