from datetime import datetime, timedelta
from collections import defaultdict

from django.db.models import Q

from core.constants import INTERN_STATUS_ACTIVE, INTERN_STATUS_LEFT, INTERN_STATUS_OFFER, MONTH_NAMES, KEYCLOAK_MANAGER_GROUPS
from directions.models import Direction
from employees.models import InternWeeklyStatus
from interns.models import Intern
from interviews.models import Interview


def get_monday(input_date):
    """Возвращает понедельник той же недели."""
    return input_date - timedelta(days=input_date.weekday())


def _build_52_weeks():
    """Строит список из 52 недель (понедельник–воскресенье) за последний год."""
    today = datetime.now().date()
    monday = get_monday(today)
    return [
        (monday - timedelta(weeks=51 - i), monday - timedelta(weeks=51 - i) + timedelta(days=6))
        for i in range(52)
    ]


def get_managers_for_employees_list():
    """Активные менеджеры с хотя бы одной менеджерской группой Keycloak."""
    from managers.models import Manager

    managers = Manager.objects.filter(is_active=True).order_by('full_name')
    return [m for m in managers if set(m.groups) & KEYCLOAK_MANAGER_GROUPS]


class ManagerDetailService:
    """Сервис для формирования контекста страницы детальной информации по менеджеру."""

    def get_context(self, manager) -> dict:
        interns = list(Intern.objects.filter(manager_email=manager.email))
        intern_ids = [intern.id for intern in interns]

        directions_dict = self._load_directions(interns)
        intern_statuses = {intern.id: intern.status for intern in interns}

        all_weeks = _build_52_weeks()
        recent_weeks = all_weeks[-6:]
        first_week_start, last_week_end = all_weeks[0][0], all_weeks[-1][1]

        interviews_by_intern_week, mock_interviews_by_intern_week = self._load_interviews(
            intern_ids, first_week_start, last_week_end, all_weeks
        )
        weekly_status_dict = self._load_weekly_statuses(
            intern_ids, first_week_start, last_week_end
        )

        intern_stats = self._build_intern_stats(
            interns, intern_statuses, all_weeks,
            interviews_by_intern_week, mock_interviews_by_intern_week, weekly_status_dict
        )

        active_interns = [
            item for item in intern_stats
            if intern_statuses.get(item['intern'].id) == INTERN_STATUS_ACTIVE
        ]
        inactive_interns = [
            item for item in intern_stats
            if intern_statuses.get(item['intern'].id) != INTERN_STATUS_ACTIVE
        ]

        coefficients = self._calculate_coefficients(active_interns, recent_weeks, all_weeks)

        all_months = self._group_weeks_by_month(all_weeks)
        all_interns = self._build_monthly_data(intern_stats, all_months, all_weeks)
        all_months_formatted = self._format_months(all_months)

        recent_weeks_formatted = [
            (s.strftime('%d.%m'), e.strftime('%d.%m'))
            for s, e in recent_weeks
        ]

        return {
            'active_interns': active_interns,
            'inactive_interns': inactive_interns,
            'recent_weeks': recent_weeks_formatted,
            'coefficients': coefficients,
            'all_months': dict(all_months),
            'all_months_formatted': all_months_formatted,
            'all_interns': all_interns,
            'directions_dict': directions_dict,
            'intern_statuses': intern_statuses,
        }

    def _load_directions(self, interns) -> dict:
        direction_ids = {intern.direction_id for intern in interns if intern.direction_id}
        if not direction_ids:
            return {}
        directions = Direction.objects.filter(id__in=direction_ids)
        return {d.id: d.name for d in directions}

    def _load_interviews(self, intern_ids, first_week_start, last_week_end, all_weeks):
        """Загружает собеседования и индексирует их по студенту и номеру недели."""
        interviews_by_intern_week = defaultdict(lambda: defaultdict(int))
        mock_interviews_by_intern_week = defaultdict(lambda: defaultdict(bool))

        all_interviews = Interview.objects.filter(
            intern_id__in=intern_ids,
            date__range=[first_week_start, last_week_end]
        ).values('intern_id', 'date', 'interview_type')

        # Оптимизация: номер недели за O(1) через (date - reference).days // 7
        reference_monday = all_weeks[0][0]
        for interview in all_interviews:
            intern_id = interview['intern_id']
            interview_date = interview['date']
            interview_type = interview['interview_type']
            if interview_date is None:
                continue
            days_from_start = (interview_date - reference_monday).days
            if days_from_start < 0:
                continue
            week_idx = days_from_start // 7
            if week_idx >= len(all_weeks):
                continue
            if interview_type == 'mock':
                mock_interviews_by_intern_week[intern_id][week_idx] = True
            interviews_by_intern_week[intern_id][week_idx] += 1

        return interviews_by_intern_week, mock_interviews_by_intern_week

    def _load_weekly_statuses(self, intern_ids, first_week_start, last_week_end) -> dict:
        """Загружает недельные статусы и индексирует по (intern_id, week_start)."""
        weekly_statuses = InternWeeklyStatus.objects.filter(
            intern_id__in=intern_ids,
            week_start__range=[first_week_start, last_week_end]
        )
        return {(s.intern_id, s.week_start): s for s in weekly_statuses}

    def _build_intern_stats(
        self, interns, intern_statuses, all_weeks,
        interviews_by_intern_week, mock_interviews_by_intern_week, weekly_status_dict
    ) -> list:
        """Формирует статистику собеседований по каждому студенту за каждую неделю."""
        status_display_map = {
            INTERN_STATUS_ACTIVE: 'Активный',
            INTERN_STATUS_LEFT: 'Ушёл',
            INTERN_STATUS_OFFER: 'Оффер',
        }
        intern_stats = []

        for intern in interns:
            stats = []
            week_statuses = []
            exclude_from_coefficient = []

            for week_idx, (week_start, week_end) in enumerate(all_weeks):
                count = interviews_by_intern_week[intern.id][week_idx]
                week_status = weekly_status_dict.get((intern.id, week_start))
                absence_info = None
                should_exclude = False

                if week_status:
                    if week_status.manual_interview_count is not None:
                        count = week_status.manual_interview_count
                    if week_status.absence_status:
                        absence_info = {
                            'status': week_status.absence_status,
                            'status_display': week_status.get_absence_status_display(),
                            'notes': week_status.absence_notes or '',
                        }
                        should_exclude = True

                # Логика исключения МОК-собеседований для новых разработчиков
                if intern.real_interview_date:
                    has_mock = mock_interviews_by_intern_week[intern.id][week_idx]
                    # Неделя выхода: если МОК был — исключаем
                    if week_start <= intern.real_interview_date <= week_end and has_mock:
                        should_exclude = True
                    # Следующая неделя после выхода: если был ТОЛЬКО МОК — исключаем
                    elif intern.real_interview_date < week_start:
                        days_since_start = (week_start - intern.real_interview_date).days
                        if 0 < days_since_start <= 7:
                            interview_count_this_week = interviews_by_intern_week[intern.id][week_idx]
                            if has_mock and interview_count_this_week == 1:
                                should_exclude = True
                                count = 0

                stats.append(count)
                week_statuses.append(absence_info)
                exclude_from_coefficient.append(should_exclude)

            status = intern_statuses.get(intern.id, INTERN_STATUS_LEFT)
            recent_weeks_data = [
                {
                    'count': stats[i],
                    'week_start': all_weeks[i][0].isoformat(),
                    'absence_info': week_statuses[i],
                    'week_idx': i - (len(all_weeks) - 6),
                }
                for i in range(len(all_weeks) - 6, len(all_weeks))
            ]

            intern_stats.append({
                'intern': intern,
                'stats': stats,
                'recent_stats': stats[-6:],
                'recent_weeks_data': recent_weeks_data,
                'week_statuses': week_statuses,
                'exclude_from_coefficient': exclude_from_coefficient,
                'status': status,
                'status_display': status_display_map.get(status, 'Активный'),
            })

        return intern_stats

    def _calculate_coefficients(self, active_interns, recent_weeks, all_weeks) -> list:
        """Считает коэффициент (среднее собеседований на активного) за каждую из 6 последних недель."""
        coefficients = []
        for i in range(len(recent_weeks)):
            week_idx = len(all_weeks) - 6 + i
            active_count = 0
            total_interviews = 0
            for item in active_interns:
                if not item['exclude_from_coefficient'][week_idx]:
                    active_count += 1
                    total_interviews += item['stats'][week_idx]
            coefficients.append(total_interviews / active_count if active_count > 0 else 0)
        return coefficients

    def _group_weeks_by_month(self, all_weeks) -> defaultdict:
        """Группирует недели по месяцам (ключ: 'Январь 2025')."""
        all_months = defaultdict(list)
        for start, end in all_weeks:
            month_key = f"{MONTH_NAMES[start.month - 1]} {start.year}"
            all_months[month_key].append((start, end))
        return all_months

    def _build_monthly_data(self, intern_stats, all_months, all_weeks) -> list:
        """Формирует данные по студентам в разбивке по месяцам (только активные месяцы)."""
        week_to_idx = {(start, end): i for i, (start, end) in enumerate(all_weeks)}
        all_interns = []
        for item in intern_stats:
            for month, weeks_in_month in all_months.items():
                has_activity = any(
                    week_to_idx.get((s, e)) is not None
                    and item['stats'][week_to_idx[(s, e)]] > 0
                    for s, e in weeks_in_month
                )
                if not has_activity:
                    continue

                month_weeks_data: list[dict] = []
                for start, end in weeks_in_month[:5]:
                    idx = week_to_idx.get((start, end))
                    if idx is not None:
                        month_weeks_data.append({
                            'count': item['stats'][idx],
                            'week_start': start.isoformat(),
                            'absence_info': item['week_statuses'][idx],
                            'week_idx': len(month_weeks_data),
                        })
                    else:
                        month_weeks_data.append({
                            'count': 0,
                            'week_start': None,
                            'absence_info': None,
                            'week_idx': len(month_weeks_data),
                        })

                while len(month_weeks_data) < 5:
                    month_weeks_data.append({
                        'count': '—',
                        'week_start': None,
                        'absence_info': None,
                        'week_idx': len(month_weeks_data),
                    })

                all_interns.append({
                    'intern': item['intern'],
                    'month': month,
                    'month_weeks_data': month_weeks_data,
                    'status': item['status'],
                    'status_display': item['status_display'],
                })
        return all_interns

    def _format_months(self, all_months) -> dict:
        """Форматирует недели каждого месяца для шаблона — всегда 5 столбцов."""
        result = {}
        for month, weeks_in_month in all_months.items():
            formatted = [
                (s.strftime('%d.%m'), e.strftime('%d.%m'))
                for s, e in weeks_in_month[:5]
            ]
            while len(formatted) < 5:
                formatted.append(('—', '—'))
            result[month] = formatted
        return result


