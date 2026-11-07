"""
Точка подключения API interviews к core/urls.py — делегирует в interviews.api.urls.
"""
from django.urls import include, path

urlpatterns = [
    path('', include('interviews.api.urls')),
]
