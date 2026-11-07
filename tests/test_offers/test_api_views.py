"""
Тесты для API-эндпоинтов приложения offers (offers.api.views.OfferViewSet).

Покрывают:
- OfferViewSet GET    /api/offers/        — список офферов (менеджер / администратор)
- OfferViewSet GET    /api/offers/{id}/   — детали оффера
- OfferViewSet POST   /api/offers/        — создание (только admin)
- OfferViewSet PATCH  /api/offers/{id}/   — частичное обновление (только admin)
- OfferViewSet DELETE /api/offers/{id}/   — удаление (только admin)

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.api       - для группировки API-тестов
"""
import pytest
from decimal import Decimal

from offers.models import Offer
from tests.helpers import get_api_results


# ============================================================================
# Аутентификация и права доступа
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestOfferViewSetAuth:
    """Тесты аутентификации и прав доступа к /api/offers/."""

    def test_unauthenticated_list_returns_401_or_403(self, api_client):
        """Неаутентифицированный запрос к списку получает 401/403."""
        response = api_client.get('/api/offers/')
        assert response.status_code in (401, 403)

    def test_unauthenticated_retrieve_returns_401_or_403(self, api_client, offer):
        """Неаутентифицированный запрос к деталям получает 401/403."""
        response = api_client.get(f'/api/offers/{offer.id}/')
        assert response.status_code in (401, 403)

    def test_unauthenticated_create_returns_401_or_403(self, api_client, intern, direction):
        """Неаутентифицированный POST получает 401/403."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'company': 'Test',
            'amount': '100000.00',
            'month': 1,
            'year': 2025,
        }
        response = api_client.post('/api/offers/', data, format='json')
        assert response.status_code in (401, 403)

    def test_unauthenticated_patch_returns_401_or_403(self, api_client, offer):
        """Неаутентифицированный PATCH получает 401/403."""
        response = api_client.patch(f'/api/offers/{offer.id}/', {'company': 'New'}, format='json')
        assert response.status_code in (401, 403)

    def test_unauthenticated_delete_returns_401_or_403(self, api_client, offer):
        """Неаутентифицированный DELETE получает 401/403."""
        response = api_client.delete(f'/api/offers/{offer.id}/')
        assert response.status_code in (401, 403)

    def test_manager_can_access_list(self, api_client, api_manager_user):
        """Менеджер может получить список офферов."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/offers/')
        assert response.status_code == 200

    def test_admin_can_access_list(self, api_client, api_admin_user):
        """Администратор может получить список офферов."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/')
        assert response.status_code == 200

    def test_user_without_groups_cannot_access_list(self, api_client, api_anon_user):
        """Пользователь без групп получает 403."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get('/api/offers/')
        assert response.status_code == 403

    def test_manager_cannot_create_offer(self, api_client, api_manager_user, intern, direction):
        """Обычный менеджер не может создать оффер."""
        api_client.force_authenticate(user=api_manager_user)
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'company': 'Test',
            'amount': '100000.00',
            'month': 3,
            'year': 2025,
        }
        response = api_client.post('/api/offers/', data, format='json')
        assert response.status_code == 403

    def test_manager_cannot_patch_offer(self, api_client, api_manager_user, offer):
        """Обычный менеджер не может обновить оффер."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(f'/api/offers/{offer.id}/', {'company': 'New'}, format='json')
        assert response.status_code == 403

    def test_manager_delete_returns_403(self, api_client, api_manager_user, offer):
        """Менеджер не может удалить оффер — 403."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.delete(f'/api/offers/{offer.id}/')
        assert response.status_code == 403
        assert Offer.objects.filter(id=offer.id).exists()

    def test_response_content_type_is_json(self, api_client, api_manager_user):
        """Ответ возвращается в формате JSON."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/offers/')
        assert 'application/json' in response['Content-Type']


# ============================================================================
# GET /api/offers/ — список офферов
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestOfferViewSetList:
    """Тесты GET /api/offers/ — список офферов."""

    def test_admin_sees_all_offers(self, api_client, api_admin_user, offer, offer_other):
        """Администратор видит все офферы."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert offer.id in ids
        assert offer_other.id in ids

    def test_manager_sees_only_own_offers(self, api_client, api_manager_user, offer, offer_other):
        """Менеджер видит только офферы своих студентов."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/offers/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert offer.id in ids
        assert offer_other.id not in ids

    def test_manager2_sees_only_own_offers(self, api_client, api_manager2_user, offer, offer_other):
        """Второй менеджер видит только свои офферы."""
        api_client.force_authenticate(user=api_manager2_user)
        response = api_client.get('/api/offers/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert offer_other.id in ids
        assert offer.id not in ids

    def test_empty_list_when_no_offers(self, api_client, api_admin_user):
        """Пустой список при отсутствии офферов."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert results == []

    def test_list_response_has_required_fields(self, api_client, api_admin_user, offer):
        """Ответ содержит все обязательные поля OfferListSerializer."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/')
        results = get_api_results(response)
        assert len(results) >= 1
        item = results[0]
        expected_fields = {
            'id', 'intern', 'intern_name', 'intern_telegram_username',
            'direction_id', 'direction_name', 'company', 'amount', 'month', 'year', 'created_at',
        }
        assert expected_fields.issubset(set(item.keys()))

    def test_list_response_has_no_updated_at(self, api_client, api_admin_user, offer):
        """В списочном ответе нет поля updated_at (только в detail)."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/')
        results = get_api_results(response)
        assert 'updated_at' not in results[0]

    def test_list_intern_name_is_correct(self, api_client, api_admin_user, offer):
        """Поле intern_name отображает ФИО студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/')
        results = get_api_results(response)
        item = next(r for r in results if r['id'] == offer.id)
        assert item['intern_name'] == offer.intern.full_name

    def test_filter_by_intern_id(self, api_client, api_admin_user, offer, offer_other):
        """Фильтр intern_id возвращает только офферы данного студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/', {'intern_id': offer.intern.id})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert offer.id in ids
        assert offer_other.id not in ids

    def test_filter_by_direction_id(self, api_client, api_admin_user, offer, direction):
        """Фильтр direction_id возвращает офферы по направлению."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/', {'direction_id': direction.id})
        assert response.status_code == 200
        results = get_api_results(response)
        assert any(r['id'] == offer.id for r in results)

    def test_filter_by_year(self, api_client, api_admin_user, offer, intern, direction):
        """Фильтр year возвращает только офферы за указанный год."""
        other_year_offer = Offer.objects.create(
            intern=intern, direction=direction,
            company='VK', amount=Decimal('100000.00'), month=6, year=2024,
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/', {'year': 2025})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert offer.id in ids
        assert other_year_offer.id not in ids

    def test_filter_by_month(self, api_client, api_admin_user, offer, offer_other):
        """Фильтр month возвращает только офферы за указанный месяц."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/', {'month': 1})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert offer.id in ids
        assert offer_other.id not in ids

    def test_filter_by_year_and_month(self, api_client, api_admin_user, intern, direction):
        """Одновременный фильтр по году и месяцу."""
        target = Offer.objects.create(
            intern=intern, direction=direction,
            company='Target', amount=Decimal('100000.00'), month=3, year=2024,
        )
        other = Offer.objects.create(
            intern=intern, direction=direction,
            company='Other', amount=Decimal('110000.00'), month=3, year=2025,
        )
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/', {'year': 2024, 'month': 3})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [r['id'] for r in results]
        assert target.id in ids
        assert other.id not in ids

    @pytest.mark.parametrize('param, value', [
        ('intern_id', 'not-a-number'),
        ('direction_id', 'abc'),
        ('year', 'bad'),
        ('month', 'bad'),
    ])
    def test_invalid_filter_does_not_break_list(self, api_client, api_admin_user, offer, param, value):
        """Невалидный query-параметр фильтра не ломает список."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/', {param: value})
        assert response.status_code == 200

    def test_unknown_query_param_does_not_break_list(self, api_client, api_admin_user, offer):
        """Неизвестные query-параметры не ломают список."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/', {'foo': 'bar'})
        assert response.status_code == 200

    def test_amount_field_value_is_correct(self, api_client, api_admin_user, offer):
        """Поле amount в ответе соответствует сохранённому значению."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/')
        results = get_api_results(response)
        item = next(r for r in results if r['id'] == offer.id)
        assert Decimal(item['amount']) == Decimal('150000.00')


# ============================================================================
# GET /api/offers/{id}/ — детали оффера
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestOfferViewSetRetrieve:
    """Тесты GET /api/offers/{id}/ — детали оффера."""

    def test_admin_can_retrieve_any_offer(self, api_client, api_admin_user, offer):
        """Администратор может получить детали любого оффера."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/offers/{offer.id}/')
        assert response.status_code == 200
        assert response.data['id'] == offer.id

    def test_admin_can_retrieve_other_manager_offer(self, api_client, api_admin_user, offer_other):
        """Администратор видит оффер, принадлежащий другому менеджеру."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/offers/{offer_other.id}/')
        assert response.status_code == 200

    def test_manager_can_retrieve_own_offer(self, api_client, api_manager_user, offer):
        """Менеджер может получить детали своего оффера."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/offers/{offer.id}/')
        assert response.status_code == 200
        assert response.data['id'] == offer.id

    def test_manager_cannot_retrieve_other_offer(self, api_client, api_manager_user, offer_other):
        """Менеджер не может получить оффер чужого студента (404 — не в queryset)."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/offers/{offer_other.id}/')
        assert response.status_code == 404

    def test_retrieve_nonexistent_returns_404(self, api_client, api_admin_user):
        """Запрос несуществующего оффера возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/99999/')
        assert response.status_code == 404

    def test_retrieve_response_has_all_detail_fields(self, api_client, api_admin_user, offer):
        """Ответ детального эндпоинта содержит все поля OfferDetailSerializer."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/offers/{offer.id}/')
        assert response.status_code == 200
        expected_fields = {
            'id', 'intern', 'intern_name', 'direction_id',
            'company', 'amount', 'month', 'year', 'created_at', 'updated_at',
        }
        assert expected_fields.issubset(set(response.data.keys()))

    def test_retrieve_includes_updated_at(self, api_client, api_admin_user, offer):
        """Детальный ответ включает поле updated_at."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/offers/{offer.id}/')
        assert 'updated_at' in response.data
        assert response.data['updated_at'] is not None

    def test_retrieve_correct_data(self, api_client, api_admin_user, offer):
        """Данные в ответе соответствуют данным оффера в БД."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/offers/{offer.id}/')
        assert response.status_code == 200
        assert response.data['company'] == offer.company
        assert response.data['month'] == offer.month
        assert response.data['year'] == offer.year
        assert response.data['direction_id'] == offer.direction_id

    def test_retrieve_intern_name_is_correct(self, api_client, api_admin_user, offer):
        """Поле intern_name в деталях отображает ФИО студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/offers/{offer.id}/')
        assert response.data['intern_name'] == offer.intern.full_name


