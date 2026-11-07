"""
Тесты для core/urls.py.

Покрывают:
- resolve/reverse для основных URL (accounts, SPA root, import_status, api schema).
- Включение vector_search в urlpatterns при наличии в INSTALLED_APPS.
"""
import pytest
from django.urls import reverse, resolve


class TestCoreUrlResolve:
    """Проверка разрешения основных URL."""

    def test_admin_not_exposed(self):
        """Django Admin URL удалён из urls.py — /admin/ не должен резолвиться в admin-namespace."""
        match = resolve('/admin/')
        assert match.namespace != 'admin', (
            'URL /admin/ не должен указывать на Django Admin (admin-namespace). '
            'Убедитесь, что path("admin/", admin.site.urls) удалён из core/urls.py.'
        )

    def test_accounts_included(self):
        match = resolve('/accounts/login/')
        assert match.func is not None

    def test_help_resolves_to_spa(self):
        match = resolve('/help/')
        assert match.url_name == 'react_spa_catchall'

    def test_import_status_resolves(self):
        match = resolve('/import/status/some-task-id/')
        assert match.url_name == 'import_status'
        assert match.kwargs['task_id'] == 'some-task-id'

    def test_api_schema_resolves(self):
        match = resolve('/api/schema/')
        assert match.url_name == 'schema'

    def test_reverse_interview_list_is_root(self):
        url = reverse('interview_list')
        assert url == '/'

    def test_reverse_import_status(self):
        url = reverse('import_status', kwargs={'task_id': 'abc-123'})
        assert url == '/import/status/abc-123/'

    def test_intern_data_api_resolves(self):
        match = resolve('/api/intern-data/')
        assert match.url_name == 'get_intern_data'

    def test_api_docs_resolves(self):
        match = resolve('/api/docs/')
        assert match.url_name == 'swagger-ui'


class TestVectorSearchUrls:
    """URL векторного поиска добавляются только при включённом приложении."""

    def test_vector_route_resolvable_if_app_loaded(self):
        """Если vector_search в INSTALLED_APPS, маршрут /api/vector/search/ резолвится."""
        from django.conf import settings
        if 'vector_search' not in settings.INSTALLED_APPS:
            pytest.skip('vector_search не в INSTALLED_APPS')
        match = resolve('/api/vector/search/')
        assert match.func is not None
