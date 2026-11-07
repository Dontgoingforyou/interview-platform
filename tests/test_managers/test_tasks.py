"""
Тесты для Celery-задачи managers.tasks.delete_stale_hidden_managers.

Покрывают:
- Удаление скрытых менеджеров, скрытых более 3 месяцев назад
- Сохранение менеджеров при различных условиях (недавно скрыт, активен, без hidden_at)
- Корректный возврат количества удалённых записей
- Удаление нескольких устаревших менеджеров за один вызов
- Разделение: удаляет устаревших, оставляет недавних
"""
import pytest
from datetime import timedelta

from django.utils import timezone

from managers.models import Manager
from managers.tasks import delete_stale_hidden_managers, HIDDEN_MANAGER_TTL_DAYS


def make_manager(db, email, is_active=True, hidden_at=None, **kwargs):
    """Фабрика Manager для тестов."""
    defaults = dict(
        full_name=f'Менеджер {email}',
        username=email.split('@')[0],
        groups=['employment-managers'],
        is_active=is_active,
        hidden_at=hidden_at,
    )
    defaults.update(kwargs)
    return Manager.objects.create(email=email, **defaults)


@pytest.mark.django_db
class TestDeleteStaleHiddenManagers:
    """Тесты задачи удаления устаревших скрытых менеджеров."""

    def test_deletes_manager_hidden_over_3_months_ago(self, db):
        """Менеджер, скрытый более 90 дней назад, должен быть удалён."""
        hidden_at = timezone.now() - timedelta(days=HIDDEN_MANAGER_TTL_DAYS + 1)
        make_manager(db, 'stale@example.com', is_active=False, hidden_at=hidden_at)

        result = delete_stale_hidden_managers()

        assert result == 1
        assert not Manager.objects.filter(email='stale@example.com').exists()

    @pytest.mark.parametrize('is_active,hidden_ago,email', [
        # скрыт менее 90 дней назад — ещё не истёк срок
        (False, timedelta(days=HIDDEN_MANAGER_TTL_DAYS - 1), 'fresh@example.com'),
        # активен, но поле hidden_at устаревшее — is_active=True защищает от удаления
        (True, timedelta(days=HIDDEN_MANAGER_TTL_DAYS + 10), 'active@example.com'),
        # скрыт без даты — hidden_at=NULL, условие __lt не срабатывает
        (False, None, 'no-date@example.com'),
        # скрыт за час до порога (89д 23ч) — ещё не истёк
        (False, timedelta(days=HIDDEN_MANAGER_TTL_DAYS) - timedelta(hours=1), 'almost@example.com'),
    ], ids=['недавно-скрыт', 'активен', 'без-даты', 'за-час-до-порога'])
    def test_manager_is_not_deleted(self, db, is_active, hidden_ago, email):
        """Менеджер не удаляется при различных условиях, не попадающих под порог."""
        hidden_at = (timezone.now() - hidden_ago) if hidden_ago is not None else None
        make_manager(db, email, is_active=is_active, hidden_at=hidden_at)

        result = delete_stale_hidden_managers()

        assert result == 0
        assert Manager.objects.filter(email=email).exists()

    def test_deletes_only_stale_leaves_fresh(self, db):
        """Удаляет только устаревших, оставляет недавно скрытых."""
        stale_at = timezone.now() - timedelta(days=HIDDEN_MANAGER_TTL_DAYS + 5)
        fresh_at = timezone.now() - timedelta(days=HIDDEN_MANAGER_TTL_DAYS - 5)

        make_manager(db, 'stale@example.com', is_active=False, hidden_at=stale_at)
        make_manager(db, 'fresh@example.com', is_active=False, hidden_at=fresh_at)

        result = delete_stale_hidden_managers()

        assert result == 1
        assert not Manager.objects.filter(email='stale@example.com').exists()
        assert Manager.objects.filter(email='fresh@example.com').exists()

    def test_returns_zero_when_nothing_to_delete(self, db):
        """При отсутствии кандидатов на удаление возвращает 0."""
        make_manager(db, 'normal@example.com', is_active=True)

        result = delete_stale_hidden_managers()

        assert result == 0

    def test_deletes_multiple_stale_managers(self, db):
        """Удаляет несколько устаревших менеджеров за один вызов."""
        stale_at = timezone.now() - timedelta(days=HIDDEN_MANAGER_TTL_DAYS + 1)
        make_manager(db, 'stale0@example.com', is_active=False, hidden_at=stale_at)
        make_manager(db, 'stale1@example.com', is_active=False, hidden_at=stale_at)
        make_manager(db, 'stale2@example.com', is_active=False, hidden_at=stale_at)

        result = delete_stale_hidden_managers()

        assert result == 3
        assert Manager.objects.filter(is_active=False).count() == 0
