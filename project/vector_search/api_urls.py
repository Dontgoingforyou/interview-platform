"""
Точка подключения API vector_search к core/urls.py — делегирует в vector_search.api.urls.
"""
from django.urls import include, path

urlpatterns = [
    path('', include('vector_search.api.urls')),
]
