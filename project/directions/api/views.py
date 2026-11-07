from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsAdminRole, IsManagerOrAdmin
from core.decorators import ANALYTICS_CACHE_TIMEOUT, get_analytics_cache_key
from core.logging_mixins import ApiCRUDLoggingMixin

from ..analytics_views import compute_direction_metrics, compute_direction_observations
from ..models import Direction
from ..serializers import DirectionSerializer


class DirectionMetricsAPIView(APIView):
    """Метрики по направлениям (карточки, таблица, данные для графиков)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            raise NotAuthenticated()

    @extend_schema(
        summary='Аналитика по направлениям',
        description=(
            'Агрегаты по собеседованиям по направлениям.\n\n'
            '**Параметры:** `date_filter` (YYYY-MM-DD), `direction` (id), `min_conversion` (%).'
        ),
        tags=['Направления'],
    )
    def get(self, request):
        params = request.query_params.dict()
        cache_key = get_analytics_cache_key('direction_metrics_api', params)
        data = cache.get(cache_key)
        if data is None:
            data = compute_direction_metrics(params)
            cache.set(cache_key, data, ANALYTICS_CACHE_TIMEOUT)
        return Response(data)


class DirectionsObservationsAPIView(APIView):
    """Структурированные данные для текстовых наблюдений по направлениям."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            raise NotAuthenticated()

    @extend_schema(
        summary='Наблюдения по направлениям',
        description='Данные для формирования блока наблюдений на странице метрик.',
        tags=['Направления'],
    )
    def get(self, request):
        params = request.query_params.dict()
        cache_key = get_analytics_cache_key('directions_observations_api', params)
        data = cache.get(cache_key)
        if data is None:
            data = compute_direction_observations()
            cache.set(cache_key, data, ANALYTICS_CACHE_TIMEOUT)
        return Response(data)


class DirectionViewSet(ApiCRUDLoggingMixin, viewsets.ModelViewSet):
    """
    Список и детали направлений; создание — только администратор.
    """

    api_logger_name = 'directions.direction'
    serializer_class = DirectionSerializer
    queryset = Direction.objects.all().order_by('name')
    http_method_names = ['get', 'post', 'head', 'options']

    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminRole()]
        return [IsManagerOrAdmin()]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def perform_create(self, serializer):
        super().perform_create(serializer)
        cache.delete(get_analytics_cache_key('direction_metrics_api', {}))
        cache.delete(get_analytics_cache_key('directions_observations_api', {}))

    @extend_schema(
        summary='Список направлений',
        description=(
            'Возвращает список направлений.\n\n'
            '**Фильтр:** `q` — поиск по названию.'
        ),
        tags=['Направления'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Детали направления',
        description='Возвращает информацию о направлении по id.',
        tags=['Направления'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Создать направление',
        description='Доступно только администраторам.',
        tags=['Направления'],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
