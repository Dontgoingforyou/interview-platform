"""
Тесты для логики определения статуса студента в модуле employees.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.models - для группировки тестов моделей

После обновления логики:
- Автоматическое определение статуса на основе офферов/долгов/собеседований УБРАНО
- Новые студенты по умолчанию "активные" (если manual_status не задан)
- Статус изменяется только вручную через manual_status
"""
import pytest
from datetime import date, timedelta

from core.constants import (
    INTERN_STATUS_ACTIVE,
    INTERN_STATUS_LEFT,
    INTERN_STATUS_OFFER,
    INTERN_TRAINING_INTERNAL,
)
from interns.models import Intern
from interviews.models import Interview
from offers.models import Offer
from debts.models import Debt


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestInternStatusLogic:
    """Тесты для свойства status в модели Intern."""

    def test_default_status_is_active(self, intern):
        """По умолчанию новый студент получает статус INTERN_STATUS_ACTIVE."""
        assert intern.manual_status is None
        assert intern.status == INTERN_STATUS_ACTIVE

    def test_manual_status_can_be_set(self, intern):
        """Можно вручную установить статус."""
        intern.manual_status = INTERN_STATUS_LEFT
        intern.save()

        assert intern.status == INTERN_STATUS_LEFT
        assert intern.manual_status == INTERN_STATUS_LEFT

    def test_status_not_affected_by_offers(self, intern, direction):
        """Наличие оффера НЕ влияет на статус автоматически."""
        # Создаем оффер
        Offer.objects.create(
            intern=intern,
            direction=direction,
            month=12,
            year=2025
        )

        # Статус остаётся INTERN_STATUS_ACTIVE по умолчанию
        assert intern.status == INTERN_STATUS_ACTIVE

    def test_status_not_affected_by_debts(self, intern, direction):
        """Наличие долга НЕ влияет на статус автоматически."""
        # Создаем долг
        Debt.objects.create(
            intern=intern,
            direction=direction,
            total_amount=100000,
            paid_amount=0,
        )

        # Статус остаётся INTERN_STATUS_ACTIVE по умолчанию
        assert intern.status == INTERN_STATUS_ACTIVE

    def test_status_not_affected_by_recent_interviews(self, intern, direction, manager):
        """Наличие недавних собеседований НЕ влияет на статус автоматически."""
        # Создаем собеседование 30 дней назад
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date.today() - timedelta(days=30)
        )

        # Статус остаётся INTERN_STATUS_ACTIVE по умолчанию
        assert intern.status == INTERN_STATUS_ACTIVE

    def test_status_not_affected_by_old_interviews(self, direction, manager):
        """Отсутствие недавних собеседований НЕ влияет на статус автоматически."""
        # Создаем студента без собеседований
        old_date = date.today() - timedelta(days=70)
        intern = Intern.objects.create(
            full_name='Старый студент',
            email='old@example.com',
            manager_email=manager.email,
            direction=direction,
            date_of_receipt=old_date,
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training=INTERN_TRAINING_INTERNAL
        )

        # Статус по умолчанию INTERN_STATUS_ACTIVE
        assert intern.status == INTERN_STATUS_ACTIVE

    def test_manual_status_offer_with_offers_table(self, intern, direction):
        """Можно вручную установить статус INTERN_STATUS_OFFER при наличии оффера."""
        # Создаем оффер
        Offer.objects.create(
            intern=intern,
            direction=direction,
            month=12,
            year=2025
        )

        # Вручную устанавливаем статус
        intern.manual_status = INTERN_STATUS_OFFER
        intern.save()

        assert intern.status == INTERN_STATUS_OFFER

    def test_manual_status_can_override(self, intern, direction):
        """Ручной статус можно установить независимо от других данных."""
        # Создаем оффер
        Offer.objects.create(
            intern=intern,
            direction=direction,
            month=12,
            year=2025
        )

        # Вручную устанавливаем статус INTERN_STATUS_ACTIVE (не INTERN_STATUS_OFFER)
        intern.manual_status = INTERN_STATUS_ACTIVE
        intern.save()

        assert intern.status == INTERN_STATUS_ACTIVE

    def test_manual_status_left(self, intern, direction, manager):
        """Можно вручную установить статус INTERN_STATUS_LEFT даже при наличии собеседований."""
        # Создаем недавнее собеседование
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date.today() - timedelta(days=5)
        )

        # Вручную устанавливаем статус INTERN_STATUS_LEFT
        intern.manual_status = INTERN_STATUS_LEFT
        intern.save()

        assert intern.status == INTERN_STATUS_LEFT

    @pytest.mark.parametrize('manual_status, expected_display', [
        (None, 'Активный'),
        (INTERN_STATUS_ACTIVE, 'Активный'),
        (INTERN_STATUS_LEFT, 'Ушёл'),
        (INTERN_STATUS_OFFER, 'Оффер'),
    ])
    def test_status_display_property(self, intern, manual_status, expected_display):
        """Проверка свойства status_display для каждого значения manual_status."""
        if manual_status is not None:
            intern.manual_status = manual_status
            intern.save()
        assert intern.status_display == expected_display

    def test_status_remains_active_without_manual_change(self, intern, direction, manager):
        """Статус остаётся INTERN_STATUS_ACTIVE без ручного изменения."""
        # Создаем несколько собеседований
        for days_ago in [5, 10, 20, 40, 55]:
            Interview.objects.create(
                intern=intern,
                direction=direction,
                manager_email=manager.email,
                interview_type='screening',
                date=date.today() - timedelta(days=days_ago)
            )

        # Статус по-прежнему INTERN_STATUS_ACTIVE по умолчанию
        assert intern.status == INTERN_STATUS_ACTIVE

    def test_status_with_offers_and_debts(self, intern, direction):
        """Даже при наличии офферов и долгов статус по умолчанию INTERN_STATUS_ACTIVE."""
        # Создаем и оффер, и долг
        Offer.objects.create(
            intern=intern,
            direction=direction,
            month=12,
            year=2025
        )
        Debt.objects.create(
            intern=intern,
            direction=direction,
            total_amount=100000,
            paid_amount=0,
        )

        # Статус по умолчанию INTERN_STATUS_ACTIVE
        assert intern.status == INTERN_STATUS_ACTIVE

    def test_status_change_from_active_to_offer(self, intern):
        """Можно изменить статус с 'активный' на 'оффер'."""
        assert intern.status == 'активный'

        intern.manual_status = INTERN_STATUS_OFFER
        intern.save()

        assert intern.status == INTERN_STATUS_OFFER

    def test_status_change_from_offer_to_left(self, intern):
        """Можно изменить статус с INTERN_STATUS_OFFER на INTERN_STATUS_LEFT."""
        intern.manual_status = INTERN_STATUS_OFFER
        intern.save()
        assert intern.status == INTERN_STATUS_OFFER

        intern.manual_status = INTERN_STATUS_LEFT
        intern.save()
        assert intern.status == INTERN_STATUS_LEFT
