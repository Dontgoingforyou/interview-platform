"""
Тесты для employees/api/admin_api_views.py (админский API: KPI, разработчики).

Покрывают:
- AdminKpiReportAPIView: GET /api/employees/admin/kpi/ — права доступа, валидация, успех
- AdminDeveloperCountAPIView: GET /api/employees/admin/developers/ — права, show_hidden, структура
- Сериализация менеджера и студента проверяется через структуру ответа API.
"""
import pytest
from unittest.mock import patch


KPI_URL = '/api/employees/admin/kpi/'
DEVELOPERS_URL = '/api/employees/admin/developers/'


# ---------------------------------------------------------------------------
# AdminKpiReportAPIView — аутентификация и права
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestAdminKpiReportAPIViewAuth:
    """Права доступа к GET /api/employees/admin/kpi/."""

    def test_unauthenticated_returns_401_or_403(self, api_client):
        """Неаутентифицированный запрос получает 401 или 403."""
        response = api_client.get(KPI_URL, {'date_from': '2025-01-01', 'date_to': '2025-01-31'})
        assert response.status_code in (401, 403)

    def test_manager_returns_403(self, api_client, api_manager_user):
        """Обычный менеджер получает 403."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(KPI_URL, {'date_from': '2025-01-01', 'date_to': '2025-01-31'})
        assert response.status_code == 403

    def test_anon_user_returns_403(self, api_client, api_anon_user):
        """Пользователь без групп получает 403."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get(KPI_URL, {'date_from': '2025-01-01', 'date_to': '2025-01-31'})
        assert response.status_code == 403

    def test_admin_can_access(self, api_client, api_admin_user):
        """Администратор имеет доступ (200 при валидных параметрах)."""
        api_client.force_authenticate(user=api_admin_user)
        with patch('employees.api.admin_api_views.get_kpi_report_data') as mock_get:
            mock_get.return_value = {'results': []}
            response = api_client.get(KPI_URL, {
                'date_from': '2025-01-01',
                'date_to': '2025-01-31',
            })
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# AdminKpiReportAPIView — валидация параметров
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestAdminKpiReportAPIViewValidation:
    """Валидация query-параметров KPI."""

    def test_missing_date_from_returns_400(self, api_client, api_admin_user):
        """Отсутствие date_from возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(KPI_URL, {'date_to': '2025-01-31'})
        assert response.status_code == 400
        assert response.data['error'] == 'Укажите date_from и date_to (YYYY-MM-DD)'

    def test_missing_date_to_returns_400(self, api_client, api_admin_user):
        """Отсутствие date_to возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(KPI_URL, {'date_from': '2025-01-01'})
        assert response.status_code == 400
        assert response.data['error'] == 'Укажите date_from и date_to (YYYY-MM-DD)'

    def test_empty_date_from_returns_400(self, api_client, api_admin_user):
        """Пустой date_from возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(KPI_URL, {'date_from': '', 'date_to': '2025-01-31'})
        assert response.status_code == 400

    @pytest.mark.parametrize('date_from,date_to', [
        ('2025-13-01', '2025-01-31'),
        ('not-a-date', '2025-01-31'),
        ('2025-01-01', 'invalid'),
    ])
    def test_invalid_date_format_returns_400(
        self, api_client, api_admin_user, date_from, date_to
    ):
        """Некорректный формат даты возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(KPI_URL, {'date_from': date_from, 'date_to': date_to})
        assert response.status_code == 400
        assert response.data['error'] == 'Некорректный формат даты или порога KPI'

    def test_invalid_min_kpi_returns_400(self, api_client, api_admin_user):
        """Некорректный min_kpi возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(KPI_URL, {
            'date_from': '2025-01-01',
            'date_to': '2025-01-31',
            'min_kpi': 'not-a-number',
        })
        assert response.status_code == 400
        assert response.data['error'] == 'Некорректный формат даты или порога KPI'

    def test_service_error_returns_400(self, api_client, api_admin_user):
        """Когда get_kpi_report_data возвращает error, ответ 400."""
        api_client.force_authenticate(user=api_admin_user)
        with patch('employees.api.admin_api_views.get_kpi_report_data') as mock_get:
            mock_get.return_value = {'error': 'Дата начала не может быть позже даты окончания'}
            response = api_client.get(KPI_URL, {
                'date_from': '2025-02-01',
                'date_to': '2025-01-01',
            })
        assert response.status_code == 400
        assert response.data['error'] == 'Дата начала не может быть позже даты окончания'


# ---------------------------------------------------------------------------
# AdminKpiReportAPIView — успешный ответ
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestAdminKpiReportAPIViewSuccess:
    """Успешный ответ KPI и структура (сериализация менеджера)."""

    def test_200_returns_date_from_date_to_min_kpi_results(
        self, api_client, api_admin_user, manager
    ):
        """Успешный ответ содержит date_from, date_to, min_kpi, results."""
        api_client.force_authenticate(user=api_admin_user)
        with patch('employees.api.admin_api_views.get_kpi_report_data') as mock_get:
            mock_get.return_value = {
                'results': [{
                    'manager': manager,
                    'qualifying_weeks_count': 4,
                    'qualifying_weeks': [['2025-01-06', '2025-01-12']],
                    'total_active_devs': 2,
                }],
            }
            response = api_client.get(KPI_URL, {
                'date_from': '2025-01-01',
                'date_to': '2025-01-31',
                'min_kpi': '3.5',
            })
        assert response.status_code == 200
        assert response.data['date_from'] == '2025-01-01'
        assert response.data['date_to'] == '2025-01-31'
        assert response.data['min_kpi'] == 3.5
        assert len(response.data['results']) == 1
        item = response.data['results'][0]
        assert item['qualifying_weeks_count'] == 4
        assert item['qualifying_weeks'] == [['2025-01-06', '2025-01-12']]
        assert item['total_active_devs'] == 2

    def test_result_manager_has_serialized_fields(
        self, api_client, api_admin_user, manager
    ):
        """Элемент results содержит manager с full_name, email, is_active."""
        api_client.force_authenticate(user=api_admin_user)
        with patch('employees.api.admin_api_views.get_kpi_report_data') as mock_get:
            mock_get.return_value = {
                'results': [{
                    'manager': manager,
                    'qualifying_weeks_count': 0,
                    'qualifying_weeks': [],
                    'total_active_devs': 0,
                }],
            }
            response = api_client.get(KPI_URL, {
                'date_from': '2025-01-01',
                'date_to': '2025-01-31',
            })
        assert response.status_code == 200
        m = response.data['results'][0]['manager']
        assert m['full_name'] == manager.full_name
        assert m['email'] == manager.email
        assert m['is_active'] is True

    def test_default_min_kpi_is_3(self, api_client, api_admin_user):
        """Без min_kpi вызывается сервис с min_kpi=3.0."""
        api_client.force_authenticate(user=api_admin_user)
        with patch('employees.api.admin_api_views.get_kpi_report_data') as mock_get:
            mock_get.return_value = {'results': []}
            api_client.get(KPI_URL, {
                'date_from': '2025-01-01',
                'date_to': '2025-01-31',
            })
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0]
        assert call_args[2] == 3.0

    def test_empty_min_kpi_defaults_to_3(self, api_client, api_admin_user):
        """Пустая строка min_kpi интерпретируется как 3.0."""
        api_client.force_authenticate(user=api_admin_user)
        with patch('employees.api.admin_api_views.get_kpi_report_data') as mock_get:
            mock_get.return_value = {'results': []}
            api_client.get(KPI_URL, {
                'date_from': '2025-01-01',
                'date_to': '2025-01-31',
                'min_kpi': '',
            })
        call_args = mock_get.call_args[0]
        assert call_args[2] == 3.0


# ---------------------------------------------------------------------------
# AdminDeveloperCountAPIView — аутентификация и права
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestAdminDeveloperCountAPIViewAuth:
    """Права доступа к GET /api/employees/admin/developers/."""

    def test_unauthenticated_returns_401_or_403(self, api_client):
        """Неаутентифицированный запрос получает 401 или 403."""
        response = api_client.get(DEVELOPERS_URL)
        assert response.status_code in (401, 403)

    def test_manager_returns_403(self, api_client, api_manager_user):
        """Обычный менеджер получает 403."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(DEVELOPERS_URL)
        assert response.status_code == 403

    def test_admin_can_access(self, api_client, api_admin_user):
        """Администратор имеет доступ."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(DEVELOPERS_URL)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# AdminDeveloperCountAPIView — успешный ответ и show_hidden
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestAdminDeveloperCountAPIViewSuccess:
    """Успешный ответ и структура (сериализация менеджера и студента)."""

    def test_200_has_results_hidden_results_total_active_hidden_count(
        self, api_client, api_admin_user
    ):
        """Ответ содержит results, hidden_results, total_active, hidden_count."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(DEVELOPERS_URL)
        assert response.status_code == 200
        assert 'results' in response.data
        assert 'hidden_results' in response.data
        assert 'total_active' in response.data
        assert 'hidden_count' in response.data
        assert isinstance(response.data['results'], list)
        assert isinstance(response.data['hidden_results'], list)

    def test_result_item_has_manager_active_count_interns(
        self, api_client, api_admin_user, manager, intern
    ):
        """Элемент results содержит manager (сериализован), active_count, interns."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(DEVELOPERS_URL)
        assert response.status_code == 200
        assert len(response.data['results']) >= 1
        item = next(
            (r for r in response.data['results'] if r['manager']['email'] == manager.email),
            None,
        )
        assert item is not None
        assert item['manager']['full_name'] == manager.full_name
        assert item['manager']['email'] == manager.email
        assert item['manager']['is_active'] is True
        assert item['active_count'] == 1
        assert len(item['interns']) == 1
        inv = item['interns'][0]
        assert inv['id'] == intern.id
        assert inv['full_name'] == intern.full_name
        assert inv['email'] == intern.email
        assert inv['group'] == intern.group
        assert inv['manager_email'] == intern.manager_email

    def test_intern_serialization_null_fields_as_empty_string(
        self, api_client, api_admin_user, manager, direction, db
    ):
        """Студент с пустыми email/group сериализуется с ''."""
        from datetime import date
        from interns.models import Intern
        Intern.objects.create(
            full_name='Пустой Студент',
            email=None,
            manager_email='manager@example.com',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='',
            responsible_hr='',
            group='',
            type_of_training='internal',
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(DEVELOPERS_URL)
        assert response.status_code == 200
        item = next(
            (r for r in response.data['results'] if r['manager']['email'] == manager.email),
            None,
        )
        assert item is not None
        intern_repr = next(
            (i for i in item['interns'] if i['full_name'] == 'Пустой Студент'),
            None,
        )
        assert intern_repr is not None
        assert intern_repr['email'] == ''
        assert intern_repr['group'] == ''
        assert intern_repr['manager_email'] == 'manager@example.com'

    @pytest.mark.parametrize('query_value', ['1', 'true', 'yes'])
    def test_show_hidden_true_includes_hidden(
        self, api_client, api_admin_user, manager2, query_value, db
    ):
        """show_hidden=1/true/yes передаётся в get_developer_count_data."""
        from managers.models import Manager
        Manager.objects.filter(email=manager2.email).update(is_active=False)
        api_client.force_authenticate(user=api_admin_user)
        with patch('employees.api.admin_api_views.get_developer_count_data') as mock_get:
            mock_get.return_value = {
                'results': [],
                'hidden_results': [{
                    'manager': manager2,
                    'active_count': 0,
                    'interns': [],
                }],
                'total_active': 0,
                'hidden_count': 1,
            }
            response = api_client.get(DEVELOPERS_URL, {'show_hidden': query_value})
        assert response.status_code == 200
        mock_get.assert_called_once_with(True)
        assert response.data['hidden_count'] == 1
        assert len(response.data['hidden_results']) == 1

    def test_show_hidden_omitted_calls_service_with_false(
        self, api_client, api_admin_user
    ):
        """Без show_hidden сервис вызывается с show_hidden=False."""
        api_client.force_authenticate(user=api_admin_user)
        with patch('employees.api.admin_api_views.get_developer_count_data') as mock_get:
            mock_get.return_value = {
                'results': [],
                'hidden_results': [],
                'total_active': 0,
                'hidden_count': 0,
            }
            api_client.get(DEVELOPERS_URL)
        mock_get.assert_called_once_with(False)

    def test_response_content_type_json(self, api_client, api_admin_user):
        """Ответ возвращается в формате JSON."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(DEVELOPERS_URL)
        assert response.status_code == 200
        assert 'application/json' in response.get('Content-Type', '')
