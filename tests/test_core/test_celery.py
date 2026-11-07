"""
Тесты для core/celery.py.

Покрывают:
- Конфигурация приложения Celery (app, config_from_object, autodiscover_tasks).
- Сигнал setup_logging: config_loggers не падает при вызове.
- Noop-задачи vector_search (если зарегистрированы при DISABLE_VECTOR) — вызов не падает.
"""
import importlib

import pytest


class TestCeleryApp:
    """Конфигурация Celery-приложения."""

    def test_app_name_is_core(self):
        from core.celery import app
        assert app.main == 'core'

    def test_app_has_conf(self):
        from core.celery import app
        assert hasattr(app, 'conf')

    def test_app_tasks_registry_exists(self):
        from core.celery import app
        assert app.tasks is not None

    def test_autodiscover_tasks_configured(self):
        from core.celery import app
        assert app.conf.include is not None or len(app.tasks) > 0


class TestSetupLogging:
    """Сигнал setup_logging подключает config_loggers."""

    def test_config_loggers_callable_no_error(self):
        from core.celery import config_loggers
        config_loggers()


class TestDisableVectorNoopTasks:
    """Noop-задачи vector_search при DISABLE_VECTOR=true."""

    @pytest.fixture
    def celery_with_disable_vector(self, monkeypatch):
        monkeypatch.setenv('DISABLE_VECTOR', 'true')
        import core.celery as celery_module

        importlib.reload(celery_module)
        yield celery_module
        monkeypatch.delenv('DISABLE_VECTOR', raising=False)
        importlib.reload(celery_module)

    def test_noop_tasks_registered(self, celery_with_disable_vector):
        app = celery_with_disable_vector.app
        expected = {
            'vector_search.update_embedding',
            'vector_search.delete_embedding',
            'vector_search.reindex_all',
            'vector_search.vectorize_batch',
        }
        assert expected.issubset(app.tasks.keys())

    def test_noop_tasks_invokable(self, celery_with_disable_vector):
        app = celery_with_disable_vector.app
        assert 'noop' in app.tasks['vector_search.update_embedding'].run.__name__
        assert 'noop' in app.tasks['vector_search.delete_embedding'].run.__name__
        assert 'noop' in app.tasks['vector_search.reindex_all'].run.__name__
        assert 'noop' in app.tasks['vector_search.vectorize_batch'].run.__name__

        app.tasks['vector_search.update_embedding'].run(entity_type='intern', entity_id=1)
        app.tasks['vector_search.delete_embedding'].run(entity_type='intern', entity_id=1)
        app.tasks['vector_search.reindex_all'].run(entity_type='intern')
        app.tasks['vector_search.vectorize_batch'].run(
            entity_type='intern',
            entity_ids=[1, 2],
            batch_size=32,
        )


@pytest.mark.django_db(databases=['default'])
class TestNoopTasksIfRegistered:
    """Если при импорте был DISABLE_VECTOR, noop-задачи можно вызвать без ошибки."""

    def test_update_embedding_noop_invokable_if_present(self):
        from core.celery import app
        if 'vector_search.update_embedding' not in app.tasks:
            pytest.skip('noop зарегистрирована только при DISABLE_VECTOR')
        app.tasks['vector_search.update_embedding'].run(entity_type='intern', entity_id=1)

    def test_delete_embedding_noop_invokable_if_present(self):
        from core.celery import app
        if 'vector_search.delete_embedding' not in app.tasks:
            pytest.skip('noop зарегистрирована только при DISABLE_VECTOR')
        app.tasks['vector_search.delete_embedding'].run(entity_type='intern', entity_id=1)

    def test_reindex_all_noop_invokable_if_present(self):
        from core.celery import app
        if 'vector_search.reindex_all' not in app.tasks:
            pytest.skip('noop зарегистрирована только при DISABLE_VECTOR')
        app.tasks['vector_search.reindex_all'].run(entity_type='intern')

    def test_vectorize_batch_noop_invokable_if_present(self):
        from core.celery import app
        if 'vector_search.vectorize_batch' not in app.tasks:
            pytest.skip('noop зарегистрирована только при DISABLE_VECTOR')
        app.tasks['vector_search.vectorize_batch'].run(
            entity_type='intern', entity_ids=[1, 2], batch_size=32
        )
