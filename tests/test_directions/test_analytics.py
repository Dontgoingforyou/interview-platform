"""
Тесты для analytics_views приложения directions.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.views - для группировки тестов views
"""
import pytest
import json
from datetime import date, timedelta
from django.urls import reverse

from interns.models import Intern
from interviews.models import Interview


@pytest.mark.django_db(databases=['default'])
@pytest.mark.views
class TestDirectionMetricsAPI:
    """Тесты для direction_metrics_api."""

    def test_api_requires_login(self, client):
        """API требует авторизации."""
        response = client.get(reverse('directions_analytics_api'))
        assert response.status_code == 401

    def test_api_accessible_to_manager(self, logged_in_manager):
        """Менеджер может получить данные аналитики."""
        response = logged_in_manager.get(reverse('directions_analytics_api'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

    def test_api_accessible_to_admin(self, logged_in_admin):
        """Админ может получить данные аналитики."""
        response = logged_in_admin.get(reverse('directions_analytics_api'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

    def test_response_structure(self, logged_in_admin):
        """Проверка структуры ответа API."""
        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert 'total-directions' in data
        assert 'total_interviews' in data
        assert 'total_tech_interviews_count' in data
        assert 'total_candidates' in data
        assert 'total_upcoming' in data
        assert 'metrics' in data
        assert 'metrics_data' in data
        assert 'target_date' in data
        assert 'directions' in data
        assert 'top_direction_30' in data
        assert 'top_direction_90' in data
        assert 'best_conversion' in data
        assert 'worst_conversion' in data
        assert 'fastest_direction' in data
        assert 'fastest_direction_person' in data
        assert 'slowest_direction' in data
        assert 'slowest_direction_person' in data
        assert 'best_month' in data
        assert 'worst_month' in data
        assert 'tech_share' in data
        assert 'chart_directions' in data
        assert 'chart_months' in data
        assert 'tooltips' in data

    def test_metrics_is_list(self, logged_in_admin):
        """Поле metrics должно быть списком."""
        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert isinstance(data['metrics'], list)

    def test_direction_count(self, logged_in_admin, interview, direction):
        """Подсчет количества направлений."""
        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert data['directions'] == 1
        assert data['total-directions'] == 1

    def test_total_interviews_with_direction(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет интервью по направлению."""
        today = date.today()

        for i in range(3):
            Interview.objects.create(
                intern=intern,
                direction=direction,
                manager_email=manager.email,
                interview_type='screening',
                date=today - timedelta(days=i)
            )

        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert data['total_interviews'] == 3

    def test_total_tech_interviews_count_in_api(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет технических интервью в ответе API."""
        today = date.today()

        for i in range(2):
            Interview.objects.create(
                intern=intern,
                direction=direction,
                manager_email=manager.email,
                interview_type='tech',
                date=today - timedelta(days=i)
            )

        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert data['total_tech_interviews_count'] == 2
        assert len(data['metrics_data']) == 1
        assert data['metrics_data'][0]['tech_interviews'] == 2

    def test_total_candidates_count(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет уникальных кандидатов (3 интервью одного студента = 1 кандидат)."""
        today = date.today()

        for i in range(3):
            Interview.objects.create(
                intern=intern,
                direction=direction,
                manager_email=manager.email,
                interview_type='screening',
                date=today - timedelta(days=i)
            )

        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert data['total_candidates'] == 1

    def test_upcoming_interviews_count(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет предстоящих интервью."""
        today = date.today()

        # Прошлое интервью — чтобы направление попало в статистику
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=5)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='tech',
            date=today + timedelta(days=10)
        )

        response = logged_in_admin.get(
            reverse('directions_analytics_api') + f'?date_filter={today.isoformat()}'
        )
        data = json.loads(response.content)

        assert data['total_upcoming'] == 1

    def test_conversion_rate_calculation(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Расчет конверсии из скрининга в tech."""
        today = date.today()

        # 2 скрининга и 1 tech → конверсия 50%
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=10)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=9)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='tech',
            date=today - timedelta(days=5)
        )

        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert len(data['metrics']) == 1
        assert data['metrics'][0]['conversion_rate'] == 50.0

    @pytest.mark.parametrize('days_back, field', [
        (5, 'top_direction_30'),
        (60, 'top_direction_90'),
    ])
    def test_top_direction_by_period(
        self,
        logged_in_admin,
        intern,
        direction,
        manager,
        days_back,
        field
    ):
        """Определение самого активного направления за 30/90 дней."""
        today = date.today()

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=days_back)
        )

        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert data[field] in [direction.name, f'ID: {direction.id}']

    def test_fastest_direction_with_person(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка самого быстрого направления с ФИО кандидата."""
        today = date.today()

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=50)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=today - timedelta(days=40)
        )

        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert any(name in data['fastest_direction'] for name in [direction.name, f'ID: {direction.id}'])
        assert '10 дн.' in data['fastest_direction']
        assert data['fastest_direction_person'] == intern.full_name

    def test_slowest_direction_with_person(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка самого медленного направления с ФИО кандидата."""
        today = date.today()

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=100)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=today - timedelta(days=40)
        )

        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert any(name in data['slowest_direction'] for name in [direction.name, f'ID: {direction.id}'])
        assert '60 дн.' in data['slowest_direction']
        assert data['slowest_direction_person'] == intern.full_name

    def test_tech_share_calculation(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Расчет доли технических собеседований (2 screening + 2 tech = 50%)."""
        today = date.today()

        for i in range(2):
            Interview.objects.create(
                intern=intern,
                direction=direction,
                manager_email=manager.email,
                interview_type='screening',
                date=today - timedelta(days=i)
            )
            Interview.objects.create(
                intern=intern,
                direction=direction,
                manager_email=manager.email,
                interview_type='tech',
                date=today - timedelta(days=i)
            )

        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert data['tech_share'] == 50.0

    @pytest.mark.parametrize('chart_key', ['chart_directions', 'chart_months'])
    def test_chart_structure(self, logged_in_admin, interview, chart_key):
        """Поля chart_* содержат labels и data в виде списков."""
        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert isinstance(data[chart_key]['labels'], list)
        assert isinstance(data[chart_key]['data'], list)

    def test_tooltips_present(self, logged_in_admin):
        """Проверка наличия подсказок в ответе."""
        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        tooltips = data['tooltips']
        assert 'total-directions' in tooltips
        assert 'directions' in tooltips
        assert 'top-direction' in tooltips
        assert 'best-conversion' in tooltips
        assert 'worst-conversion' in tooltips
        assert 'fastest' in tooltips
        assert 'slowest' in tooltips
        assert 'best-month' in tooltips
        assert 'worst-month' in tooltips
        assert 'tech-share' in tooltips

    def test_zero_values_when_no_data(self, logged_in_admin):
        """Нулевые значения при отсутствии данных."""
        response = logged_in_admin.get(reverse('directions_analytics_api'))
        data = json.loads(response.content)

        assert data['directions'] == 0
        assert data['total_interviews'] == 0
        assert data['total_candidates'] == 0
        assert data['total_upcoming'] == 0
        assert data['fastest_direction'] == '—'
        assert data['fastest_direction_person'] == ''
        assert data['slowest_direction'] == '—'
        assert data['slowest_direction_person'] == ''

    def test_date_filter_parameter(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка работы фильтра по дате."""
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date(2025, 11, 1)
        )

        response = logged_in_admin.get(
            reverse('directions_analytics_api') + '?date_filter=2025-11-15'
        )
        data = json.loads(response.content)

        assert data['target_date'] == '2025-11-15'
        assert data['total_interviews'] == 1

    def test_direction_filter_parameter(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка работы фильтра по направлению."""
        today = date.today()

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=5)
        )

        response = logged_in_admin.get(
            reverse('directions_analytics_api') + f'?direction={direction.id}'
        )
        data = json.loads(response.content)

        assert len(data['metrics']) == 1
        assert data['metrics'][0]['direction']['id'] == direction.id

    def test_min_conversion_filter(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка работы фильтра по минимальной конверсии."""
        today = date.today()

        # 2 скрининга и 1 tech → конверсия 50%
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=10)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=9)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='tech',
            date=today - timedelta(days=5)
        )

        # Фильтруем с минимальной конверсией 60% — ничего не должно вернуться
        response = logged_in_admin.get(
            reverse('directions_analytics_api') + '?min_conversion=60'
        )
        data = json.loads(response.content)

        assert len(data['metrics']) == 0


@pytest.mark.django_db(databases=['default'])
@pytest.mark.views
class TestDirectionsObservationsAPI:
    """Тесты для directions_observations_api."""

    def test_api_requires_login(self, client):
        """API требует авторизации."""
        response = client.get(reverse('directions_observations_api'))
        assert response.status_code == 401

    def test_api_accessible_to_manager(self, logged_in_manager):
        """Менеджер может получить данные наблюдений."""
        response = logged_in_manager.get(reverse('directions_observations_api'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

    def test_api_accessible_to_admin(self, logged_in_admin):
        """Админ может получить данные наблюдений."""
        response = logged_in_admin.get(reverse('directions_observations_api'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

    def test_response_structure(self, logged_in_admin):
        """Проверка структуры ответа API наблюдений."""
        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        assert 'list' in data
        assert 'totalDirections' in data
        assert 'totalCandidates' in data
        assert 'totalInterviews' in data
        assert 'fastest' in data
        assert 'slowest' in data
        assert 'highestCancel' in data
        assert 'mostManagers' in data
        assert 'highestUpcoming' in data
        assert 'bestConversion' in data
        assert 'worstConversion' in data
        assert 'focusNeeded' in data
        assert 'bestMonth' in data
        assert 'worstMonth' in data
        assert isinstance(data['list'], list)

    def test_direction_data_structure_in_list(
        self,
        logged_in_admin,
        interview,
        direction
    ):
        """Проверка структуры данных направления в списке."""
        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        assert len(data['list']) == 1
        direction_data = data['list'][0]
        assert 'direction' in direction_data
        assert 'candidates' in direction_data
        assert 'interviews' in direction_data
        assert 'successful' in direction_data
        assert 'upcoming' in direction_data
        assert 'cancelled' in direction_data
        assert 'week_count' in direction_data
        assert 'managers' in direction_data
        assert 'avgSpeed' in direction_data
        assert 'successRate' in direction_data
        assert 'cancelRate' in direction_data

    def test_total_directions_count(self, logged_in_admin, interview, direction):
        """Подсчет общего количества направлений."""
        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        assert data['totalDirections'] == 1

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

        response = logged_in_admin.get(reverse('directions_observations_api'))
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
        today = date.today()

        for i in range(3):
            Interview.objects.create(
                intern=intern,
                direction=direction,
                manager_email=manager.email,
                interview_type='screening',
                date=today - timedelta(days=i)
            )

        response = logged_in_admin.get(reverse('directions_observations_api'))
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
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=date.today() - timedelta(days=35)
        )

        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        direction_data = next(
            (d for d in data['list'] if d['direction'] == direction.name),
            None
        )
        assert direction_data is not None
        assert direction_data['successful'] == 1

    def test_upcoming_interviews_count(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет предстоящих интервью."""
        today = date.today()

        # Прошлое интервью — чтобы направление попало в список
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=5)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today + timedelta(days=5)
        )

        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        direction_data = next(
            (d for d in data['list'] if d['direction'] == direction.name),
            None
        )
        assert direction_data is not None
        assert direction_data['upcoming'] == 1

    def test_cancelled_interviews_count(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет отмененных интервью."""
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='cancelled',
            date=date.today()
        )

        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        direction_data = next(
            (d for d in data['list'] if d['direction'] == direction.name),
            None
        )
        assert direction_data is not None
        assert direction_data['cancelled'] == 1

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

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=start_of_week + timedelta(days=2)
        )

        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        direction_data = next(
            (d for d in data['list'] if d['direction'] == direction.name),
            None
        )
        assert direction_data is not None
        assert direction_data['week_count'] == 1

    def test_managers_count(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет количества менеджеров для направления."""
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date.today()
        )

        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        direction_data = next(
            (d for d in data['list'] if d['direction'] == direction.name),
            None
        )
        assert direction_data is not None
        assert direction_data['managers'] == 1

    def test_avg_speed_calculation(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка расчета средней скорости до финала (50 - 40 = 10 дней)."""
        today = date.today()

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=50)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=today - timedelta(days=40)
        )

        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        direction_data = next(
            (d for d in data['list'] if d['direction'] == direction.name),
            None
        )
        assert direction_data is not None
        assert direction_data['avgSpeed'] == 10.0

    def test_success_rate_calculation(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка расчета коэффициента успешности (1 из 2 кандидатов = 0.5)."""
        intern2 = Intern.objects.create(
            full_name='Петр Петров',
            manager_email=manager.email,
            direction=direction,
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )

        today = date.today()

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=today - timedelta(days=40)
        )
        Interview.objects.create(
            intern=intern2,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=5)
        )

        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        direction_data = next(
            (d for d in data['list'] if d['direction'] == direction.name),
            None
        )
        assert direction_data is not None
        assert direction_data['successRate'] == 0.5

    def test_cancel_rate_calculation(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка расчета коэффициента отмен (1 из 3 ≈ 0.333)."""
        today = date.today()

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=10)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='tech',
            date=today - timedelta(days=5)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='cancelled',
            date=today
        )

        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        direction_data = next(
            (d for d in data['list'] if d['direction'] == direction.name),
            None
        )
        assert direction_data is not None
        assert 0.3 <= direction_data['cancelRate'] <= 0.4

    def test_fastest_direction_data(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка данных о самом быстром направлении."""
        today = date.today()

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=50)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=today - timedelta(days=40)
        )

        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        assert data['fastest'] is not None
        assert 'direction' in data['fastest']
        assert 'avgSpeed' in data['fastest']

    def test_slowest_direction_data(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Проверка данных о самом медленном направлении."""
        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        assert 'slowest' in data

    def test_highest_cancel_data(self, logged_in_admin, interview):
        """Проверка наличия направления с наибольшим количеством отмен."""
        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        assert 'highestCancel' in data
        if data['highestCancel'] is not None:
            assert 'direction' in data['highestCancel']
            assert 'cancelRate' in data['highestCancel']

    def test_best_conversion_data(self, logged_in_admin, interview):
        """Проверка данных о лучшей конверсии."""
        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        assert 'bestConversion' in data

    def test_worst_conversion_data(self, logged_in_admin, interview):
        """Проверка данных о худшей конверсии."""
        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        assert 'worstConversion' in data

    def test_empty_data_when_no_interviews(self, logged_in_admin):
        """Проверка пустых данных при отсутствии интервью."""
        response = logged_in_admin.get(reverse('directions_observations_api'))
        data = json.loads(response.content)

        assert data['totalDirections'] == 0
        assert data['totalCandidates'] == 0
        assert data['totalInterviews'] == 0
        assert len(data['list']) == 0
