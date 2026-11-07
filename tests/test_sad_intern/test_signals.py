"""
Тесты для сигналов приложения sad_intern.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.signals - для группировки тестов сигналов
"""
import pytest
from decimal import Decimal
from datetime import date

from core.constants import SAD_INTERN_ELIGIBLE_MIN_REAL_INTERVIEW_DATE
from sad_intern.models import SadIntern
from interns.models import Intern
from interviews.models import Interview
from offers.models import Offer
from debts.models import Debt


ELIGIBLE_WAIT = date(2026, 1, 15)
BEFORE_MIN = date(2026, 1, 9)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.signals
class TestAutoCreateOrUpdateSadIntern:
    """Тесты для сигнала auto_create_or_update_sad_intern."""

    def test_signal_creates_sad_intern_when_eligible(self, direction):
        """Автосоздание SadIntern при менеджере и real_interview_date >= MIN."""
        intern = Intern.objects.create(
            full_name='Тест Сигнал',
            direction=direction,
            manager_email='manager@example.com',
            telegram_username='@signal_test',
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            real_interview_date=ELIGIBLE_WAIT,
        )

        assert SadIntern.objects.filter(intern=intern).exists()
        sad_intern = SadIntern.objects.get(intern=intern)
        assert sad_intern.waiting_since == ELIGIBLE_WAIT
        assert sad_intern.telegram_username == '@signal_test'
        assert sad_intern.manager_email == 'manager@example.com'

    def test_signal_does_not_create_without_real_interview_date(self, direction):
        """SadIntern не создаётся без real_interview_date."""
        Intern.objects.create(
            full_name='Без даты',
            direction=direction,
            manager_email='manager@example.com',
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            real_interview_date=None,
        )

        assert SadIntern.objects.count() == 0

    def test_signal_does_not_create_without_manager_email(self, direction):
        """SadIntern не создаётся без manager_email."""
        Intern.objects.create(
            full_name='Без менеджера',
            direction=direction,
            manager_email=None,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            real_interview_date=ELIGIBLE_WAIT,
        )

        assert SadIntern.objects.count() == 0

    def test_signal_does_not_create_when_date_before_min(self, direction):
        """SadIntern не создаётся, если real_interview_date раньше порога."""
        Intern.objects.create(
            full_name='Старая дата',
            direction=direction,
            manager_email='manager@example.com',
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            real_interview_date=BEFORE_MIN,
        )

        assert SadIntern.objects.count() == 0

    def test_signal_does_not_update_existing_when_save_ineligible(self, intern, direction):
        """При невыполнении условий сигнал не меняет уже существующую SadIntern."""
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 10, 1),
            telegram_username='@old',
            manager_email='manager@example.com',
        )
        intern.real_interview_date = BEFORE_MIN
        intern.telegram_username = '@new'
        intern.save()

        sad_intern.refresh_from_db()
        assert sad_intern.waiting_since == date(2025, 10, 1)
        assert sad_intern.telegram_username == '@old'

    def test_signal_updates_existing_sad_intern_when_eligible(self, intern):
        """Обновление SadIntern при выполнении условий сигнала."""
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2026, 1, 10),
            telegram_username='@old',
            manager_email='manager@example.com',
        )

        intern.real_interview_date = ELIGIBLE_WAIT
        intern.telegram_username = '@new'
        intern.save()

        sad_intern.refresh_from_db()
        assert sad_intern.waiting_since == ELIGIBLE_WAIT
        assert sad_intern.telegram_username == '@new'
        assert sad_intern.manager_email == 'manager@example.com'

    def test_signal_uses_real_interview_date_always(self, intern, direction):
        """waiting_since = real_interview_date (не даты интервью)."""
        intern.real_interview_date = ELIGIBLE_WAIT
        intern.save()

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            date=date(2026, 2, 5),
        )

        intern.telegram_username = '@updated'
        intern.save()

        sad_intern = SadIntern.objects.get(intern=intern)
        assert sad_intern.waiting_since == ELIGIBLE_WAIT

    def test_signal_preserves_telegram_if_not_set_in_intern(self, intern):
        """Telegram из SadIntern сохраняется, если в Intern пусто (при eligible save)."""
        intern.real_interview_date = ELIGIBLE_WAIT
        intern.save()

        sad_intern = SadIntern.objects.get(intern=intern)
        sad_intern.telegram_username = '@original'
        sad_intern.save()

        intern.telegram_username = None
        intern.save()

        sad_intern.refresh_from_db()
        assert sad_intern.telegram_username == '@original'

    def test_signal_updates_telegram_if_set_in_intern(self, intern):
        """Telegram обновляется из Intern при eligible save."""
        intern.real_interview_date = ELIGIBLE_WAIT
        intern.save()

        sad_intern = SadIntern.objects.get(intern=intern)
        sad_intern.telegram_username = '@old'
        sad_intern.save()

        intern.telegram_username = '@new'
        intern.save()

        sad_intern.refresh_from_db()
        assert sad_intern.telegram_username == '@new'

    def test_signal_preserves_manager_if_not_set_in_intern(self, intern):
        """manager_email в SadIntern сохраняется, если в Intern очистили (ineligible save не трогает)."""
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=ELIGIBLE_WAIT,
            manager_email='manager@example.com',
        )
        intern.manager_email = None
        intern.real_interview_date = ELIGIBLE_WAIT
        intern.save()

        sad_intern.refresh_from_db()
        assert sad_intern.manager_email == 'manager@example.com'

    def test_signal_updates_manager_if_set_in_intern(self, intern):
        """manager_email обновляется из Intern при eligible save."""
        intern.real_interview_date = ELIGIBLE_WAIT
        intern.save()

        sad_intern = SadIntern.objects.get(intern=intern)
        intern.manager_email = 'manager2@example.com'
        intern.save()

        sad_intern.refresh_from_db()
        assert sad_intern.manager_email == 'manager2@example.com'

    def test_signal_updates_days_waiting_on_save(self, intern):
        """days_waiting пересчитывается при обновлении через сигнал."""
        intern.real_interview_date = date(2026, 1, 20)
        intern.save()

        sad_intern = SadIntern.objects.get(intern=intern)
        old_days = sad_intern.days_waiting

        intern.real_interview_date = date(2026, 1, 12)
        intern.save()

        sad_intern.refresh_from_db()
        assert sad_intern.days_waiting > old_days

    def test_min_date_boundary_inclusive(self, direction):
        """Дата ровно SAD_INTERN_ELIGIBLE_MIN_REAL_INTERVIEW_DATE допускается."""
        Intern.objects.create(
            full_name='На границе',
            direction=direction,
            manager_email='manager@example.com',
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            real_interview_date=SAD_INTERN_ELIGIBLE_MIN_REAL_INTERVIEW_DATE,
        )

        assert SadIntern.objects.filter(
            intern__full_name='На границе',
        ).exists()


