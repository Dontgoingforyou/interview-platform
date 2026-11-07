"""
Тесты для REST API приложения developers.

Покрывают эндпоинт:
- GET /api/developers/ — список разработчиков со статистикой собеседований

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.api      - для группировки API-тестов
"""
import pytest
from datetime import date, timedelta

from django.urls import reverse

from directions.models import Direction
from tests.helpers import get_api_results
from interns.models import Intern
from interviews.models import Interview
from offers.models import Offer


# ---------------------------------------------------------------------------
# Тесты GET /api/developers/ — аутентификация и права доступа
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDeveloperStatsAPIAuth:
    """Тесты аутентификации и прав доступа к GET /api/developers/."""

    URL = 'api-developer-stats'

    def test_unauthenticated_returns_403(self, api_client):
        """Неаутентифицированный запрос получает 403."""
        response = api_client.get(reverse(self.URL))
        assert response.status_code in (401, 403)

    def test_admin_can_access(self, api_client, api_admin_user):
        """Администратор имеет доступ к эндпоинту."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 200

    def test_manager_can_access(self, api_client, api_manager_user):
        """Менеджер имеет доступ к эндпоинту."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 200

    def test_cv_manager_can_access(self, api_client, cv_api_manager_user):
        """CV-менеджер имеет доступ (входит в IsManagerOrAdmin)."""
        api_client.force_authenticate(user=cv_api_manager_user)
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 200

    def test_user_without_groups_gets_403(self, api_client, api_anon_user):
        """Пользователь без групп получает 403."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 403

    def test_response_content_type_is_json(self, api_client, api_admin_user):
        """Ответ возвращается в формате JSON."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))
        assert 'application/json' in response['Content-Type']

    @pytest.mark.parametrize('method', ['post', 'put', 'delete'])
    def test_disallowed_methods_return_405(self, api_client, api_admin_user, method):
        """Методы POST, PUT, DELETE не поддерживаются."""
        api_client.force_authenticate(user=api_admin_user)
        response = getattr(api_client, method)(reverse(self.URL), {})
        assert response.status_code == 405


