"""
Тесты для модели Offer.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.models - для группировки тестов моделей
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from offers.models import Offer


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestOfferModel:
    """Тесты для модели Offer."""

    def test_offer_creation(self, intern, direction):
        """Проверка создания оффера."""
        offer = Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Yandex',
            amount=Decimal('120000.00'),
            month=2,
            year=2025
        )
        assert offer.pk is not None
        assert offer.intern == intern
        assert offer.direction_id == direction.id
        assert offer.company == 'Yandex'
        assert offer.amount == Decimal('120000.00')
        assert offer.month == 2
        assert offer.year == 2025

    def test_offer_str_representation(self, offer):
        """Проверка строкового представления оффера."""
        expected = f'{offer.intern.full_name} - {offer.company} ({offer.amount})'
        assert str(offer) == expected

    def test_offer_direction_property(self, offer, direction):
        """Проверка свойства direction."""
        assert offer.direction is not None
        assert offer.direction.id == direction.id
        assert offer.direction.name == direction.name

    def test_offer_direction_fk_access(self, offer, direction):
        """Проверка FK-доступа к направлению через offer.direction."""
        assert offer.direction_id == direction.id
        assert offer.direction.name == direction.name

    def test_offer_ordering(self, intern, direction):
        """Проверка сортировки офферов."""
        offer1 = Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=Decimal('100000.00'),
            month=1,
            year=2024
        )
        offer2 = Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Yandex',
            amount=Decimal('120000.00'),
            month=12,
            year=2025
        )
        offer3 = Offer.objects.create(
            intern=intern,
            direction=direction,
            company='VK',
            amount=Decimal('110000.00'),
            month=6,
            year=2025
        )

        offers = list(Offer.objects.all())
        # Сортировка: -year, -month, -created_at
        assert offers[0] == offer2  # 2025/12
        assert offers[1] == offer3  # 2025/6
        assert offers[2] == offer1  # 2024/1

    def test_offer_without_company(self, intern, direction):
        """Проверка создания оффера без компании (nullable)."""
        offer = Offer.objects.create(
            intern=intern,
            direction=direction,
            company=None,
            amount=Decimal('100000.00'),
            month=3,
            year=2025
        )
        assert offer.company is None

    def test_offer_without_amount(self, intern, direction):
        """Проверка создания оффера без суммы (nullable)."""
        offer = Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Test',
            amount=None,
            month=4,
            year=2025
        )
        assert offer.amount is None

    def test_offer_month_validation_min(self, intern, direction):
        """Проверка валидации минимального месяца."""
        offer = Offer(
            intern=intern,
            direction=direction,
            company='Test',
            amount=Decimal('100000.00'),
            month=0,  # Невалидный месяц
            year=2025
        )
        with pytest.raises(ValidationError):
            offer.full_clean()

    def test_offer_month_validation_max(self, intern, direction):
        """Проверка валидации максимального месяца."""
        offer = Offer(
            intern=intern,
            direction=direction,
            company='Test',
            amount=Decimal('100000.00'),
            month=13,  # Невалидный месяц
            year=2025
        )
        with pytest.raises(ValidationError):
            offer.full_clean()

    @pytest.mark.parametrize('month', list(range(1, 13)))
    def test_offer_month_validation_valid(self, intern, direction, month):
        """Проверка валидации валидных месяцев."""
        offer = Offer(
            intern=intern,
            direction=direction,
            company='Test',
            amount=Decimal('100000.00'),
            month=month,
            year=2025,
        )
        offer.full_clean()

    def test_offer_created_at_auto_now_add(self, offer):
        """Проверка автоматического заполнения created_at."""
        assert offer.created_at is not None

    def test_offer_updated_at_auto_now(self, offer):
        """Проверка автоматического обновления updated_at."""
        old_updated_at = offer.updated_at
        offer.amount = Decimal('200000.00')
        offer.save()
        assert offer.updated_at > old_updated_at

    def test_offer_cascade_delete_with_intern(self, intern, direction):
        """Проверка каскадного удаления оффера при удалении студента."""
        offer = Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Test',
            amount=Decimal('100000.00'),
            month=5,
            year=2025
        )
        offer_id = offer.id
        intern.delete()
        assert not Offer.objects.filter(id=offer_id).exists()

    def test_offer_verbose_names(self):
        """Проверка verbose_name полей."""
        assert Offer._meta.get_field('intern').verbose_name == 'Студент'
        assert Offer._meta.get_field('direction').verbose_name == 'Направление'
        assert Offer._meta.get_field('company').verbose_name == 'Компания'
        assert Offer._meta.get_field('amount').verbose_name == 'Сумма в оффере'
        assert Offer._meta.get_field('month').verbose_name == 'Месяц'
        assert Offer._meta.get_field('year').verbose_name == 'Год'

    def test_offer_meta_db_table(self):
        """Проверка имени таблицы в БД."""
        assert Offer._meta.db_table == 'offers'

    def test_offer_meta_verbose_name(self):
        """Проверка verbose_name модели."""
        assert Offer._meta.verbose_name == 'Оффер'
        assert Offer._meta.verbose_name_plural == 'Офферы'

    def test_offer_amount_decimal_places(self, intern, direction):
        """Проверка точности десятичного поля amount."""
        offer = Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Test',
            amount=Decimal('123456.78'),
            month=6,
            year=2025
        )
        assert offer.amount == Decimal('123456.78')

    def test_offer_direction_id_index(self):
        """Проверка наличия индекса на direction_id."""
        field = Offer._meta.get_field('direction_id')
        assert field.db_index is True

    def test_offer_month_index(self):
        """Проверка наличия индекса на month."""
        field = Offer._meta.get_field('month')
        assert field.db_index is True

    def test_offer_year_index(self):
        """Проверка наличия индекса на year."""
        field = Offer._meta.get_field('year')
        assert field.db_index is True
