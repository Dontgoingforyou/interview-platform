from django.db.models import Count, Q, Min, Max
from django.http import JsonResponse
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from core.constants import INTERVIEW_TYPE_CANCELLED, INTERVIEW_TYPE_FINAL
from core.intern_utils import transliterate_name_to_cyrillic
from interviews.models import Interview
from managers.models import Manager
from managers.utils import get_inactive_intern_ids
from core.decorators import manager_required_api, cache_analytics


def compute_managers_analytics():
    """Вычисляет аналитику по менеджерам. Вызывается из API-вью и из list-вью для прогрева кэша."""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_hot_period = today - timedelta(days=7)
    start_of_active_period = today - timedelta(days=20)
    start_of_portfolio_period = today - timedelta(days=60)
    start_of_avg_period = today - timedelta(days=29)  # 29 дней назад + сегодня = 30 дней

    inactive_interns = get_inactive_intern_ids()

    base_qs = Interview.objects.filter(
        manager_email__isnull=False
    ).exclude(
        manager_email=''
    ).exclude(
        intern_id__in=inactive_interns
    )

    managers_in_work = base_qs.values('manager_email').distinct().count()

    hot_candidates = base_qs.filter(
        date__gte=start_of_hot_period
    ).values('intern__full_name').distinct().count()

    active_candidates = base_qs.filter(
        date__gte=start_of_active_period
    ).values('intern__full_name').distinct().count()

    portfolio_candidates = base_qs.filter(
        date__gte=start_of_portfolio_period
    ).values('intern__full_name').distinct().count()

    interviews_last_period = base_qs.filter(date__gte=start_of_avg_period)
    total_interviews_last_period = interviews_last_period.count()
    managers_with_interviews_last_period = interviews_last_period.values('manager_email').distinct().count()

    if managers_with_interviews_last_period > 0:
        avg_raw = total_interviews_last_period / managers_with_interviews_last_period
        avg_interviews_per_manager = Decimal(avg_raw).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    else:
        avg_interviews_per_manager = Decimal('0.00')

    top_manager_info = base_qs.filter(
        date__gte=start_of_active_period
    ).values('manager_email').annotate(
        interview_count=Count('id')
    ).order_by('-interview_count').first()

    top_manager_name = '—'
    top_manager_stat = 0
    if top_manager_info:
        manager_email = top_manager_info['manager_email']
        mgr = Manager.objects.filter(email=manager_email).values('full_name').first()
        raw_name = mgr['full_name'] if mgr else manager_email
        # Транслитерируем только имя (не email при fallback)
        top_manager_name = (transliterate_name_to_cyrillic(raw_name) or raw_name) if '@' not in (raw_name or '') else raw_name
        top_manager_stat = top_manager_info['interview_count']

    interviews_this_week = base_qs.filter(date__gte=start_of_week).count()

    data = {
        'managers': managers_in_work,
        'hot-candidates': hot_candidates,
        'active-candidates': active_candidates,
        'portfolio-candidates': portfolio_candidates,
        'avg-candidates': float(avg_interviews_per_manager),
        'top-speed': top_manager_name,
        'top-speed-count': top_manager_stat,
        'this-week': interviews_this_week,
        'tooltips': {
            'managers': 'Всего менеджеров в работе.',
            'hot-candidates': 'Горячие кандидаты (интервью за 7 дней) — активно проходят сейчас.',
            'active-candidates': 'В работе (интервью за 20 дней) — текущий активный пайплайн.',
            'portfolio-candidates': 'В портфеле (интервью за 60 дней) — все кандидаты у менеджеров.',
            'avg-candidates': 'Среднее кол-во собесов на менеджера за 30 дней.',
            'top-speed': 'Менеджер с наибольшим числом собесов за период.',
            'this-week': 'Кол-во интервью на этой неделе.',
        }
    }

    return data


@manager_required_api
@cache_analytics()
def managers_analytics_api(request):
    """Подсчёт аналитики по менеджерам на основе существующих данных."""
    return JsonResponse(compute_managers_analytics())


