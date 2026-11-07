"""
Тесты сериализаторов приложения offers.

Покрывают:
- OfferListSerializer       — поля списочного ответа, intern_name
- OfferDetailSerializer     — расширенные поля (+ updated_at)
- OfferCreateUpdateSerializer — создание и обновление оффера

Используются маркеры pytest:
- @pytest.mark.django_db   - для работы с БД
- @pytest.mark.serializers - для группировки тестов
"""
import pytest
from decimal import Decimal

from offers.models import Offer
from offers.serializers import (
    OfferListSerializer,
    OfferDetailSerializer,
    OfferCreateUpdateSerializer,
)


# ============================================================================
# OfferListSerializer
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestOfferListSerializer:
    """Тесты OfferListSerializer (GET /api/offers/)."""

    def test_serializes_all_expected_fields(self, offer):
        """Сериализатор включает все поля списочного ответа."""
        serializer = OfferListSerializer(offer)
        expected_fields = {
            'id', 'intern', 'intern_name', 'intern_telegram_username',
            'direction_id', 'direction_name',
            'company', 'amount', 'month', 'year', 'created_at',
        }
        assert expected_fields == set(serializer.data.keys())

    def test_does_not_include_updated_at(self, offer):
        """Списочный сериализатор не включает updated_at."""
        serializer = OfferListSerializer(offer)
        assert 'updated_at' not in serializer.data

    def test_id_matches_offer(self, offer):
        """Поле id соответствует первичному ключу оффера."""
        serializer = OfferListSerializer(offer)
        assert serializer.data['id'] == offer.id

    def test_intern_is_pk(self, offer):
        """Поле intern — это ID студента (PrimaryKeyRelatedField)."""
        serializer = OfferListSerializer(offer)
        assert serializer.data['intern'] == offer.intern.id

    def test_intern_name_matches_full_name(self, offer):
        """intern_name возвращает полное имя студента."""
        serializer = OfferListSerializer(offer)
        assert serializer.data['intern_name'] == offer.intern.full_name

    def test_direction_id_matches(self, offer):
        """direction_id соответствует сохранённому значению."""
        serializer = OfferListSerializer(offer)
        assert serializer.data['direction_id'] == offer.direction_id

    def test_company_matches(self, offer):
        """company соответствует сохранённому значению."""
        serializer = OfferListSerializer(offer)
        assert serializer.data['company'] == 'Google'

    def test_amount_matches(self, offer):
        """amount соответствует сохранённой сумме."""
        serializer = OfferListSerializer(offer)
        assert Decimal(serializer.data['amount']) == offer.amount

    def test_month_matches(self, offer):
        """month соответствует месяцу оффера."""
        serializer = OfferListSerializer(offer)
        assert serializer.data['month'] == 1

    def test_year_matches(self, offer):
        """year соответствует году оффера."""
        serializer = OfferListSerializer(offer)
        assert serializer.data['year'] == 2025

    def test_created_at_is_present(self, offer):
        """created_at присутствует и не None."""
        serializer = OfferListSerializer(offer)
        assert serializer.data['created_at'] is not None

    def test_company_none_serialized_correctly(self, offer_no_company):
        """Nullable company сериализуется без ошибок."""
        serializer = OfferListSerializer(offer_no_company)
        assert serializer.data['company'] is None

    def test_amount_none_serialized_correctly(self, offer_no_amount):
        """Nullable amount сериализуется без ошибок."""
        serializer = OfferListSerializer(offer_no_amount)
        assert serializer.data['amount'] is None

    def test_serializes_multiple_offers(self, intern, direction):
        """Сериализатор корректно работает со списком объектов."""
        o1 = Offer.objects.create(
            intern=intern, direction=direction,
            company='A', amount=Decimal('100000.00'), month=4, year=2025,
        )
        o2 = Offer.objects.create(
            intern=intern, direction=direction,
            company='B', amount=Decimal('200000.00'), month=5, year=2025,
        )
        serializer = OfferListSerializer([o1, o2], many=True)
        assert len(serializer.data) == 2
        companies = [item['company'] for item in serializer.data]
        assert 'A' in companies
        assert 'B' in companies

    def test_id_and_created_at_are_read_only(self, offer):
        """Поля id и created_at объявлены read_only."""
        serializer = OfferListSerializer(offer)
        assert serializer.fields['id'].read_only is True
        assert serializer.fields['created_at'].read_only is True


