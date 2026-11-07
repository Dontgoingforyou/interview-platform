from datetime import date, timedelta
from urllib.parse import quote

import pytest

from core.constants import INTERN_STATUS_LEFT
from employees.models import InternWeeklyStatus
from interviews.models import Interview

LIST_URL = '/api/employees/managers/'


def board_url(email: str) -> str:
    return f'/api/employees/managers/{quote(email, safe="")}/board/'


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestEmployeeManagersListAPIView:
    """GET /api/employees/managers/"""

    def test_unauthenticated_returns_401_or_403(self, api_client):
        response = api_client.get(LIST_URL)
        assert response.status_code in (401, 403)

    def test_anon_user_returns_403(self, api_client, api_anon_user):
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get(LIST_URL)
        assert response.status_code == 403

    def test_manager_returns_200_with_managers(self, api_client, api_manager_user, manager, manager2):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(LIST_URL)
        assert response.status_code == 200
        assert isinstance(response.data, list)
        emails = {row['email'] for row in response.data}
        assert manager.email in emails
        assert manager2.email in emails
        for row in response.data:
            assert 'email' in row
            assert 'full_name' in row

    def test_pure_admin_manager_excluded_from_list(
        self, api_client, api_admin_user, pure_admin_manager, manager
    ):
        """Менеджер только с группой админов (без employment/cv/education) не попадает в список."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(LIST_URL)
        assert response.status_code == 200
        emails = {row['email'] for row in response.data}
        assert pure_admin_manager.email not in emails
        assert manager.email in emails


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestManagerBoardAPIView:
    """GET /api/employees/managers/<email>/board/"""

    def test_unauthenticated_returns_401_or_403(self, api_client, manager):
        response = api_client.get(board_url(manager.email))
        assert response.status_code in (401, 403)

    def test_manager_returns_200_and_structure(self, api_client, api_manager_user, manager, intern):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(board_url(manager.email))
        assert response.status_code == 200
        data = response.data
        assert data['manager']['email'] == manager.email
        assert 'full_name' in data['manager']
        for key in (
            'recent_weeks',
            'coefficients',
            'active_interns',
            'inactive_interns',
            'all_months',
            'all_months_formatted',
            'all_interns',
            'directions_dict',
            'intern_statuses',
        ):
            assert key in data

    def test_inactive_manager_returns_404(self, api_client, api_manager_user, manager):
        manager.is_active = False
        manager.save(update_fields=['is_active'])
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(board_url(manager.email))
        assert response.status_code == 404

    def test_board_with_interviews_and_weekly_status(
        self, api_client, api_manager_user, manager, intern, direction,
    ):
        """Smoke: реальные данные сервиса — активный интерн, собес и недельный статус."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=week_start + timedelta(days=1),
        )
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=week_start,
            manual_interview_count=2,
        )
        intern.manual_status = INTERN_STATUS_LEFT
        intern.save(update_fields=['manual_status'])

        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(board_url(manager.email))
        assert response.status_code == 200
        data = response.data
        assert len(data['inactive_interns']) == 1
        assert data['inactive_interns'][0]['intern']['id'] == intern.id
        assert data['inactive_interns'][0]['status_display'] == 'Ушёл'
        assert len(data['coefficients']) == 6
        assert data['active_interns'] == []
