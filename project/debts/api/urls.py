"""
URL-маршруты REST API приложения debts (эталон: пакет api/ как в interviews).
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ..debt_analytics_drf import DebtAnalyticsAPIView
from .import_views import DebtImportAPIView
from .views import DebtViewSet

router = DefaultRouter()
router.register(r'debts', DebtViewSet, basename='debt')

urlpatterns = [
    path('analytics/debts/', DebtAnalyticsAPIView.as_view(), name='api_debt_analytics'),
    path('debts/import/', DebtImportAPIView.as_view(), name='api_debt_import'),
    path('', include(router.urls)),
]
