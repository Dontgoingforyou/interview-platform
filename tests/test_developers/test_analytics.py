"""
Тесты для analytics_views приложения developers.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.views - для группировки тестов views
"""
import pytest
import json
from datetime import date, timedelta
from django.urls import reverse

from directions.models import Direction
from interns.models import Intern
from interviews.models import Interview
from offers.models import Offer


@pytest.mark.django_db(databases=['default'])
@pytest.mark.views
class TestDeveloperAnalyticsAPI:
    """Тесты для developer_analytics_api."""

    def test_api_requires_login(self, client):
        """API требует авторизации."""
        response = client.get(reverse('developer_analytics_api'))
        # API возвращает 401 вместо редиректа
        assert response.status_code == 401

    def test_api_accessible_to_manager(self, logged_in_manager):
        """Менеджер может получить данные аналитики."""
        response = logged_in_manager.get(reverse('developer_analytics_api'))
        assert response.status_code == 200
        assert 'application/json' in response['Content-Type']

    def test_api_accessible_to_admin(self, logged_in_admin):
        """Админ может получить данные аналитики."""
        response = logged_in_admin.get(reverse('developer_analytics_api'))
        assert response.status_code == 200
        assert 'application/json' in response['Content-Type']

    def test_response_structure(self, logged_in_admin):
        """Проверка структуры ответа API."""
        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        assert 'active-specialists' in data
        assert 'offers-this-year' in data
        assert 'avg-offer-last-month' in data
        assert 'fastest-direction' in data
        assert 'fastest-direction-days' in data
        assert 'top-direction-offers' in data
        assert 'chart_months' in data
        assert 'tooltips' in data

    def test_active_specialists_count(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Подсчет активных специалистов за последние 15 дней."""
        today = date.today()

        # Создаём интервью в последние 15 дней
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=10)
        )

        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        assert data['active-specialists'] == 1

    def test_active_specialists_exclude_old_interviews(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Интервью старше 15 дней не учитываются."""
        today = date.today()

        # Создаём старое интервью (больше 15 дней назад)
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=20)
        )

        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        # Не должно учитываться
        assert data['active-specialists'] == 0

    def test_active_specialists_exclude_cancelled(
        self,
        logged_in_admin,
        intern,
        direction,
        manager
    ):
        """Отменённые интервью не учитываются."""
        today = date.today()

        # Создаём отменённое интервью
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='cancelled',
            date=today - timedelta(days=5)
        )

        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        # Не должно учитываться
        assert data['active-specialists'] == 0

    def test_offers_this_year_count(
        self,
        logged_in_admin,
        intern,
        direction,
        offer_this_year
    ):
        """Подсчет офферов за текущий год."""
        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        assert data['offers-this-year'] == 1

    def test_offers_this_year_unique_pairs(
        self,
        logged_in_admin,
        intern,
        direction
    ):
        """Офферы считаются по уникальным парам (intern_id, direction_id)."""
        today = date.today()

        # Создаём два оффера для одной пары (intern, direction)
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=150000,
            month=today.month,
            year=today.year
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Yandex',
            amount=140000,
            month=today.month,
            year=today.year
        )

        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        # Должен быть учтен как 1 уникальная пара
        assert data['offers-this-year'] == 1

    def test_avg_offer_last_month(
        self,
        logged_in_admin,
        offer_last_month
    ):
        """Средний оффер за последний месяц."""
        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        avg_offer = data['avg-offer-last-month']
        assert float(avg_offer) == 150000.0

    def test_avg_offer_last_month_calculation(
        self,
        logged_in_admin,
        intern,
        direction
    ):
        """Проверка расчета среднего оффера."""
        today = date.today()
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1

        # Создаём офферы с известными суммами
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=100000,
            month=last_month,
            year=last_month_year
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Yandex',
            amount=200000,
            month=last_month,
            year=last_month_year
        )

        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        # Средний оффер должен быть 150000 (может быть int, float или строка)
        avg_offer = data['avg-offer-last-month']
        if isinstance(avg_offer, str):
            avg_offer = float(avg_offer)
        assert float(avg_offer) == 150000.0

    def test_fastest_direction_calculation(
        self,
        logged_in_admin,
        intern,
        direction,
        manager,
        offer_last_month
    ):
        """Проверка расчета самого быстрого направления."""
        today = date.today()
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1

        # Вычисляем последний день месяца оффера
        if last_month == 12:
            next_month = 1
            next_year = last_month_year + 1
        else:
            next_month = last_month + 1
            next_year = last_month_year
        last_day = date(next_year, next_month, 1) - timedelta(days=1)

        # Создаём первое и последнее интервью (разница 10 дней)
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=last_day - timedelta(days=20)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=last_day - timedelta(days=10)
        )

        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        assert data['fastest-direction'] == direction.name
        assert data['fastest-direction-days'] == 11.0  # +1 день включительно

    def test_fastest_direction_excludes_single_interview(
        self,
        logged_in_admin,
        intern,
        direction,
        manager,
        offer_last_month
    ):
        """Направления с одним интервью не учитываются."""
        today = date.today()
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1

        # Вычисляем последний день месяца оффера
        if last_month == 12:
            next_month = 1
            next_year = last_month_year + 1
        else:
            next_month = last_month + 1
            next_year = last_month_year
        last_day = date(next_year, next_month, 1) - timedelta(days=1)

        # Создаём только одно интервью
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=last_day - timedelta(days=10)
        )

        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        assert data['fastest-direction'] == '—'
        assert data['fastest-direction-days'] is None

    def test_fastest_direction_only_before_employment(
        self,
        logged_in_admin,
        intern,
        direction,
        manager,
        offer_last_month
    ):
        """Учитываются только интервью до трудоустройства."""
        today = date.today()
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1

        # Вычисляем последний день месяца оффера
        if last_month == 12:
            next_month = 1
            next_year = last_month_year + 1
        else:
            next_month = last_month + 1
            next_year = last_month_year
        last_day = date(next_year, next_month, 1) - timedelta(days=1)

        # Создаём интервью до и после трудоустройства
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=last_day - timedelta(days=20)
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='tech',
            date=last_day - timedelta(days=10)
        )
        # Интервью после трудоустройства (не должно учитываться)
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=last_day + timedelta(days=5)
        )

        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        # Должны учитываться только интервью до конца месяца оффера
        assert data['fastest-direction-days'] == 11.0  # 20 - 10 + 1

    def test_top_direction_offers(
        self,
        logged_in_admin,
        intern,
        direction,
        offer_last_month
    ):
        """Топ направление по количеству офферов."""
        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        assert data['top-direction-offers'] in [direction.name, '—']

    def test_top_direction_offers_calculation(
        self,
        logged_in_admin,
        intern,
        direction
    ):
        """Проверка расчета топ направления."""
        today = date.today()
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1

        # Создаём второе направление
        direction2 = Direction.objects.create(
            id=2,
            name='Frontend'
        )

        # Создаём офферы для первого направления (3 шт)
        for i in range(3):
            Offer.objects.create(
                intern=intern,
                direction=direction,
                company=f'Company {i}',
                amount=150000,
                month=last_month,
                year=last_month_year
            )

        # Создаём офферы для второго направления (1 шт)
        Offer.objects.create(
            intern=intern,
            direction=direction2,
            company='Company X',
            amount=150000,
            month=last_month,
            year=last_month_year
        )

        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        # Топ направление должно быть первое
        assert data['top-direction-offers'] == direction.name

    def test_chart_months_structure(self, logged_in_admin):
        """Проверка структуры данных графика по месяцам."""
        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        assert 'labels' in data['chart_months']
        assert 'data' in data['chart_months']
        assert isinstance(data['chart_months']['labels'], list)
        assert isinstance(data['chart_months']['data'], list)

    def test_chart_months_with_offers(
        self,
        logged_in_admin,
        intern,
        direction
    ):
        """График показывает офферы по месяцам."""
        today = date.today()

        # Создаём офферы для текущего месяца
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=150000,
            month=today.month,
            year=today.year
        )

        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        chart_data = data['chart_months']

        # Должна быть хотя бы одна метка
        assert len(chart_data['labels']) > 0
        assert len(chart_data['data']) > 0

    def test_tooltips_present(self, logged_in_admin):
        """Проверка наличия подсказок в ответе."""
        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        tooltips = data['tooltips']
        assert 'active-specialists' in tooltips
        assert 'offers-this-year' in tooltips
        assert 'avg-offer-last-month' in tooltips
        assert 'fastest-direction' in tooltips
        assert 'top-direction-offers' in tooltips

    def test_zero_values_when_no_data(self, logged_in_admin):
        """Нулевые значения при отсутствии данных."""
        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        assert data['active-specialists'] == 0
        assert data['offers-this-year'] == 0
        assert data['avg-offer-last-month'] == 0
        assert data['fastest-direction'] == '—'
        assert data['fastest-direction-days'] is None
        assert data['top-direction-offers'] == '—'

    def test_multiple_interns_same_direction(
        self,
        logged_in_admin,
        direction,
        manager
    ):
        """Несколько интернов на одном направлении."""
        today = date.today()
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1

        # Вычисляем последний день месяца оффера
        if last_month == 12:
            next_month = 1
            next_year = last_month_year + 1
        else:
            next_month = last_month + 1
            next_year = last_month_year
        last_day = date(next_year, next_month, 1) - timedelta(days=1)

        # Создаём двух интернов
        intern1 = Intern.objects.create(
            full_name='Intern 1',
            manager_email=manager.email,
            direction=direction,
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )
        intern2 = Intern.objects.create(
            full_name='Intern 2',
            manager_email=manager.email,
            direction=direction,
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )

        # Создаём офферы для обоих
        Offer.objects.create(
            intern=intern1,
            direction=direction,
            company='Google',
            amount=150000,
            month=last_month,
            year=last_month_year
        )
        Offer.objects.create(
            intern=intern2,
            direction=direction,
            company='Yandex',
            amount=140000,
            month=last_month,
            year=last_month_year
        )

        # Создаём интервью для обоих (разная скорость)
        # Intern1: 5 дней
        Interview.objects.create(
            intern=intern1,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=last_day - timedelta(days=10)
        )
        Interview.objects.create(
            intern=intern1,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=last_day - timedelta(days=5)
        )

        # Intern2: 15 дней
        Interview.objects.create(
            intern=intern2,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=last_day - timedelta(days=20)
        )
        Interview.objects.create(
            intern=intern2,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=last_day - timedelta(days=5)
        )

        response = logged_in_admin.get(reverse('developer_analytics_api'))
        data = json.loads(response.content)

        # Средняя скорость: (6 + 16) / 2 = 11 дней (с учетом +1 дня)
        assert data['fastest-direction'] == direction.name
        assert data['fastest-direction-days'] == 11.0