# ---------------------------------------------------------------------------
# Тесты GET /api/developers/ — структура ответа и данные
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDeveloperStatsAPIResponse:
    """Тесты структуры ответа GET /api/developers/."""

    URL = 'api-developer-stats'

    def test_empty_list_when_no_data(self, api_client, api_admin_user):
        """Пустой список при отсутствии офферов и собеседований."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        assert response.status_code == 200
        assert get_api_results(response) == []
        assert response.data.get('count') == 0

    def test_response_fields_for_intern_with_offer(
        self, api_client, api_admin_user, intern, direction, offer
    ):
        """Ответ содержит ожидаемые поля для студента с оффером."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1

        item = results[0]
        expected_fields = {
            'intern_id', 'intern_name', 'direction_id', 'direction_name',
            'interview_count', 'first_interview_date', 'last_interview_date',
            'id', 'full_name', 'email',
        }
        assert expected_fields.issubset(set(item.keys()))

    def test_intern_with_offer_appears_in_list(
        self, api_client, api_admin_user, intern, direction, offer
    ):
        """Студент с оффером отображается в ответе."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        assert response.status_code == 200
        intern_ids = [item['intern_id'] for item in get_api_results(response)]
        assert intern.id in intern_ids

    def test_intern_with_non_cancelled_interview_appears_in_list(
        self, api_client, api_admin_user, intern, direction
    ):
        """Студент с не отменённым интервью (без оффера) отображается в списке."""
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            date=date.today(),
        )

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        assert response.status_code == 200
        intern_ids = [item['intern_id'] for item in get_api_results(response)]
        assert intern.id in intern_ids

    def test_intern_with_only_cancelled_interview_excluded(
        self, api_client, api_admin_user, intern, direction
    ):
        """Студент только с отменёнными интервью не отображается."""
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='cancelled',
            date=date.today(),
        )

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        assert response.status_code == 200
        intern_ids = [item['intern_id'] for item in get_api_results(response)]
        assert intern.id not in intern_ids

    def test_intern_without_offer_and_interviews_excluded(
        self, api_client, api_admin_user, intern, direction
    ):
        """Студент без офферов и интервью не отображается."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        assert response.status_code == 200
        intern_ids = [item['intern_id'] for item in get_api_results(response)]
        assert intern.id not in intern_ids

    def test_paginated_response_shape(self, api_client, api_admin_user, intern, direction, offer):
        """Ответ пагинирован: count, results, next, previous."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 200
        assert 'count' in response.data
        assert 'results' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert response.data['count'] >= 1


# ---------------------------------------------------------------------------
# Тесты GET /api/developers/ — данные статистики
# ---------------------------------------------------------------------------

def _get_item_for_intern(data, intern_id, direction_id=None):
    """Находит запись для указанного студента (и опционально направления)."""
    for item in data:
        if item['intern_id'] == intern_id:
            if direction_id is None or item['direction_id'] == direction_id:
                return item
    return None


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDeveloperStatsAPIData:
    """Тесты корректности данных статистики GET /api/developers/."""

    URL = 'api-developer-stats'

    def test_interview_count_zero_without_interviews(
        self, api_client, api_admin_user, intern, direction, offer
    ):
        """Количество интервью = 0, если интервью нет."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = _get_item_for_intern(get_api_results(response), intern.id)
        assert item is not None
        assert item['interview_count'] == 0
        assert item['first_interview_date'] is None
        assert item['last_interview_date'] is None

    def test_interview_count_correct_with_interviews(
        self, api_client, api_admin_user, intern, direction, offer, manager
    ):
        """Количество интервью подсчитывается корректно."""
        today = date.today()
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=10),
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='tech',
            date=today - timedelta(days=5),
        )

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = _get_item_for_intern(get_api_results(response), intern.id)
        assert item is not None
        assert item['interview_count'] == 2

    def test_first_and_last_interview_dates_correct(
        self, api_client, api_admin_user, intern, direction, offer, manager
    ):
        """Первая и последняя даты интервью корректны."""
        today = date.today()
        first_date = today - timedelta(days=10)
        last_date = today - timedelta(days=2)

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=first_date,
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='final',
            date=last_date,
        )

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = _get_item_for_intern(get_api_results(response), intern.id)
        assert item is not None
        assert item['first_interview_date'] == str(first_date)
        assert item['last_interview_date'] == str(last_date)

    def test_cancelled_interviews_excluded_from_count(
        self, api_client, api_admin_user, intern, direction, offer, manager
    ):
        """Отменённые интервью не учитываются в счётчике."""
        today = date.today()
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=10),
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='cancelled',
            date=today - timedelta(days=5),
        )

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = _get_item_for_intern(get_api_results(response), intern.id)
        assert item is not None
        assert item['interview_count'] == 1

    def test_cancelled_interviews_excluded_from_dates(
        self, api_client, api_admin_user, intern, direction, offer, manager
    ):
        """Даты отменённых интервью не влияют на first/last_interview_date."""
        today = date.today()
        normal_date = today - timedelta(days=10)
        cancelled_date = today - timedelta(days=2)

        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=normal_date,
        )
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='cancelled',
            date=cancelled_date,
        )

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = _get_item_for_intern(get_api_results(response), intern.id)
        assert item is not None
        assert item['last_interview_date'] == str(normal_date)

    def test_multiple_interns_all_returned(
        self, api_client, api_admin_user, intern, intern_other, direction, offer, offer_other
    ):
        """Несколько студентов — все отображаются."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        intern_ids = [item['intern_id'] for item in get_api_results(response)]
        assert intern.id in intern_ids
        assert intern_other.id in intern_ids

    def test_intern_with_multiple_directions_appears_multiple_times(
        self, api_client, api_admin_user, intern, direction
    ):
        """Студент с офферами по разным направлениям появляется несколько раз."""
        direction2 = Direction.objects.create(id=2, name='Frontend')

        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=150000,
            month=11,
            year=2025,
        )
        Offer.objects.create(
            intern=intern,
            direction=direction2,
            company='Yandex',
            amount=140000,
            month=11,
            year=2025,
        )

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        items_for_intern = [i for i in get_api_results(response) if i['intern_id'] == intern.id]
        assert len(items_for_intern) == 2

        direction_ids = {i['direction_id'] for i in items_for_intern}
        assert direction.id in direction_ids
        assert direction2.id in direction_ids

    def test_result_sorted_by_intern_name(
        self, api_client, api_admin_user, direction
    ):
        """Результат отсортирован по имени студента (алфавитно)."""
        intern_a = Intern.objects.create(
            full_name='Алексей Алексеев',
            manager_email='manager@example.com',
            direction=direction,
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
        )
        intern_b = Intern.objects.create(
            full_name='Борис Борисов',
            manager_email='manager@example.com',
            direction=direction,
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
        )

        Offer.objects.create(intern=intern_a, direction=direction, company='A', amount=100000, month=11, year=2025)
        Offer.objects.create(intern=intern_b, direction=direction, company='B', amount=100000, month=11, year=2025)

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(
            reverse(self.URL),
            {'order_by': 'full_name', 'order_dir': 'asc'},
        )

        names = [item['intern_name'] for item in get_api_results(response)]
        assert names == sorted(names)

    def test_interview_count_only_for_correct_direction(
        self, api_client, api_admin_user, intern, direction
    ):
        """Интервью по другому направлению не учитываются в счётчике."""
        direction2 = Direction.objects.create(id=2, name='Frontend')
        today = date.today()

        # Оффер по направлению 1
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=150000,
            month=11,
            year=2025,
        )
        # Интервью по направлению 1
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            date=today - timedelta(days=5),
        )
        # Интервью по направлению 2 (не должно учитываться для пары intern+direction1)
        Interview.objects.create(
            intern=intern,
            direction=direction2,
            manager_email='manager@example.com',
            interview_type='tech',
            date=today - timedelta(days=3),
        )

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = next(
            (
                i
                for i in get_api_results(response)
                if i['intern_id'] == intern.id and i['direction_id'] == direction.id
            ),
            None,
        )
        assert item is not None
        assert item['interview_count'] == 1


# ---------------------------------------------------------------------------
# Тесты GET /api/developers/ — фильтрация
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDeveloperStatsAPIFilters:
    """Тесты фильтров GET /api/developers/?direction_id=&q=."""

    URL = 'api-developer-stats'

    def test_filter_by_direction_id(
        self, api_client, api_admin_user, intern, direction
    ):
        """Фильтр по direction_id возвращает только записи с этим направлением."""
        direction2 = Direction.objects.create(id=2, name='Frontend')

        Offer.objects.create(intern=intern, direction=direction, company='A', amount=100000, month=11, year=2025)
        Offer.objects.create(intern=intern, direction=direction2, company='B', amount=100000, month=11, year=2025)

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL), {'direction_id': direction.id})

        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        assert results[0]['direction_id'] == direction.id

    def test_filter_by_direction_id_no_results(
        self, api_client, api_admin_user, intern, direction, offer
    ):
        """Фильтр по несуществующему direction_id возвращает пустой список."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL), {'direction_id': 9999})

        assert response.status_code == 200
        assert get_api_results(response) == []

    def test_filter_by_invalid_direction_id_ignored(
        self, api_client, api_admin_user, offer
    ):
        """Невалидный direction_id (строка) игнорируется — возвращаются все данные."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL), {'direction_id': 'invalid'})

        assert response.status_code == 200
        assert len(get_api_results(response)) == 1

    def test_filter_by_search_query(
        self, api_client, api_admin_user, intern, intern_other, direction, offer, offer_other
    ):
        """Фильтр по ФИО (q) возвращает только совпадающих студентов."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL), {'q': 'Иван'})

        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        assert 'иван' in results[0]['intern_name'].lower()

    def test_filter_by_search_query_case_insensitive(
        self, api_client, api_admin_user, intern, direction, offer
    ):
        """Поиск регистронезависим."""
        api_client.force_authenticate(user=api_admin_user)

        response_lower = api_client.get(reverse(self.URL), {'q': 'иван'})
        response_upper = api_client.get(reverse(self.URL), {'q': 'ИВАН'})

        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert len(get_api_results(response_lower)) == len(get_api_results(response_upper))

    def test_filter_by_search_no_results(
        self, api_client, api_admin_user, offer
    ):
        """Поиск с несуществующим именем возвращает пустой список."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL), {'q': 'НесуществующееИмя12345'})

        assert response.status_code == 200
        assert get_api_results(response) == []

    def test_combined_filters_direction_and_search(
        self, api_client, api_admin_user, intern, intern_other, direction
    ):
        """Комбинация фильтров direction_id и q работает корректно."""
        direction2 = Direction.objects.create(id=2, name='Frontend')

        Offer.objects.create(intern=intern, direction=direction, company='A', amount=100000, month=11, year=2025)
        Offer.objects.create(intern=intern_other, direction=direction2, company='B', amount=100000, month=11, year=2025)

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(
            reverse(self.URL),
            {'direction_id': direction.id, 'q': 'Иван'},
        )

        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1
        assert results[0]['intern_id'] == intern.id
        assert results[0]['direction_id'] == direction.id

    def test_filter_direction_id_includes_interviews_from_that_direction(
        self, api_client, api_admin_user, intern, direction
    ):
        """Фильтр по direction_id включает студентов с интервью (без оффера) по этому направлению."""
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            date=date.today(),
        )

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL), {'direction_id': direction.id})

        assert response.status_code == 200
        assert any(i['intern_id'] == intern.id for i in get_api_results(response))

    def test_empty_search_query_returns_all(
        self, api_client, api_admin_user, intern, intern_other, direction, offer, offer_other
    ):
        """Пустой параметр q возвращает всех студентов."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL), {'q': ''})

        assert response.status_code == 200
        intern_ids = [i['intern_id'] for i in get_api_results(response)]
        assert intern.id in intern_ids
        assert intern_other.id in intern_ids

    def test_filter_direction_alias_same_as_direction_id(
        self, api_client, api_admin_user, intern, direction
    ):
        """Параметр direction — синоним direction_id."""
        direction2 = Direction.objects.create(id=2, name='Frontend')
        Offer.objects.create(intern=intern, direction=direction, company='A', amount=100000, month=11, year=2025)
        Offer.objects.create(intern=intern, direction=direction2, company='B', amount=100000, month=11, year=2025)
        api_client.force_authenticate(user=api_admin_user)
        r1 = api_client.get(reverse(self.URL), {'direction_id': direction.id})
        r2 = api_client.get(reverse(self.URL), {'direction': direction.id})
        assert get_api_results(r1) == get_api_results(r2)


