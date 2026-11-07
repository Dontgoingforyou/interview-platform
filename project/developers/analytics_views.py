import logging
from datetime import date, timedelta

from django.db.models import Avg, Count, Q, Max, Min
from core.constants import MONTH_NAMES, INTERVIEW_TYPE_CANCELLED
from directions.models import Direction
from interviews.models import Interview
from interns.models import Intern
from offers.models import Offer

logger = logging.getLogger(__name__)

# Допустимые поля сортировки для разработчиков
_VALID_DEVELOPER_ORDER_FIELDS = frozenset({'full_name', 'direction_name', 'last_activity', 'interview_count'})


def get_developers_stats(direction_id=None, search_query=None):
    """
    Возвращает список разработчиков со статистикой по собеседованиям.

    Источник пар (intern_id, direction_id) — объединение двух таблиц:
    - Offer: разработчики с полученными офферами (в т.ч. без интервью → interview_count=0)
    - Interview (кроме cancelled): участники активного процесса

    Итого 4 запроса к БД:
    1. Offer → уникальные пары
    2. Interview → уникальные пары
    3. Interview GROUP BY → агрегаты
    4. Intern → ФИО

    Args:
        direction_id: ID направления для фильтрации (str, int или None)
        search_query: строка поиска по ФИО (без учёта регистра), или None

    Returns:
        list[dict]: список разработчиков без сортировки
    """
    direction_id_int = None
    if direction_id:
        try:
            direction_id_int = int(direction_id)
        except (ValueError, TypeError):
            pass

    offer_qs = Offer.objects.all()
    if direction_id_int:
        offer_qs = offer_qs.filter(direction_id=direction_id_int)
    offer_pairs = set(offer_qs.values_list('intern_id', 'direction_id').order_by().distinct())

    interview_qs = Interview.objects.exclude(interview_type=INTERVIEW_TYPE_CANCELLED)
    if direction_id_int:
        interview_qs = interview_qs.filter(direction_id=direction_id_int)
    interview_pairs = set(interview_qs.values_list('intern_id', 'direction_id').order_by().distinct())

    all_pairs = offer_pairs | interview_pairs
    if not all_pairs:
        return []

    intern_ids = {pair[0] for pair in all_pairs}
    direction_ids = {pair[1] for pair in all_pairs if pair[1]}
    directions_dict = {}
    if direction_ids:
        directions_dict = {d.id: d.name for d in Direction.objects.filter(id__in=direction_ids)}

    interviews_agg = {
        (item['intern_id'], item['direction_id']): item
        for item in Interview.objects
        .exclude(interview_type=INTERVIEW_TYPE_CANCELLED)
        .filter(intern_id__in=intern_ids)
        .values('intern_id', 'direction_id')
        .annotate(
            interview_count=Count('id'),
            first_interview_date=Min('date'),
            last_interview_date=Max('date'),
        )
        .order_by()
    }

    interns_dict = {
        intern.id: intern
        for intern in Intern.objects.filter(id__in=intern_ids).only('id', 'full_name', 'email')
    }

    search_lower = search_query.lower() if search_query else None
    result = []
    for intern_id, dir_id in all_pairs:
        intern = interns_dict.get(intern_id)
        if not intern:
            continue
        if search_lower and search_lower not in intern.full_name.lower():
            continue
        item = interviews_agg.get((intern_id, dir_id))
        direction_name = directions_dict.get(dir_id, '—') if dir_id else '—'
        if item:
            result.append({
                'intern': intern,
                'intern_id': intern_id,
                'direction_id': dir_id,
                'direction_name': direction_name,
                'last_activity': item['last_interview_date'],
                'interview_count': item['interview_count'],
                'first_interview_date': item['first_interview_date'],
                'last_interview_date': item['last_interview_date'],
            })
        else:
            result.append({
                'intern': intern,
                'intern_id': intern_id,
                'direction_id': dir_id,
                'direction_name': direction_name,
                'last_activity': None,
                'interview_count': 0,
                'first_interview_date': None,
                'last_interview_date': None,
            })
    return result


