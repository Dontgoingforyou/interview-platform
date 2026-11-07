from django.urls import path

from .views import SemanticSearchAPIView, SimilarEntitiesAPIView, VectorStatsAPIView

app_name = 'vector_search'

urlpatterns = [
    path('search/', SemanticSearchAPIView.as_view(), name='semantic_search'),
    path('similar/', SimilarEntitiesAPIView.as_view(), name='similar_entities'),
    path('stats/', VectorStatsAPIView.as_view(), name='vector_stats'),
]
