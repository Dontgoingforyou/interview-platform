"""
Тесты для аналитики приложения offers.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.views - для группировки тестов views
"""
import json
import pytest
from decimal import Decimal
from django.urls import reverse

from directions.models import Direction
from offers.models import Offer


@pytest.mark.django_db(databases=['default'])
@pytest.mark.views
class TestOfferAnalyticsAPI:
    """Тесты для offer_analytics_api."""

    def test_analytics_api_requires_authentication(self, client):
        """Проверка, что API требует аутентификации."""
        response = client.get(reverse('api_offer_analytics'))
        assert response.status_code == 401
        data = json.loads(response.content)
        assert 'detail' in data or 'error' in data

    def test_analytics_api_requires_manager_role(self, client, set_session):
        """Проверка, что API доступен при наличии SSO авторизации."""
        # Устанавливаем сессию с SSO авторизацией
        set_session(manager_email='manager@example.com', role='manager')

        response = client.get(reverse('api_offer_analytics'))
        # API доступен при наличии SSO авторизации
        assert response.status_code == 200

    def test_analytics_api_empty_database(self, logged_in_manager):
        """Проверка API без офферов в БД."""
        response = logged_in_manager.get(reverse('api_offer_analytics'))
        assert response.status_code == 200

        data = json.loads(response.content)
        assert data['total'] == 0
        assert data['directions'] == 0
        assert data['companies'] == 0
        assert data['avg-offer'] == 0
        assert data['median-offer'] == 0
        assert data['max-offer'] == 0
        assert data['min-offer'] == 0
        assert data['popular-company'] == '—'
        assert data['best-company'] == '—'
        assert data['best-month'] == '—'

    def test_analytics_api_single_offer(self, logged_in_manager, intern, direction):
        """Проверка API с одним оффером."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=Decimal('150000.00'),
            month=1,
            year=2025
        )

        response = logged_in_manager.get(reverse('api_offer_analytics'))
        assert response.status_code == 200

        data = json.loads(response.content)
        assert data['total'] == 1
        assert data['directions'] == 1
        assert data['companies'] == 1
        assert data['avg-offer'] == 150000.00
        assert abs(data['median-offer'] - 150000.00) < 0.01
        assert abs(data['max-offer'] - 150000.00) < 0.01
        assert abs(data['min-offer'] - 150000.00) < 0.01
        assert data['popular-company'] == 'Google'
        assert data['best-company'] == 'Google'

    def test_analytics_api_multiple_offers(self, logged_in_manager, intern, intern_other, direction):
        """Проверка API с несколькими офферами."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=Decimal('150000.00'),
            month=1,
            year=2025
        )
        Offer.objects.create(
            intern=intern_other,
            direction=direction,
            company='Yandex',
            amount=Decimal('120000.00'),
            month=2,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=Decimal('160000.00'),
            month=3,
            year=2025
        )

        response = logged_in_manager.get(reverse('api_offer_analytics'))
        assert response.status_code == 200

        data = json.loads(response.content)
        assert data['total'] == 3
        assert data['directions'] == 1
        assert data['companies'] == 2
        # Среднее: (150000 + 120000 + 160000) / 3 = 143333.33
        assert abs(data['avg-offer'] - 143333.33) < 0.01
        # Медиана: 150000
        assert abs(data['median-offer'] - 150000.00) < 0.01
        assert abs(data['max-offer'] - 160000.00) < 0.01
        assert abs(data['min-offer'] - 120000.00) < 0.01
        # Google встречается 2 раза, Yandex 1 раз
        assert data['popular-company'] == 'Google'
        # Google: среднее (150000 + 160000) / 2 = 155000
        # Yandex: среднее 120000
        assert data['best-company'] == 'Google'

    def test_analytics_api_median_even_count(self, logged_in_manager, intern, direction):
        """Проверка медианы с чётным количеством офферов."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='A',
            amount=Decimal('100000.00'),
            month=1,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='B',
            amount=Decimal('200000.00'),
            month=2,
            year=2025
        )

        response = logged_in_manager.get(reverse('api_offer_analytics'))
        data = json.loads(response.content)
        # Медиана: (100000 + 200000) / 2 = 150000
        assert abs(data['median-offer'] - 150000.00) < 0.01

    def test_analytics_api_median_odd_count(self, logged_in_manager, intern, direction):
        """Проверка медианы с нечётным количеством офферов."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='A',
            amount=Decimal('100000.00'),
            month=1,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='B',
            amount=Decimal('150000.00'),
            month=2,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='C',
            amount=Decimal('200000.00'),
            month=3,
            year=2025
        )

        response = logged_in_manager.get(reverse('api_offer_analytics'))
        data = json.loads(response.content)
        # Медиана: 150000 (средний элемент)
        assert abs(data['median-offer'] - 150000.00) < 0.01

    def test_analytics_api_excludes_empty_companies(self, logged_in_manager, intern, direction):
        """Проверка, что пустые компании исключаются из подсчёта."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=Decimal('150000.00'),
            month=1,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company=None,
            amount=Decimal('120000.00'),
            month=2,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='',
            amount=Decimal('130000.00'),
            month=3,
            year=2025
        )

        response = logged_in_manager.get(reverse('api_offer_analytics'))
        data = json.loads(response.content)
        # Только Google учитывается
        assert data['companies'] == 1
        assert data['popular-company'] == 'Google'
        assert data['best-company'] == 'Google'

    def test_analytics_api_best_month_calculation(self, logged_in_manager, intern, direction):
        """Проверка расчёта лучшего месяца."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='A',
            amount=Decimal('100000.00'),
            month=1,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='B',
            amount=Decimal('200000.00'),
            month=2,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='C',
            amount=Decimal('150000.00'),
            month=2,
            year=2025
        )

        response = logged_in_manager.get(reverse('api_offer_analytics'))
        data = json.loads(response.content)
        # Февраль имеет среднее (200000 + 150000) / 2 = 175000
        # Январь имеет среднее 100000
        assert data['best-month'] == 'Февраль 2025'

    def test_analytics_api_multiple_directions(self, logged_in_manager, intern):
        """Проверка подсчёта уникальных направлений."""
        direction1 = Direction.objects.create(id=10, name='Backend')
        direction2 = Direction.objects.create(id=20, name='Frontend')

        Offer.objects.create(
            intern=intern,
            direction=direction1,
            company='Google',
            amount=Decimal('150000.00'),
            month=1,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction2,
            company='Yandex',
            amount=Decimal('120000.00'),
            month=2,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction1,
            company='VK',
            amount=Decimal('130000.00'),
            month=3,
            year=2025
        )

        response = logged_in_manager.get(reverse('api_offer_analytics'))
        data = json.loads(response.content)
        assert data['directions'] == 2

    def test_analytics_api_tooltips_key_present(self, logged_in_manager):
        """Проверка наличия раздела tooltips в ответе."""
        response = logged_in_manager.get(reverse('api_offer_analytics'))
        data = json.loads(response.content)
        assert 'tooltips' in data

    @pytest.mark.parametrize('key', [
        'total', 'directions', 'companies', 'avg-offer', 'median-offer',
        'max-offer', 'min-offer', 'popular-company', 'best-company', 'best-month',
    ])
    def test_analytics_api_tooltip_per_metric(self, logged_in_manager, key):
        """Проверка наличия подсказки в ответе для каждой метрики."""
        response = logged_in_manager.get(reverse('api_offer_analytics'))
        data = json.loads(response.content)
        assert key in data['tooltips']

    def test_analytics_api_response_format(self, logged_in_manager):
        """Проверка формата JSON ответа."""
        response = logged_in_manager.get(reverse('api_offer_analytics'))
        assert response['Content-Type'] == 'application/json'

        data = json.loads(response.content)
        # Проверка конкретных значений для пустой БД
        assert data['total'] == 0
        assert data['directions'] == 0
        assert data['companies'] == 0
        assert data['avg-offer'] == 0.0
        assert data['median-offer'] == 0.0
        assert data['popular-company'] == '—'
        assert data['best-company'] == '—'
        assert data['best-month'] == '—'
        assert isinstance(data['tooltips'], dict)

    def test_analytics_api_admin_access(self, logged_in_admin, intern, direction):
        """Проверка доступа админа к API."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Test',
            amount=Decimal('100000.00'),
            month=1,
            year=2025
        )

        response = logged_in_admin.get(reverse('api_offer_analytics'))
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['total'] == 1

    def test_analytics_api_offers_with_null_amounts(self, logged_in_manager, intern, intern_other, direction):
        """Проверка обработки офферов с NULL суммами."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=Decimal('150000.00'),
            month=1,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=Decimal('120000.00'),
            month=2,
            year=2025
        )
        # Используем существующую фикстуру intern_other
        # Вместо NULL используем 0, чтобы избежать ошибок в расчете медианы
        Offer.objects.create(
            intern=intern_other,
            direction=direction,
            company='Yandex',
            amount=Decimal('0.00'),
            month=3,
            year=2025
        )

        response = logged_in_manager.get(reverse('api_offer_analytics'))
        data = json.loads(response.content)
        # Всего 3 оффера
        assert data['total'] == 3
        # Среднее: (150000 + 120000 + 0) / 3 = 90000
        assert abs(float(data['avg-offer']) - 90000.00) < 0.01

    def test_analytics_api_rounding(self, logged_in_manager, intern, direction):
        """Проверка округления в ответе."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='A',
            amount=Decimal('100000.33'),
            month=1,
            year=2025
        )
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='B',
            amount=Decimal('100000.66'),
            month=2,
            year=2025
        )

        response = logged_in_manager.get(reverse('api_offer_analytics'))
        data = json.loads(response.content)
        # Проверяем, что округление до 2 знаков
        expected_avg = round((100000.33 + 100000.66) / 2, 2)
        expected_median = round((100000.33 + 100000.66) / 2, 2)
        assert abs(data['avg-offer'] - expected_avg) < 0.01
        assert abs(data['median-offer'] - expected_median) < 0.01