@pytest.mark.django_db(databases=['default'])
@pytest.mark.signals
class TestOfferDebtDoesNotChangeSadInternStatus:
    """Offer/Debt больше не меняют статус SadIntern."""

    def test_offer_does_not_set_on_project(self, intern, direction):
        intern.real_interview_date = ELIGIBLE_WAIT
        intern.save()

        sad_intern = SadIntern.objects.get(intern=intern)
        sad_intern.status = 'accepted'
        sad_intern.save()

        Offer.objects.create(
            intern=intern, direction=direction, month=1, year=2026, amount=Decimal('100000'),
        )

        sad_intern.refresh_from_db()
        assert sad_intern.status == 'accepted'

    def test_debt_does_not_set_on_project(self, intern):
        intern.real_interview_date = ELIGIBLE_WAIT
        intern.save()

        sad_intern = SadIntern.objects.get(intern=intern)
        sad_intern.status = 'accepted'
        sad_intern.save()

        Debt.objects.create(intern=intern, total_amount=Decimal('10000'), paid_amount=Decimal('0'))

        sad_intern.refresh_from_db()
        assert sad_intern.status == 'accepted'

    def test_offer_without_sad_intern_no_error(self, intern, direction):
        Offer.objects.create(
            intern=intern, direction=direction, month=1, year=2026, amount=Decimal('100000'),
        )
        assert not SadIntern.objects.filter(intern=intern).exists()
