"""Тесты employees.services."""
from contextlib import contextmanager
from datetime import date, datetime as dt_datetime, timedelta
from unittest.mock import patch

import pytest

from core.constants import (
    INTERN_STATUS_ACTIVE,
    INTERN_STATUS_LEFT,
    INTERN_STATUS_OFFER,
)
from employees.models import InternWeeklyStatus
from employees.services import (
    ManagerDetailService,
    get_developer_count_data,
    get_kpi_report_data,
    get_monday,
    get_managers_for_employees_list,
)
from interns.models import Intern
from interviews.models import Interview

BOARD_FIXED_TODAY = date(2026, 6, 1)


@contextmanager
def fixed_board_today(today=BOARD_FIXED_TODAY):
    """Фиксирует «сегодня» для _build_52_weeks в ManagerDetailService."""
    with patch('employees.services.datetime') as mock_datetime:
        mock_datetime.now.return_value = dt_datetime(today.year, today.month, today.day)
        mock_datetime.side_effect = lambda *args, **kwargs: dt_datetime(*args, **kwargs)
        yield


class TestGetMonday:
    def test_monday_unchanged(self):
        d = date(2025, 5, 19)
        assert get_monday(d) == d

    def test_wednesday_to_monday(self):
        d = date(2025, 5, 21)
        assert get_monday(d) == date(2025, 5, 19)


@pytest.mark.django_db(databases=['default'])
class TestGetManagersForEmployeesList:
    def test_returns_active_managers(self, manager):
        result = get_managers_for_employees_list()
        emails = [m.email for m in result]
        assert manager.email in emails


@pytest.mark.django_db(databases=['default'])
class TestGetKpiReportData:
    """Unit-тесты get_kpi_report_data без моков ORM."""

    def test_date_from_after_date_to_returns_error(self):
        result = get_kpi_report_data(date(2025, 2, 1), date(2025, 1, 1), 1.0)
        assert result == {'error': 'Дата начала не может быть позже даты окончания'}

    def test_empty_results_without_active_interns(self, manager):
        Intern.objects.filter(manager_email=manager.email).update(
            manual_status=INTERN_STATUS_LEFT,
        )
        result = get_kpi_report_data(date(2025, 1, 6), date(2025, 1, 12), 1.0)
        assert result == {'results': []}

    def test_manager_qualifies_when_kpi_meets_threshold(
        self, manager, intern, direction,
    ):
        week_monday = date(2025, 1, 6)
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=week_monday + timedelta(days=2),
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='tech',
            date=week_monday + timedelta(days=3),
        )
        result = get_kpi_report_data(week_monday, week_monday + timedelta(days=6), 2.0)
        assert 'results' in result
        assert len(result['results']) == 1
        row = result['results'][0]
        assert row['manager'].email == manager.email
        assert row['qualifying_weeks_count'] == 1
        assert row['qualifying_weeks'][0]['kpi'] == 2.0
        assert row['qualifying_weeks'][0]['total_interviews'] == 2
        assert row['total_active_devs'] == 1

    def test_manual_interview_count_overrides_automatic_count(
        self, manager, intern, direction,
    ):
        week_monday = date(2025, 1, 6)
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=week_monday + timedelta(days=1),
        )
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=week_monday,
            manual_interview_count=5,
        )
        result = get_kpi_report_data(week_monday, week_monday + timedelta(days=6), 4.0)
        week_kpi = result['results'][0]['qualifying_weeks'][0]
        assert week_kpi['total_interviews'] == 5
        assert week_kpi['kpi'] == 5.0

    def test_absence_status_excludes_intern_from_kpi(
        self, manager, intern, direction,
    ):
        week_monday = date(2025, 1, 6)
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=week_monday + timedelta(days=2),
        )
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=week_monday,
            absence_status='болеет',
        )
        result = get_kpi_report_data(week_monday, week_monday + timedelta(days=6), 0.5)
        assert result['results'] == []

    def test_mock_on_real_interview_week_excludes_from_kpi(
        self, manager, intern, direction,
    ):
        week_monday = date(2025, 1, 6)
        rid = week_monday + timedelta(days=2)
        intern.real_interview_date = rid
        intern.save(update_fields=['real_interview_date'])
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='mock',
            date=rid,
        )
        result = get_kpi_report_data(week_monday, week_monday + timedelta(days=6), 0.5)
        assert result['results'] == []

    def test_mock_only_next_week_after_real_interview_zeroes_count(
        self, manager, intern, direction,
    ):
        rid = date(2025, 1, 6)
        intern.real_interview_date = rid
        intern.save(update_fields=['real_interview_date'])
        next_week = date(2025, 1, 13)
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='mock',
            date=next_week + timedelta(days=1),
        )
        result = get_kpi_report_data(next_week, next_week + timedelta(days=6), 0.5)
        assert result['results'] == []

    def test_manager_without_active_interns_omitted(self, manager2):
        result = get_kpi_report_data(date(2025, 1, 6), date(2025, 1, 12), 1.0)
        emails = [row['manager'].email for row in result['results']]
        assert manager2.email not in emails


