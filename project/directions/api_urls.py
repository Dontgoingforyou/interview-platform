from django.urls import include, path

urlpatterns = [
    path('', include('directions.api.urls')),
]
