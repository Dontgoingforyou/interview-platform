from django.urls import path
from rest_framework.routers import DefaultRouter

from ..managers_analytics_drf import (
    ManagersAnalyticsAPIView,
    ManagersDashboardTableAPIView,
    ManagersObservationsAPIView,
)
from .views import ManagerViewSet

router = DefaultRouter()
router.register(r'managers', ManagerViewSet, basename='manager')

urlpatterns = [
    path('analytics/managers/observations/', ManagersObservationsAPIView.as_view(), name='api_managers_observations'),
    path('analytics/managers/table/', ManagersDashboardTableAPIView.as_view(), name='api_managers_dashboard_table'),
    path('analytics/managers/', ManagersAnalyticsAPIView.as_view(), name='api_managers_analytics'),
] + router.urls + [
    path('users/me/', ManagerViewSet.as_view({'get': 'me'}), name='user-me'),
]
