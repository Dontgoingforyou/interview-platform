"""
Тесты для analytics_views приложения managers.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.views - для группировки тестов views
"""
import pytest
import json
from datetime import date, timedelta
from django.urls import reverse

from interviews.models import Interview
from offers.models import Offer


@pytest.mark.django_db(databases=['default'])
@pytest.mark.views
class TestManagersAnalyticsAPI:
    """Тесты для managers_analytics_api."""

    def test_api_requires_login(self, client):
        """API требует авторизации."""
        response = client.get(reverse('api_managers_analytics'))
        # API возвращает 401 вместо редиректа
        assert response.status_code == 401

    def test_api_accessible_to_manager(self, logged_in_manager):
        """Менеджер может получить данные аналитики."""
        response = logged_in_manager.get(reverse('api_managers_analytics'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

    def test_api_accessible_to_admin(self, logged_in_admin):
        """Админ может получить данные аналитики."""
        response = logged_in_admin.get(reverse('api_managers_analytics'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

    def test_response_structure(self, logged_in_admin):
        """Проверка структуры ответа API."""
        response = logged_in_admin.get(reverse('api_managers_analytics'))
        data = json.loads(response.content)

        assert 'managers' in data
        assert 'hot-candidates' in data
        assert 'active-candidates' in data
        assert 'portfolio-candidates' in data
        assert 'avg-candidates' in data
        assert 'top-speed' in data
        assert 'top-speed-count' in data
        assert 'this-week' in data
        assert 'tooltips' in data

    def test_managers_count(self, logged_in_admin, interview, manager):
        """Подсчет количества менеджеров в работе."""
        response = logged_in_admin.get(reverse('api_managers_analytics'))
        data = json.loads(response.content)

        assert data['managers'] == 1

    def test_total_candidates_with_active_interviews(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет кандидатов с интервью за последние 20 дней."""
        today = date.today()

        # Создаём интервью 10 дней назад
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=10)
        )

        response = logged_in_admin.get(reverse('api_managers_analytics'))
        data = json.loads(response.content)

        assert data['active-candidates'] == 1

    def test_excludes_interns_with_offers(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Интерны с офферами исключаются из подсчета."""
        today = date.today()

        # Создаём интервью
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=5)
        )

        # Создаём оффер
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Test Company',
            month=12,
            year=2025
        )

        response = logged_in_admin.get(reverse('api_managers_analytics'))
        data = json.loads(response.content)

        # Интерн с оффером не должен учитываться
        assert data['active-candidates'] == 0

    def test_excludes_interns_with_manual_status(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Интерны со статусом 'ушел' или 'оффер' исключаются."""
        today = date.today()

        # Создаём интервью
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=5)
        )

        # Устанавливаем статус
        intern.manual_status = 'оффер'
        intern.save()

        response = logged_in_admin.get(reverse('api_managers_analytics'))
        data = json.loads(response.content)

        assert data['active-candidates'] == 0

    def test_avg_candidates_calculation(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет среднего количества интервью на менеджера за 30 дней."""
        today = date.today()

        # Создаём 3 интервью за последние 30 дней
        for i in range(3):
            Interview.objects.create(
                intern=intern,
                direction=direction,
                manager_email=manager.email,
                interview_type='screening',
                date=today - timedelta(days=i)
            )

        response = logged_in_admin.get(reverse('api_managers_analytics'))
        data = json.loads(response.content)

        assert data['avg-candidates'] == 3.0

    def test_top_manager_with_most_interviews(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Определение менеджера с наибольшим количеством интервью за 20 дней."""
        today = date.today()

        # Создаём несколько интервью
        for i in range(5):
            Interview.objects.create(
                intern=intern,
                direction=direction,
                manager_email=manager.email,
                interview_type='screening',
                date=today - timedelta(days=i)
            )

        response = logged_in_admin.get(reverse('api_managers_analytics'))
        data = json.loads(response.content)

        assert data['top-speed'] == manager.full_name
        assert data['top-speed-count'] == 5

    def test_interviews_this_week(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет интервью на текущей неделе."""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

        # Создаём интервью на текущей неделе
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=start_of_week + timedelta(days=1)
        )

        response = logged_in_admin.get(reverse('api_managers_analytics'))
        data = json.loads(response.content)

        assert data['this-week'] == 1

    def test_zero_values_when_no_data(self, logged_in_admin):
        """Нулевые значения при отсутствии данных."""
        response = logged_in_admin.get(reverse('api_managers_analytics'))
        data = json.loads(response.content)

        assert data['managers'] == 0
        assert data['active-candidates'] == 0
        assert data['avg-candidates'] == 0.0
        assert data['top-speed'] == "—"
        assert data['top-speed-count'] == 0
        assert data['this-week'] == 0

    def test_tooltips_present(self, logged_in_admin):
        """Проверка наличия подсказок в ответе."""
        response = logged_in_admin.get(reverse('api_managers_analytics'))
        data = json.loads(response.content)

        tooltips = data['tooltips']
        assert 'managers' in tooltips
        assert 'hot-candidates' in tooltips
        assert 'active-candidates' in tooltips
        assert 'portfolio-candidates' in tooltips
        assert 'avg-candidates' in tooltips
        assert 'top-speed' in tooltips
        assert 'this-week' in tooltips


@pytest.mark.django_db(databases=['default'])
@pytest.mark.views
class TestManagersObservationsAPI:
    """Тесты для managers_observations_api."""

    def test_api_requires_login(self, client):
        """API требует авторизации."""
        response = client.get(reverse('api_managers_observations'))
        # API возвращает 401 вместо редиректа
        assert response.status_code == 401

    def test_api_accessible_to_manager(self, logged_in_manager):
        """Менеджер может получить данные наблюдений."""
        response = logged_in_manager.get(reverse('api_managers_observations'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

    def test_api_accessible_to_admin(self, logged_in_admin):
        """Админ может получить данные наблюдений."""
        response = logged_in_admin.get(reverse('api_managers_observations'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

    def test_response_structure(self, logged_in_admin):
        """Проверка структуры ответа API наблюдений."""
        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        assert 'list' in data
        assert 'totalManagers' in data
        assert 'totalCandidates' in data
        assert 'totalInterviews' in data
        assert isinstance(data['list'], list)

    def test_manager_data_structure_in_list(
        self,
        logged_in_admin,
        interview,
        manager
    ):
        """Проверка структуры данных менеджера в списке."""
        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        if data['list']:
            manager_data = data['list'][0]
            assert 'manager' in manager_data
            assert 'candidates' in manager_data
            assert 'interviews' in manager_data
            assert 'successful' in manager_data  # snake_case, не camelCase
            assert 'upcoming' in manager_data
            assert 'cancelled' in manager_data
            assert 'week_count' in manager_data  # snake_case, не camelCase
            assert 'directions' in manager_data

    def test_total_managers_count(self, logged_in_admin, interview, manager):
        """Подсчет общего количества менеджеров."""
        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        assert data['totalManagers'] == 1

    def test_total_candidates_count(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет общего количества кандидатов."""
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date.today()
        )

        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        assert data['totalCandidates'] == 1

    def test_total_interviews_count(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет общего количества интервью."""
        for i in range(3):
            Interview.objects.create(
                intern=intern,
                direction=direction,
                manager_email=manager.email,
                interview_type='screening',
                date=date.today() - timedelta(days=i)
            )

        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        assert data['totalInterviews'] == 3

    def test_successful_candidates_in_observations(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет успешных кандидатов в наблюдениях."""
        # Создаём финальное интервью
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=date.today() - timedelta(days=35)
        )

        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        manager_data = next((m for m in data['list'] if m['manager'] == manager.full_name), None)
        if manager_data:
            assert manager_data['successful'] == 1  # 'successful', не 'successfulCandidates'

    def test_upcoming_interviews_count(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет предстоящих интервью."""
        # Создаём будущее интервью
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date.today() + timedelta(days=5)
        )

        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        manager_data = next((m for m in data['list'] if m['manager'] == manager.full_name), None)
        if manager_data:
            assert manager_data['upcoming'] == 1

    def test_cancelled_interviews_count(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет отмененных интервью."""
        # Создаём отмененное интервью
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='cancelled',
            date=date.today()
        )

        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        manager_data = next((m for m in data['list'] if m['manager'] == manager.full_name), None)
        if manager_data:
            assert manager_data['cancelled'] == 1

    def test_week_count_for_current_week(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет интервью на текущей неделе в наблюдениях."""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

        # Создаём интервью на текущей неделе
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=start_of_week + timedelta(days=2)
        )

        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        manager_data = next((m for m in data['list'] if m['manager'] == manager.full_name), None)
        if manager_data:
            assert manager_data['week_count'] == 1

    def test_directions_count(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет количества направлений для менеджера."""
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date.today()
        )

        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        manager_data = next((m for m in data['list'] if m['manager'] == manager.full_name), None)
        if manager_data:
            assert manager_data['directions'] == 1

    def test_fastest_manager_data(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка данных о самом быстром менеджере."""
        # Создаём первое и финальное интервью
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date.today() - timedelta(days=40)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=date.today() - timedelta(days=35)
        )

        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        assert 'fastest' in data
        if data['fastest']:
            assert 'manager' in data['fastest']
            assert 'avgSpeed' in data['fastest']

    def test_slowest_manager_data(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка данных о самом медленном менеджере."""
        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        assert 'slowest' in data

    def test_slowest_is_none_when_only_one_manager_has_speed(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """slowest=None если только один менеджер имеет вычисленный avgSpeed.

        Когда менеджер только один — сравнивать «самого медленного» не с кем,
        поэтому slowest должен быть None.
        """
        today = date.today()
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=40)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=today - timedelta(days=35)
        )

        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        # Только один менеджер со скоростью — slowest не определён
        assert data['slowest'] is None

    def test_success_sorted_list(self, logged_in_admin, interview):
        """Проверка наличия отсортированного списка по успешности."""
        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        assert 'successSorted' in data
        assert isinstance(data['successSorted'], list)

    def test_busiest_manager_data(self, logged_in_admin, interview):
        """Проверка данных о самом загруженном менеджере."""
        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        assert 'busiest' in data

    def test_biggest_portfolio_data(self, logged_in_admin, interview):
        """Проверка данных о менеджере с наибольшим портфелем."""
        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        assert 'biggestPortfolio' in data

    def test_empty_data_when_no_interviews(self, logged_in_admin):
        """Проверка пустых данных при отсутствии интервью."""
        response = logged_in_admin.get(reverse('api_managers_observations'))
        data = json.loads(response.content)

        assert data['totalManagers'] == 0
        assert data['totalCandidates'] == 0
        assert data['totalInterviews'] == 0
        assert len(data['list']) == 0


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestManagersDashboardDRF:
    """DRF-эндпоинты дашборда менеджеров для React (Bearer)."""

    def test_analytics_unauthenticated_returns_401(self, api_client):
        response = api_client.get('/api/analytics/managers/')
        assert response.status_code == 401

    def test_analytics_manager_bearer_ok(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/analytics/managers/')
        assert response.status_code == 200
        assert 'managers' in response.data
        assert 'tooltips' in response.data
        assert 'hot-candidates' in response.data

    def test_observations_unauthenticated_returns_401(self, api_client):
        response = api_client.get('/api/analytics/managers/observations/')
        assert response.status_code == 401

    def test_observations_manager_bearer_ok(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/analytics/managers/observations/')
        assert response.status_code == 200
        assert 'list' in response.data
        assert 'totalManagers' in response.data

    def test_table_unauthenticated_returns_401(self, api_client):
        response = api_client.get('/api/analytics/managers/table/')
        assert response.status_code == 401

    def test_table_manager_bearer_ok(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/analytics/managers/table/')
        assert response.status_code == 200
        assert 'results' in response.data
        assert isinstance(response.data['results'], list)
