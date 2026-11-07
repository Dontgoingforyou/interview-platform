"""
URL-маршруты REST API приложения interns (эталон: пакет api/ как в interviews).
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .import_views import InternImportAPIView, InternImportDatesAPIView, InternSyncImportAPIView
from .views import InternViewSet

router = DefaultRouter()
router.register(r'interns', InternViewSet, basename='intern')

urlpatterns = [
    path('interns/import/', InternImportAPIView.as_view(), name='intern_import_api'),
    path('interns/import-sync/', InternSyncImportAPIView.as_view(), name='intern_sync_import_api'),
    path('interns/import-dates/', InternImportDatesAPIView.as_view(), name='intern_import_dates_api'),
    path('', include(router.urls)),
]
