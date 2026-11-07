import logging

from django.core.cache import cache
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsManagerOrAdmin
from core.decorators import ANALYTICS_CACHE_TIMEOUT, get_analytics_cache_key
from interviews.analytics_views import compute_interview_analytics
from interviews import interview_list

logger = logging.getLogger('interviews')

_CACHE_VIEW_NAME = 'interview_analytics_api'


class InterviewAnalyticsAPIView(APIView):
    """
    Аналитика собеседований (метрики за 30 дней и за всё время).

    Ключ кэша совпадает с legacy interview_analytics_api для тех же GET-параметров.
    """

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            raise NotAuthenticated()

    @extend_schema(
        summary='Аналитика по собеседованиям',
        tags=['Аналитика'],
    )
    def get(self, request):
        params = request.query_params.dict()
        cache_key = get_analytics_cache_key(_CACHE_VIEW_NAME, params)

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        data = compute_interview_analytics(params)
        try:
            cache.set(cache_key, data, timeout=ANALYTICS_CACHE_TIMEOUT)
        except Exception as e:
            logger.warning('Не удалось записать кэш аналитики собеседований: %s', e)

        return Response(data)


class InterviewTypeBreakdownAPIView(APIView):
    """
    Статистика по типам собеседований для текущих фильтров (как блок в list.html).
    Параметры query совпадают с GET /api/interviews/.
    """

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            raise NotAuthenticated()

    @extend_schema(
        summary='Разбивка собеседований по типам',
        description='Статистика по типам для текущих фильтров списка собеседований.',
        tags=['Аналитика'],
    )
    def get(self, request):
        qs = interview_list.build_interview_api_list_queryset(request)
        data = interview_list.interview_type_statistics_payload(qs)
        return Response(data)
