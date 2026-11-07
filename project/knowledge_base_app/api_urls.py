from django.urls import include, path

urlpatterns = [
    path('', include('knowledge_base_app.api.urls')),
]
