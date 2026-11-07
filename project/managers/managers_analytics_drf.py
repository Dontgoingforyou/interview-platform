import logging

from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsManagerOrAdmin
from core.decorators import ANALYTICS_CACHE_TIMEOUT, get_analytics_cache_key
from .analytics_views import compute_managers_analytics, compute_managers_observations
from .dashboard_service import build_managers_dashboard_table

logger = logging.getLogger('managers')

_CACHE_ANALYTICS = 'managers_analytics_api'


def _table_rows_for_response() -> list[dict]:
    rows = build_managers_dashboard_table()
    result = []
    for row in rows:
        lid = row['last_interview_date']
        result.append(
            {
                'email': row['email'],
                'full_name': row['full_name'],
                'candidates_count': row['candidates_count'],
                'hot_candidates_count': row['hot_candidates_count'],
                'active_candidates_count': row['active_candidates_count'],
                'portfolio_candidates_count': row['portfolio_candidates_count'],
                'interviews_count': row['interviews_count'],
                'successful_candidates_count': row['successful_candidates_count'],
                'directions': row['directions'],
                'last_interview_date': lid.isoformat() if lid else None,
            }
        )
    return result


class _ManagersDashboardAuthAPIView(APIView):
    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            raise NotAuthenticated()


@extend_schema(
    summary='Аналитика команды менеджеров',
    description='KPI по менеджерам (те же данные, что у compute_managers_analytics).',
    tags=['Менеджеры'],
)
class ManagersAnalyticsAPIView(_ManagersDashboardAuthAPIView):
    """GET /api/analytics/managers/ — кэш совместим с ManagersListView и legacy API."""

    def get(self, request):
        params = request.query_params.dict()
        cache_key = get_analytics_cache_key(_CACHE_ANALYTICS, params)

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        data = compute_managers_analytics()
        try:
            cache.set(cache_key, data, timeout=ANALYTICS_CACHE_TIMEOUT)
        except Exception as e:
            logger.warning('Не удалось записать кэш аналитики менеджеров: %s', e)

        return Response(data)


@extend_schema(
    summary='Наблюдения по менеджерам',
    description='Агрегаты для текстовых инсайтов (список по менеджерам, лидеры и т.д.).',
    tags=['Менеджеры'],
)
class ManagersObservationsAPIView(_ManagersDashboardAuthAPIView):
    """GET /api/analytics/managers/observations/"""

    def get(self, request):
        return Response(compute_managers_observations())


@extend_schema(
    summary='Таблица менеджеров дашборда',
    description='Строки таблицы «Менеджеры»: кандидаты, интервью, направления, даты.',
    tags=['Менеджеры'],
)
class ManagersDashboardTableAPIView(_ManagersDashboardAuthAPIView):
    """GET /api/analytics/managers/table/"""

    def get(self, request):
        return Response({'results': _table_rows_for_response()})
