from django.db.models import Count, Max, Min, Q
from django.db.models.functions import ExtractMonth, ExtractYear

from datetime import datetime, timedelta, date

from directions.models import Direction
from core.constants import (
    INTERVIEW_TYPE_CANCELLED,
    INTERVIEW_TYPE_TECH_QUESTIONNAIRE,
    INTERVIEW_TYPE_SCREENING,
    INTERVIEW_TYPE_TECH,
    INTERVIEW_TYPE_FINAL,
)
from interviews.models import Interview


def compute_direction_metrics(params=None):
    """Вычисляет аналитику по направлениям. Вызывается из API-вью и из list-вью для прогрева кэша."""
    params = params or {}
    date_filter = params.get('date_filter')
    direction_id = params.get('direction')
    min_conversion = params.get('min_conversion')

    # Установка целевой даты
    if date_filter:
        try:
            target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        except ValueError:
            target_date = datetime.now().date()
    else:
        target_date = datetime.now().date()

    base_qs = Interview.objects.exclude(interview_type=INTERVIEW_TYPE_TECH_QUESTIONNAIRE)
    if direction_id:
        try:
            base_qs = base_qs.filter(direction_id=int(direction_id))
        except (ValueError, TypeError):
            direction_id = None

    # Все направления (для отображения в т.ч. с нулевой активностью)
    all_directions_objs = list(Direction.objects.all().order_by('name'))
    directions_map = {d.id: d.name for d in all_directions_objs}

    # Фильтруем только нужные даты
    before_target = base_qs.filter(date__lte=target_date)
    after_target = base_qs.filter(date__gt=target_date)
    last_30_days = base_qs.filter(date__gte=target_date - timedelta(days=30))
    last_90_days = base_qs.filter(date__gte=target_date - timedelta(days=90))
    last_year = base_qs.filter(date__gte=target_date - timedelta(days=365))

    metrics_data = []
    total_interviews_count = 0
    total_candidates_count = 0
    total_upcoming_count = 0
    total_tech_interviews_count = 0

    # Группируем данные по направлениям
    direction_stats = (
        before_target
        .values('direction_id')
        .annotate(
            total_interviews=Count('id'),
            total_candidates=Count('intern__full_name', distinct=True),
            last_interview_date=Max('date'),
            screening_count=Count('id', filter=Q(interview_type=INTERVIEW_TYPE_SCREENING)),
            tech_count=Count('id', filter=Q(interview_type=INTERVIEW_TYPE_TECH)),
        )
    )

    upcoming_map = {
        item['direction_id']: item['cnt']
        for item in after_target.values('direction_id').annotate(cnt=Count('id'))
    }
    total_upcoming_count = sum(upcoming_map.values())

    for stat in direction_stats:
        dir_id = stat['direction_id']
        dir_name = directions_map.get(dir_id, f'ID: {dir_id}')

        screening_count = stat['screening_count']
        tech_count = stat['tech_count']

        conversion_rate = 0
        if screening_count > 0:
            conversion_rate = round((tech_count / screening_count) * 100, 2)

        # Проверяем фильтр по минимальной конверсии
        if min_conversion:
            try:
                min_conv_value = float(min_conversion)
                if conversion_rate < min_conv_value:
                    continue  # Пропускаем это направление
            except ValueError:
                pass

        upcoming = upcoming_map.get(dir_id, 0)

        metrics_data.append({
            'direction': {
                'id': dir_id,
                'name': dir_name,
            },
            'interviews': stat['total_interviews'],
            'tech_interviews': tech_count,
            'candidates': stat['total_candidates'],
            'conversion_rate': conversion_rate,
            'upcoming_interviews': upcoming,
            'last_interview_date': stat['last_interview_date'].isoformat() if stat['last_interview_date'] else None,
        })

        total_interviews_count += stat['total_interviews']
        total_tech_interviews_count += tech_count
        total_candidates_count += stat['total_candidates']

    # Добавляем направления без интервью (с нулевыми показателями)
    direction_ids_with_data = {stat['direction_id'] for stat in direction_stats}
    for d in all_directions_objs:
        if d.id in direction_ids_with_data:
            continue
        if min_conversion:
            try:
                if 0 < float(min_conversion):
                    continue
            except ValueError:
                pass
        metrics_data.append({
            'direction': {'id': d.id, 'name': d.name},
            'interviews': 0,
            'tech_interviews': 0,
            'candidates': 0,
            'conversion_rate': 0,
            'upcoming_interviews': upcoming_map.get(d.id, 0),
            'last_interview_date': None,
        })
    metrics_data.sort(key=lambda x: (x['direction']['name'] or ''))

    # Самое активное направление за 30 дней
    top_30 = (
        last_30_days
        .values('direction_id')
        .annotate(count=Count('id'))
        .order_by('-count')
        .first()
    )
    top_direction_30 = directions_map.get(top_30['direction_id'], f'ID: {top_30["direction_id"]}') if top_30 else '—'

    # Самое активное направление за 90 дней
    top_90 = (
        last_90_days
        .values('direction_id')
        .annotate(count=Count('id'))
        .order_by('-count')
        .first()
    )
    top_direction_90 = directions_map.get(top_90['direction_id'], f'ID: {top_90["direction_id"]}') if top_90 else '—'

    # Лидер по конверсии (screening -> tech)
    conversion_qs = before_target.filter(interview_type__in=[INTERVIEW_TYPE_SCREENING, INTERVIEW_TYPE_TECH])
    conv_stats = (
        conversion_qs
        .values('direction_id')
        .annotate(
            screening_count=Count('id', filter=Q(interview_type=INTERVIEW_TYPE_SCREENING)),
            tech_count=Count('id', filter=Q(interview_type=INTERVIEW_TYPE_TECH)),
        )
        .filter(screening_count__gt=0)
    )

    best_conversion = '—'
    worst_conversion = '—'
    conversion_rates = []
    for stat in conv_stats:
        rate = round((stat['tech_count'] / stat['screening_count']) * 100, 2)
        dir_name = directions_map.get(stat['direction_id'], f'ID: {stat["direction_id"]}')
        conversion_rates.append({'name': dir_name, 'rate': rate})

    if conversion_rates:
        best_conv = max(conversion_rates, key=lambda x: x['rate'])
        worst_conv = min(conversion_rates, key=lambda x: x['rate'])
        best_conversion = f"{best_conv['name']} ({best_conv['rate']}%)"
        # Направления с наименьшей активностью за 30 дней
        worst_conversion = f"{worst_conv['name']} ({worst_conv['rate']}%)"

    # Самое быстрое/медленное направление (время до финала).
    # ОПТИМИЗАЦИЯ: Получаем все первые интервью для всех кандидатов одним запросом
    first_interviews_map = {}
    first_interviews_qs = (
        before_target
        .values('intern__full_name', 'direction_id')
        .annotate(first_date=Min('date'))
    )
    for item in first_interviews_qs:
        key = (item['intern__full_name'], item['direction_id'])
        first_interviews_map[key] = item['first_date']

    # Получаем финальные интервью
    final_interviews = (
        before_target
        .filter(interview_type=INTERVIEW_TYPE_FINAL)
        .values('intern__full_name', 'direction_id', 'date')
    )

    duration_data = []
    for final_int in final_interviews:
        full_name = final_int['intern__full_name']
        direction_id = final_int['direction_id']
        final_date = final_int['date']

        # Используем предзагруженные данные вместо запроса к БД
        key = (full_name, direction_id)
        first_interview = first_interviews_map.get(key)

        if first_interview and final_date:
            duration = (final_date - first_interview).days
            dir_name = directions_map.get(direction_id, f'ID: {direction_id}')
            duration_data.append({
                'direction_name': dir_name,
                'duration': duration,
                'full_name': full_name
            })

    fastest_direction = '—'
    fastest_direction_person = ''
    slowest_direction = '—'
    slowest_direction_person = ''
    if duration_data:
        fastest = min(duration_data, key=lambda x: x['duration'])
        slowest = max(duration_data, key=lambda x: x['duration'])
        fastest_direction = f"{fastest['direction_name']} ({fastest['duration']} дн.)"
        fastest_direction_person = fastest['full_name']
        slowest_direction = f"{slowest['direction_name']} ({slowest['duration']} дн.)"
        slowest_direction_person = slowest['full_name']

    # Лучший и худший месяц — один запрос, затем min/max в Python
    monthly_counts_list = list(
        last_year
        .annotate(year=ExtractYear('date'), month=ExtractMonth('date'))
        .values('year', 'month')
        .annotate(count=Count('id'))
        .values('year', 'month', 'count')
    )
    best_month = '—'
    worst_month = '—'
    if monthly_counts_list:
        best_item = max(monthly_counts_list, key=lambda x: x['count'])
        worst_item = min(monthly_counts_list, key=lambda x: x['count'])
        best_month = f"{best_item['month']}.{best_item['year']} ({best_item['count']} шт.)"
        worst_month = f"{worst_item['month']}.{worst_item['year']} ({worst_item['count']} шт.)"

    # Доля технических собеседований за 30 дней — один aggregate
    last_30_agg = last_30_days.aggregate(
        total=Count('id'),
        tech=Count('id', filter=Q(interview_type=INTERVIEW_TYPE_TECH)),
    )
    total_last_30 = last_30_agg['total']
    tech_last_30 = last_30_agg['tech']
    tech_share = round((tech_last_30 / total_last_30) * 100, 2) if total_last_30 > 0 else 0

    # График 1: Собесы по направлениям за последние 30 дней
    last_30_days_date = target_date - timedelta(days=30)
    interviews_by_direction = (
        base_qs.filter(date__gte=last_30_days_date)
        .values('direction_id')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # График включает все направления (без интервью — 0)
    count_by_direction_id = {item['direction_id']: item['count'] for item in interviews_by_direction}
    direction_names = []
    direction_counts = []
    for d in all_directions_objs:
        direction_names.append(d.name)
        direction_counts.append(count_by_direction_id.get(d.id, 0))

    # График 2: Собесы по месяцам за последний год
    last_year_date = target_date - timedelta(days=365)
    monthly_interviews = (
        base_qs.filter(date__gte=last_year_date)
        .annotate(year=ExtractYear('date'), month=ExtractMonth('date'))
        .values('year', 'month')
        .annotate(count=Count('id'))
        .order_by('year', 'month')
    )

    months = []
    counts = []

    for item in monthly_interviews:
        month_str = f"{item['year']}-{item['month']:02d}"
        months.append(month_str)
        counts.append(item['count'])

    response_data = {
        'total-directions': len(metrics_data),
        'total_interviews': total_interviews_count,
        'total_tech_interviews_count': total_tech_interviews_count,
        'total_candidates': total_candidates_count,
        'total_upcoming': total_upcoming_count,
        'metrics': metrics_data,
        'metrics_data': metrics_data,
        'target_date': target_date.isoformat(),

        'directions': len(metrics_data),
        'top_direction_30': top_direction_30,
        'top_direction_90': top_direction_90,
        'best_conversion': best_conversion,
        'worst_conversion': worst_conversion,
        'fastest_direction': fastest_direction,
        'fastest_direction_person': fastest_direction_person,
        'slowest_direction': slowest_direction,
        'slowest_direction_person': slowest_direction_person,
        'best_month': best_month,
        'worst_month': worst_month,
        'tech_share': tech_share,

        # Метрики для графиков
        'chart_directions': {
            'labels': direction_names,
            'data': direction_counts,
        },
        'chart_months': {
            'labels': months,
            'data': counts,
        },
        'tooltips': {
            'total-directions': 'Всего направлений',
            'directions': 'Направлений в работе.',
            'top-direction': 'Самое активное направление за 90 дней.',
            'best-conversion': 'Больше всего из скрининга в тех собес.',
            'worst-conversion': 'Направление, по которому меньше всего собесов за последние 30 дней.',
            'fastest': 'Считаем медиану времени от выхода разработчика на собеседования по направлению до момента, когда он: доходит до первого финального этапа, и после этого по нему перестают появляться новые записи (то есть он “выбывает” из воронки).',
            'slowest': 'Считаем медиану времени от выхода разработчика на собеседования по направлению до момента, когда он: доходит до первого финального этапа, и после этого по нему перестают появляться новые записи (то есть он “выбывает” из воронки).',
            'best-month': 'На основе последнего года, в каком месяце больше всего собесов в сумме.',
            'worst-month': 'На основе последнего года, в каком месяце меньше всего собесов в сумме',
            'tech-share': 'За последние 30 дней, процент технических собеседований.',
        }
    }
    return response_data


def compute_direction_observations():
    """
    Структурированные данные для наблюдений по направлениям (единый источник для DRF и кэша).
    """
    # --- Определяем временные интервалы ---
    today = date.today()
    start_of_last_7_days = today - timedelta(days=6)  # 6 дней назад + сегодня = 7 дней
    start_of_current_week = today - timedelta(days=today.weekday())

    # --- 1. Основные метрики для всех направлений ---
    # Получаем агрегированные данные по каждому direction_id
    aggregated_data = Interview.objects.exclude(interview_type=INTERVIEW_TYPE_TECH_QUESTIONNAIRE).filter(
        direction_id__isnull=False
    ).values('direction_id').annotate(
        # Всего кандидатов
        candidates=Count('intern__full_name', distinct=True),
        # Всего интервью
        interviews=Count('id'),
        # Успешные кандидаты (с финальным интервью)
        successful_candidates=Count('intern__full_name', filter=Q(interview_type=INTERVIEW_TYPE_FINAL), distinct=True),
        # Предстоящие интервью (без отмен)
        upcoming=Count('id', filter=Q(date__gte=today) & ~Q(interview_type=INTERVIEW_TYPE_CANCELLED)),
        # Отменённые интервью
        cancelled=Count('id', filter=Q(interview_type=INTERVIEW_TYPE_CANCELLED)),
        # Интервью за текущую неделю
        week_count=Count('id', filter=Q(date__gte=start_of_current_week)),
        # Уникальные manager_email (SSO)
        managers=Count('manager_email', distinct=True),
        # Последнее интервью (для проверки активности)
        last_interview_date=Max('date', filter=~Q(interview_type=INTERVIEW_TYPE_CANCELLED)),
        # Кандидаты за последние 7 дней (активные)
        active_candidates=Count('intern__full_name', filter=Q(date__gte=start_of_last_7_days), distinct=True),
    )

    # Получаем объекты Direction для связывания ID с именами
    all_direction_ids = [item['direction_id'] for item in aggregated_data]
    directions_dict = {}
    if all_direction_ids:
        directions_dict = {
            d.id: d.name for d in Direction.objects.filter(id__in=all_direction_ids)
        }

    # Сначала соберём основные данные, включая имена
    list_data = []
    for item in aggregated_data:
        direction_name = directions_dict.get(item['direction_id'], f"ID {item['direction_id']}")
        # Пока avgSpeed ставим в null, его нужно вычислять отдельно
        list_item = {
            'direction': direction_name,
            'candidates': item['candidates'],
            'interviews': item['interviews'],
            'successful': item['successful_candidates'],
            'upcoming': item['upcoming'],
            'cancelled': item['cancelled'],
            'week_count': item['week_count'],
            'managers': item['managers'],  # Это будет число, не список, как в JS. Возможно, нужно получить имена менеджеров.
            'last_interview_date': item['last_interview_date'],
            'active_candidates': item['active_candidates'],
            'avgSpeed': None,  # Пока не вычисляем
            'successRate': item['candidates'] and item['successful_candidates'] / item['candidates'] or 0,
            'cancelRate': item['interviews'] and item['cancelled'] / item['interviews'] or 0,
        }
        list_data.append(list_item)

    # --- 3. Вычисление avgSpeed (среднее время до успеха) ---
    # ОПТИМИЗАЦИЯ: Получаем все первые интервью для всех кандидатов одним запросом
    first_interviews_map = {}
    first_interviews_qs = (
        Interview.objects
        .exclude(interview_type=INTERVIEW_TYPE_TECH_QUESTIONNAIRE)
        .filter(direction_id__isnull=False)
        .values('intern__full_name', 'direction_id')
        .annotate(first_date=Min('date'))
    )
    for item in first_interviews_qs:
        key = (item['intern__full_name'], item['direction_id'])
        first_interviews_map[key] = item['first_date']

    # Получаем финальные интервью
    final_interviews = Interview.objects.filter(
        interview_type=INTERVIEW_TYPE_FINAL,
        direction_id__isnull=False
    ).values('intern__full_name', 'direction_id', 'date')

    speed_data = {}
    for final_int in final_interviews:
        full_name = final_int['intern__full_name']
        direction_id = final_int['direction_id']
        final_date = final_int['date']

        # Используем предзагруженные данные вместо запроса к БД
        key = (full_name, direction_id)
        first_interview_date = first_interviews_map.get(key)

        if first_interview_date and final_date:
            days_to_success = (final_date - first_interview_date).days
            if direction_id not in speed_data:
                speed_data[direction_id] = []
            speed_data[direction_id].append(days_to_success)

    # ОПТИМИЗАЦИЯ: Создаем обратный словарь для быстрого поиска ID по имени
    name_to_id_dict = {name: did for did, name in directions_dict.items()}

    # Вычислим среднее для каждого направления
    for item in list_data:
        # Используем обратный словарь вместо цикла
        direction_id_from_list = name_to_id_dict.get(item['direction'])

        # Если нашли ID и есть данные по скорости — вычисляем среднее
        if direction_id_from_list and direction_id_from_list in speed_data:
            avg_speed = sum(speed_data[direction_id_from_list]) / len(speed_data[direction_id_from_list])
            item['avgSpeed'] = avg_speed
        else:
            item['avgSpeed'] = None

    # --- 4. Формирование итогового словаря для JSON ---
    total_directions = len(list_data)
    total_candidates = sum(item['candidates'] for item in list_data)
    total_interviews = sum(item['interviews'] for item in list_data)

    # Остальные метрики, как в JS-коде
    sorted_by_speed = sorted([item for item in list_data if item['avgSpeed'] is not None], key=lambda x: x['avgSpeed'])
    fastest = sorted_by_speed[0] if sorted_by_speed else None
    slowest = sorted_by_speed[-1] if sorted_by_speed else None

    success_sorted = sorted(list_data, key=lambda x: x['successRate'], reverse=True)
    cancel_sorted = sorted(list_data, key=lambda x: x['cancelRate'], reverse=True)
    highest_cancel = cancel_sorted[0] if cancel_sorted else None
    most_managers = max(list_data, key=lambda x: x['managers']) if list_data else None
    highest_upcoming = max(list_data, key=lambda x: x['upcoming']) if any(item['upcoming'] > 0 for item in list_data) else None
    best_conversion = success_sorted[0] if success_sorted else None
    worst_conversion = success_sorted[-1] if success_sorted else None
    focus_needed = len([item for item in list_data if item['successRate'] < 0.2])

    # Месячные метрики
    last_year = today - timedelta(days=365)
    monthly_interviews = (
        Interview.objects.exclude(interview_type=INTERVIEW_TYPE_TECH_QUESTIONNAIRE).filter(date__gte=last_year)
        .annotate(year=ExtractYear('date'), month=ExtractMonth('date'))
        .values('year', 'month')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    best_month = None
    worst_month = None
    if monthly_interviews:
        best_month_item = monthly_interviews.first()
        worst_month_item = monthly_interviews.last()
        best_month = (f"{best_month_item['year']}-{best_month_item['month']:02d}", best_month_item['count'])
        worst_month = (f"{worst_month_item['year']}-{worst_month_item['month']:02d}", worst_month_item['count'])

    return {
        'list': list_data,
        'totalDirections': total_directions,
        'totalCandidates': total_candidates,
        'totalInterviews': total_interviews,
        'fastest': fastest,
        'slowest': slowest,
        'highestCancel': highest_cancel,
        'mostManagers': most_managers,
        'highestUpcoming': highest_upcoming,
        'bestConversion': best_conversion,
        'worstConversion': worst_conversion,
        'focusNeeded': focus_needed,
        'bestMonth': best_month,
        'worstMonth': worst_month,
    }
