# Функция find_intern_by_name перенесена в core.intern_utils для устранения дублирования
# Импортируем из общего модуля для обратной совместимости
from core.intern_utils import find_intern_by_name  # noqa: F401