def get_kpi_report_data(date_from, date_to, min_kpi):
    """
    Данные для отчёта KPI: менеджеры с KPI >= min_kpi за период.

    Args:
        date_from: дата начала (date)
        date_to: дата окончания (date)
        min_kpi: минимальный порог KPI (float)

    Returns:
        dict: {'error': str} при ошибке валидации, иначе
        {'results': [{'manager': Manager, 'qualifying_weeks_count': int,
                      'qualifying_weeks': [...], 'total_active_devs': int}, ...]}
    """
    from managers.models import Manager

    if date_from > date_to:
        return {'error': 'Дата начала не может быть позже даты окончания'}

    weeks = []
    monday = get_monday(date_from)
    while monday <= date_to:
        weeks.append((monday, monday + timedelta(days=6)))
        monday += timedelta(weeks=1)

    manager_groups = KEYCLOAK_MANAGER_GROUPS
    all_managers = [
        m for m in Manager.objects.filter(is_active=True).order_by('full_name')
        if set(m.groups) & manager_groups
    ]

    active_interns = Intern.objects.filter(
        Q(manual_status__isnull=True) | Q(manual_status=INTERN_STATUS_ACTIVE),
        manager_email__isnull=False,
    ).exclude(manager_email='')

    active_interns_by_manager = defaultdict(list)
    for intern in active_interns:
        active_interns_by_manager[intern.manager_email].append(intern)

    all_active_intern_ids = [
        intern.id
        for interns_list in active_interns_by_manager.values()
        for intern in interns_list
    ]

    if not weeks or not all_active_intern_ids:
        return {'results': []}

    first_week_start = weeks[0][0]
    last_week_end = weeks[-1][1]

    all_interviews = Interview.objects.filter(
        intern_id__in=all_active_intern_ids,
        date__range=[first_week_start, last_week_end]
    ).values('intern_id', 'date', 'interview_type')

    all_statuses = InternWeeklyStatus.objects.filter(
        intern_id__in=all_active_intern_ids,
        week_start__range=[first_week_start, last_week_end]
    )
    weekly_status_dict = {(s.intern_id, s.week_start): s for s in all_statuses}

    interviews_by_intern_week = defaultdict(lambda: defaultdict(int))
    mock_by_intern_week = defaultdict(lambda: defaultdict(bool))

    for interview in all_interviews:
        intern_id = interview['intern_id']
        idate = interview['date']
        for week_idx, (wstart, wend) in enumerate(weeks):
            if wstart <= idate <= wend:
                interviews_by_intern_week[intern_id][week_idx] += 1
                if interview['interview_type'] == 'mock':
                    mock_by_intern_week[intern_id][week_idx] = True
                break

    results = []
    for manager in all_managers:
        manager_interns = active_interns_by_manager.get(manager.email, [])
        if not manager_interns:
            continue

        qualifying_weeks = []
        for week_idx, (wstart, wend) in enumerate(weeks):
            active_count = 0
            total_interviews = 0

            for intern in manager_interns:
                week_status = weekly_status_dict.get((intern.id, wstart))
                should_exclude = False
                count = interviews_by_intern_week[intern.id][week_idx]

                if week_status:
                    if week_status.manual_interview_count is not None:
                        count = week_status.manual_interview_count
                    if week_status.absence_status:
                        should_exclude = True

                if not should_exclude and getattr(intern, 'real_interview_date', None):
                    rid = intern.real_interview_date
                    if wstart <= rid <= wend:
                        if mock_by_intern_week[intern.id][week_idx]:
                            should_exclude = True
                    elif rid < wstart:
                        days_since = (wstart - rid).days
                        if 0 < days_since <= 7:
                            if (mock_by_intern_week[intern.id][week_idx] and
                                    interviews_by_intern_week[intern.id][week_idx] == 1):
                                should_exclude = True
                                count = 0

                if not should_exclude:
                    active_count += 1
                    total_interviews += count

            kpi = total_interviews / active_count if active_count > 0 else 0
            if kpi >= min_kpi:
                qualifying_weeks.append({
                    'week_start': wstart.strftime('%d.%m.%Y'),
                    'week_end': wend.strftime('%d.%m.%Y'),
                    'kpi': round(kpi, 2),
                    'active_count': active_count,
                    'total_interviews': total_interviews,
                })

        if qualifying_weeks:
            results.append({
                'manager': manager,
                'qualifying_weeks_count': len(qualifying_weeks),
                'qualifying_weeks': qualifying_weeks,
                'total_active_devs': len(manager_interns),
            })

    return {'results': results}


