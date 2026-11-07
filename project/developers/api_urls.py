from django.urls import include, path

urlpatterns = [
    path('', include('developers.api.urls')),
]
