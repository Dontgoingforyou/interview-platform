from django.urls import include, path

urlpatterns = [
    path('', include('managers.api.urls')),
]
