"""
Общая фильтрация и сортировка списка студентов (Django ListView и DRF InternViewSet в interns.api.views).
"""
from django.db.models import F, Q

from core.constants import INTERN_INACTIVE_STATUSES, INTERN_STATUS_ACTIVE

INTERN_LIST_ORDER_FIELD_MAP = {
    'id': 'id',
    'full_name': 'full_name',
    'direction_name': 'direction_id',
    'group': 'group',
    'city': 'city',
    'type_of_training': 'type_of_training',
    'real_interview_date': 'real_interview_date',
    'manager_name': 'manager_email',
    'manual_status': 'manual_status',
}


def apply_intern_text_search(qs, q):
    """Поиск по ФИО, email, группе, нанимающему HR (как в InternListView)."""
    if not q or not str(q).strip():
        return qs
    term = str(q).strip()
    return qs.filter(
        Q(full_name__icontains=term)
        | Q(email__icontains=term)
        | Q(group__icontains=term)
        | Q(hiring_hr__icontains=term)
        | Q(city__icontains=term)
    )


def apply_intern_status_filters(qs, *, status=None):
    """Фильтр списка студентов по статусу."""
    if status == INTERN_STATUS_ACTIVE:
        qs = qs.filter(
            Q(manual_status=INTERN_STATUS_ACTIVE) | Q(manual_status__isnull=True) | Q(manual_status='')
        ).filter(Q(manager_email__isnull=False) & ~Q(manager_email=''))
    elif status in INTERN_INACTIVE_STATUSES:
        qs = qs.filter(manual_status=status)
    return qs


def apply_intern_manager_direction_group_filters(qs, *, manager_email=None, direction_id=None, group=None):
    """Менеджер (email), направление, группа — фильтры списка студентов в API."""
    if manager_email and '@' in str(manager_email):
        qs = qs.filter(manager_email=manager_email)
    if direction_id not in (None, ''):
        try:
            qs = qs.filter(direction_id=int(direction_id))
        except (ValueError, TypeError):
            pass
    if group:
        qs = qs.filter(group__icontains=group)
    return qs


def apply_intern_list_ordering(
    qs,
    order_by,
    order_dir,
    *,
    default_order_by='id',
    default_order_dir='desc',
):
    """Сортировка списка студентов в API (F-выражения для связанных полей)."""
    if order_by not in INTERN_LIST_ORDER_FIELD_MAP:
        order_by = default_order_by
    if order_dir not in ('asc', 'desc'):
        order_dir = default_order_dir
    field_name = INTERN_LIST_ORDER_FIELD_MAP[order_by]
    if order_dir == 'desc':
        return qs.order_by(F(field_name).desc(nulls_last=True))
    return qs.order_by(F(field_name).asc(nulls_last=True))
