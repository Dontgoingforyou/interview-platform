from django.urls import path

from .views import (
    KnowledgeBaseArticleDetailAPIView,
    KnowledgeBaseArticleListCreateAPIView,
    KnowledgeBaseSearchAPIView,
    KnowledgeBaseSectionDetailAPIView,
    KnowledgeBaseSectionListCreateAPIView,
)

urlpatterns = [
    path('knowledge-base/search/', KnowledgeBaseSearchAPIView.as_view(), name='kb_api_search'),
    path('knowledge-base/sections/', KnowledgeBaseSectionListCreateAPIView.as_view(), name='kb_api_sections'),
    path(
        'knowledge-base/sections/<str:section_id>/articles/<str:filename>/',
        KnowledgeBaseArticleDetailAPIView.as_view(),
        name='kb_api_article_detail',
    ),
    path(
        'knowledge-base/sections/<str:section_id>/articles/',
        KnowledgeBaseArticleListCreateAPIView.as_view(),
        name='kb_api_articles',
    ),
    path(
        'knowledge-base/sections/<str:section_id>/',
        KnowledgeBaseSectionDetailAPIView.as_view(),
        name='kb_api_section_detail',
    ),
]
