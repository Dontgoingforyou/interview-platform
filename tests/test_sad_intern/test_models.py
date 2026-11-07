"""
Тесты для моделей приложения sad_intern.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.models - для группировки тестов моделей
"""
import pytest
from datetime import date, timedelta
from django.utils import timezone

from sad_intern.models import SadIntern
from interns.models import Intern


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestSadInternModel:
    """Тесты для модели SadIntern."""

    def test_create_sad_intern(self, intern):
        """Создание грустящего студента."""
        waiting_date = date(2025, 11, 1)
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=waiting_date,
            telegram_username='@test_user',
            manager_email='manager@example.com',
            status='rejected',
            note='Тестовое примечание'
        )
        assert sad_intern.pk is not None
        assert sad_intern.intern == intern
        assert sad_intern.waiting_since == waiting_date
        assert sad_intern.telegram_username == '@test_user'
        assert sad_intern.manager_email == 'manager@example.com'
        assert sad_intern.status == 'rejected'
        assert sad_intern.note == 'Тестовое примечание'

    def test_sad_intern_str(self, sad_intern):
        """Проверка строкового представления."""
        expected = f'{sad_intern.intern.full_name} - {sad_intern.days_waiting} дней в ожидании'
        assert str(sad_intern) == expected

    def test_sad_intern_auto_calculate_days_waiting(self, intern):
        """Проверка автоматического вычисления days_waiting."""
        today = timezone.now().date()
        waiting_date = today - timedelta(days=15)
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=waiting_date,
        )
        assert sad_intern.days_waiting == 15

    def test_sad_intern_update_days_waiting_on_save(self, sad_intern):
        """Проверка обновления days_waiting при сохранении."""
        old_days = sad_intern.days_waiting
        # Изменяем дату ожидания
        sad_intern.waiting_since = sad_intern.waiting_since - timedelta(days=5)
        sad_intern.save()
        assert sad_intern.days_waiting == old_days + 5

    @pytest.mark.parametrize('status', ['rejected', 'accepted', 'offered', 'fired', 'on_project'])
    def test_sad_intern_status_choices(self, intern, status):
        """Проверка создания записи с каждым из допустимых статусов."""
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 11, 1),
            status=status
        )
        assert sad_intern.status == status

    def test_sad_intern_ordering(self, direction):
        """Проверка сортировки по days_waiting."""
        intern1 = Intern.objects.create(
            full_name='Первый',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )
        intern2 = Intern.objects.create(
            full_name='Второй',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR2',
            type_of_training='internal'
        )
        intern3 = Intern.objects.create(
            full_name='Третий',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR3',
            type_of_training='internal'
        )

        # Создаём sad_interns с разными датами ожидания
        today = timezone.now().date()
        sad1 = SadIntern.objects.create(
            intern=intern1,
            waiting_since=today - timedelta(days=10)
        )
        sad2 = SadIntern.objects.create(
            intern=intern2,
            waiting_since=today - timedelta(days=25)
        )
        sad3 = SadIntern.objects.create(
            intern=intern3,
            waiting_since=today - timedelta(days=15)
        )

        sad_interns = list(SadIntern.objects.all())
        # Должны быть отсортированы по убыванию days_waiting
        assert sad_interns[0] == sad2  # 25 дней
        assert sad_interns[1] == sad3  # 15 дней
        assert sad_interns[2] == sad1  # 10 дней

    def test_sad_intern_with_manager(self, intern, manager):
        """Создание грустящего студента с менеджером."""
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 11, 1),
            manager_email=manager.email
        )
        assert sad_intern.manager_email == manager.email
        assert sad_intern.manager == manager

    def test_sad_intern_without_manager(self, intern):
        """Создание грустящего студента без менеджера."""
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 11, 1)
        )
        assert sad_intern.manager_email is None
        assert sad_intern.manager is None

    def test_sad_intern_manager_property(self, sad_intern, manager):
        """Проверка свойства manager."""
        sad_intern.manager_email = manager.email
        sad_intern.save()
        assert sad_intern.manager is not None
        assert sad_intern.manager.email == manager.email
        assert sad_intern.manager.full_name == manager.full_name

    def test_sad_intern_manager_property_none(self, sad_intern):
        """Проверка свойства manager для студента без менеджера."""
        sad_intern.manager_email = None
        sad_intern.save()
        assert sad_intern.manager is None

    def test_sad_intern_manager_property_nonexistent(self, sad_intern):
        """Проверка свойства manager для несуществующего менеджера."""
        sad_intern.manager_email = 'nonexistent@example.com'
        sad_intern.save()
        assert sad_intern.manager is None

    def test_sad_intern_nullable_fields(self, intern):
        """Проверка nullable полей."""
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 11, 1),
            telegram_username=None,
            manager_email=None,
            status=None,
            note=None
        )
        assert sad_intern.telegram_username is None
        assert sad_intern.manager_email is None
        assert sad_intern.status is None
        assert sad_intern.note is None

    def test_sad_intern_date_added_auto_now(self, intern):
        """Проверка автоматической установки date_added."""
        today = timezone.now().date()
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 11, 1)
        )
        assert sad_intern.date_added is not None
        # Проверяем, что дата находится в разумном диапазоне (с учетом временных зон)
        # Допускаем разницу в 1 день из-за возможных проблем с timezone
        date_diff = abs((sad_intern.date_added - today).days)
        assert date_diff <= 1, f"date_added ({sad_intern.date_added}) слишком отличается от today ({today})"

    def test_sad_intern_days_waiting_zero_if_today(self, intern):
        """Проверка days_waiting=0 если waiting_since сегодня."""
        today = timezone.now().date()
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=today
        )
        assert sad_intern.days_waiting == 0

    def test_sad_intern_days_waiting_negative_future_date(self, intern):
        """days_waiting устанавливается в 0 если waiting_since в будущем (защита от отрицательных значений)."""
        future_date = timezone.now().date() + timedelta(days=5)
        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=future_date
        )
        assert sad_intern.days_waiting == 0

    def test_sad_intern_cascade_delete(self, sad_intern, intern):
        """Проверка каскадного удаления при удалении intern."""
        sad_intern_id = sad_intern.pk
        intern.delete()
        assert not SadIntern.objects.filter(pk=sad_intern_id).exists()

    def test_sad_intern_related_name(self, intern):
        """Проверка обратной связи через related_name."""
        sad1 = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 11, 1)
        )
        sad2 = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 10, 1)
        )

        assert intern.sad_periods.count() == 2
        assert sad1 in intern.sad_periods.all()
        assert sad2 in intern.sad_periods.all()

    def test_sad_intern_db_table(self):
        """Проверка имени таблицы в БД."""
        assert SadIntern._meta.db_table == 'sad_interns'

    def test_sad_intern_verbose_names(self, sad_intern):
        """Проверка verbose_name для полей."""
        assert SadIntern._meta.get_field('intern').verbose_name == 'Студент'
        assert SadIntern._meta.get_field('date_added').verbose_name == 'Дата добавления в список грустящих'
        assert SadIntern._meta.get_field('waiting_since').verbose_name == 'Ждет с'
        assert SadIntern._meta.get_field('days_waiting').verbose_name == 'Дней с нами'
        assert SadIntern._meta.get_field('telegram_username').verbose_name == '@tg'
        assert SadIntern._meta.get_field('manager_email').verbose_name == 'Email менеджера'
        assert SadIntern._meta.get_field('status').verbose_name == 'Статус'
        assert SadIntern._meta.get_field('note').verbose_name == 'Примечание'

    def test_sad_intern_days_waiting_not_editable(self):
        """Проверка, что days_waiting не редактируемое."""
        field = SadIntern._meta.get_field('days_waiting')
        assert field.editable is False
