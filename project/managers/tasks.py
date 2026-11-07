import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

HIDDEN_MANAGER_TTL_DAYS = 90  # 3 месяца


@shared_task(name='managers.tasks.delete_stale_hidden_managers', soft_time_limit=55, time_limit=60)
def delete_stale_hidden_managers():
    """
    Удаляет скрытых менеджеров, которых не возвращали в активный пул 3 месяца.

    Условие удаления: is_active=False И hidden_at < (сейчас − 90 дней).
    Если менеджер зайдёт снова — запись воссоздастся автоматически из Keycloak.
    """
    from managers.models import Manager

    threshold = timezone.now() - timedelta(days=HIDDEN_MANAGER_TTL_DAYS)
    stale_qs = Manager.objects.filter(is_active=False, hidden_at__lt=threshold)

    managers_info = list(stale_qs.values_list('email', 'full_name'))
    count = len(managers_info)

    if not count:
        logger.info('Устаревших скрытых менеджеров не найдено.')
        return 0

    stale_qs.delete()

    for _email, full_name in managers_info:
        logger.info(
            'Удалён скрытый менеджер: %s, скрыт более %s дней назад.',
            full_name,
            HIDDEN_MANAGER_TTL_DAYS,
        )

    logger.info(f'Итого удалено скрытых менеджеров: {count}.')
    return count