def get_developer_count_data(show_hidden):
    """
    Данные для отчёта по количеству активных разработчиков у менеджеров.

    Args:
        show_hidden: включать ли неактивных менеджеров

    Returns:
        dict: {'results': [...], 'hidden_results': [...], 'total_active': int,
               'hidden_count': int}
    """
    from managers.models import Manager

    manager_groups = KEYCLOAK_MANAGER_GROUPS
    active_managers = [
        m for m in Manager.objects.filter(is_active=True).order_by('full_name')
        if set(m.groups) & manager_groups
    ]
    all_hidden = [
        m for m in Manager.objects.filter(is_active=False).order_by('full_name')
        if set(m.groups) & manager_groups
    ]
    hidden_managers = all_hidden if show_hidden else []

    active_interns = Intern.objects.filter(
        Q(manual_status__isnull=True) | Q(manual_status=INTERN_STATUS_ACTIVE),
        manager_email__isnull=False,
    ).exclude(manager_email='')

    active_interns_by_manager = defaultdict(list)
    for intern in active_interns:
        active_interns_by_manager[intern.manager_email].append(intern)

    def build_results(managers):
        out = []
        for manager in managers:
            manager_interns = sorted(
                active_interns_by_manager.get(manager.email, []),
                key=lambda i: i.full_name
            )
            out.append({
                'manager': manager,
                'active_count': len(manager_interns),
                'interns': manager_interns,
            })
        return out

    results = build_results(active_managers)
    hidden_results = build_results(hidden_managers)
    total_active = sum(r['active_count'] for r in results)

    return {
        'results': results,
        'hidden_results': hidden_results,
        'total_active': total_active,
        'hidden_count': len(all_hidden),
    }
