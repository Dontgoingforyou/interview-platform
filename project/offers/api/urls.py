from django.urls import path
from rest_framework.routers import DefaultRouter

from ..offer_analytics_drf import OfferAnalyticsAPIView
from .import_views import OfferImportAPIView
from .views import OfferViewSet

router = DefaultRouter()
router.register(r'offers', OfferViewSet, basename='offer')

urlpatterns = [
    path('analytics/offers/', OfferAnalyticsAPIView.as_view(), name='api_offer_analytics'),
    path('offers/import/', OfferImportAPIView.as_view(), name='api_offer_import'),
] + router.urls
