from django.db.models import F, Q

OFFER_VALID_ORDER_FIELDS = {
    'id': 'id',
    'intern_name': 'intern__full_name',
    'direction_name': 'direction_id',
    'company': 'company',
    'amount': 'amount',
    'month': 'month',
    'year': 'year',
}


def apply_offer_list_filters(qs, query_params):
    """Применяет фильтры из query params к queryset офферов."""
    q = query_params.get('search') or query_params.get('q')
    if q:
        qs = qs.filter(
            Q(intern__full_name__icontains=q) | Q(company__icontains=q),
        )

    intern_id = query_params.get('intern_id')
    if intern_id:
        try:
            qs = qs.filter(intern_id=int(intern_id))
        except (ValueError, TypeError):
            pass

    direction_id = query_params.get('direction_id')
    if direction_id:
        try:
            qs = qs.filter(direction_id=int(direction_id))
        except (ValueError, TypeError):
            pass

    year = query_params.get('year')
    if year:
        try:
            qs = qs.filter(year=int(year))
        except (ValueError, TypeError):
            pass

    month = query_params.get('month')
    if month:
        try:
            qs = qs.filter(month=int(month))
        except (ValueError, TypeError):
            pass

    return qs


def apply_offer_ordering(qs, query_params):
    """Сортировка по order_by / order_dir (whitelist)."""
    order_by = query_params.get('order_by') or 'year'
    order_dir = (query_params.get('order_dir') or 'desc').lower()
    if order_dir not in ('asc', 'desc'):
        order_dir = 'desc'

    if order_by in OFFER_VALID_ORDER_FIELDS:
        field_name = OFFER_VALID_ORDER_FIELDS[order_by]
        if order_dir == 'desc':
            return qs.order_by(F(field_name).desc(nulls_last=True))
        return qs.order_by(F(field_name).asc(nulls_last=True))

    if order_dir == 'desc':
        return qs.order_by(
            F('year').desc(nulls_last=True),
            F('month').desc(nulls_last=True),
        )
    return qs.order_by(
        F('year').asc(nulls_last=True),
        F('month').asc(nulls_last=True),
    )
