"""
Точка подключения API interns к core/urls.py — делегирует в interns.api.urls.
"""
from django.urls import include, path

urlpatterns = [
    path('', include('interns.api.urls')),
]
