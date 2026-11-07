from django.urls import include, path

urlpatterns = [
    path('', include('interns_portal.api.urls')),
]
