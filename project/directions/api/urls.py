from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DirectionMetricsAPIView, DirectionViewSet, DirectionsObservationsAPIView

router = DefaultRouter()
router.register(r'directions', DirectionViewSet, basename='direction')

urlpatterns = [
    path('analytics/directions/', DirectionMetricsAPIView.as_view(), name='directions_analytics_api'),
    path(
        'observations/directions/',
        DirectionsObservationsAPIView.as_view(),
        name='directions_observations_api',
    ),
    path('', include(router.urls)),
]