@pytest.mark.django_db(databases=['default'])
class TestGetDeveloperCountData:
    def test_active_counts_and_sorted_interns(self, manager, intern, intern_other):
        intern_other.manager_email = manager.email
        intern_other.full_name = 'Ааа Ааа'
        intern_other.save(update_fields=['manager_email', 'full_name'])
        intern.full_name = 'Яяя Яяя'
        intern.save(update_fields=['full_name'])

        result = get_developer_count_data(show_hidden=False)

        assert result['total_active'] == 2
        assert result['hidden_count'] == 0
        assert result['hidden_results'] == []
        manager_row = next(r for r in result['results'] if r['manager'].email == manager.email)
        assert manager_row['active_count'] == 2
        assert [i.full_name for i in manager_row['interns']] == ['Ааа Ааа', 'Яяя Яяя']

    def test_show_hidden_includes_inactive_manager(
        self, manager, inactive_manager, intern,
    ):
        intern.manager_email = inactive_manager.email
        intern.save(update_fields=['manager_email'])

        without_hidden = get_developer_count_data(show_hidden=False)
        with_hidden = get_developer_count_data(show_hidden=True)

        assert without_hidden['hidden_results'] == []
        assert without_hidden['hidden_count'] == 1
        hidden_emails = [r['manager'].email for r in with_hidden['hidden_results']]
        assert inactive_manager.email in hidden_emails
        hidden_row = next(
            r for r in with_hidden['hidden_results']
            if r['manager'].email == inactive_manager.email
        )
        assert hidden_row['active_count'] == 1

    def test_excludes_interns_with_non_active_manual_status(self, manager, intern):
        intern.manual_status = INTERN_STATUS_LEFT
        intern.save(update_fields=['manual_status'])

        result = get_developer_count_data(show_hidden=False)
        manager_row = next(r for r in result['results'] if r['manager'].email == manager.email)
        assert manager_row['active_count'] == 0
        assert result['total_active'] == 0


@pytest.mark.django_db(databases=['default'])
class TestManagerDetailService:
    def test_get_context_empty_manager(self, manager):
        with fixed_board_today():
            context = ManagerDetailService().get_context(manager)
        assert context['active_interns'] == []
        assert context['inactive_interns'] == []
        assert context['directions_dict'] == {}
        assert len(context['coefficients']) == 6
        assert context['coefficients'] == [0, 0, 0, 0, 0, 0]

    def test_active_and_inactive_interns_split(self, manager, intern, direction):
        intern_left = Intern.objects.create(
            full_name='Ушедший',
            email='left@example.com',
            manager_email=manager.email,
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            manual_status=INTERN_STATUS_LEFT,
        )
        with fixed_board_today():
            context = ManagerDetailService().get_context(manager)
        active_ids = {item['intern'].id for item in context['active_interns']}
        inactive_ids = {item['intern'].id for item in context['inactive_interns']}
        assert intern.id in active_ids
        assert intern_left.id in inactive_ids

    def test_recent_week_interview_count_and_coefficient(
        self, manager, intern, direction,
    ):
        recent_date = BOARD_FIXED_TODAY + timedelta(days=2)
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=recent_date,
        )
        with fixed_board_today():
            context = ManagerDetailService().get_context(manager)
        active = context['active_interns'][0]
        assert active['recent_stats'][-1] == 1
        assert context['coefficients'][-1] == 1.0

    def test_manual_interview_count_and_absence_in_week_stats(
        self, manager, intern,
    ):
        week_start = BOARD_FIXED_TODAY
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=week_start,
            manual_interview_count=3,
            absence_status='отпуск',
            absence_notes='отдых',
        )

        with fixed_board_today():
            context = ManagerDetailService().get_context(manager)

        active = context['active_interns'][0]
        recent_entry = next(
            w for w in active['recent_weeks_data']
            if w['week_start'] == week_start.isoformat()
        )
        assert recent_entry['count'] == 3
        assert recent_entry['absence_info']['status'] == 'отпуск'
        assert recent_entry['absence_info']['notes'] == 'отдых'

    def test_mock_exclusion_on_real_interview_week(
        self, manager, intern, direction,
    ):
        rid = BOARD_FIXED_TODAY
        intern.real_interview_date = rid
        intern.save(update_fields=['real_interview_date'])
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='mock',
            date=rid,
        )
        with fixed_board_today():
            context = ManagerDetailService().get_context(manager)
        active = context['active_interns'][0]
        assert active['exclude_from_coefficient'][-1] is True
        assert context['coefficients'][-1] == 0

    def test_mock_only_next_week_zeroes_count(
        self, manager, intern, direction,
    ):
        rid = BOARD_FIXED_TODAY - timedelta(days=7)
        intern.real_interview_date = rid
        intern.save(update_fields=['real_interview_date'])
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='mock',
            date=BOARD_FIXED_TODAY + timedelta(days=1),
        )
        with fixed_board_today():
            context = ManagerDetailService().get_context(manager)
        assert context['active_interns'][0]['stats'][-1] == 0

    def test_interview_outside_52_weeks_and_null_date_ignored(
        self, manager, intern, direction,
    ):
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date(2020, 1, 1),
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='tech',
            date=None,
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='mock',
            date=BOARD_FIXED_TODAY + timedelta(days=400),
        )
        with fixed_board_today():
            context = ManagerDetailService().get_context(manager)
        assert sum(context['active_interns'][0]['stats']) == 0

    def test_all_interns_monthly_data_and_formatted_months(
        self, manager, intern, direction,
    ):
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date(2026, 5, 15),
        )
        with fixed_board_today():
            context = ManagerDetailService().get_context(manager)
        assert len(context['all_interns']) >= 1
        month_entry = context['all_interns'][0]
        assert month_entry['intern'].id == intern.id
        assert month_entry['status'] == INTERN_STATUS_ACTIVE
        assert len(month_entry['month_weeks_data']) == 5
        assert 'Июнь 2026' in context['all_months_formatted']
        formatted = context['all_months_formatted']['Июнь 2026']
        assert len(formatted) == 5

    def test_offer_status_display(self, manager, intern):
        intern.manual_status = INTERN_STATUS_OFFER
        intern.save(update_fields=['manual_status'])
        with fixed_board_today():
            context = ManagerDetailService().get_context(manager)
        assert context['inactive_interns'][0]['status_display'] == 'Оффер'
