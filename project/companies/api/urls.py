from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CompanyMergeAPIView, CompanyStatsAPIView, CompanyViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')

urlpatterns = [
    path('companies/stats/', CompanyStatsAPIView.as_view(), name='company_stats_api'),
    path('companies/merge/', CompanyMergeAPIView.as_view(), name='company_merge_api'),
    path('', include(router.urls)),
]
