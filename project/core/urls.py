import os
import sys
from django.urls import path, include
from django.conf import settings
from .mcp_views import HttpMcpView
from .views import (
    GetInternDataView,
    ImportTaskStatusView,
    ProtectedSwaggerView,
    ProtectedSchemaView,
    ProtectedRedocView,
    ReactSPAView,
)

urlpatterns = [
    path('mcp', HttpMcpView.as_view(), name='http_mcp'),
    path('mcp/', HttpMcpView.as_view(), name='http_mcp_slash'),
    path('accounts/', include('accounts.urls')),

    # REST API (v1)
    path('api/', include('accounts.api_urls')),
    path('api/', include('interviews.api_urls')),
    path('api/', include('interns.api_urls')),
    path('api/', include('managers.api_urls')),
    path('api/', include('debts.api_urls')),
    path('api/', include('offers.api_urls')),
    path('api/', include('employees.api_urls')),
    path('api/', include('sad_intern.api_urls')),
    path('api/', include('developers.api_urls')),
    path('api/', include('companies.api_urls')),
    path('api/', include('directions.api_urls')),
    path('api/', include('knowledge_base_app.api_urls')),
    path('api/', include('interviews_database.api_urls')),
    path('api/', include('interns_portal.api_urls')),

    # Прочие API endpoints
    path('api/intern-data/', GetInternDataView.as_view(), name='get_intern_data'),

    # Swagger/OpenAPI: view отдаёт 404 при DEBUG=False; при DEBUG=True — только менеджер и админ
    path('api/schema/', ProtectedSchemaView.as_view(), name='schema'),
    path('api/docs/', ProtectedSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', ProtectedRedocView.as_view(url_name='schema'), name='redoc'),

    # Универсальный эндпоинт для проверки статуса импорта (используется всеми модулями)
    path('import/status/<str:task_id>/', ImportTaskStatusView.as_view(), name='import_status'),

    path('', ReactSPAView.as_view(), name='interview_list'),
    path('<path:path>', ReactSPAView.as_view(), name='react_spa_catchall'),
]

# Векторный поиск API — только если приложение включено (не DISABLE_VECTOR).
# Вставляем ПЕРЕД catch-all (<path:path>), иначе POST /api/vector/search/ перехватывается
# ReactSPAView и возвращает 405 Method Not Allowed.
if 'vector_search' in settings.INSTALLED_APPS:
    urlpatterns.insert(-1, path('api/vector/', include('vector_search.api_urls')))

# Django Debug Toolbar URLs (только для разработки, не в тестах)
if settings.DEBUG and not (os.getenv('DJANGO_TESTING') == '1' or 'test' in sys.argv or 'pytest' in sys.modules):
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