@pytest.mark.django_db(databases=['default'])
@pytest.mark.views
class TestGetDevelopersData:
    """Тесты для функции get_developers_data."""

    def test_get_developers_data_basic(
        self,
        intern,
        direction,
        offer
    ):
        """Базовый тест получения данных разработчиков."""
        from developers.analytics_views import get_developers_data

        data = get_developers_data()

        assert isinstance(data, list)
        assert len(data) == 1

    def test_get_developers_data_structure(
        self,
        intern,
        direction,
        offer
    ):
        """Проверка структуры данных."""
        from developers.analytics_views import get_developers_data

        data = get_developers_data()

        if data:
            developer = data[0]
            assert 'ФИО' in developer
            assert 'Направление' in developer
            assert 'Последняя активность' in developer
            assert 'Количество интервью' in developer

    def test_get_developers_data_with_direction_filter(
        self,
        intern,
        direction,
        offer
    ):
        """Фильтрация по направлению."""
        from developers.analytics_views import get_developers_data

        # Создаём второе направление
        direction2 = Direction.objects.create(
            id=2,
            name='Frontend'
        )

        # Создаём оффер для второго направления
        Offer.objects.create(
            intern=intern,
            direction=direction2,
            company='Google',
            amount=150000,
            month=11,
            year=2025
        )

        # Фильтруем по первому направлению
        data = get_developers_data({'direction': direction.id})

        assert len(data) == 1
        assert data[0]['Направление'] == direction.name

    def test_get_developers_data_with_search_filter(
        self,
        intern,
        direction,
        offer
    ):
        """Фильтрация по поиску."""
        from developers.analytics_views import get_developers_data

        data = get_developers_data({'q': 'Иван'})

        assert len(data) == 1
        assert 'Иван' in data[0]['ФИО']

    def test_get_developers_data_with_ordering(
        self,
        direction,
        manager
    ):
        """Сортировка данных."""
        from developers.analytics_views import get_developers_data

        # Создаём двух интернов
        intern1 = Intern.objects.create(
            full_name='Алексей',
            manager_email=manager.email,
            direction=direction,
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )
        intern2 = Intern.objects.create(
            full_name='Борис',
            manager_email=manager.email,
            direction=direction,
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )

        # Создаём офферы
        Offer.objects.create(
            intern=intern1,
            direction=direction,
            company='Google',
            amount=150000,
            month=11,
            year=2025
        )
        Offer.objects.create(
            intern=intern2,
            direction=direction,
            company='Google',
            amount=150000,
            month=11,
            year=2025
        )

        # Сортировка по ФИО по возрастанию
        data = get_developers_data({'order_by': 'full_name', 'order_dir': 'asc'})

        assert len(data) == 2
        assert data[0]['ФИО'] < data[1]['ФИО']

    def test_get_developers_data_with_interviews(
        self,
        intern,
        direction,
        manager,
        offer
    ):
        """Данные с интервью."""
        from developers.analytics_views import get_developers_data

        today = date.today()

        # Создаём интервью
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=5)
        )

        data = get_developers_data()

        assert len(data) == 1
        assert data[0]['Количество интервью'] == 1
        assert data[0]['Последняя активность'] != '—'

    def test_get_developers_data_without_interviews(
        self,
        intern,
        direction,
        offer
    ):
        """Данные без интервью."""
        from developers.analytics_views import get_developers_data

        data = get_developers_data()

        assert len(data) == 1
        assert data[0]['Количество интервью'] == 0
        assert data[0]['Последняя активность'] == '—'

    def test_get_developers_data_empty(self):
        """Пустой результат при отсутствии офферов."""
        from developers.analytics_views import get_developers_data

        data = get_developers_data()

        assert isinstance(data, list)
        assert len(data) == 0
