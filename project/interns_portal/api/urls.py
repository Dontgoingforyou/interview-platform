from django.urls import path

from .views import (
    InternPortalInterviewListAPIView,
    InternPortalUploadTaskStatusAPIView,
    InternPortalVideoUploadAPIView,
)

urlpatterns = [
    path(
        'interns-portal/interviews/',
        InternPortalInterviewListAPIView.as_view(),
        name='api_intern_portal_interviews',
    ),
    path(
        'interns-portal/interviews/<int:interview_id>/upload/',
        InternPortalVideoUploadAPIView.as_view(),
        name='api_intern_portal_upload',
    ),
    path(
        'interns-portal/upload-tasks/<str:task_id>/',
        InternPortalUploadTaskStatusAPIView.as_view(),
        name='api_intern_portal_upload_task',
    ),
]
