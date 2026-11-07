import os
import sys

from django.apps import AppConfig


def _is_test_like_process() -> bool:
    """True в pytest / django test / CI без полноценных ключей API для векторизации."""
    return (
        os.environ.get('DJANGO_TESTING') == '1'
        or 'test' in sys.argv
        or 'pytest' in sys.modules
    )


class VectorSearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vector_search'
    verbose_name = 'Векторный поиск'

    def ready(self):
        """Подключаем сигналы при инициализации приложения."""
        # В тестах не подключаем сигналы здесь: eager-Celery вызывает update_embedding_task без OPENAI_API_KEY.
        # Тесты vector_search подключают сигналы явным import vector_search.signals (см. test_vector_search/conftest).
        # Даже если сигналы подключены, обработчики проверяют DISABLE_VECTOR_SIGNALS перед вызовом задачи.
        if _is_test_like_process():
            return
        if not os.getenv('DISABLE_VECTOR_SIGNALS'):
            import vector_search.signals  # noqa
