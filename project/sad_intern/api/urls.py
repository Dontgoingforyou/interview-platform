from django.urls import include, path
from rest_framework.routers import DefaultRouter

from sad_intern.sad_intern_analytics_drf import SadInternAnalyticsAPIView

from .import_views import SadInternImportAPIView
from .views import SadInternViewSet

router = DefaultRouter()
router.register(r'sad-interns', SadInternViewSet, basename='sad-intern')

urlpatterns = [
    path('analytics/sad-intern/', SadInternAnalyticsAPIView.as_view(), name='api_sad_intern_analytics'),
    path('sad-interns/import/', SadInternImportAPIView.as_view(), name='api_sad_intern_import'),
    path('', include(router.urls)),
]
