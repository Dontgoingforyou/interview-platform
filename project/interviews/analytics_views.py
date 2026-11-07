from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from core.decorators import manager_required_api, cache_analytics
from core.constants import INTERVIEW_TYPE_CANCELLED, INTERVIEW_TYPE_SCREENING, INTERVIEW_TYPE_TECH
from core.intern_utils import transliterate_name_to_cyrillic
from interviews.models import Interview
from managers.models import Manager


def compute_interview_analytics(params=None):
    """Вычисляет аналитику по собеседованиям. Вызывается из API-вью и из list-вью для прогрева кэша."""
    params = params or {}
    date_from = params.get('date_from')
    date_to = params.get('date_to')

    qs = Interview.objects.all()
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    # Вычисляем диапазон дат для текущей и прошлой недели
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    start_of_last_week = start_of_week - timedelta(days=7)
    end_of_last_week = start_of_last_week + timedelta(days=6)

    # ============ МЕТРИКИ ЗА ВСЕ ВРЕМЯ и ЗА МЕСЯЦ — один aggregate на период ============
    agg_all = qs.aggregate(
        total_all_time=Count('id'),
        unique_companies_all_time=Count('company_id', distinct=True, filter=Q(company_id__isnull=False)),
        upcoming_all_time=Count('id', filter=Q(date__gt=today)),
        this_week_all_time=Count(
            'id',
            filter=Q(date__gte=start_of_week, date__lte=end_of_week),
        ),
        last_week_all_time=Count(
            'id',
            filter=Q(date__gte=start_of_last_week, date__lte=end_of_last_week),
        ),
        cancelled_all_time=Count('id', filter=Q(interview_type=INTERVIEW_TYPE_CANCELLED)),
    )
    total_all_time = agg_all['total_all_time']
    unique_companies_all_time = agg_all['unique_companies_all_time']
    upcoming_all_time = agg_all['upcoming_all_time']
    this_week_all_time = agg_all['this_week_all_time']
    last_week_all_time = agg_all['last_week_all_time']
    cancelled_all_time = agg_all['cancelled_all_time']

    qs_last_30_days = qs.filter(date__gte=thirty_days_ago)
    agg_30 = qs_last_30_days.aggregate(
        total=Count('id'),
        unique_companies=Count('company_id', distinct=True, filter=Q(company_id__isnull=False)),
        upcoming=Count('id', filter=Q(date__gt=today)),
        this_week=Count('id', filter=Q(date__gte=start_of_week, date__lte=end_of_week)),
        last_week=Count(
            'id',
            filter=Q(date__gte=start_of_last_week, date__lte=end_of_last_week),
        ),
        cancelled=Count('id', filter=Q(interview_type=INTERVIEW_TYPE_CANCELLED)),
    )
    total = agg_30['total']
    unique_companies = agg_30['unique_companies']
    upcoming = agg_30['upcoming']
    this_week = agg_30['this_week']
    last_week = agg_30['last_week']
    cancelled = agg_30['cancelled']

    # Расчет доли успешных: успешный скрининг + назначение тех собеса в ту же компанию у того же разработчика
    # Подзапрос через Subquery (без Exists) для совместимости с SQLite в тестах
    from django.db.models import OuterRef, Subquery

    # ============ Доля успешных ЗА ВСЕ ВРЕМЯ (для аккордеона) ============
    screenings_all_time = qs.filter(interview_type=INTERVIEW_TYPE_SCREENING).exclude(company_id=None).exclude(date=None)
    success_rate_all_time = 0
    total_screenings_all_time = screenings_all_time.count()

    if total_screenings_all_time > 0:
        tech_after_screening_all_time = Interview.objects.filter(
            interview_type=INTERVIEW_TYPE_TECH,
            intern_id=OuterRef('intern_id'),
            company_id=OuterRef('company_id'),
            date__gt=OuterRef('date'),
            date__isnull=False
        )

        if date_from:
            tech_after_screening_all_time = tech_after_screening_all_time.filter(date__gte=date_from)
        if date_to:
            tech_after_screening_all_time = tech_after_screening_all_time.filter(date__lte=date_to)

        successful_count_all_time = screenings_all_time.annotate(
            has_tech_after=Subquery(tech_after_screening_all_time.values('id')[:1])
        ).filter(has_tech_after__isnull=False).count()

        success_rate_all_time = successful_count_all_time / total_screenings_all_time if total_screenings_all_time > 0 else 0

    # ============ Доля успешных ЗА МЕСЯЦ (основные блоки) ============
    screenings = qs_last_30_days.filter(interview_type=INTERVIEW_TYPE_SCREENING).exclude(company_id=None).exclude(date=None)
    success_rate = 0
    total_screenings = screenings.count()

    if total_screenings > 0:
        # Подзапрос: наличие тех собеседования ПОСЛЕ скрининга
        tech_after_screening = Interview.objects.filter(
            interview_type=INTERVIEW_TYPE_TECH,
            intern_id=OuterRef('intern_id'),
            company_id=OuterRef('company_id'),
            date__gt=OuterRef('date'),
            date__isnull=False,
            date__gte=thirty_days_ago
        )

        if date_from:
            tech_after_screening = tech_after_screening.filter(date__gte=date_from)
        if date_to:
            tech_after_screening = tech_after_screening.filter(date__lte=date_to)

        successful_count = screenings.annotate(
            has_tech_after=Subquery(tech_after_screening.values('id')[:1])
        ).filter(has_tech_after__isnull=False).count()

        success_rate = successful_count / total_screenings if total_screenings > 0 else 0

    # ============ Самый активный менеджер ЗА ВСЕ ВРЕМЯ (для аккордеона) ============
    top_manager_data_all_time = (
        qs.exclude(manager_email=None)
        .exclude(manager_email='')
        .values('manager_email')
        .annotate(count=Count('id'))
        .order_by('-count')
        .first()
    )
    top_manager_email_all_time = top_manager_data_all_time['manager_email'] if top_manager_data_all_time else None
    top_manager_count_all_time = top_manager_data_all_time['count'] if top_manager_data_all_time else 0

    # ============ Самый быстрый менеджер (за месяц) ============
    fastest_manager_data = (
        qs_last_30_days.exclude(manager_email=None)
        .exclude(manager_email='')
        .values('manager_email')
        .annotate(count=Count('id'))
        .order_by('-count')
        .first()
    )
    fastest_manager_email = fastest_manager_data['manager_email'] if fastest_manager_data else None
    fastest_manager_count = fastest_manager_data['count'] if fastest_manager_data else 0

    # ============ Интервью на кандидата ЗА ВСЕ ВРЕМЯ (для аккордеона) ============
    avg_per_person_all_time = 0
    unique_candidates_all_time = qs.values('intern_id').distinct().count()
    if unique_candidates_all_time > 0:
        avg_per_person_all_time = total_all_time / unique_candidates_all_time

    # ============ Интервью на менеджера ЗА ВСЕ ВРЕМЯ (для аккордеона) ============
    avg_per_manager_all_time = 0
    active_managers_count_all_time = (
        qs.exclude(manager_email=None)
        .exclude(manager_email='')
        .values('manager_email')
        .distinct()
        .count()
    )
    if active_managers_count_all_time > 0:
        avg_per_manager_all_time = total_all_time / active_managers_count_all_time

    top_manager_name_all_time = ''
    fastest_manager_name = ''

    emails_to_lookup = [e for e in [top_manager_email_all_time, fastest_manager_email] if e]
    if emails_to_lookup:
        managers_by_email = {
            m.email: m.full_name
            for m in Manager.objects.filter(email__in=emails_to_lookup).only('email', 'full_name')
        }
        if top_manager_email_all_time:
            raw = managers_by_email.get(top_manager_email_all_time, top_manager_email_all_time)
            # Транслитерируем только имя (не email при fallback)
            top_manager_name_all_time = (transliterate_name_to_cyrillic(raw) or raw) if '@' not in (raw or '') else raw
        if fastest_manager_email:
            raw = managers_by_email.get(fastest_manager_email, fastest_manager_email)
            fastest_manager_name = (transliterate_name_to_cyrillic(raw) or raw) if '@' not in (raw or '') else raw

    # ============ Интервью на кандидата ЗА МЕСЯЦ (основные блоки) ============
    avg_per_person = 0
    total_last_30_days = total  # уже из aggregate
    unique_candidates_last_30_days = qs_last_30_days.values('intern_id').distinct().count()
    if unique_candidates_last_30_days > 0:
        avg_per_person = total_last_30_days / unique_candidates_last_30_days

    # ============ Интервью на менеджера ЗА МЕСЯЦ (основные блоки) ============
    avg_per_manager = 0
    active_managers_count_last_30_days = (
        qs_last_30_days
        .exclude(manager_email=None)
        .exclude(manager_email='')
        .values('manager_email')
        .distinct()
        .count()
    )
    if active_managers_count_last_30_days > 0:
        avg_per_manager = total_last_30_days / active_managers_count_last_30_days

    data = {
        # Метрики за месяц (основные блоки)
        'total': total,
        'companies': unique_companies,
        'upcoming': upcoming,
        'this-week': this_week,
        'last-week': last_week,
        'success_rate': round(success_rate, 2),
        'cancelled': cancelled,
        'fastest_manager': fastest_manager_name,
        'fastest_manager_count': fastest_manager_count,
        'avg_per_person': round(avg_per_person, 2),
        'avg_per_manager': round(avg_per_manager, 2),

        # Метрики за все время (для аккордеона)
        'total_all_time': total_all_time,
        'companies_all_time': unique_companies_all_time,
        'upcoming_all_time': upcoming_all_time,
        'this_week_all_time': this_week_all_time,
        'last_week_all_time': last_week_all_time,
        'success_rate_all_time': round(success_rate_all_time, 2),
        'cancelled_all_time': cancelled_all_time,
        'top_manager_all_time': top_manager_name_all_time,
        'top_manager_count_all_time': top_manager_count_all_time,
        'avg_per_person_all_time': round(avg_per_person_all_time, 2),
        'avg_per_manager_all_time': round(avg_per_manager_all_time, 2),

        'tooltips': {
            'total': 'За последние 30 дней.',
            'companies': 'С какими уникальными компаниями были собесы за последние 30 дней.',
            'upcoming': 'Сколько назначено на "будущее" (из последних 30 дней).',
            'this-week': 'Сколько интервью назначено на этой неделе (из последних 30 дней).',
            'last-week': 'Сколько собесов в прошлой календарной неделе (пн–вс), в пределах последних 30 дней.',
            'success-rate': 'Процент перехода из скрининга в тех этап за последние 30 дней.',
            'cancelled': 'Кол-во собесов, которые отменили за последние 30 дней.',
            'fastest-manager': 'Менеджер с самым большим кол-во собесов за последние 30 дней.',
            'avg-per-person': 'Сколько в среднем собеседований проходит кандидат за последние 30 дней.',
            'avg-per-manager': 'Сколько интервью в среднем на менеджера за последние 30 дней.',

            # Тултипы для аккордеона (только релевантные метрики)
            'total-all-time': 'За все время.',
            'companies-all-time': 'С какими уникальными компаниями (всего) были собесы.',
            'success-rate-all-time': 'Процент перехода из скрининга в тех этап за все время.',
            'cancelled-all-time': 'Кол-во собесов, которые отменили за все время.',
            'top-manager-all-time': 'Менеджер с самым большим кол-во собесов за все время.',
            'avg-per-person-all-time': 'Сколько в среднем собеседований проходит кандидат за все время.',
            'avg-per-manager-all-time': 'Сколько интервью в среднем на менеджера за все время.',
        }
    }

    return data


@manager_required_api
@cache_analytics()
def interview_analytics_api(request):
    """Подсчет аналитики на основе существующих данных."""
    return JsonResponse(compute_interview_analytics(request.GET.dict()))
