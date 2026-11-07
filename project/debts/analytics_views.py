from django.http import JsonResponse
from django.db.models import Sum, Max
from decimal import Decimal
from core.decorators import manager_required_api, cache_analytics
from .models import Debt, PaymentHistory


def compute_debt_analytics():
    """Вычисляет аналитику долгов. Вызывается из API-вью и из list-вью для прогрева кэша."""
    qs = Debt.objects.all()

    # Вычисление метрик

    # Общее кол-во людей в таблице
    total_people = qs.count()

    # Активные должники. Считается количество записей Debt, где поле balance > 0
    active_debtors = qs.filter(balance__gt=0).count()

    # Закрытых договоров. Считается количество записей Debt, где поле balance <= 0
    closed_contracts = qs.filter(balance__lte=0).count()

    # Общая сумма договоров. Суммируются значение поля total_amount для всех записей Debt
    total_sum_obj = qs.aggregate(total=Sum('total_amount'))
    total_sum = total_sum_obj['total'] or Decimal('0')

    # Выплачено по таблице. Суммируется значение поля paid_amount для всех записей Debt
    paid_sum_obj = qs.aggregate(total=Sum('paid_amount'))
    paid_sum = paid_sum_obj['total'] or Decimal('0')

    # Остаток к получению. Суммируем значение поля balance для всех записей Debt
    # (balance вычисляется как total_amount - paid_amount)
    outstanding_sum_obj = qs.aggregate(total=Sum('balance'))
    outstanding_sum = outstanding_sum_obj['total'] or Decimal('0')

    # Средний остаток на активного должника. Делим общий остаток (outstanding_sum) на количество активных должников
    avg_outstanding = Decimal('0')
    if active_debtors > 0:
        avg_outstanding = outstanding_sum / active_debtors

    # Средний прогресс выплат (%). Считаем процент людей, которые стабильно платят каждый месяц
    # Стабильно платящие - это те, у кого есть платежи за каждый из последних 3 месяцев
    avg_progress = Decimal('0')
    if total_people > 0:
        from datetime import date
        from dateutil.relativedelta import relativedelta
        from django.db.models import Q
        from collections import defaultdict

        today = date.today()
        last_3_months = []
        for i in range(3):
            month_date = today - relativedelta(months=i)
            last_3_months.append((month_date.year, month_date.month))

        # ОПТИМИЗАЦИЯ: Делаем один запрос и обрабатываем в Python
        payment_filters = Q()
        for year, month in last_3_months:
            payment_filters |= Q(year=year, month=month)

        # Получаем все платежи за последние 3 месяца одним запросом
        payments = PaymentHistory.objects.filter(payment_filters).values('debt_id', 'year', 'month')

        # Группируем по debt_id и считаем уникальные пары (year, month)
        debt_months = defaultdict(set)
        for payment in payments:
            debt_id = payment['debt_id']
            period = (payment['year'], payment['month'])
            debt_months[debt_id].add(period)

        # Считаем долги, у которых есть платежи за все 3 месяца
        stable_payers_count = sum(1 for months_set in debt_months.values() if len(months_set) >= 3)

        avg_progress = (Decimal(stable_payers_count) / Decimal(total_people)) * 100

    # Максимальный остаток. Находим самое большое значение поля balance среди всех записей Debt
    top_outstanding_obj = qs.aggregate(max_balance=Max('balance'))
    top_outstanding_amount = top_outstanding_obj['max_balance'] or Decimal('0')
    top_outstanding_person = ''
    if top_outstanding_amount > 0:
        top_debt_record = qs.filter(balance=top_outstanding_amount).select_related('intern').first()
        if top_debt_record:
            top_outstanding_person = top_debt_record.intern.full_name

    # Кол-во людей без платежей. Находим ID всех долгов, для которых существуют записи в PaymentHistory
    people_with_payments = PaymentHistory.objects.values_list('debt__id', flat=True).distinct()
    people_without_payments = qs.exclude(id__in=people_with_payments).count()

    data = {
        'total': total_people,
        'active': active_debtors,
        'closed': closed_contracts,
        'sum-total': float(total_sum),
        'sum-paid': float(paid_sum),
        'sum-out': float(outstanding_sum),
        'avg-out': round(float(avg_outstanding), 2),
        'avg-progress': round(float(avg_progress), 2),
        'top-out': float(top_outstanding_amount),
        'top-out-person': top_outstanding_person,
        'no-payments': people_without_payments,
        'tooltips': {
            'total': 'Сколько было устроено/создано актов за все время.',
            'active': 'Сколько людей до сих пор платят.',
            'closed': 'Людей, которые все выплатили.',
            'sum-total': 'Всего сумма всех договоров.',
            'sum-paid': 'Всего выплачено.',
            'sum-out': 'Сколько осталось выплатить',
            'avg-out': 'Ср. знач. сколько должен примерно каждый (кто не выплатил всю сумму).',
            'avg-progress': 'Процент людей, которые стабильно платят каждый месяц.',
            'top-out': 'Самый большой долг.',
            'no-payments': 'Ни разу не платили по договору.',
        }
    }

    return data


@manager_required_api
@cache_analytics()
def debt_analytics_api(request):
    """Подсчет аналитики долгов на основе существующих данных."""
    return JsonResponse(compute_debt_analytics())
