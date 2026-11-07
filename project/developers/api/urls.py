from django.urls import path

from .export_views import (
    DeveloperChartExportAPIView,
    DeveloperMetricsExportAPIView,
    DeveloperTableExportAPIView,
)
from .views import DeveloperAnalyticsAPIView, DeveloperStatsAPIView

urlpatterns = [
    path('developers/', DeveloperStatsAPIView.as_view(), name='api-developer-stats'),
    path('developers/export/table/', DeveloperTableExportAPIView.as_view(), name='api-developers-export-table'),
    path('developers/export/metrics/', DeveloperMetricsExportAPIView.as_view(), name='api-developers-export-metrics'),
    path('developers/export/chart/', DeveloperChartExportAPIView.as_view(), name='api-developers-export-chart'),
    path('analytics/developers/', DeveloperAnalyticsAPIView.as_view(), name='developer_analytics_api'),
]
