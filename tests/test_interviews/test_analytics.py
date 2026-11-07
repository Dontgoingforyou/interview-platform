"""
Тесты для interview_analytics_api (interviews/analytics_views.py).

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.views - для группировки тестов views
"""
import json
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from interviews.models import Interview

URL = 'interview_analytics_api'


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInterviewAnalyticsAPIDRF:
    """Тот же URL, аутентификация Bearer (React SPA)."""

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get('/api/analytics/interviews/')
        assert response.status_code == 401

    def test_manager_bearer_ok(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/analytics/interviews/')
        assert response.status_code == 200
        assert 'total' in response.data
        assert 'tooltips' in response.data


@pytest.mark.django_db(databases=['default'])
@pytest.mark.views
class TestInterviewAnalyticsAPI:
    """Тесты для interview_analytics_api."""

    # ===== Авторизация =====

    def test_requires_authentication(self, client):
        """GET без сессии → 401 (DRF NotAuthenticated)."""
        response = client.get(reverse(URL))
        assert response.status_code == 401
        data = json.loads(response.content)
        assert 'detail' in data

    def test_accessible_with_manager_session(self, logged_in_manager):
        """GET с сессией менеджера → 200."""
        response = logged_in_manager.get(reverse(URL))
        assert response.status_code == 200

    # ===== Response format =====

    def test_response_is_json(self, logged_in_manager):
        """Ответ должен быть JSON."""
        response = logged_in_manager.get(reverse(URL))
        assert 'application/json' in response['Content-Type']

    @pytest.mark.parametrize('tooltip_key', [
        'total', 'companies', 'upcoming', 'this-week', 'last-week',
        'success-rate', 'cancelled', 'fastest-manager', 'avg-per-person',
        'avg-per-manager', 'total-all-time', 'companies-all-time',
        'success-rate-all-time', 'cancelled-all-time', 'top-manager-all-time',
        'avg-per-person-all-time', 'avg-per-manager-all-time',
    ])
    def test_tooltip_key_present(self, logged_in_manager, tooltip_key):
        """Каждый ожидаемый под-ключ присутствует в tooltips."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert tooltip_key in data['tooltips']

    # ===== Пустая БД =====

    def test_empty_database(self, logged_in_manager):
        """Все метрики равны нулю/пусты при отсутствии данных в БД."""
        response = logged_in_manager.get(reverse(URL))
        assert response.status_code == 200

        data = json.loads(response.content)
        assert data['total'] == 0
        assert data['companies'] == 0
        assert data['upcoming'] == 0
        assert data['this-week'] == 0
        assert data['last-week'] == 0
        assert data['success_rate'] == 0.0
        assert data['cancelled'] == 0
        assert data['fastest_manager'] == ''
        assert data['fastest_manager_count'] == 0
        assert data['avg_per_person'] == 0.0
        assert data['avg_per_manager'] == 0.0
        assert data['total_all_time'] == 0
        assert data['companies_all_time'] == 0
        assert data['success_rate_all_time'] == 0.0
        assert data['top_manager_all_time'] == ''
        assert data['top_manager_count_all_time'] == 0
        assert data['avg_per_person_all_time'] == 0.0
        assert data['avg_per_manager_all_time'] == 0.0
        assert 'tooltips' in data

    # ===== Метрики за 30 дней =====

    def test_total_last_30_days(self, logged_in_manager, interview_last_30, interview_old):
        """total учитывает только интервью в рамках последних 30 дней."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['total'] == 1           # только interview_last_30 (10 дней назад)
        assert data['total_all_time'] == 2  # оба

    def test_unique_companies_last_30_days(self, logged_in_manager, interview_last_30):
        """companies считает уникальные компании за последние 30 дней."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['companies'] == 1

    def test_unique_companies_excludes_null(self, logged_in_manager, intern, direction):
        """Интервью без company не учитывается в companies."""
        today = timezone.now().date()
        Interview.objects.create(
            intern=intern,
            direction=direction,
            company=None,
            manager_email='manager@example.com',
            interview_type='screening',
            date=today - timedelta(days=5),
        )
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['companies'] == 0

    def test_upcoming_count(self, logged_in_manager, interview_upcoming):
        """upcoming = количество интервью с date > today."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['upcoming'] == 1

    def test_cancelled_count(self, logged_in_manager, interview_cancelled_30):
        """cancelled = количество интервью типа cancelled за последние 30 дней."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['cancelled'] == 1

    def test_this_week_count(self, logged_in_manager, interview_this_week):
        """this-week = количество интервью на текущей неделе."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['this-week'] == 1

    def test_last_week_count(self, logged_in_manager, interview_last_week):
        """last-week = количество интервью на прошлой неделе."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['last-week'] == 1

    # ===== Фильтрация по датам (GET-параметры) =====

    def test_date_from_filter(self, logged_in_manager, interview_last_30, interview_old):
        """date_from исключает интервью до указанной даты."""
        today = timezone.now().date()
        date_from = (today - timedelta(days=20)).isoformat()
        response = logged_in_manager.get(reverse(URL), {'date_from': date_from})
        data = json.loads(response.content)
        # interview_last_30 (10 дней назад) попадает, interview_old (40 дней назад) — нет
        assert data['total_all_time'] == 1

    def test_date_to_filter(self, logged_in_manager, interview_last_30, interview_upcoming):
        """date_to исключает интервью после указанной даты."""
        today = timezone.now().date()
        date_to = today.isoformat()
        response = logged_in_manager.get(reverse(URL), {'date_to': date_to})
        data = json.loads(response.content)
        # interview_last_30 (прошлое) попадает, interview_upcoming (будущее) — нет
        assert data['total_all_time'] == 1

    # ===== Success rate =====

    def test_success_rate_zero_when_no_screenings(self, logged_in_manager, interview_cancelled_30):
        """success_rate = 0.0 при отсутствии скринингов за последние 30 дней."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['success_rate'] == 0.0

    def test_success_rate_zero_when_no_tech_after(self, logged_in_manager, interview_last_30):
        """success_rate = 0.0 когда скрининг есть, но tech-интервью после него нет."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['success_rate'] == 0.0

    def test_success_rate_calculated_correctly(
        self, logged_in_manager, interview_last_30, interview_tech_after
    ):
        """success_rate = 1.0 когда скрининг (today-10) + tech (today-5) у того же intern в той же компании."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['success_rate'] == 1.0

    def test_success_rate_all_time_calculated(
        self, logged_in_manager, interview_last_30, interview_tech_after
    ):
        """success_rate_all_time корректно рассчитывается за всё время."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['success_rate_all_time'] == 1.0

    # ===== Метрики менеджеров =====

    def test_fastest_manager_name_resolved(
        self, logged_in_manager, manager, interview_last_30
    ):
        """fastest_manager возвращает full_name, если Manager с таким email есть в БД."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['fastest_manager'] == manager.full_name

    def test_fastest_manager_email_fallback(
        self, logged_in_manager, interview_unknown_manager
    ):
        """fastest_manager возвращает email, если Manager с таким email не найден в БД."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['fastest_manager'] == 'unknown@example.com'

    def test_top_manager_all_time_resolved(
        self, logged_in_manager, manager, interview_last_30
    ):
        """top_manager_all_time возвращает full_name, если Manager есть в БД."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['top_manager_all_time'] == manager.full_name

    def test_top_manager_count_all_time(
        self, logged_in_manager, manager, interview_last_30, interview_old
    ):
        """top_manager_count_all_time = количество интервью самого активного менеджера за всё время."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['top_manager_count_all_time'] == 2

    # ===== Средние значения =====

    def test_avg_per_person_last_30_days(
        self, logged_in_manager, intern, direction, company
    ):
        """avg_per_person = total_last_30 / количество уникальных студентов."""
        today = timezone.now().date()
        Interview.objects.create(
            intern=intern, direction=direction, company=company,
            manager_email='manager@example.com', interview_type='screening',
            date=today - timedelta(days=5),
        )
        Interview.objects.create(
            intern=intern, direction=direction, company=company,
            manager_email='manager@example.com', interview_type='tech',
            date=today - timedelta(days=3),
        )
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        # 2 интервью, 1 уникальный студент → avg = 2.0
        assert data['avg_per_person'] == 2.0

    def test_avg_per_manager_last_30_days(
        self, logged_in_manager, intern, intern_other, direction, company
    ):
        """avg_per_manager = total_last_30 / количество уникальных manager_email."""
        today = timezone.now().date()
        Interview.objects.create(
            intern=intern, direction=direction, company=company,
            manager_email='manager@example.com', interview_type='screening',
            date=today - timedelta(days=5),
        )
        Interview.objects.create(
            intern=intern_other, direction=direction, company=company,
            manager_email='manager2@example.com', interview_type='tech',
            date=today - timedelta(days=3),
        )
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        # 2 интервью, 2 разных менеджера → avg = 1.0
        assert data['avg_per_manager'] == 1.0

    # ===== Метрики за всё время (аккордеон) =====

    @pytest.mark.parametrize('metric_key', [
        'total_all_time', 'companies_all_time', 'upcoming_all_time',
        'this_week_all_time', 'last_week_all_time', 'success_rate_all_time',
        'cancelled_all_time', 'top_manager_all_time', 'top_manager_count_all_time',
        'avg_per_person_all_time', 'avg_per_manager_all_time',
    ])
    def test_all_time_key_present(self, logged_in_manager, metric_key):
        """Каждый ключ блока all_time присутствует в ответе."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert metric_key in data

    def test_all_time_values(self, logged_in_manager, interview_last_30):
        """Значения метрик all_time корректны при наличии одного интервью с компанией."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['total_all_time'] == 1
        assert data['companies_all_time'] == 1

    def test_all_time_includes_old_interviews(
        self, logged_in_manager, interview_last_30, interview_old
    ):
        """total_all_time включает интервью старше 30 дней, total — нет."""
        response = logged_in_manager.get(reverse(URL))
        data = json.loads(response.content)
        assert data['total'] == 1
        assert data['total_all_time'] == 2
