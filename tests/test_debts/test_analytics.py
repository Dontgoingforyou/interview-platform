"""
Тесты для analytics_views приложения debts.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.views - для группировки тестов views
"""
import pytest
import json
from datetime import date
from decimal import Decimal
from django.urls import reverse

from debts.models import Debt, PaymentHistory


@pytest.mark.django_db(databases=['default'])
@pytest.mark.views
class TestDebtAnalyticsAPI:
    """Тесты для debt_analytics_api."""

    def test_analytics_api_basic(self, logged_in_manager, intern):
        """Проверка базовой работы API аналитики."""
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('5000.00')
        )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        assert response.status_code == 200

        data = json.loads(response.content)
        assert 'total' in data
        assert 'active' in data
        assert 'closed' in data
        assert data['total'] == 1

    def test_analytics_total_people(self, logged_in_manager, intern):
        """Проверка подсчёта общего количества людей."""
        for i in range(5):
            Debt.objects.create(
                intern=intern,
                total_amount=Decimal('10000.00'),
                paid_amount=Decimal('0.00')
            )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['total'] == 5

    def test_analytics_active_debtors(self, logged_in_manager, intern):
        """Проверка подсчёта активных должников."""
        # Активные должники (balance > 0)
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('3000.00')  # balance = 7000
        )
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('15000.00'),
            paid_amount=Decimal('5000.00')  # balance = 10000
        )
        # Закрытый договор (balance <= 0)
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('10000.00')  # balance = 0
        )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['active'] == 2
        assert data['closed'] == 1

    def test_analytics_closed_contracts(self, logged_in_manager, intern):
        """Проверка подсчёта закрытых договоров."""
        # Закрытые договоры (balance <= 0)
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('10000.00')  # balance = 0
        )
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('12000.00')  # balance = -2000
        )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['closed'] == 2

    def test_analytics_total_sum(self, logged_in_manager, intern):
        """Проверка подсчёта общей суммы договоров."""
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('0.00')
        )
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('15000.00'),
            paid_amount=Decimal('0.00')
        )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['sum-total'] == 25000.0

    def test_analytics_paid_sum(self, logged_in_manager, intern):
        """Проверка подсчёта выплаченной суммы."""
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('5000.00')
        )
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('15000.00'),
            paid_amount=Decimal('7000.00')
        )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['sum-paid'] == 12000.0

    def test_analytics_outstanding_sum(self, logged_in_manager, intern):
        """Проверка подсчёта остатка к получению."""
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('3000.00')  # balance = 7000
        )
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('15000.00'),
            paid_amount=Decimal('5000.00')  # balance = 10000
        )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['sum-out'] == 17000.0

    def test_analytics_avg_outstanding(self, logged_in_manager, intern):
        """Проверка подсчёта среднего остатка на активного должника."""
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('2000.00')  # balance = 8000
        )
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('3000.00')  # balance = 7000
        )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['avg-out'] == 7500.0  # (8000 + 7000) / 2

    def test_analytics_avg_outstanding_no_active(self, logged_in_manager, intern):
        """Проверка среднего остатка при отсутствии активных должников."""
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('10000.00')  # balance = 0
        )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['avg-out'] == 0.0

    def test_analytics_avg_progress(self, logged_in_manager, intern):
        """Проверка подсчёта процента людей, которые стабильно платят каждый месяц.

        Стабильно платящие - это те, у кого есть платежи за каждый из последних 3 месяцев.
        """
        from dateutil.relativedelta import relativedelta

        today = date.today()
        month1 = today - relativedelta(months=2)
        month2 = today - relativedelta(months=1)
        month3 = today

        # Создаем 3 долга
        debt1 = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('5000.00')
        )
        debt2 = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('8000.00')
        )
        debt3 = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('15000.00'),
            paid_amount=Decimal('3000.00')
        )

        # debt1 - стабильно платит (все 3 месяца)
        PaymentHistory.objects.create(debt=debt1, month=month1.month, year=month1.year, amount=Decimal('1000.00'))
        PaymentHistory.objects.create(debt=debt1, month=month2.month, year=month2.year, amount=Decimal('1000.00'))
        PaymentHistory.objects.create(debt=debt1, month=month3.month, year=month3.year, amount=Decimal('1000.00'))

        # debt2 - стабильно платит (все 3 месяца)
        PaymentHistory.objects.create(debt=debt2, month=month1.month, year=month1.year, amount=Decimal('2000.00'))
        PaymentHistory.objects.create(debt=debt2, month=month2.month, year=month2.year, amount=Decimal('2000.00'))
        PaymentHistory.objects.create(debt=debt2, month=month3.month, year=month3.year, amount=Decimal('2000.00'))

        # debt3 - не стабильно платит (только 1 месяц)
        PaymentHistory.objects.create(debt=debt3, month=month1.month, year=month1.year, amount=Decimal('1000.00'))

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        # 2 из 3 долгов стабильно платят: 2/3 * 100 = 66.67%
        assert abs(data['avg-progress'] - 66.67) < 0.1

    def test_analytics_avg_progress_no_total(self, logged_in_manager):
        """Проверка среднего прогресса при отсутствии договоров."""
        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['avg-progress'] == 0.0

    def test_analytics_top_outstanding(self, logged_in_manager, intern):
        """Проверка нахождения максимального остатка."""
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('2000.00')  # balance = 8000
        )
        top_debt = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('20000.00'),
            paid_amount=Decimal('5000.00')  # balance = 15000
        )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['top-out'] == 15000.0
        assert data['top-out-person'] == top_debt.intern.full_name

    def test_analytics_top_outstanding_no_debts(self, logged_in_manager):
        """Проверка максимального остатка при отсутствии долгов."""
        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['top-out'] == 0.0
        assert data['top-out-person'] == ''

    def test_analytics_people_without_payments(self, logged_in_manager, intern):
        """Проверка подсчёта людей без платежей."""
        debt1 = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('0.00')
        )
        debt2 = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('15000.00'),
            paid_amount=Decimal('0.00')
        )
        # Создаём платеж только для одного долга
        PaymentHistory.objects.create(
            debt=debt1,
            month=1,
            year=2025,
            amount=Decimal('1000.00')
        )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['no-payments'] == 1  # Только debt2 без платежей

    def test_analytics_all_people_with_payments(self, logged_in_manager, intern):
        """Проверка, когда у всех есть платежи."""
        debt1 = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('0.00')
        )
        debt2 = Debt.objects.create(
            intern=intern,
            total_amount=Decimal('15000.00'),
            paid_amount=Decimal('0.00')
        )
        PaymentHistory.objects.create(debt=debt1, month=1, year=2025, amount=Decimal('1000.00'))
        PaymentHistory.objects.create(debt=debt2, month=2, year=2025, amount=Decimal('2000.00'))

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        data = json.loads(response.content)
        assert data['no-payments'] == 0

    def test_analytics_empty_database(self, logged_in_manager):
        """Проверка работы API при пустой базе данных."""
        response = logged_in_manager.get(reverse('api_debt_analytics'))
        assert response.status_code == 200

        data = json.loads(response.content)
        assert data['total'] == 0
        assert data['active'] == 0
        assert data['closed'] == 0
        assert data['sum-total'] == 0.0
        assert data['sum-paid'] == 0.0
        assert data['sum-out'] == 0.0
        assert data['avg-out'] == 0.0
        assert data['avg-progress'] == 0.0
        assert data['top-out'] == 0.0
        assert data['top-out-person'] == ''
        assert data['no-payments'] == 0

    def test_analytics_response_format(self, logged_in_manager, intern):
        """Проверка формата ответа API."""
        Debt.objects.create(
            intern=intern,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('5000.00')
        )

        response = logged_in_manager.get(reverse('api_debt_analytics'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'

        data = json.loads(response.content)
        required_keys = {
            'total', 'active', 'closed', 'sum-total', 'sum-paid',
            'sum-out', 'avg-out', 'avg-progress', 'top-out',
            'top-out-person', 'no-payments',
        }
        assert required_keys.issubset(set(data.keys()))
