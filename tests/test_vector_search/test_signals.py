"""
Тесты для сигналов приложения vector_search.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.signals - для группировки тестов сигналов
"""
import pytest
from unittest.mock import patch
from datetime import date, time, timedelta

from companies.models import Company
from interviews.models import Interview
from interns.models import Intern
from offers.models import Offer
from debts.models import Debt
from sad_intern.models import SadIntern
from managers.models import Manager


@pytest.mark.django_db(databases=['default'])
@pytest.mark.signals
class TestInterviewSignals:
    """Тесты для сигналов Interview."""

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_interview_post_save_triggers_update(self, mock_task, intern, direction):
        """Проверка что сохранение интервью запускает обновление эмбеддинга."""
        interview = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            date=date(2025, 12, 1),
            time=time(10, 0)
        )

        mock_task.assert_called_once_with('interview', interview.id)

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_interview_update_triggers_update(self, mock_task, interview):
        """Проверка что изменение интервью запускает обновление эмбеддинга."""
        mock_task.reset_mock()  # Сброс предыдущих вызовов

        interview.interview_type = 'screening'
        interview.save()

        # Должен был быть вызван для обновления
        assert mock_task.called
        assert mock_task.call_args[0] == ('interview', interview.id)

    @patch('vector_search.tasks.delete_embedding_task.delay')
    def test_interview_post_delete_triggers_deletion(self, mock_task, interview):
        """Проверка что удаление интервью запускает удаление эмбеддинга."""
        interview_id = interview.id
        interview.delete()

        mock_task.assert_called_once_with('interview', interview_id)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.signals
class TestInternSignals:
    """Тесты для сигналов Intern."""

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_intern_post_save_triggers_update(self, mock_task, direction):
        """Проверка что сохранение студента запускает обновление эмбеддинга."""
        intern = Intern.objects.create(
            full_name='Test Student',
            email='test@example.com',
            manager_email='manager@example.com',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )

        mock_task.assert_called_once_with('intern', intern.id)

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_intern_update_triggers_update(self, mock_task, intern):
        """Проверка что изменение студента запускает обновление эмбеддинга."""
        mock_task.reset_mock()

        intern.email = 'newemail@example.com'
        intern.save()

        assert mock_task.called
        assert mock_task.call_args[0] == ('intern', intern.id)

    @patch('vector_search.tasks.delete_embedding_task.delay')
    def test_intern_post_delete_triggers_deletion(self, mock_task, intern):
        """Проверка что удаление студента запускает удаление эмбеддинга."""
        intern_id = intern.id
        intern.delete()

        mock_task.assert_called_once_with('intern', intern_id)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.signals
class TestOfferSignals:
    """Тесты для сигналов Offer."""

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_offer_post_save_triggers_update(self, mock_task, intern, direction):
        """Проверка что сохранение оффера запускает обновление эмбеддинга."""
        offer = Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Test Company',
            amount=100000,
            month=12,
            year=2025
        )

        mock_task.assert_called_once_with('offer', offer.id)

    @patch('vector_search.tasks.delete_embedding_task.delay')
    def test_offer_post_delete_triggers_deletion(self, mock_task, intern, direction):
        """Проверка что удаление оффера запускает удаление эмбеддинга."""
        offer = Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Test Company',
            amount=100000,
            month=12,
            year=2025
        )

        offer_id = offer.id
        offer.delete()

        mock_task.assert_called_with('offer', offer_id)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.signals
class TestDebtSignals:
    """Тесты для сигналов Debt."""

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_debt_post_save_triggers_update(self, mock_task, intern, direction):
        """Проверка что сохранение долга запускает обновление эмбеддинга."""
        debt = Debt.objects.create(
            intern=intern,
            direction=direction,
            email=intern.email,
            total_amount=50000,
            paid_amount=0,
            balance=50000
        )

        mock_task.assert_called_once_with('debt', debt.id)

    @patch('vector_search.tasks.delete_embedding_task.delay')
    def test_debt_post_delete_triggers_deletion(self, mock_task, intern, direction):
        """Проверка что удаление долга запускает удаление эмбеддинга."""
        debt = Debt.objects.create(
            intern=intern,
            direction=direction,
            email=intern.email,
            total_amount=50000,
            paid_amount=0,
            balance=50000
        )

        debt_id = debt.id
        debt.delete()

        mock_task.assert_called_with('debt', debt_id)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.signals
