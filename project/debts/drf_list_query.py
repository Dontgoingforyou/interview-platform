from datetime import date

from dateutil.relativedelta import relativedelta
from django.db.models import Case, F, IntegerField, Q, When

from debts.models import PaymentHistory


def apply_debt_list_filters(qs, query_params):
    """Применяет фильтры из query params к queryset долгов."""
    q = query_params.get('search') or query_params.get('q')
    if q:
        qs = qs.filter(
            Q(intern__full_name__icontains=q)
            | Q(telegram_username__icontains=q)
            | Q(email__icontains=q)
            | Q(intern__telegram_username__icontains=q)
            | Q(intern__email__icontains=q)
        )

    direction_id = query_params.get('direction')
    if direction_id:
        try:
            qs = qs.filter(direction_id=int(direction_id))
        except (ValueError, TypeError):
            pass

    payment_status = query_params.get('payment_status')
    if payment_status:
        qs = qs.filter(payment_status=payment_status)

    intern_id = query_params.get('intern_id')
    if intern_id:
        try:
            qs = qs.filter(intern_id=int(intern_id))
        except (ValueError, TypeError):
            pass

    not_paid_filter = query_params.get('not_paid_filter')
    if not_paid_filter == '3months':
        today = date.today()
        last_3_months = []
        for i in range(3):
            month_date = today - relativedelta(months=i)
            last_3_months.append((month_date.year, month_date.month))
        payment_filters = Q()
        for year, month in last_3_months:
            payment_filters |= Q(year=year, month=month)
        debts_with_payments = (
            PaymentHistory.objects.filter(payment_filters).values_list('debt_id', flat=True).distinct()
        )
        act_date_threshold = today - relativedelta(months=3)
        qs = qs.exclude(id__in=debts_with_payments).filter(balance__gt=0, act_date__lt=act_date_threshold)

    act_date_filter = query_params.get('act_date_filter')
    act_date_from = query_params.get('act_date_from')
    act_date_to = query_params.get('act_date_to')
    today = date.today()
    if act_date_filter == 'today':
        qs = qs.filter(act_date=today)
    elif act_date_filter == 'this_month':
        qs = qs.filter(act_date__year=today.year, act_date__month=today.month)
    elif act_date_from and act_date_to:
        qs = qs.filter(act_date__gte=act_date_from, act_date__lte=act_date_to)
    elif act_date_from:
        qs = qs.filter(act_date__gte=act_date_from)
    elif act_date_to:
        qs = qs.filter(act_date__lte=act_date_to)

    return qs


def apply_debt_list_ordering(qs, query_params):
    """Сортировка: полностью оплатившие (balance=0) в конец, затем выбранное поле."""
    order_by = query_params.get('order_by', 'balance')
    order_dir = query_params.get('order_dir', 'desc')

    qs = qs.annotate(
        is_paid_fully=Case(
            When(balance=0, then=1),
            default=0,
            output_field=IntegerField(),
        )
    )

    valid_order_fields = {
        'id': 'id',
        'full_name': 'intern__full_name',
        'direction_id': 'direction_id',
        'total_amount': 'total_amount',
        'paid_amount': 'paid_amount',
        'balance': 'balance',
        'act_date': 'act_date',
        'payment_status': 'payment_status',
    }
    default_field = 'balance'
    field_name = valid_order_fields.get(order_by, default_field)

    if order_dir == 'desc':
        user_order = F(field_name).desc(nulls_last=True)
    else:
        user_order = F(field_name).asc(nulls_last=True)

    return qs.order_by('is_paid_fully', user_order)
