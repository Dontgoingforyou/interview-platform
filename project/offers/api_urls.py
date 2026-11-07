from django.urls import include, path

urlpatterns = [
    path('', include('offers.api.urls')),
]
