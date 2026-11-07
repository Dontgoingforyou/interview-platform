"""
URLs для API Interview приложения.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .config_views import DeepgramBalanceAPIView
from .import_views import ImportTaskStatusAPIView, InterviewImportAPIView
from .interview_analytics import InterviewAnalyticsAPIView, InterviewTypeBreakdownAPIView
from .views import InterviewViewSet

router = DefaultRouter()
router.register(r'interviews', InterviewViewSet, basename='interview')

urlpatterns = [
    path('analytics/interviews/', InterviewAnalyticsAPIView.as_view(), name='interview_analytics_api'),
    path(
        'analytics/interviews/type-breakdown/',
        InterviewTypeBreakdownAPIView.as_view(),
        name='interview_type_breakdown_api',
    ),
    path('import/status/<str:task_id>/', ImportTaskStatusAPIView.as_view(), name='api_import_status'),
    path('interviews/import/', InterviewImportAPIView.as_view(), name='interview_import_api'),
    path('transcriptions/deepgram-balance/', DeepgramBalanceAPIView.as_view(), name='deepgram_balance_api'),
    path('', include(router.urls)),
]
