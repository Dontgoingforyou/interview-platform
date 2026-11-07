import logging

from celery.result import AsyncResult

logger = logging.getLogger(__name__)


def celery_task_status_payload(task_id: str) -> dict:
    """Состояние задачи Celery в формате, совместимом с ImportTaskStatusView и SPA."""
    task: AsyncResult = AsyncResult(task_id)
    try:
        task_state = task.state
    except ValueError as e:
        logger.warning('Ошибка при получении статуса задачи %s: %s', task_id, e)
        return {
            'state': 'FAILURE',
            'status': (
                'Задача завершена с устаревшим форматом данных. Попробуйте запустить импорт заново.'
            ),
            'current': 0,
            'total': 100,
        }

    if task_state == 'PENDING':
        return {
            'state': task.state,
            'status': 'Ожидание начала импорта...',
            'current': 0,
            'total': 100,
        }
    if task_state == 'PROGRESS':
        return {
            'state': task_state,
            'status': task.info.get('status', ''),
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 100),
        }
    if task_state == 'SUCCESS':
        return {
            'state': task_state,
            'status': 'Импорт завершен успешно',
            'current': 100,
            'total': 100,
            'result': task.result,
        }
    if task_state == 'FAILURE':
        return {
            'state': task_state,
            'status': str(task.info),
            'current': 0,
            'total': 100,
        }
    return {
        'state': task_state,
        'status': str(task.info) if task.info else 'Неизвестное состояние',
        'current': 0,
        'total': 100,
    }