# ============================================================================
# POST /api/offers/ — создание оффера
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestOfferViewSetCreate:
    """Тесты POST /api/offers/ — создание оффера."""

    def _valid_payload(self, intern, direction):
        return {
            'intern': intern.id,
            'direction_id': direction.id,
            'company': 'VK',
            'amount': '130000.00',
            'month': 3,
            'year': 2025,
        }

    def test_admin_can_create_offer(self, api_client, api_admin_user, intern, direction):
        """Администратор может создать оффер."""
        api_client.force_authenticate(user=api_admin_user)
        data = self._valid_payload(intern, direction)
        response = api_client.post('/api/offers/', data, format='json')
        assert response.status_code == 201
        assert Offer.objects.filter(company='VK').exists()

    def test_create_returns_201(self, api_client, api_admin_user, intern, direction):
        """POST с корректными данными возвращает 201."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post('/api/offers/', self._valid_payload(intern, direction), format='json')
        assert response.status_code == 201

    def test_create_saves_all_fields(self, api_client, api_admin_user, intern, direction):
        """Созданный оффер содержит переданные данные."""
        api_client.force_authenticate(user=api_admin_user)
        api_client.post('/api/offers/', self._valid_payload(intern, direction), format='json')
        offer = Offer.objects.get(company='VK')
        assert offer.intern == intern
        assert offer.direction_id == direction.id
        assert offer.amount == Decimal('130000.00')
        assert offer.month == 3
        assert offer.year == 2025

    def test_manager_cannot_create(self, api_client, api_manager_user, intern, direction):
        """Обычный менеджер не может создать оффер — 403."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post('/api/offers/', self._valid_payload(intern, direction), format='json')
        assert response.status_code == 403

    def test_create_without_company_is_allowed(self, api_client, api_admin_user, intern, direction):
        """Создание оффера без поля company (nullable) возвращает 201."""
        api_client.force_authenticate(user=api_admin_user)
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'amount': '100000.00',
            'month': 5,
            'year': 2025,
        }
        response = api_client.post('/api/offers/', data, format='json')
        assert response.status_code == 201

    def test_create_without_amount_is_allowed(self, api_client, api_admin_user, intern, direction):
        """Создание оффера без суммы (nullable) возвращает 201."""
        api_client.force_authenticate(user=api_admin_user)
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'company': 'Test',
            'month': 6,
            'year': 2025,
        }
        response = api_client.post('/api/offers/', data, format='json')
        assert response.status_code == 201

    def test_create_without_intern_returns_400(self, api_client, api_admin_user, direction):
        """Создание без обязательного поля intern возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        data = {
            'direction_id': direction.id,
            'company': 'Test',
            'amount': '100000.00',
            'month': 1,
            'year': 2025,
        }
        response = api_client.post('/api/offers/', data, format='json')
        assert response.status_code == 400

    def test_create_without_month_returns_400(self, api_client, api_admin_user, intern, direction):
        """Создание без обязательного поля month возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'company': 'Test',
            'amount': '100000.00',
            'year': 2025,
        }
        response = api_client.post('/api/offers/', data, format='json')
        assert response.status_code == 400

    def test_create_without_year_returns_400(self, api_client, api_admin_user, intern, direction):
        """Создание без обязательного поля year возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'company': 'Test',
            'amount': '100000.00',
            'month': 1,
        }
        response = api_client.post('/api/offers/', data, format='json')
        assert response.status_code == 400

    def test_create_with_nonexistent_intern_returns_400(self, api_client, api_admin_user, direction):
        """Создание с несуществующим intern_id возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        data = {
            'intern': 99999,
            'direction_id': direction.id,
            'company': 'Test',
            'amount': '100000.00',
            'month': 1,
            'year': 2025,
        }
        response = api_client.post('/api/offers/', data, format='json')
        assert response.status_code == 400

    def test_create_response_contains_id(self, api_client, api_admin_user, intern, direction):
        """Ответ на создание содержит поля intern и direction_id."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post('/api/offers/', self._valid_payload(intern, direction), format='json')
        assert response.status_code == 201
        assert 'intern' in response.data
        assert 'direction_id' in response.data


# ============================================================================
# PATCH /api/offers/{id}/ — частичное обновление оффера
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestOfferViewSetPartialUpdate:
    """Тесты PATCH /api/offers/{id}/ — частичное обновление оффера."""

    def test_admin_can_patch_offer(self, api_client, api_admin_user, offer):
        """Администратор может обновить оффер."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/offers/{offer.id}/', {'company': 'Updated Company'}, format='json',
        )
        assert response.status_code == 200
        offer.refresh_from_db()
        assert offer.company == 'Updated Company'

    def test_admin_can_patch_amount(self, api_client, api_admin_user, offer):
        """Администратор может обновить сумму оффера."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/offers/{offer.id}/', {'amount': '200000.00'}, format='json',
        )
        assert response.status_code == 200
        offer.refresh_from_db()
        assert offer.amount == Decimal('200000.00')

    def test_admin_can_patch_month_and_year(self, api_client, api_admin_user, offer):
        """Администратор может обновить месяц и год оффера."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/offers/{offer.id}/', {'month': 6, 'year': 2026}, format='json',
        )
        assert response.status_code == 200
        offer.refresh_from_db()
        assert offer.month == 6
        assert offer.year == 2026

    def test_manager_cannot_patch_offer(self, api_client, api_manager_user, offer):
        """Обычный менеджер не может обновить оффер — 403."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/offers/{offer.id}/', {'company': 'Hacked'}, format='json',
        )
        assert response.status_code == 403

    def test_patch_nonexistent_offer_returns_404(self, api_client, api_admin_user):
        """PATCH несуществующего оффера возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            '/api/offers/99999/', {'company': 'Test'}, format='json',
        )
        assert response.status_code == 404

    def test_partial_patch_does_not_reset_other_fields(self, api_client, api_admin_user, offer):
        """PATCH обновляет только переданное поле, остальные сохраняются."""
        original_amount = offer.amount
        api_client.force_authenticate(user=api_admin_user)
        api_client.patch(f'/api/offers/{offer.id}/', {'company': 'Only Company'}, format='json')
        offer.refresh_from_db()
        assert offer.amount == original_amount

    def test_patch_response_reflects_new_data(self, api_client, api_admin_user, offer):
        """Ответ на PATCH отражает обновлённые данные."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/offers/{offer.id}/', {'company': 'Reflected'}, format='json',
        )
        assert response.status_code == 200
        assert response.data['company'] == 'Reflected'

    def test_patch_with_invalid_month_returns_400(self, api_client, api_admin_user, offer):
        """PATCH с невалидным месяцем (0 или 13) возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/offers/{offer.id}/', {'month': 0}, format='json',
        )
        assert response.status_code == 400


