import logging

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.views import APIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsManagerOrAdmin

from ..services import DeveloperExportService

logger = logging.getLogger('developers')


def _user_label_for_log(request: Request) -> str:
    from core.logging_mixins import get_user_label_for_log

    return get_user_label_for_log(request)


def _table_filters_from_request(request: Request) -> dict:
    direction = request.query_params.get('direction_id') or request.query_params.get('direction')
    q = request.query_params.get('q')
    order_by = request.query_params.get('order_by', 'full_name')
    order_dir = request.query_params.get('order_dir', 'desc')
    filters = {
        'direction': direction,
        'q': q,
        'order_by': order_by,
        'order_dir': order_dir,
    }
    return {k: v for k, v in filters.items() if v is not None}


# Константы вместо миксина: mypy не считает совместимыми объявления с APIView в общем предке.
_DEVELOPER_EXPORT_PERMISSION_CLASSES = [IsManagerOrAdmin]


class DeveloperTableExportAPIView(APIView):
    """GET — Excel с таблицей разработчиков (учитывает фильтры в query)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = _DEVELOPER_EXPORT_PERMISSION_CLASSES

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        filters = _table_filters_from_request(request)
        logger.info(
            'Экспорт таблицы разработчиков (API, фильтры: %s) — %s',
            filters,
            _user_label_for_log(request),
        )
        return DeveloperExportService.export_table_to_excel(filters)


class DeveloperMetricsExportAPIView(APIView):
    """GET — Excel с метриками разработчиков."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = _DEVELOPER_EXPORT_PERMISSION_CLASSES

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        logger.info('Экспорт метрик разработчиков (API) — %s', _user_label_for_log(request))
        return DeveloperExportService.export_metrics_to_excel()


class DeveloperChartExportAPIView(APIView):
    """GET — Excel с данными графика активности по месяцам."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = _DEVELOPER_EXPORT_PERMISSION_CLASSES

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        logger.info('Экспорт графика активности разработчиков (API) — %s', _user_label_for_log(request))
        return DeveloperExportService.export_chart_to_excel()
