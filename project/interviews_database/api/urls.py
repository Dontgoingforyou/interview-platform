from django.urls import path

from .views import InterviewsDatabaseListAPIView

urlpatterns = [
    path('interviews-database/', InterviewsDatabaseListAPIView.as_view(), name='api_interviews_database_list'),
]
