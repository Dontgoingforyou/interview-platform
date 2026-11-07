from datetime import date, timedelta

from django.db.models import Count, Max, Q

from core.constants import INTERVIEW_TYPE_CANCELLED, INTERVIEW_TYPE_FINAL
from core.intern_utils import transliterate_name_to_cyrillic
from directions.models import Direction
from interviews.models import Interview
from managers.models import Manager
from managers.utils import get_inactive_intern_ids


def _display_manager_name(raw_name: str) -> str:
    """Отображаемое ФИО: транслитерация как в analytics_views / шаблоне."""
    if not raw_name:
        return '—'
    if '@' in raw_name:
        return raw_name
    return transliterate_name_to_cyrillic(raw_name) or raw_name


def build_managers_dashboard_table() -> list[dict]:
    """
    Строки таблицы «Менеджеры»: только активные менеджеры из БД с агрегатами по Interview.

    Ключи строк: email, full_name, счётчики, directions, last_interview_date (date | None).
    """
    today = date.today()
    start_of_hot_period = today - timedelta(days=7)
    start_of_active_period = today - timedelta(days=20)
    start_of_portfolio_period = today - timedelta(days=60)
    no_interview_period = today - timedelta(days=30)

    inactive_interns = get_inactive_intern_ids()

    aggregated_interviews = (
        Interview.objects.filter(manager_email__isnull=False)
        .exclude(manager_email='')
        .exclude(intern_id__in=inactive_interns)
        .values('manager_email')
        .annotate(
            candidates_count=Count('intern__full_name', distinct=True),
            hot_candidates_count=Count(
                'intern__full_name',
                filter=Q(date__gte=start_of_hot_period),
                distinct=True,
            ),
            active_candidates_count=Count(
                'intern__full_name',
                filter=Q(date__gte=start_of_active_period),
                distinct=True,
            ),
            portfolio_candidates_count=Count(
                'intern__full_name',
                filter=Q(date__gte=start_of_portfolio_period),
                distinct=True,
            ),
            interviews_count=Count('id'),
            last_interview_date=Max('date', filter=~Q(interview_type=INTERVIEW_TYPE_CANCELLED)),
        )
    )

    successful_candidates_qs = (
        Interview.objects.filter(manager_email__isnull=False)
        .exclude(manager_email='')
        .filter(interview_type=INTERVIEW_TYPE_FINAL)
        .exclude(date__gte=no_interview_period)
        .values('manager_email', 'intern__full_name')
        .distinct()
    )

    successful_candidates_by_manager: dict[str, set] = {}
    for item in successful_candidates_qs:
        mgr_email = item['manager_email']
        if mgr_email not in successful_candidates_by_manager:
            successful_candidates_by_manager[mgr_email] = set()
        successful_candidates_by_manager[mgr_email].add(item['intern__full_name'])

    all_manager_emails = [item['manager_email'] for item in aggregated_interviews]

    managers_dict: dict[str, Manager] = {}
    if all_manager_emails:
        managers_dict = {
            m.email: m
            for m in Manager.objects.filter(email__in=all_manager_emails, is_active=True)
        }

    all_direction_ids: set[int] = set()
    manager_directions_map: dict[str, dict] = {}
    if all_manager_emails:
        direction_mappings = (
            Interview.objects.filter(manager_email__in=all_manager_emails)
            .exclude(intern_id__in=inactive_interns)
            .values('manager_email', 'direction_id')
            .annotate(count=Count('intern_id', distinct=True))
        )
        for dir_row in direction_mappings:
            mgr_email = dir_row['manager_email']
            dir_id = dir_row['direction_id']
            count = dir_row['count']
            if mgr_email not in manager_directions_map:
                manager_directions_map[mgr_email] = {}
            manager_directions_map[mgr_email][dir_id] = count
            all_direction_ids.add(dir_id)

    directions_dict: dict[int, str] = {}
    if all_direction_ids:
        directions_dict = {d.id: d.name for d in Direction.objects.filter(id__in=all_direction_ids)}

    rows: list[dict] = []
    for agg_data in aggregated_interviews:
        manager_email = agg_data['manager_email']
        manager_obj = managers_dict.get(manager_email)
        if not manager_obj:
            continue

        direction_counts = manager_directions_map.get(manager_email, {})
        direction_list: list[str] = []
        for dir_id, count in direction_counts.items():
            dir_name = directions_dict.get(dir_id)
            if dir_name:
                direction_list.append(f'{dir_name} ({count})' if count > 1 else dir_name)
        direction_list.sort()
        directions_str = ', '.join(direction_list)

        raw_name = manager_obj.full_name or manager_email
        rows.append(
            {
                'email': manager_email,
                'full_name': _display_manager_name(raw_name),
                'candidates_count': agg_data['candidates_count'],
                'hot_candidates_count': agg_data['hot_candidates_count'],
                'active_candidates_count': agg_data['active_candidates_count'],
                'portfolio_candidates_count': agg_data['portfolio_candidates_count'],
                'interviews_count': agg_data['interviews_count'],
                'successful_candidates_count': len(successful_candidates_by_manager.get(manager_email, set())),
                'directions': directions_str or '—',
                'last_interview_date': agg_data['last_interview_date'],
            }
        )

    return rows
