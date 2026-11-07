"""Тесты debts.drf_list_query."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from dateutil.relativedelta import relativedelta

from core.constants import (
    DEBT_PAYMENT_STATUS_PAYING
)
from debts.drf_list_query import apply_debt_list_filters, apply_debt_list_ordering
from debts.models import Debt, PaymentHistory


@pytest.mark.django_db(databases=['default'])
class TestApplyDebtListFilters:
    def test_search_by_intern_name(self, debt, intern):
        qs = apply_debt_list_filters(Debt.objects.all(), {'search': intern.full_name[:5]})
        assert qs.filter(pk=debt.pk).exists()

    def test_search_by_intern_email(self, debt, intern):
        intern.email = 'unique.debt.search@example.com'
        intern.save(update_fields=['email'])
        qs = apply_debt_list_filters(Debt.objects.all(), {'q': 'unique.debt.search'})
        assert qs.filter(pk=debt.pk).exists()

    def test_search_by_intern_telegram(self, debt, intern):
        intern.telegram_username = '@debt_search_tg'
        intern.save(update_fields=['telegram_username'])
        qs = apply_debt_list_filters(Debt.objects.all(), {'search': 'debt_search_tg'})
        assert qs.filter(pk=debt.pk).exists()

    def test_invalid_direction_ignored(self, debt):
        qs = apply_debt_list_filters(Debt.objects.all(), {'direction': 'abc'})
        assert qs.count() >= 1

    def test_direction_filter(self, debt, direction):
        debt.direction = direction
        debt.save(update_fields=['direction'])
        qs = apply_debt_list_filters(Debt.objects.all(), {'direction': str(direction.id)})
        assert qs.filter(pk=debt.pk).exists()
        assert not qs.exclude(direction_id=direction.id).exists()

    def test_payment_status_filter(self, debt, debt_other):
        qs = apply_debt_list_filters(Debt.objects.all(), {'payment_status': DEBT_PAYMENT_STATUS_PAYING})
        assert qs.filter(pk=debt.pk).exists()
        assert not qs.filter(pk=debt_other.pk).exists()

    def test_intern_id_filter(self, debt, intern):
        qs = apply_debt_list_filters(Debt.objects.all(), {'intern_id': str(intern.id)})
        assert qs.filter(pk=debt.pk).exists()

    def test_invalid_intern_id_ignored(self, debt):
        qs = apply_debt_list_filters(Debt.objects.all(), {'intern_id': 'not-int'})
        assert qs.filter(pk=debt.pk).exists()

    def test_act_date_filter_today(self, debt):
        debt.act_date = date.today()
        debt.save(update_fields=['act_date'])
        qs = apply_debt_list_filters(Debt.objects.all(), {'act_date_filter': 'today'})
        assert qs.filter(pk=debt.pk).exists()

    def test_act_date_filter_this_month(self, debt):
        today = date.today()
        debt.act_date = today
        debt.save(update_fields=['act_date'])
        qs = apply_debt_list_filters(Debt.objects.all(), {'act_date_filter': 'this_month'})
        assert qs.filter(pk=debt.pk).exists()

    def test_act_date_range_filter(self, debt):
        qs = apply_debt_list_filters(
            Debt.objects.all(),
            {'act_date_from': '2025-01-01', 'act_date_to': '2025-01-31'},
        )
        assert qs.filter(pk=debt.pk).exists()

    def test_not_paid_filter_3months(self, intern, direction):
        fixed_today = date(2026, 6, 15)
        old_act = fixed_today - relativedelta(months=4)
        debt_unpaid = Debt.objects.create(
            intern=intern,
            direction=direction,
            total_amount=Decimal('5000.00'),
            paid_amount=Decimal('1000.00'),
            act_date=old_act,
        )
        debt_paid_recent = Debt.objects.create(
            intern=intern,
            direction=direction,
            total_amount=Decimal('3000.00'),
            paid_amount=Decimal('0.00'),
            act_date=old_act,
        )
        PaymentHistory.objects.create(
            debt=debt_paid_recent,
            month=fixed_today.month,
            year=fixed_today.year,
            amount=Decimal('500.00'),
        )
        with patch('debts.drf_list_query.date') as mock_date:
            mock_date.today.return_value = fixed_today
            qs = apply_debt_list_filters(Debt.objects.all(), {'not_paid_filter': '3months'})
        assert qs.filter(pk=debt_unpaid.pk).exists()
        assert not qs.filter(pk=debt_paid_recent.pk).exists()


@pytest.mark.django_db(databases=['default'])
class TestApplyDebtListOrdering:
    def test_order_by_balance_desc(self, debt):
        qs = apply_debt_list_ordering(Debt.objects.all(), {'order_by': 'balance', 'order_dir': 'desc'})
        assert list(qs.values_list('pk', flat=True))

    def test_fully_paid_debt_sorted_last(self, debt, debt_other):
        debt.paid_amount = debt.total_amount
        debt.save()
        qs = apply_debt_list_ordering(Debt.objects.all(), {'order_by': 'balance', 'order_dir': 'desc'})
        pks = list(qs.values_list('pk', flat=True))
        assert pks[-1] == debt.pk
        assert pks[0] == debt_other.pk

    def test_order_by_full_name_asc(self, debt, debt_other, intern, intern_other):
        qs = apply_debt_list_ordering(
            Debt.objects.all(),
            {'order_by': 'full_name', 'order_dir': 'asc'},
        )
        first_name = qs.first().intern.full_name
        assert first_name == min(intern.full_name, intern_other.full_name)

    def test_invalid_order_by_falls_back_to_balance(self, debt):
        qs = apply_debt_list_ordering(Debt.objects.all(), {'order_by': 'unknown_field'})
        assert qs.query.order_by