# ============================================================================
# OfferDetailSerializer
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestOfferDetailSerializer:
    """Тесты OfferDetailSerializer (GET /api/offers/{id}/)."""

    def test_serializes_all_expected_fields(self, offer):
        """Сериализатор включает все поля детального ответа."""
        serializer = OfferDetailSerializer(offer)
        expected_fields = {
            'id', 'intern', 'intern_name', 'intern_telegram_username',
            'direction_id', 'direction_name',
            'company', 'amount', 'month', 'year', 'created_at', 'updated_at',
        }
        assert expected_fields == set(serializer.data.keys())

    def test_includes_updated_at(self, offer):
        """Детальный сериализатор включает поле updated_at."""
        serializer = OfferDetailSerializer(offer)
        assert 'updated_at' in serializer.data
        assert serializer.data['updated_at'] is not None

    def test_id_matches(self, offer):
        """Поле id соответствует PK оффера."""
        serializer = OfferDetailSerializer(offer)
        assert serializer.data['id'] == offer.id

    def test_intern_name_matches_full_name(self, offer):
        """intern_name возвращает полное имя студента."""
        serializer = OfferDetailSerializer(offer)
        assert serializer.data['intern_name'] == offer.intern.full_name

    def test_company_matches(self, offer):
        """company соответствует сохранённому значению."""
        serializer = OfferDetailSerializer(offer)
        assert serializer.data['company'] == 'Google'

    def test_amount_matches(self, offer):
        """amount соответствует сумме в БД."""
        serializer = OfferDetailSerializer(offer)
        assert Decimal(serializer.data['amount']) == offer.amount

    def test_read_only_fields(self, offer):
        """Поля id, created_at и updated_at являются read_only."""
        serializer = OfferDetailSerializer(offer)
        assert serializer.fields['id'].read_only is True
        assert serializer.fields['created_at'].read_only is True
        assert serializer.fields['updated_at'].read_only is True

    def test_updated_at_changes_after_save(self, offer):
        """updated_at обновляется после сохранения оффера."""
        original = offer.updated_at
        offer.company = 'Changed'
        offer.save()
        offer.refresh_from_db()
        serializer = OfferDetailSerializer(offer)
        assert offer.updated_at >= original

    def test_direction_id_matches(self, offer):
        """direction_id соответствует сохранённому значению."""
        serializer = OfferDetailSerializer(offer)
        assert serializer.data['direction_id'] == offer.direction_id

    def test_nullable_company_in_detail(self, offer_no_company):
        """Детальный сериализатор корректно обрабатывает nullable company."""
        serializer = OfferDetailSerializer(offer_no_company)
        assert serializer.data['company'] is None

    def test_nullable_amount_in_detail(self, offer_no_amount):
        """Детальный сериализатор корректно обрабатывает nullable amount."""
        serializer = OfferDetailSerializer(offer_no_amount)
        assert serializer.data['amount'] is None


# ============================================================================
# OfferCreateUpdateSerializer
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestOfferCreateUpdateSerializer:
    """Тесты OfferCreateUpdateSerializer (POST/PATCH /api/offers/)."""

    def test_contains_only_writable_fields(self, offer):
        """Сериализатор содержит только поля для записи (без id, created_at, updated_at, intern_name)."""
        serializer = OfferCreateUpdateSerializer(offer)
        expected_fields = {'intern', 'direction_id', 'company', 'amount', 'month', 'year'}
        assert expected_fields == set(serializer.fields.keys())

    @pytest.mark.parametrize('field_name', ['intern_name', 'created_at', 'updated_at'])
    def test_read_only_fields_absent(self, offer, field_name):
        """Read-only поля (intern_name, created_at, updated_at) отсутствуют в сериализаторе создания/обновления."""
        serializer = OfferCreateUpdateSerializer(offer)
        assert field_name not in serializer.fields

    def test_valid_data_is_valid(self, intern, direction):
        """Валидные данные проходят валидацию."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'company': 'Test',
            'amount': '100000.00',
            'month': 4,
            'year': 2025,
        }
        serializer = OfferCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_create_saves_offer_to_db(self, intern, direction):
        """Сохранение через сериализатор создаёт запись в БД."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'company': 'SavedCo',
            'amount': '100000.00',
            'month': 4,
            'year': 2025,
        }
        serializer = OfferCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        offer = serializer.save()
        assert offer.pk is not None
        assert Offer.objects.filter(id=offer.pk).exists()

    def test_update_company_via_serializer(self, offer):
        """Частичное обновление company через сериализатор."""
        serializer = OfferCreateUpdateSerializer(offer, data={'company': 'Updated'}, partial=True)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        offer.refresh_from_db()
        assert offer.company == 'Updated'

    def test_update_amount_via_serializer(self, offer):
        """Частичное обновление amount через сериализатор."""
        serializer = OfferCreateUpdateSerializer(offer, data={'amount': '999999.99'}, partial=True)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        offer.refresh_from_db()
        assert offer.amount == Decimal('999999.99')

    def test_missing_intern_is_invalid(self, direction):
        """Отсутствие intern делает данные невалидными."""
        data = {
            'direction_id': direction.id,
            'company': 'Test',
            'amount': '100000.00',
            'month': 1,
            'year': 2025,
        }
        serializer = OfferCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'intern' in serializer.errors

    def test_missing_month_is_invalid(self, intern, direction):
        """Отсутствие month делает данные невалидными."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'company': 'Test',
            'amount': '100000.00',
            'year': 2025,
        }
        serializer = OfferCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'month' in serializer.errors

    def test_missing_year_is_invalid(self, intern, direction):
        """Отсутствие year делает данные невалидными."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'company': 'Test',
            'amount': '100000.00',
            'month': 1,
        }
        serializer = OfferCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'year' in serializer.errors

    def test_company_is_optional(self, intern, direction):
        """Поле company не является обязательным."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'amount': '100000.00',
            'month': 1,
            'year': 2025,
        }
        serializer = OfferCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_amount_is_optional(self, intern, direction):
        """Поле amount не является обязательным (nullable)."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'company': 'Test',
            'month': 1,
            'year': 2025,
        }
        serializer = OfferCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_nonexistent_intern_is_invalid(self, direction):
        """Несуществующий intern_id делает данные невалидными."""
        data = {
            'intern': 99999,
            'direction_id': direction.id,
            'company': 'Test',
            'amount': '100000.00',
            'month': 1,
            'year': 2025,
        }
        serializer = OfferCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'intern' in serializer.errors

    def test_partial_update_does_not_require_all_fields(self, offer):
        """При partial=True можно передавать одно поле."""
        serializer = OfferCreateUpdateSerializer(offer, data={'year': 2026}, partial=True)
        assert serializer.is_valid(), serializer.errors

    def test_intern_name_not_serialized_in_output(self, offer):
        """intern_name не попадает в сериализованный вывод."""
        serializer = OfferCreateUpdateSerializer(offer)
        assert 'intern_name' not in serializer.data
