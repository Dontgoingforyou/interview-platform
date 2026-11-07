"""
Точка подключения API debts к core/urls.py — делегирует в debts.api.urls.
"""
from django.urls import include, path

urlpatterns = [
    path('', include('debts.api.urls')),
]
