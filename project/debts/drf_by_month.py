from datetime import date

from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum


def resolve_debt_by_month_query(base_qs, query_params):
    """
    base_qs — уже с role scope и select_related.

    Returns:
        dict с ключами ok=True, qs, meta — или ok=False, error, status.
    """
    from debts.models import PaymentHistory

    month_from_str = query_params.get('month_from')
    year_from_str = query_params.get('year_from')
    month_to_str = query_params.get('month_to')
    year_to_str = query_params.get('year_to')

    try:
        month_from = int(month_from_str) if month_from_str else None
        year_from = int(year_from_str) if year_from_str else None
        month_to = int(month_to_str) if month_to_str else None
        year_to = int(year_to_str) if year_to_str else None
    except (ValueError, TypeError):
        return {'ok': False, 'error': 'Неверный формат месяца или года', 'status': 400}

    if not (year_from and month_from) or not (year_to and month_to):
        return {'ok': False, 'error': 'Укажите начальный и конечный месяц/год.', 'status': 400}

    if (year_to < year_from) or (year_to == year_from and month_to < month_from):
        return {'ok': False, 'error': 'Конечная дата не может быть раньше начальной.', 'status': 400}

    filter_months = []
    current_date = date(year=year_from, month=month_from, day=1)
    end_date = date(year=year_to, month=month_to, day=1)

    while current_date <= end_date:
        filter_months.append((current_date.year, current_date.month))
        current_date = current_date + relativedelta(months=1)

    payment_filters = Q()
    for year, month in filter_months:
        payment_filters |= Q(year=year, month=month)

    payment_debt_ids = PaymentHistory.objects.filter(payment_filters).values_list('debt_id', flat=True).distinct()

    qs = base_qs.filter(id__in=payment_debt_ids)

    payment_status_filter = query_params.get('payment_status_filter')
    if payment_status_filter == 'paying':
        paying_debt_ids = PaymentHistory.objects.filter(year=year_to, month=month_to).values_list(
            'debt_id', flat=True
        ).distinct()
        qs = qs.filter(id__in=paying_debt_ids).exclude(balance=0)
    elif payment_status_filter == 'not_paying':
        paying_debt_ids = PaymentHistory.objects.filter(year=year_to, month=month_to).values_list(
            'debt_id', flat=True
        ).distinct()
        qs = qs.exclude(id__in=paying_debt_ids).exclude(balance=0)
    elif payment_status_filter == 'paid_fully':
        qs = qs.filter(balance=0)

    final_debt_ids = list(qs.values_list('id', flat=True))

    payments_summary = (
        PaymentHistory.objects.filter(debt_id__in=final_debt_ids)
        .filter(payment_filters)
        .values('debt_id', 'year', 'month')
        .annotate(total_period_amount=Sum('amount'))
    )

    period_sums = {debt_id: {} for debt_id in final_debt_ids}
    total_period_sums = {}

    for p in payments_summary:
        debt_id = p['debt_id']
        month_str = f"{p['month']:02d}/{p['year'] % 100:02d}"
        amount = p.get('total_period_amount') or 0
        period_sums[debt_id][month_str] = amount
        total_period_sums[debt_id] = total_period_sums.get(debt_id, 0) + amount

    export_months = [f"{m:02d}/{y % 100:02d}" for y, m in filter_months]
    selected_period = f'{month_from:02d}/{year_from} - {month_to:02d}/{year_to}'

    meta = {
        'export_months': export_months,
        'selected_period': selected_period,
        'period_sums': period_sums,
        'total_period_sums': total_period_sums,
        'month_to': month_to,
        'year_to': year_to,
    }

    return {'ok': True, 'qs': qs.order_by('id'), 'meta': meta}


def highlight_sets_for_page(debts_page, month_to, year_to):
    """Подсветка строк для текущей страницы."""
    from debts.models import PaymentHistory

    debt_ids = [d.id for d in debts_page]
    debts_paid_fully = {d.id for d in debts_page if d.balance == 0}
    debts_to_highlight = set()

    if month_to and year_to and debt_ids:
        debts_with_payment = set(
            PaymentHistory.objects.filter(debt_id__in=debt_ids, year=year_to, month=month_to).values_list(
                'debt_id', flat=True
            ).distinct()
        )
        for d in debts_page:
            if d.id not in debts_with_payment and d.balance != 0:
                debts_to_highlight.add(d.id)

    return {'debts_paid_fully': debts_paid_fully, 'debts_to_highlight': debts_to_highlight}
