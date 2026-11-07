"""Тесты managers.dashboard_service."""
import pytest
from datetime import date, timedelta

from core.constants import INTERVIEW_TYPE_TECH
from interviews.models import Interview
from managers.dashboard_service import _display_manager_name, build_managers_dashboard_table


@pytest.mark.django_db(databases=['default'])
class TestDisplayManagerName:
    def test_empty(self):
        assert _display_manager_name('') == '—'

    def test_email_passthrough(self):
        assert _display_manager_name('mgr@corp.ru') == 'mgr@corp.ru'


@pytest.mark.django_db(databases=['default'])
class TestBuildManagersDashboardTable:
    def test_manager_with_recent_interview(self, manager, intern, direction):
        today = date.today()
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type=INTERVIEW_TYPE_TECH,
            date=today - timedelta(days=3),
        )
        rows = build_managers_dashboard_table()
        emails = [r['email'] for r in rows]
        assert manager.email in emails
        row = next(r for r in rows if r['email'] == manager.email)
        assert row['hot_candidates_count'] >= 1