def apply_developers_ordering(data, order_by='full_name', order_dir='asc'):
    """
    Сортирует список разработчиков (результат get_developers_stats).

    Args:
        data: список dict от get_developers_stats()
        order_by: поле сортировки (full_name, direction_name, last_activity, interview_count)
        order_dir: направление ('asc' или 'desc')

    Returns:
        list[dict]: тот же список, отсортированный in-place
    """
    if order_by not in _VALID_DEVELOPER_ORDER_FIELDS:
        order_by = 'full_name'
    reverse = (order_dir == 'desc')

    if order_by == 'full_name':
        data.sort(key=lambda x: x['intern'].full_name or '', reverse=reverse)
    elif order_by == 'direction_name':
        data.sort(key=lambda x: (x.get('direction_name') or '').lower(), reverse=reverse)
    elif order_by == 'last_activity':
        data.sort(
            key=lambda x: x['last_activity'] if x['last_activity'] else date(1900, 1, 1),
            reverse=reverse,
        )
    elif order_by == 'interview_count':
        data.sort(key=lambda x: x['interview_count'] or 0, reverse=reverse)
    return data


def compute_developer_analytics():
    """Вычисляет аналитику по разработчикам. Вызывается из API-вью и из list-вью для прогрева кэша."""
    return get_developer_analytics_data()


