import os
from celery import Celery
from celery.signals import setup_logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig
    from django.conf import settings
    dictConfig(settings.LOGGING)


# При отключённой векторизации регистрируем заглушки, чтобы старые/случайные
# сообщения в очереди не вызывали "unregistered task" в воркере.
# Если vector_search уже в INSTALLED_APPS (например, после reload в тестах),
# autodiscover мог зарегистрировать реальные задачи — снимаем их явно.
_VECTOR_NOOP_TASK_NAMES = (
    'vector_search.update_embedding',
    'vector_search.delete_embedding',
    'vector_search.reindex_all',
    'vector_search.vectorize_batch',
)

if os.getenv('DISABLE_VECTOR', '').lower() in ('true', '1', 'yes'):
    for _task_name in _VECTOR_NOOP_TASK_NAMES:
        app.tasks.pop(_task_name, None)

    @app.task(name='vector_search.update_embedding', bind=True)
    def _noop_update_embedding(self, entity_type: str, entity_id: int):
        pass

    @app.task(name='vector_search.delete_embedding', bind=True)
    def _noop_delete_embedding(self, entity_type: str, entity_id: int):
        pass

    @app.task(name='vector_search.reindex_all', bind=True)
    def _noop_reindex_all(self, entity_type: str = None):
        pass

    @app.task(name='vector_search.vectorize_batch', bind=True)
    def _noop_vectorize_batch(self, entity_type: str, entity_ids: list, batch_size: int = 32):
        pass
