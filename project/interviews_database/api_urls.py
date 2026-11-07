from django.urls import include, path

urlpatterns = [
    path('', include('interviews_database.api.urls')),
]