# ============================================================================
# DELETE /api/offers/{id}/ — удаление оффера
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestOfferViewSetDelete:
    """Тесты DELETE /api/offers/{id}/ — только администратор."""

    def test_admin_delete_returns_204(self, api_client, api_admin_user, offer):
        """Администратор удаляет оффер — 204, запись исчезает из БД."""
        offer_id = offer.id
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/offers/{offer_id}/')
        assert response.status_code == 204
        assert not Offer.objects.filter(id=offer_id).exists()

    def test_manager_delete_returns_403(self, api_client, api_manager_user, offer):
        """Менеджер при DELETE получает 403."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.delete(f'/api/offers/{offer.id}/')
        assert response.status_code == 403
        assert Offer.objects.filter(id=offer.id).exists()

    def test_delete_nonexistent_offer_returns_404(self, api_client, api_admin_user):
        """DELETE несуществующего оффера возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete('/api/offers/99999/')
        assert response.status_code == 404

    def test_admin_can_delete_any_offer(self, api_client, api_admin_user, offer_other):
        """Администратор может удалить оффер другого менеджера."""
        offer_id = offer_other.id
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/offers/{offer_id}/')
        assert response.status_code == 204
        assert not Offer.objects.filter(id=offer_id).exists()


# ============================================================================
# GET /api/offers/month-groups/
# ============================================================================


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestOfferViewSetMonthGroups:
    """Тесты GET /api/offers/month-groups/ — группы по месяцам."""

    def test_requires_auth(self, api_client):
        """Без авторизации — 401/403."""
        response = api_client.get('/api/offers/month-groups/')
        assert response.status_code in (401, 403)

    def test_admin_returns_shape(self, api_client, api_admin_user, offer):
        """Ответ содержит groups, offset, limit, has_more."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/month-groups/')
        assert response.status_code == 200
        data = response.json()
        assert 'groups' in data
        assert isinstance(data['groups'], list)
        assert data['offset'] == 0
        assert data['limit'] == 3
        assert 'has_more' in data
        assert 'next_offset' in data

    def test_group_contains_year_month_count(self, api_client, api_admin_user, offer):
        """Элемент группы: year, month, total_count."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/offers/month-groups/')
        assert response.status_code == 200
        groups = response.json()['groups']
        assert len(groups) >= 1
        g0 = groups[0]
        assert g0['year'] == offer.year
        assert g0['month'] == offer.month
        assert g0['total_count'] >= 1


# ============================================================================
# GET /api/analytics/offers/
# ============================================================================


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestOfferAnalyticsDrf:
    """Тесты DRF-аналитики офферов."""

    def test_requires_auth(self, api_client):
        response = api_client.get('/api/analytics/offers/')
        assert response.status_code in (401, 403)

    def test_admin_returns_total(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/analytics/offers/')
        assert response.status_code == 200
        data = response.json()
        assert 'total' in data
        assert 'tooltips' in data
