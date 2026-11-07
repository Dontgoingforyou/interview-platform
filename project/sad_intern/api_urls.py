from django.urls import include, path

urlpatterns = [
    path('', include('sad_intern.api.urls')),
]
