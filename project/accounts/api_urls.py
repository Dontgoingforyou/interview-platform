from django.urls import path

from .api_views import LoginView

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='api_auth_login'),
]