def get_developer_analytics_data():
    """
    Возвращает словарь с аналитикой по разработчикам.

    Метрики:
    - active-specialists: количество активных специалистов (активность за 15 дней)
    - offers-this-year: количество специалистов, получивших офферы за текущий год
    - avg-offer-last-month: средний размер оффера за последний месяц
    - fastest-direction: направление с минимальным средним временем от первого до последнего интервью
    - top-direction-offers: направление с наибольшим количеством офферов
    - chart_months: данные для графика активности по месяцам

    Returns:
        dict: словарь с аналитическими данными
    """
    today = date.today()

    # 1. Активные специалисты — интервью за последние 15 дней
    days_ago_15 = today - timedelta(days=15)
    active_specialists = (
        Interview.objects
        .filter(date__gte=days_ago_15)
        .exclude(interview_type=INTERVIEW_TYPE_CANCELLED)
        .values('intern_id')
        .distinct()
        .count()
    )

    # 2. Офферы за текущий год
    current_year = today.year
    offers_this_year = (
        Offer.objects
        .filter(year=current_year)
        .values('intern_id', 'direction_id')
        .distinct()
        .count()
    )

    # 3. Средний оффер за последний месяц
    last_month = today.month - 1 if today.month > 1 else 12
    last_month_year = today.year if today.month > 1 else today.year - 1

    avg_offer_last_month = (
        Offer.objects
        .filter(year=last_month_year, month=last_month)
        .aggregate(Avg('amount'))['amount__avg'] or 0
    )

    # 4. Топ направление по скорости — мин. среднее время от первого до последнего интервью
    recent_offers_qs = Offer.objects.filter(year=last_month_year, month=last_month)
    recent_offers_pairs = list(recent_offers_qs.values_list('intern_id', 'direction_id').distinct())

    fastest_direction_id = None
    fastest_avg_days = 0

    if recent_offers_pairs:
        if last_month == 12:
            next_month, next_year = 1, last_month_year + 1
        else:
            next_month, next_year = last_month + 1, last_month_year
        last_day_of_offer_month = date(next_year, next_month, 1) - timedelta(days=1)

        # Фильтруем интервью по intern_id (а не OR-цепочкой из пар)
        intern_ids_in_offers = {pair[0] for pair in recent_offers_pairs}
        interviews_agg = (
            Interview.objects
            .filter(intern_id__in=intern_ids_in_offers, date__lte=last_day_of_offer_month)
            .exclude(interview_type=INTERVIEW_TYPE_CANCELLED)
            .values('intern_id', 'direction_id')
            .annotate(
                interview_count=Count('id'),
                first_interview=Min('date'),
                last_interview=Max('date'),
            )
        )
        interviews_dict = {
            (item['intern_id'], item['direction_id']): item
            for item in interviews_agg
        }

        direction_stats = {}
        for intern_id, direction_id in recent_offers_pairs:
            interview_data = interviews_dict.get((intern_id, direction_id))
            if not interview_data:
                continue
            if interview_data['first_interview'] == interview_data['last_interview']:
                continue
            days_spent = (interview_data['last_interview'] - interview_data['first_interview']).days + 1
            direction_stats.setdefault(direction_id, []).append(days_spent)

        fastest_avg_days_val = float('inf')
        for direction_id, days_list in direction_stats.items():
            avg_days = sum(days_list) / len(days_list)
            if avg_days < fastest_avg_days_val:
                fastest_avg_days_val = avg_days
                fastest_direction_id = direction_id

        if fastest_direction_id:
            fastest_avg_days = fastest_avg_days_val

    # 5. Топ направление по количеству офферов за последний месяц
    top_directions_offers = (
        Offer.objects
        .filter(year=last_month_year, month=last_month)
        .values('direction_id')
        .annotate(offer_count=Count('id'))
        .order_by('-offer_count')
        .first()
    )
    top_direction_offer_id = top_directions_offers['direction_id'] if top_directions_offers else None

    # Один запрос за обоими именами направлений
    direction_ids_to_fetch = {d for d in [fastest_direction_id, top_direction_offer_id] if d}
    directions_lookup = {}
    if direction_ids_to_fetch:
        directions_lookup = {
            d.id: d.name for d in Direction.objects.filter(id__in=direction_ids_to_fetch)
        }

    fastest_direction_name = directions_lookup.get(fastest_direction_id, '—')
    top_direction_name = directions_lookup.get(top_direction_offer_id, '—')

    # График: количество офферов за последние 12 месяцев
    last_12_months = []
    for i in range(12):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        last_12_months.append((year, month))

    month_filters = Q()
    for year, month in last_12_months:
        month_filters |= Q(year=year, month=month)

    monthly_offers = (
        Offer.objects
        .filter(month_filters)
        .values('year', 'month')
        .annotate(offer_count=Count('id'))
        .order_by('year', 'month')
    )

    months_labels = []
    months_data = []
    for item in monthly_offers:
        month_name = MONTH_NAMES[item['month'] - 1]
        months_labels.append(f"{month_name} {item['year']} г.")
        months_data.append(item['offer_count'])

    return {
        'active-specialists': active_specialists,
        'offers-this-year': offers_this_year,
        'avg-offer-last-month': round(avg_offer_last_month, 2) if avg_offer_last_month else 0,
        'fastest-direction': fastest_direction_name,
        'fastest-direction-days': round(fastest_avg_days, 1) if fastest_direction_id else None,
        'top-direction-offers': top_direction_name,
        'chart_months': {
            'labels': months_labels,
            'data': months_data,
        },
        'tooltips': {
            'active-specialists': 'Активность за последние 15 дней.',
            'offers-this-year': 'За последний год.',
            'avg-offer-last-month': 'Средний оффер.',
            'fastest-direction': 'За последний месяц. Среднее количество дней от первого до финального собеседования.',
            'top-direction-offers': 'За последний месяц.',
        },
    }


def get_developers_data(filters=None):
    """Получает данные разработчиков с учётом фильтров для экспорта в Excel."""
    filters = filters or {}
    direction_id = filters.get('direction')
    search_query = filters.get('q') or None
    order_by = filters.get('order_by', 'full_name')
    order_dir = filters.get('order_dir', 'asc')

    developers_data_raw = get_developers_stats(direction_id=direction_id, search_query=search_query)
    apply_developers_ordering(developers_data_raw, order_by=order_by, order_dir=order_dir)

    # direction_name уже присутствует в каждом элементе из get_developers_stats —
    # повторный запрос Direction.objects не нужен
    return [
        {
            'ФИО': dev['intern'].full_name if dev['intern'] else '—',
            'Направление': dev.get('direction_name') or '—',
            'Последняя активность': dev['last_activity'].strftime('%d.%m.%Y') if dev['last_activity'] else '—',
            'Количество интервью': dev['interview_count'],
        }
        for dev in developers_data_raw
    ]
