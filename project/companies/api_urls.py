from django.urls import include, path

urlpatterns = [
    path('', include('companies.api.urls')),
]
