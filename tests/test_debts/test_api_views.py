import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from debts.models import Debt, PaymentHistory
from tests.helpers import make_keycloak_user, get_api_results


# ---------------------------------------------------------------------------
# Тесты GET /api/debts/ (list)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDebtListEndpoint:
    """Тесты для GET /api/debts/."""

    def test_unauthenticated_returns_403(self, api_client):
        """Неаутентифицированный запрос получает 403."""
        url = reverse('debt-list')
        response = api_client.get(url)
        assert response.status_code in (401, 403)

    def test_admin_sees_all_debts(self, api_client, api_admin_user, debt, debt_other):
        """Администратор видит все долги."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-list')
        response = api_client.get(url)

        assert response.status_code == 200
        ids = [item['id'] for item in get_api_results(response)]
        assert debt.pk in ids
        assert debt_other.pk in ids

    def test_manager_sees_only_own_debts(self, api_client, api_manager_user, debt, debt_other):
        """Менеджер видит только долги своих студентов."""
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('debt-list')
        response = api_client.get(url)

        assert response.status_code == 200
        ids = [item['id'] for item in get_api_results(response)]
        assert debt.pk in ids
        assert debt_other.pk not in ids

    def test_manager_other_sees_own_debts(self, api_client, api_manager2_user, debt, debt_other):
        """Второй менеджер видит только долги своих студентов."""
        api_client.force_authenticate(user=api_manager2_user)
        url = reverse('debt-list')
        response = api_client.get(url)

        assert response.status_code == 200
        ids = [item['id'] for item in get_api_results(response)]
        assert debt_other.pk in ids
        assert debt.pk not in ids

    def test_filter_by_payment_status(self, api_client, api_admin_user, debt, debt_other):
        """Фильтрация по payment_status."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-list')

        response = api_client.get(url, {'payment_status': 'paying'})
        assert response.status_code == 200
        ids = [item['id'] for item in get_api_results(response)]
        assert debt.pk in ids
        assert debt_other.pk not in ids

    def test_filter_by_intern_id(self, api_client, api_admin_user, debt, debt_other):
        """Фильтрация по intern_id."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-list')

        response = api_client.get(url, {'intern_id': debt.intern.pk})
        assert response.status_code == 200
        ids = [item['id'] for item in get_api_results(response)]
        assert debt.pk in ids
        assert debt_other.pk not in ids

    def test_filter_by_invalid_intern_id_ignored(self, api_client, api_admin_user, debt):
        """Невалидный intern_id не вызывает ошибку (игнорируется)."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-list')

        response = api_client.get(url, {'intern_id': 'not-a-number'})
        assert response.status_code == 200

    def test_response_contains_expected_fields(self, api_client, api_admin_user, debt):
        """Проверка наличия ожидаемых полей в ответе."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-list')
        response = api_client.get(url)

        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        item = results[0]
        expected_fields = {
            'id',
            'intern',
            'intern_name',
            'direction_id',
            'display_telegram',
            'display_email',
            'total_amount',
            'paid_amount',
            'balance',
            'payment_status',
            'act_date',
            'last_payment_month',
            'last_payment_year',
            'payments_four_months',
            'row_highlight',
        }
        assert expected_fields.issubset(set(item.keys()))

    def test_list_includes_last_four_month_labels(self, api_client, api_admin_user, debt):
        """Пагинированный ответ содержит подписи последних 4 месяцев для колонок."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse('debt-list'))
        assert response.status_code == 200
        assert 'last_four_month_labels' in response.data
        assert len(response.data['last_four_month_labels']) == 4

    def test_search_q_filters_by_intern_name(self, api_client, api_admin_user, debt, debt_other):
        """Параметр q / search фильтрует по ФИО студента."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-list')
        r = api_client.get(url, {'q': debt.intern.full_name})
        assert r.status_code == 200
        ids = [item['id'] for item in get_api_results(r)]
        assert debt.pk in ids

    def test_manager_with_no_debts_gets_empty_list(self, api_client):
        """Менеджер без студентов с долгами получает пустой список."""
        lonely_manager = make_keycloak_user(
            groups=['employment-managers'],
            email='lonely@example.com',
        )
        api_client.force_authenticate(user=lonely_manager)
        url = reverse('debt-list')
        response = api_client.get(url)

        assert response.status_code == 200
        results = response.data.get('results', response.data)
        assert list(results) == []


# ---------------------------------------------------------------------------
# Тесты GET /api/debts/{id}/ (retrieve)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDebtRetrieveEndpoint:
    """Тесты для GET /api/debts/{id}/."""

    def test_admin_can_retrieve_any_debt(self, api_client, api_admin_user, debt):
        """Администратор может получить любой долг."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['id'] == debt.pk

    def test_manager_can_retrieve_own_debt(self, api_client, api_manager_user, debt):
        """Менеджер может получить детали своего долга."""
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data['id'] == debt.pk

    def test_manager_cannot_retrieve_other_debt(self, api_client, api_manager_user, debt_other):
        """Менеджер не может получить чужой долг."""
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('debt-detail', args=[debt_other.pk])
        response = api_client.get(url)

        assert response.status_code == 404

    def test_retrieve_includes_payment_history(self, api_client, api_admin_user, debt, payment):
        """Детальное представление включает историю платежей."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.get(url)

        assert response.status_code == 200
        assert 'payment_history' in response.data
        assert len(response.data['payment_history']) == 1
        assert response.data['payment_history'][0]['month'] == 1
        assert response.data['payment_history'][0]['year'] == 2025

    def test_retrieve_returns_all_detail_fields(self, api_client, api_admin_user, debt):
        """Детальный ответ содержит все ожидаемые поля."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.get(url)

        expected_fields = {
            'id', 'intern', 'intern_name', 'direction_id',
            'telegram_username', 'email',
            'total_amount', 'paid_amount', 'balance',
            'payment_status', 'act_date',
            'payment_history',
        }
        assert expected_fields.issubset(set(response.data.keys()))

    def test_retrieve_nonexistent_returns_404(self, api_client, api_admin_user):
        """Несуществующий долг возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[99999])
        response = api_client.get(url)

        assert response.status_code == 404

    def test_unauthenticated_retrieve_returns_403(self, api_client, debt):
        """Неаутентифицированный запрос получает 403."""
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.get(url)
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Тесты POST /api/debts/ (create)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDebtCreateEndpoint:
    """Тесты для POST /api/debts/."""

    def test_admin_can_create_debt(self, api_client, api_admin_user, intern, direction):
        """Администратор может создать долг."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-list')
        data = {
            'intern': intern.pk,
            'direction_id': direction.id,
            'paid_amount': '2000.00',
            'payment_status': 'paying',
            'telegram_username': '@created_by_api',
            'email': 'api@example.com',
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == 201
        assert Debt.objects.filter(intern=intern, telegram_username='@created_by_api').exists()

    def test_manager_cannot_create_debt(self, api_client, api_manager_user, intern):
        """Менеджер не может создать долг (403)."""
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('debt-list')
        data = {
            'intern': intern.pk,
            'paid_amount': '1000.00',
            'payment_status': 'paying',
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == 403

    def test_unauthenticated_cannot_create(self, api_client, intern):
        """Неаутентифицированный запрос получает 403."""
        url = reverse('debt-list')
        data = {'intern': intern.pk, 'paid_amount': '1000.00'}
        response = api_client.post(url, data, format='json')
        assert response.status_code in (401, 403)

    def test_create_with_missing_intern_returns_400(self, api_client, api_admin_user):
        """Создание без intern возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-list')
        response = api_client.post(url, {}, format='json')

        assert response.status_code == 400
        assert 'intern' in response.data

    def test_create_with_invalid_payment_status_returns_400(self, api_client, api_admin_user, intern):
        """Создание с невалидным payment_status возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-list')
        data = {'intern': intern.pk, 'payment_status': 'invalid_status'}
        response = api_client.post(url, data, format='json')

        assert response.status_code == 400

    def test_create_with_invalid_email_returns_400(self, api_client, api_admin_user, intern):
        """Создание с невалидным email возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-list')
        data = {'intern': intern.pk, 'email': 'not-an-email'}
        response = api_client.post(url, data, format='json')

        assert response.status_code == 400

    def test_create_minimal_data_succeeds(self, api_client, api_admin_user, intern):
        """Создание с минимальным набором полей (только intern)."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-list')
        data = {'intern': intern.pk}
        response = api_client.post(url, data, format='json')

        assert response.status_code == 201


# ---------------------------------------------------------------------------
# Тесты PATCH /api/debts/{id}/ (partial_update)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDebtPartialUpdateEndpoint:
    """Тесты для PATCH /api/debts/{id}/."""

    def test_admin_can_partially_update_debt(self, api_client, api_admin_user, debt):
        """Администратор может частично обновить долг."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.patch(url, {'telegram_username': '@updated'}, format='json')

        assert response.status_code == 200
        debt.refresh_from_db()
        assert debt.telegram_username == '@updated'

    def test_admin_can_update_paid_amount(self, api_client, api_admin_user, debt):
        """Администратор может изменить paid_amount."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.patch(url, {'paid_amount': '8000.00'}, format='json')

        assert response.status_code == 200
        debt.refresh_from_db()
        assert debt.paid_amount == Decimal('8000.00')

    def test_manager_cannot_update_debt(self, api_client, api_manager_user, debt):
        """Менеджер не может обновить долг (403)."""
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.patch(url, {'telegram_username': '@hacked'}, format='json')

        assert response.status_code == 403

    def test_unauthenticated_cannot_update(self, api_client, debt):
        """Неаутентифицированный запрос получает 403."""
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.patch(url, {'telegram_username': '@hacked'}, format='json')
        assert response.status_code in (401, 403)

    def test_update_nonexistent_returns_404(self, api_client, api_admin_user):
        """Обновление несуществующего долга возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[99999])
        response = api_client.patch(url, {'telegram_username': '@nobody'}, format='json')

        assert response.status_code == 404

    def test_update_with_invalid_payment_status_returns_400(self, api_client, api_admin_user, debt):
        """Обновление с невалидным payment_status возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.patch(url, {'payment_status': 'bad_status'}, format='json')

        assert response.status_code == 400

    def test_update_with_invalid_email_returns_400(self, api_client, api_admin_user, debt):
        """Обновление с невалидным email возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.patch(url, {'email': 'not-email'}, format='json')

        assert response.status_code == 400

    @pytest.mark.parametrize('status', ['searching', 'paying', 'unknown'])
    def test_update_payment_status_choices(self, api_client, api_admin_user, debt, status):
        """Проверка всех допустимых значений payment_status."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.patch(url, {'payment_status': status}, format='json')
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Тесты DELETE /api/debts/{id}/ — только администратор
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDebtDestroyEndpoint:
    """Тесты для DELETE /api/debts/{id}/."""

    def test_admin_delete_returns_204(self, api_client, api_admin_user, debt):
        """Администратор удаляет долг — 204."""
        debt_pk = debt.pk
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[debt_pk])
        response = api_client.delete(url)

        assert response.status_code == 204
        assert not Debt.objects.filter(pk=debt_pk).exists()

    def test_manager_delete_returns_403(self, api_client, api_manager_user, debt):
        """Менеджер не может удалить долг."""
        debt_pk = debt.pk
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('debt-detail', args=[debt_pk])
        response = api_client.delete(url)

        assert response.status_code == 403
        assert Debt.objects.filter(pk=debt_pk).exists()

    def test_unauthenticated_cannot_delete(self, api_client, debt):
        """Неаутентифицированный запрос не может удалить долг."""
        url = reverse('debt-detail', args=[debt.pk])
        response = api_client.delete(url)
        assert response.status_code in (401, 403)

    def test_delete_nonexistent_returns_404(self, api_client, api_admin_user):
        """Удаление несуществующего долга возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[99999])
        response = api_client.delete(url)

        assert response.status_code == 404

    def test_admin_delete_cascades_payment_history(
        self, api_client, api_admin_user, debt, payment
    ):
        """После DELETE долга удаляются связанные платежи (CASCADE)."""
        payment_pk = payment.pk
        debt_pk = debt.pk

        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-detail', args=[debt_pk])
        response = api_client.delete(url)

        assert response.status_code == 204
        assert not Debt.objects.filter(pk=debt_pk).exists()
        assert not PaymentHistory.objects.filter(pk=payment_pk).exists()


# ---------------------------------------------------------------------------
# Тесты POST /api/debts/{id}/add-payment/ (add_payment)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDebtAddPaymentEndpoint:
    """Тесты для POST /api/debts/{id}/add-payment/."""

    def test_admin_can_add_payment(self, api_client, api_admin_user, debt):
        """Администратор может добавить запись о платеже."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-add-payment', args=[debt.pk])
        data = {'month': 3, 'year': 2025, 'amount': '2000.00'}
        response = api_client.post(url, data, format='json')

        assert response.status_code == 201
        assert response.data['message'] == 'Платёж успешно добавлен.'
        assert PaymentHistory.objects.filter(debt=debt, month=3, year=2025).exists()

    def test_manager_cannot_add_payment(self, api_client, api_manager_user, debt):
        """Менеджер не может добавить платёж (403)."""
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('debt-add-payment', args=[debt.pk])
        data = {'month': 3, 'year': 2025, 'amount': '2000.00'}
        response = api_client.post(url, data, format='json')

        assert response.status_code == 403

    def test_unauthenticated_cannot_add_payment(self, api_client, debt):
        """Неаутентифицированный запрос получает 403."""
        url = reverse('debt-add-payment', args=[debt.pk])
        response = api_client.post(url, {'month': 1, 'year': 2025, 'amount': '1000.00'}, format='json')
        assert response.status_code in (401, 403)

    def test_add_payment_missing_month_returns_400(self, api_client, api_admin_user, debt):
        """Добавление платежа без month возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-add-payment', args=[debt.pk])
        response = api_client.post(url, {'year': 2025, 'amount': '1000.00'}, format='json')

        assert response.status_code == 400
        assert 'month' in response.data

    def test_add_payment_missing_year_returns_400(self, api_client, api_admin_user, debt):
        """Добавление платежа без year возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-add-payment', args=[debt.pk])
        response = api_client.post(url, {'month': 1, 'amount': '1000.00'}, format='json')

        assert response.status_code == 400
        assert 'year' in response.data

    def test_add_payment_missing_amount_returns_400(self, api_client, api_admin_user, debt):
        """Добавление платежа без amount возвращает 400."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-add-payment', args=[debt.pk])
        response = api_client.post(url, {'month': 1, 'year': 2025}, format='json')

        assert response.status_code == 400
        assert 'amount' in response.data

    def test_add_duplicate_payment_raises_integrity_error(self, api_client, api_admin_user, debt, payment):
        """Добавление дублирующего платежа нарушает unique_together (month+year+debt).

        Текущее поведение API: IntegrityError не перехватывается на уровне view,
        поэтому возвращается 400 или 500 в зависимости от конфигурации.
        Фиксируем, что запрос НЕ возвращает 2xx.
        """
        from django.db import IntegrityError
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-add-payment', args=[debt.pk])
        # payment уже создан для month=1, year=2025
        data = {'month': 1, 'year': 2025, 'amount': '500.00'}

        with pytest.raises(IntegrityError, match=r'UNIQUE constraint'):
            api_client.post(url, data, format='json')

    def test_add_payment_to_nonexistent_debt_returns_404(self, api_client, api_admin_user):
        """Добавление платежа к несуществующему долгу возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-add-payment', args=[99999])
        response = api_client.post(url, {'month': 1, 'year': 2025, 'amount': '1000.00'}, format='json')

        assert response.status_code == 404

    def test_add_multiple_payments_different_months(self, api_client, api_admin_user, debt):
        """Добавление платежей за разные месяцы работает корректно."""
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('debt-add-payment', args=[debt.pk])

        r1 = api_client.post(url, {'month': 1, 'year': 2025, 'amount': '1000.00'}, format='json')
        r2 = api_client.post(url, {'month': 2, 'year': 2025, 'amount': '1000.00'}, format='json')
        r3 = api_client.post(url, {'month': 3, 'year': 2025, 'amount': '1000.00'}, format='json')

        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r3.status_code == 201
        assert PaymentHistory.objects.filter(debt=debt).count() == 3

    def test_add_payment_updates_payment_history(self, api_client, api_admin_user, debt):
        """После добавления платёж доступен в детальном представлении долга."""
        api_client.force_authenticate(user=api_admin_user)

        add_url = reverse('debt-add-payment', args=[debt.pk])
        api_client.post(add_url, {'month': 5, 'year': 2025, 'amount': '3000.00'}, format='json')

        detail_url = reverse('debt-detail', args=[debt.pk])
        response = api_client.get(detail_url)
        assert response.status_code == 200
        months = [p['month'] for p in response.data['payment_history']]
        assert 5 in months


# ---------------------------------------------------------------------------
# GET /api/analytics/debts/ (DRF, Bearer)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDebtAnalyticsAPIDRF:
    """Аналитика долгов для React SPA."""

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get('/api/analytics/debts/')
        assert response.status_code == 401

    def test_manager_bearer_ok(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/analytics/debts/')
        assert response.status_code == 200
        assert 'total' in response.data
        assert 'tooltips' in response.data


# ---------------------------------------------------------------------------
# GET /api/debts/by-month/
# ---------------------------------------------------------------------------


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDebtByMonthEndpoint:
    """Отчёт по месяцам."""

    def test_missing_period_returns_400(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse('debt-by-month'))
        assert response.status_code == 400
        assert 'detail' in response.data

    def test_end_before_start_returns_400(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(
            reverse('debt-by-month'),
            {
                'month_from': 6,
                'year_from': 2025,
                'month_to': 1,
                'year_to': 2025,
            },
        )
        assert response.status_code == 400

    def test_valid_range_with_payment_returns_200(self, api_client, api_admin_user, debt, payment):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(
            reverse('debt-by-month'),
            {
                'month_from': 1,
                'year_from': 2025,
                'month_to': 1,
                'year_to': 2025,
            },
        )
        assert response.status_code == 200
        assert response.data['selected_period'] == '01/2025 - 01/2025'
        assert '01/25' in response.data['export_months']
        results = get_api_results(response)
        assert len(results) >= 1
        row = next(r for r in results if r['id'] == debt.pk)
        assert 'period_amounts' in row
        assert 'total_period_amount' in row


# ---------------------------------------------------------------------------
# POST /api/debts/import/
# ---------------------------------------------------------------------------


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDebtImportAPI:
    """Асинхронный импорт долгов (только admin)."""

    def test_unauthenticated_returns_401_or_403(self, api_client):
        url = reverse('api_debt_import')
        response = api_client.post(url, {})
        assert response.status_code in (401, 403)

    def test_manager_forbidden(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('api_debt_import')
        response = api_client.post(url, {})
        assert response.status_code == 403

    def test_admin_no_file_returns_400(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('api_debt_import')
        response = api_client.post(url, {})
        assert response.status_code == 400

    @patch('debts.api.import_views.async_import_from_file.delay')
    def test_admin_upload_returns_task_id(self, mock_delay, api_client, api_admin_user):
        mock_task = MagicMock()
        mock_task.id = 'celery-task-debts-import'
        mock_delay.return_value = mock_task
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('api_debt_import')
        upload = SimpleUploadedFile(
            'debts.xlsx',
            b'x',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response = api_client.post(url, {'file': upload}, format='multipart')
        assert response.status_code == 200
        assert response.data['status'] == 'started'
        assert response.data['task_id'] == 'celery-task-debts-import'
        mock_delay.assert_called_once()
