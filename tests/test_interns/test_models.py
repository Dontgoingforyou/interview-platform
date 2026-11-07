"""
Тесты для моделей приложения interns.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.models - для группировки тестов моделей
"""
import pytest
from datetime import date

from core.constants import (
    INTERN_INACTIVE_STATUSES,
    INTERN_STATUS_ACTIVE,
    INTERN_STATUS_LEFT,
    INTERN_STATUS_OFFER,
    INTERN_TRAINING_EXTERNAL,
    INTERN_TRAINING_EXTERNAL_OR_OUTSTAFF,
    INTERN_TRAINING_INTERNAL,
    INTERN_TRAINING_OUTSTAFF,
)
from interns.models import Intern


def _make_intern(direction, **kwargs):
    """Создаёт студента с минимальным набором обязательных полей."""
    defaults = {
        'date_of_receipt': date(2025, 1, 1),
        'date_of_birth': date(2000, 1, 1),
        'hiring_hr': 'HR1',
        'responsible_hr': 'HR2',
        'group': 'GR1',
        'type_of_training': INTERN_TRAINING_INTERNAL,
    }
    defaults.update(kwargs)
    return Intern.objects.create(direction=direction, **defaults)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestInternModel:
    """Тесты для модели Intern."""

    def test_create_intern(self, direction):
        """Создание студента."""
        intern = _make_intern(
            direction,
            full_name='Иван Иванов',
            email='ivan@example.com',
        )
        assert intern.pk is not None
        assert intern.full_name == 'Иван Иванов'
        assert intern.email == 'ivan@example.com'
        assert intern.direction_id == direction.id
        assert intern.type_of_training == INTERN_TRAINING_INTERNAL

    def test_intern_str(self, intern):
        """Проверка строкового представления."""
        expected = f'{intern.full_name} ({intern.group})'
        assert str(intern) == expected

    @pytest.mark.parametrize(
        'training_type',
        [
            INTERN_TRAINING_INTERNAL,
            INTERN_TRAINING_OUTSTAFF,
            INTERN_TRAINING_EXTERNAL,
            INTERN_TRAINING_EXTERNAL_OR_OUTSTAFF,
        ],
    )
    def test_intern_type_of_training_choices(self, direction, training_type):
        """Проверка всех допустимых типов обучения."""
        intern = _make_intern(direction, full_name=f'Тест {training_type}', type_of_training=training_type)
        assert intern.type_of_training == training_type

    def test_intern_type_of_training_display_external(self, direction):
        """Импорт «во вне» сохраняет код external — подпись читаемая."""
        intern = _make_intern(direction, full_name='Внешний', type_of_training=INTERN_TRAINING_EXTERNAL)
        assert intern.type_of_training_display == 'Во вне'

    def test_intern_ordering(self, direction):
        """Проверка сортировки студентов."""
        intern1 = _make_intern(direction, full_name='Первый', date_of_receipt=date(2025, 1, 1), group='GR1')
        intern2 = _make_intern(
            direction, full_name='Второй', date_of_receipt=date(2025, 2, 1),
            group='GR2', type_of_training=INTERN_TRAINING_OUTSTAFF,
        )
        intern3 = _make_intern(direction, full_name='Третий', date_of_receipt=date(2025, 3, 1), group='GR3')

        interns = list(Intern.objects.all())
        # Должны быть отсортированы по убыванию date_of_receipt
        assert interns[0] == intern3
        assert interns[1] == intern2
        assert interns[2] == intern1

    def test_intern_with_manager(self, direction, manager):
        """Создание студента с менеджером."""
        intern = _make_intern(direction, full_name='С менеджером', manager_email=manager.email)
        assert intern.manager_email == manager.email

    def test_intern_without_manager(self, direction):
        """Создание студента без менеджера."""
        intern = _make_intern(direction, full_name='Без менеджера')
        assert intern.manager_email is None

    def test_intern_direction_property(self, intern, direction):
        """Проверка свойства direction."""
        assert intern.direction is not None
        assert intern.direction.id == direction.id
        assert intern.direction.name == direction.name

    def test_intern_direction_fk_access(self, intern, direction):
        """Проверка FK-доступа к направлению через intern.direction."""
        assert intern.direction_id == direction.id
        assert intern.direction.name == direction.name

    def test_intern_manager_property(self, intern, manager):
        """Проверка свойства manager."""
        intern.manager_email = manager.email
        intern.save()
        assert intern.manager is not None
        assert intern.manager.email == manager.email
        assert intern.manager.full_name == manager.full_name

    def test_intern_manager_property_none(self, intern):
        """Проверка свойства manager для студента без менеджера."""
        intern.manager_email = None
        intern.save()
        assert intern.manager is None

    def test_intern_manager_property_nonexistent(self, intern):
        """Проверка свойства manager для несуществующего менеджера."""
        intern.manager_email = 'nonexistent@example.com'
        intern.save()
        assert intern.manager is None

    def test_intern_status_default(self, intern):
        """Проверка статуса по умолчанию - INTERN_STATUS_ACTIVE."""
        assert intern.status == INTERN_STATUS_ACTIVE
        assert intern.status_display == 'Активный'

    def test_intern_status_manual(self, intern):
        """Проверка ручной установки статуса."""
        intern.manual_status = INTERN_STATUS_OFFER
        intern.save()
        assert intern.status == INTERN_STATUS_OFFER
        assert intern.status_display == 'Оффер'

    def test_intern_status_not_affected_by_offers(self, intern):
        """Наличие оффера не влияет на статус автоматически."""
        from offers.models import Offer
        # Создаем оффер для интерна
        Offer.objects.create(
            intern=intern,
            direction_id=intern.direction_id,
            company='Test Company',
            month=12,
            year=2025
        )
        # Статус остаётся INTERN_STATUS_ACTIVE по умолчанию
        assert intern.status == INTERN_STATUS_ACTIVE

    def test_intern_status_not_affected_by_interviews(self, intern):
        """Наличие собеседований не влияет на статус автоматически."""
        from interviews.models import Interview
        from datetime import timedelta
        # Создаем недавнее собеседование
        recent_date = date.today() - timedelta(days=30)
        Interview.objects.create(
            intern=intern,
            direction_id=intern.direction_id,
            interview_type='screening',
            date=recent_date
        )
        # Статус остаётся INTERN_STATUS_ACTIVE по умолчанию
        assert intern.status == INTERN_STATUS_ACTIVE

    def test_intern_status_not_affected_by_debts(self, intern):
        """Наличие долгов не влияет на статус автоматически."""
        from debts.models import Debt
        from decimal import Decimal
        # Создаем долг для интерна
        Debt.objects.create(
            intern=intern,
            direction_id=intern.direction_id,
            total_amount=Decimal('10000.00'),
            paid_amount=Decimal('5000.00'),
            payment_status='paying'
        )
        # Статус остаётся INTERN_STATUS_ACTIVE по умолчанию
        assert intern.status == INTERN_STATUS_ACTIVE

    def test_intern_manual_status_priority(self, intern):
        """Ручной статус (manual_status) определяет фактический статус."""
        from interviews.models import Interview
        from datetime import timedelta
        # Создаем недавнее собеседование
        recent_date = date.today() - timedelta(days=10)
        Interview.objects.create(
            intern=intern,
            direction_id=intern.direction_id,
            interview_type='screening',
            date=recent_date
        )
        # По умолчанию INTERN_STATUS_ACTIVE
        assert intern.status == INTERN_STATUS_ACTIVE

        # Устанавливаем manual_status
        intern.manual_status = INTERN_STATUS_LEFT
        intern.save()
        assert intern.status == INTERN_STATUS_LEFT

    @pytest.mark.parametrize('inactive_status', INTERN_INACTIVE_STATUSES)
    def test_inactive_since_set_when_transition_to_inactive(self, intern, inactive_status):
        """При переходе в статус «ушел» или «оффер» выставляется inactive_since."""
        assert intern.inactive_since is None
        intern.manual_status = inactive_status
        intern.save()
        intern.refresh_from_db()
        assert intern.inactive_since is not None

    def test_inactive_since_cleared_when_transition_to_active(self, intern):
        """При переходе обратно в «активный» inactive_since сбрасывается."""
        intern.manual_status = INTERN_STATUS_LEFT
        intern.save()
        intern.refresh_from_db()
        assert intern.inactive_since is not None
        intern.manual_status = INTERN_STATUS_ACTIVE
        intern.save()
        intern.refresh_from_db()
        assert intern.inactive_since is None

    def test_inactive_since_unchanged_when_already_inactive(self, intern):
        """При повторном save() в неактивном статусе inactive_since не перезаписывается."""
        intern.manual_status = INTERN_STATUS_OFFER
        intern.save()
        intern.refresh_from_db()
        first_since = intern.inactive_since
        assert first_since is not None
        intern.save()
        intern.refresh_from_db()
        assert intern.inactive_since == first_since

    def test_intern_status_without_activity(self, intern):
        """Статус по умолчанию INTERN_STATUS_ACTIVE даже без активности."""
        from interviews.models import Interview
        from datetime import timedelta
        # Создаем старое собеседование (более 60 дней назад)
        old_date = date.today() - timedelta(days=70)
        Interview.objects.create(
            intern=intern,
            direction_id=intern.direction_id,
            interview_type='screening',
            date=old_date
        )
        # Статус по умолчанию INTERN_STATUS_ACTIVE
        assert intern.status == INTERN_STATUS_ACTIVE

    def test_intern_nullable_fields(self, direction):
        """Проверка nullable полей."""
        intern = _make_intern(
            direction,
            full_name='Минимальные данные',
            email=None,
            telegram_username=None,
            cv=None,
            legend=None,
            hr_feedback=None,
            mentor_feedback=None,
            real_interview_date=None,
        )
        assert intern.email is None
        assert intern.telegram_username is None
        assert intern.cv is None
        assert intern.legend is None
        assert intern.hr_feedback is None
        assert intern.mentor_feedback is None
        assert intern.real_interview_date is None
        assert intern.manager_email is None