class TestSadInternSignals:
    """Тесты для сигналов SadIntern."""

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_sad_intern_post_save_triggers_update(self, mock_task, intern, direction):
        """Проверка что сохранение грустного студента запускает обновление эмбеддинга."""
        from datetime import date
        from django.utils import timezone

        today = timezone.now().date()
        intern.real_interview_date = today - timedelta(days=10)
        intern.save()

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            date=today - timedelta(days=5)
        )

        mock_task.reset_mock()

        sad_intern = SadIntern.objects.create(
            intern=intern,
            waiting_since=date(2025, 11, 1),
            telegram_username='@ivan_tg',
            manager_email='manager@example.com',
            status='rejected',
            note='Тестовое примечание'
        )

        mock_task.assert_called_with('sad_intern', sad_intern.id)

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_sad_intern_update_triggers_update(self, mock_task, sad_intern):
        """Проверка что изменение грустного студента запускает обновление эмбеддинга."""
        mock_task.reset_mock()

        sad_intern.status = 'accepted'
        sad_intern.save()

        assert mock_task.called
        assert mock_task.call_args[0] == ('sad_intern', sad_intern.id)

    @patch('vector_search.tasks.delete_embedding_task.delay')
    def test_sad_intern_post_delete_triggers_deletion(self, mock_task, sad_intern):
        """Проверка что удаление грустного студента запускает удаление эмбеддинга."""
        sad_intern_id = sad_intern.id
        sad_intern.delete()

        mock_task.assert_called_with('sad_intern', sad_intern_id)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.signals
class TestManagerSignals:
    """Тесты для сигналов Manager."""

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_manager_post_save_triggers_update(self, mock_task):
        """Проверка что сохранение менеджера запускает обновление эмбеддинга."""
        manager = Manager.objects.create(
            email='newmanager@example.com',
            full_name='Новый Менеджер',
            username='noviy',
            groups=['employment-managers'],
            is_active=True
        )

        mock_task.assert_called_once_with('manager', manager.email)

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_manager_update_triggers_update(self, mock_task, manager):
        """Проверка что изменение менеджера запускает обновление эмбеддинга."""
        mock_task.reset_mock()

        manager.full_name = 'Обновленное Имя'
        manager.save()

        assert mock_task.called
        assert mock_task.call_args[0] == ('manager', manager.email)

    @patch('vector_search.tasks.delete_embedding_task.delay')
    def test_manager_post_delete_triggers_deletion(self, mock_task, manager):
        """Проверка что удаление менеджера запускает удаление эмбеддинга."""
        email = manager.email
        manager.delete()

        mock_task.assert_called_once_with('manager', email)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.signals
class TestCompanySignals:
    """Тесты для сигналов Company."""

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_company_post_save_triggers_update(self, mock_task):
        """Создание компании запускает задачу векторизации."""
        company = Company.objects.create(name='Новая Компания', is_bigtech=False)

        mock_task.assert_called_once_with('company', company.id)

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_company_update_triggers_update(self, mock_task, company):
        """Изменение компании запускает задачу обновления эмбеддинга."""
        mock_task.reset_mock()

        company.is_bigtech = True
        company.save()

        assert mock_task.called
        assert mock_task.call_args[0] == ('company', company.id)

    @patch('vector_search.tasks.delete_embedding_task.delay')
    def test_company_post_delete_triggers_deletion(self, mock_task, company):
        """Удаление компании запускает задачу удаления эмбеддинга."""
        company_id = company.id
        company.delete()

        mock_task.assert_called_once_with('company', company_id)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.signals
class TestSignalsIntegration:
    """Интеграционные тесты для сигналов."""

    @patch('vector_search.tasks.update_embedding_task.delay')
    def test_multiple_creates_trigger_multiple_updates(
        self,
        mock_task,
        intern,
        direction
    ):
        """Проверка что создание нескольких сущностей вызывает несколько обновлений."""
        mock_task.reset_mock()

        # Создаём несколько интервью
        interview1 = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            date=date(2025, 12, 1)
        )

        interview2 = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='hr',
            date=date(2025, 12, 2)
        )

        # Должно быть два вызова
        assert mock_task.call_count == 2

        calls = mock_task.call_args_list
        assert calls[0][0] == ('interview', interview1.id)
        assert calls[1][0] == ('interview', interview2.id)

    @patch('vector_search.tasks.update_embedding_task.delay')
    @patch('vector_search.tasks.delete_embedding_task.delay')
    def test_create_and_delete_trigger_both_tasks(
        self,
        mock_delete,
        mock_update,
        intern,
        direction
    ):
        """Проверка что создание и удаление вызывают соответствующие задачи."""
        interview = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='tech',
            date=date(2025, 12, 1)
        )

        interview_id = interview.id
        interview.delete()

        # Должны быть вызваны обе задачи
        mock_update.assert_called_with('interview', interview_id)
        mock_delete.assert_called_with('interview', interview_id)
