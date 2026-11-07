"""
Корневой conftest.py для установки переменных окружения до инициализации Django.
Этот файл загружается pytest раньше всех остальных conftest.py.

ВАЖНО: DISABLE_VECTOR_SIGNALS=1 отключает post_save/post_delete векторизации (vector_search.signals),
иначе при CELERY_TASK_ALWAYS_EAGER синхронно вызывается update_embedding_task и нужен OPENAI_API_KEY.

Секция env в pyproject.toml обрабатывает только плагин pytest-env; если он не загрузился или в CI
задана пустая строка DISABLE_VECTOR_SIGNALS=, setdefault не сработает — поэтому ниже принудительная
нормализация пустого значения.
"""
import os


def _ensure_pytest_django_env():
    """Выставляет DJANGO_TESTING и гарантированно отключает вектор-сигналы при пустом значении."""
    os.environ.setdefault('DJANGO_TESTING', '1')
    raw = os.environ.get('DISABLE_VECTOR_SIGNALS')
    if raw is None or (isinstance(raw, str) and raw.strip() == ''):
        os.environ['DISABLE_VECTOR_SIGNALS'] = '1'


def pytest_load_initial_conftests(early_config, parser, args):
    """
    Этот хук вызывается самым первым, до любой инициализации Django.
    Используем его для установки переменных окружения.
    """
    _ensure_pytest_django_env()


# Импорт conftest до django.setup() — дублируем на уровне модуля
_ensure_pytest_django_env()
