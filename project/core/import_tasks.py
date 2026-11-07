"""
Универсальные Celery задачи для асинхронного импорта данных.
"""
import logging
import os
import importlib
from celery import shared_task
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from core.file_utils import read_file_content, validate_required_columns, rename_columns

logger = logging.getLogger('import')

_IMPORT_TASK_OWNER_PREFIX = 'import_task_owner'
_IMPORT_TASK_OWNER_TTL = 3600


def register_import_task_owner(task_id: str, user_email: str) -> None:
    """Сохраняет владельца задачи импорта в кэше (TTL 1 час)."""
    cache.set(f'{_IMPORT_TASK_OWNER_PREFIX}:{task_id}', user_email, _IMPORT_TASK_OWNER_TTL)


def get_import_task_owner(task_id: str) -> str | None:
    """Возвращает email владельца задачи импорта или None (задача до введения проверки)."""
    return cache.get(f'{_IMPORT_TASK_OWNER_PREFIX}:{task_id}')


@shared_task(bind=True)
def async_import_from_file(self, file_path, service_class_path, column_mapping=None, required_columns=None):
    """
    Универсальная задача для асинхронного импорта любых данных через Celery.

    Args:
        file_path: Путь к загруженному файлу
        service_class_path: Путь к классу сервиса (например, 'debts.services.DebtImportService')
        column_mapping: Словарь маппинга колонок (опционально)
        required_columns: Список обязательных колонок (опционально)

    Returns:
        dict: Результаты импорта {'status': 'success', 'created': N, 'skipped': M, 'errors': K}
    """
    try:
        logger.info(f"Запуск фонового импорта из файла: {file_path}")

        # Обновляем состояние: чтение файла (5%)
        self.update_state(
            state='PROGRESS',
            meta={'current': 5, 'total': 100, 'status': 'Чтение файла...'}
        )

        # Читаем файл
        with open(file_path, 'rb') as f:
            uploaded = SimpleUploadedFile(os.path.basename(file_path), f.read())
            df = read_file_content(uploaded)

        # Обновляем состояние: проверка колонок (10%)
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Проверка структуры файла...'}
        )

        # Проверяем и переименовываем колонки
        if required_columns:
            if column_mapping:
                is_valid, missing_headers = validate_required_columns(df, required_columns, column_mapping)
                if not is_valid:
                    msg = f"В файле отсутствуют обязательные столбцы: {', '.join(missing_headers)}"
                    logger.error(msg)
                    return {"status": "error", "message": msg}
                df = rename_columns(df, column_mapping)
            else:
                is_valid, missing_headers = validate_required_columns(df, required_columns)
                if not is_valid:
                    msg = f"В файле отсутствуют обязательные столбцы: {', '.join(missing_headers)}"
                    logger.error(msg)
                    return {"status": "error", "message": msg}

        # Обновляем состояние: начало импорта (15%)
        self.update_state(
            state='PROGRESS',
            meta={'current': 15, 'total': 100, 'status': 'Начало импорта данных...'}
        )

        # Динамически импортируем класс сервиса
        module_path, class_name = service_class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        service_class = getattr(module, class_name)

        # Создаем callback для обновления прогресса
        def progress_callback(processed, total):
            """Callback для обновления прогресса от сервиса импорта"""
            # Прогресс от 15% до 95% (оставляем 5% на финализацию)
            progress_percent = 15 + int((processed / total) * 80)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': progress_percent,
                    'total': 100,
                    'status': f'Обработка строк: {processed}/{total}'
                }
            )

        # Запускаем сервис импорта
        service = service_class(df, progress_callback=progress_callback)
        created, skipped, duplicates, errors_log = service.run()

        # Обновляем состояние: завершение (95%)
        self.update_state(
            state='PROGRESS',
            meta={'current': 95, 'total': 100, 'status': 'Завершение импорта...'}
        )

        logger.info(
            f"Фоновый импорт завершен. "
            f"Создано: {created}, Дубликатов: {duplicates}, Ошибок: {skipped} ({len(errors_log)} записей)"
        )

        # Ограничиваем количество ошибок для отправки клиенту (макс 20)
        errors_list_to_send = errors_log[:20] if len(errors_log) > 20 else errors_log

        return {
            "status": "success",
            "created": created,
            "duplicates": duplicates,
            "skipped": skipped,
            "errors": len(errors_log),
            "errors_list": errors_list_to_send
        }

    except Exception as e:
        logger.exception(f"Ошибка фонового импорта: {e}")
        self.update_state(
            state='FAILURE',
            meta={'status': f'Ошибка: {str(e)}'}
        )
        raise
    finally:
        # Удаляем временный файл
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning('Не удалось удалить временный файл %s: %s', file_path, e)