# ---------------------------------------------------------------------------
# Тесты GET /api/developers/ — сериализатор DeveloperStatSerializer
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDeveloperStatSerializer:
    """Тесты сериализации полей DeveloperStatSerializer."""

    URL = 'api-developer-stats'

    def test_intern_id_is_integer(
        self, api_client, api_admin_user, intern, direction, offer
    ):
        """intern_id совпадает с id студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = get_api_results(response)[0]
        assert item['intern_id'] == intern.id

    def test_intern_name_is_string(
        self, api_client, api_admin_user, intern, direction, offer
    ):
        """intern_name совпадает с именем студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = get_api_results(response)[0]
        assert item['intern_name'] == intern.full_name

    def test_direction_id_is_integer(
        self, api_client, api_admin_user, intern, direction, offer
    ):
        """direction_id совпадает с direction студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = get_api_results(response)[0]
        assert item['direction_id'] == direction.id

    def test_interview_count_is_non_negative_integer(
        self, api_client, api_admin_user, intern, direction, offer
    ):
        """interview_count равен 0 при отсутствии собеседований."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = get_api_results(response)[0]
        assert item['interview_count'] == 0

    def test_dates_are_null_when_no_interviews(
        self, api_client, api_admin_user, intern, direction, offer
    ):
        """Даты null при отсутствии интервью."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = get_api_results(response)[0]
        assert item['first_interview_date'] is None
        assert item['last_interview_date'] is None

    def test_dates_are_strings_when_interviews_present(
        self, api_client, api_admin_user, intern, direction, offer, manager
    ):
        """Даты возвращаются в формате строки YYYY-MM-DD при наличии интервью."""
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date(2025, 6, 15),
        )

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse(self.URL))

        item = next(i for i in get_api_results(response) if i['intern_id'] == intern.id)
        assert item['first_interview_date'] == '2025-06-15'
        assert item['last_interview_date'] == '2025-06-15'


# ---------------------------------------------------------------------------
# Экспорт Excel (DRF API)
# ---------------------------------------------------------------------------

_XLSX_CT = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestDeveloperExportAPI:
    """Тесты GET /api/developers/export/*."""

    @pytest.mark.parametrize(
        'url_name',
        [
            'api-developers-export-table',
            'api-developers-export-metrics',
            'api-developers-export-chart',
        ],
    )
    def test_export_unauthenticated(self, api_client, url_name):
        response = api_client.get(reverse(url_name))
        assert response.status_code in (401, 403)

    @pytest.mark.parametrize(
        'url_name',
        [
            'api-developers-export-table',
            'api-developers-export-metrics',
            'api-developers-export-chart',
        ],
    )
    def test_export_forbidden_without_role(self, api_client, api_anon_user, url_name):
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get(reverse(url_name))
        assert response.status_code == 403

    def test_export_table_manager_xlsx(self, api_client, api_manager_user, offer):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(reverse('api-developers-export-table'))
        assert response.status_code == 200
        assert _XLSX_CT in response['Content-Type']
        assert len(response.content) > 0

    def test_export_metrics_admin_xlsx(self, api_client, api_admin_user, offer):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse('api-developers-export-metrics'))
        assert response.status_code == 200
        assert _XLSX_CT in response['Content-Type']

    def test_export_chart_admin_xlsx(self, api_client, api_admin_user, offer):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(reverse('api-developers-export-chart'))
        assert response.status_code == 200
        assert _XLSX_CT in response['Content-Type']
