"""
Тесты для вспомогательных функций приложения managers (managers/utils.py).

Покрывают:
- get_inactive_intern_ids(): корректное определение неактивных интернов
"""
import pytest

from core.constants import INTERN_STATUS_LEFT, INTERN_STATUS_OFFER
from managers.utils import get_inactive_intern_ids
from offers.models import Offer


@pytest.mark.django_db(databases=['default'])
class TestGetInactiveInternIds:
    """Тесты функции get_inactive_intern_ids."""

    def test_returns_empty_set_when_no_interns(self):
        """Пустое множество при отсутствии интернов и офферов."""
        result = get_inactive_intern_ids()
        assert result == set()

    def test_includes_intern_with_offer(self, intern, direction):
        """Интерн с оффером включается в множество неактивных."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Test Company',
            month=12,
            year=2025
        )
        result = get_inactive_intern_ids()
        assert intern.id in result

    @pytest.mark.parametrize('status', [INTERN_STATUS_LEFT, INTERN_STATUS_OFFER])
    def test_includes_intern_with_inactive_manual_status(self, intern, status):
        """Интерн со статусом INTERN_STATUS_LEFT или INTERN_STATUS_OFFER включается в множество неактивных."""
        intern.manual_status = status
        intern.save()
        result = get_inactive_intern_ids()
        assert intern.id in result

    def test_excludes_active_intern_without_offer(self, intern):
        """Активный интерн без оффера не попадает в неактивные."""
        result = get_inactive_intern_ids()
        assert intern.id not in result

    def test_excludes_intern_with_other_manual_status(self, intern):
        """Интерн с другим manual_status не считается неактивным."""
        intern.manual_status = 'в работе'
        intern.save()
        result = get_inactive_intern_ids()
        assert intern.id not in result

    def test_includes_intern_with_both_offer_and_status(self, intern, direction):
        """Интерн и с оффером, и со статусом учитывается один раз (set)."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Test Company',
            month=12,
            year=2025
        )
        intern.manual_status = INTERN_STATUS_OFFER
        intern.save()
        result = get_inactive_intern_ids()
        assert intern.id in result
        # Множество — дубликатов нет по природе set
        assert len([x for x in result if x == intern.id]) == 1

    def test_multiple_interns_partial_inactive(self, intern, intern_other, direction):
        """Только неактивные интерны попадают в множество при наличии нескольких."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Test Company',
            month=12,
            year=2025
        )
        result = get_inactive_intern_ids()
        assert intern.id in result
        assert intern_other.id not in result

    def test_multiple_interns_all_inactive(self, intern, intern_other, direction):
        """Все интерны неактивны — все попадают в множество."""
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Test Company',
            month=12,
            year=2025
        )
        intern_other.manual_status = INTERN_STATUS_LEFT
        intern_other.save()
        result = get_inactive_intern_ids()
        assert intern.id in result
        assert intern_other.id in result