def compute_managers_observations():
    """
    Структурированные данные для наблюдений по менеджерам.
    """
    today = date.today()
    start_of_hot_period = today - timedelta(days=7)
    start_of_active_period = today - timedelta(days=20)
    start_of_portfolio_period = today - timedelta(days=60)
    start_of_current_week = today - timedelta(days=today.weekday())
    no_interview_period = today - timedelta(days=30)

    inactive_interns = get_inactive_intern_ids()

    base_qs = Interview.objects.filter(
        manager_email__isnull=False
    ).exclude(
        manager_email=''
    ).exclude(
        intern_id__in=inactive_interns
    )

    aggregated_data = base_qs.values('manager_email').annotate(
        candidates=Count('intern__full_name', distinct=True),
        interviews=Count('id'),
        upcoming=Count('id', filter=Q(date__gte=today) & ~Q(interview_type=INTERVIEW_TYPE_CANCELLED)),
        cancelled=Count('id', filter=Q(interview_type=INTERVIEW_TYPE_CANCELLED)),
        week_count=Count('id', filter=Q(date__gte=start_of_current_week)),
        directions=Count('direction_id', distinct=True),
        last_interview_date=Max('date', filter=~Q(interview_type=INTERVIEW_TYPE_CANCELLED)),
        hot_candidates=Count('intern__full_name', filter=Q(date__gte=start_of_hot_period), distinct=True),
        active_candidates=Count('intern__full_name', filter=Q(date__gte=start_of_active_period), distinct=True),
        portfolio_candidates=Count(
            'intern__full_name', filter=Q(date__gte=start_of_portfolio_period), distinct=True
        ),
    )

    successful_qs = Interview.objects.filter(
        manager_email__isnull=False,
        interview_type=INTERVIEW_TYPE_FINAL,
    ).exclude(
        manager_email=''
    ).exclude(
        intern_id__in=inactive_interns
    ).exclude(
        date__gte=no_interview_period
    ).values('manager_email', 'intern__full_name').distinct()

    successful_by_manager = {}
    for item in successful_qs:
        mgr_email = item['manager_email']
        successful_by_manager[mgr_email] = successful_by_manager.get(mgr_email, 0) + 1

    all_manager_emails = [item['manager_email'] for item in aggregated_data]
    managers_dict = {}
    if all_manager_emails:
        managers_dict = {
            m.email: m.full_name for m in Manager.objects.filter(email__in=all_manager_emails)
        }

    list_data = []
    for item in aggregated_data:
        mgr_email = item['manager_email']
        raw_name = managers_dict.get(mgr_email, mgr_email)
        manager_name = (transliterate_name_to_cyrillic(raw_name) or raw_name) if '@' not in (raw_name or '') else raw_name
        successful = successful_by_manager.get(mgr_email, 0)
        list_item = {
            'manager': manager_name,
            '_email': mgr_email,
            'candidates': item['candidates'],
            'interviews': item['interviews'],
            'successful': successful,
            'upcoming': item['upcoming'],
            'cancelled': item['cancelled'],
            'week_count': item['week_count'],
            'directions': item['directions'],
            'last_interview_date': item['last_interview_date'].isoformat() if item['last_interview_date'] else None,
            'hot_candidates': item['hot_candidates'],
            'active_candidates': item['active_candidates'],
            'portfolio_candidates': item['portfolio_candidates'],
            'avgSpeed': None,
            'successRate': successful / item['candidates'] if item['candidates'] else 0,
        }
        list_data.append(list_item)

    first_interviews_map = {}
    first_interviews_qs = (
        Interview.objects
        .filter(manager_email__isnull=False)
        .exclude(manager_email='')
        .values('intern__full_name', 'manager_email')
        .annotate(first_date=Min('date'))
    )
    for row in first_interviews_qs:
        key = (row['intern__full_name'], row['manager_email'])
        first_interviews_map[key] = row['first_date']

    final_interviews = Interview.objects.filter(
        interview_type=INTERVIEW_TYPE_FINAL,
        manager_email__isnull=False,
    ).exclude(
        manager_email=''
    ).values('intern__full_name', 'manager_email', 'date')

    speed_data = {}
    for final_int in final_interviews:
        full_name = final_int['intern__full_name']
        mgr_email = final_int['manager_email']
        final_date = final_int['date']
        first_date = first_interviews_map.get((full_name, mgr_email))
        if first_date and final_date:
            days = (final_date - first_date).days
            speed_data.setdefault(mgr_email, []).append(days)

    for list_item in list_data:
        mgr_email = list_item.pop('_email')
        if mgr_email in speed_data:
            list_item['avgSpeed'] = sum(speed_data[mgr_email]) / len(speed_data[mgr_email])

    total_managers = len(list_data)
    total_candidates = sum(item['candidates'] for item in list_data)
    total_interviews = sum(item['interviews'] for item in list_data)

    with_speed = [item for item in list_data if item['avgSpeed'] is not None]
    sorted_by_speed = sorted(with_speed, key=lambda x: x['avgSpeed'])
    fastest = sorted_by_speed[0] if sorted_by_speed else None
    slowest = sorted_by_speed[-1] if len(sorted_by_speed) > 1 else None

    success_sorted = sorted(list_data, key=lambda x: x['successRate'], reverse=True)
    busiest = max(list_data, key=lambda x: x['interviews']) if list_data else None
    biggest_portfolio = max(list_data, key=lambda x: x['candidates']) if list_data else None
    upcoming_champ = (
        max(list_data, key=lambda x: x['upcoming'])
        if any(item['upcoming'] > 0 for item in list_data)
        else None
    )
    cancelled_champ = (
        max(list_data, key=lambda x: x['cancelled'])
        if any(item['cancelled'] > 0 for item in list_data)
        else None
    )
    no_success_yet = [item for item in list_data if item['successful'] == 0]

    return {
        'list': list_data,
        'totalManagers': total_managers,
        'totalCandidates': total_candidates,
        'totalInterviews': total_interviews,
        'fastest': fastest,
        'slowest': slowest,
        'successSorted': success_sorted,
        'busiest': busiest,
        'biggestPortfolio': biggest_portfolio,
        'upcomingChamp': upcoming_champ,
        'cancelledChamp': cancelled_champ,
        'noSuccessYet': no_success_yet,
    }


@manager_required_api
def managers_observations_api(request):
    """Legacy JSON API наблюдений (session SSO)."""
    return JsonResponse(compute_managers_observations())
