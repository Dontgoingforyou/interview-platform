"""
Вспомогательные функции для приложения managers.
"""

from core.constants import INTERN_INACTIVE_STATUSES


def get_inactive_intern_ids():
    """
    Возвращает множество id интернов, считающихся неактивными:
    - имеют оффер в системе
    - или имеют manual_status из INTERN_INACTIVE_STATUSES ('ушел' / 'оффер')

    Используется во views и analytics_views для исключения таких интернов из расчётов.
    """
    from offers.models import Offer
    from interns.models import Intern

    inactive = set(Offer.objects.values_list('intern_id', flat=True))
    inactive.update(
        Intern.objects.filter(
            manual_status__in=INTERN_INACTIVE_STATUSES
        ).values_list('id', flat=True)
    )
    return inactive
