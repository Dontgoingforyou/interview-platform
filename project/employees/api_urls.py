"""
Точка подключения API employees к core/urls.py — делегирует в employees.api.urls.
"""
from django.urls import include, path

urlpatterns = [
    path('', include('employees.api.urls')),
]
