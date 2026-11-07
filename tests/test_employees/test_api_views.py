"""
Тесты для API-эндпоинтов приложения employees.

Покрывают:
- SearchInternView         GET  /employees/api/search-intern/
- UpdateWeekInterviewCountView  POST /employees/api/update-week-interviews/
- SetManagerActiveView     POST /employees/api/set-manager-active/
- UpdateWeekAbsenceStatusView   POST /employees/api/update-week-absence/
- InternWeeklyStatusViewSet     /api/employees/weekly-statuses/ (DRF ViewSet)

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.api       - для группировки API-тестов
"""
import json
import pytest
from datetime import date

from django.urls import reverse
from tests.helpers import get_api_results

from employees.models import InternWeeklyStatus
from interns.models import Intern


# ============================================================================
# SearchInternView — GET /employees/api/search-intern/
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSearchInternView:
    """Тесты для SearchInternView (GET /employees/api/search-intern/)."""

    URL = 'employees_search_intern'

    # --- Аутентификация ---

    def test_unauthenticated_returns_401(self, client):
        """Неавторизованный запрос получает 401."""
        response = client.get(reverse(self.URL), {'q': 'Иван'})
        assert response.status_code == 401

    def test_authenticated_can_access(self, logged_in_manager, intern):
        """Авторизованный менеджер может делать поиск."""
        response = logged_in_manager.get(reverse(self.URL), {'q': 'Иван'})
        assert response.status_code == 200

    def test_admin_can_access(self, logged_in_admin, intern):
        """Авторизованный администратор может делать поиск."""
        response = logged_in_admin.get(reverse(self.URL), {'q': 'Иван'})
        assert response.status_code == 200

    # --- Валидация запроса ---

    @pytest.mark.parametrize('params', [{}, {'q': ''}, {'q': '   '}])
    def test_invalid_query_param_returns_400(self, logged_in_manager, params):
        """Запрос без q, с пустым q или только с пробелами возвращает 400."""
        response = logged_in_manager.get(reverse(self.URL), params)
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    # --- Результаты поиска ---

    def test_search_finds_intern_by_name(self, logged_in_manager, intern):
        """Поиск по имени находит студента."""
        response = logged_in_manager.get(reverse(self.URL), {'q': intern.full_name[:4]})
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'results' in data
        assert 'count' in data
        ids = [r['id'] for r in data['results']]
        assert intern.id in ids

    def test_search_case_insensitive(self, logged_in_manager, intern):
        """Поиск находит студента по частичному совпадению имени."""
        # Берём часть имени без учёта регистра (icontains для латиницы работает всегда,
        # для SQLite+кириллица может не работать — используем нейтральный фрагмент)
        fragment = intern.full_name.split()[0]
        response = logged_in_manager.get(reverse(self.URL), {'q': fragment})
        assert response.status_code == 200
        data = json.loads(response.content)
        ids = [r['id'] for r in data['results']]
        assert intern.id in ids

    def test_search_no_results_for_unknown_name(self, logged_in_manager, intern):
        """Поиск несуществующего имени возвращает пустой список."""
        response = logged_in_manager.get(reverse(self.URL), {'q': 'НесуществующееИмя99999'})
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['count'] == 0
        assert data['results'] == []

    def test_search_result_has_required_fields(self, logged_in_manager, intern):
        """Элемент результата содержит обязательные поля."""
        response = logged_in_manager.get(reverse(self.URL), {'q': intern.full_name[:4]})
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data['results']) == 1
        item = data['results'][0]
        assert 'id' in item
        assert 'full_name' in item
        assert 'group' in item
        assert 'manager_email' in item

    def test_search_result_count_matches_results(self, logged_in_manager, intern, intern_other):
        """Поле count соответствует длине results."""
        response = logged_in_manager.get(reverse(self.URL), {'q': 'ст'})
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['count'] == len(data['results'])

    def test_search_limits_to_10_results(self, logged_in_manager, direction):
        """Поиск ограничивает результаты до 10."""
        Intern.objects.bulk_create([
            Intern(
                full_name=f'Общий Студент {i}',
                email=f'common_intern_{i}@example.com',
                manager_email='manager@example.com',
                direction=direction,
                date_of_receipt=date(2025, 1, 1),
                date_of_birth=date(2000, 1, 1),
                hiring_hr='HR1',
                responsible_hr='HR2',
                group='GR1',
                type_of_training='internal',
            )
            for i in range(15)
        ])
        response = logged_in_manager.get(reverse(self.URL), {'q': 'Общий'})
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data['results']) <= 10

    def test_search_excludes_interns_without_manager_email(self, logged_in_manager, direction):
        """Студенты без manager_email не попадают в результаты."""
        Intern.objects.create(
            full_name='БезМенеджера Студент',
            email='no_manager@example.com',
            manager_email='',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
        )
        response = logged_in_manager.get(reverse(self.URL), {'q': 'БезМенеджера'})
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['count'] == 0

    def test_response_is_json(self, logged_in_manager):
        """Ответ возвращается в формате JSON."""
        response = logged_in_manager.get(reverse(self.URL), {'q': 'test'})
        assert 'application/json' in response.get('Content-Type', '')


# ============================================================================
# UpdateWeekInterviewCountView — POST /employees/api/update-week-interviews/
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestUpdateWeekInterviewCountView:
    """Тесты для UpdateWeekInterviewCountView (POST /employees/api/update-week-interviews/)."""

    URL = 'employees_update_week_interviews'

    # --- Аутентификация и права ---

    def test_unauthenticated_returns_401(self, client, intern):
        """Неавторизованный запрос получает 401."""
        response = client.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'count': '3',
        })
        assert response.status_code == 401

    def test_manager_cannot_edit_returns_403(self, logged_in_manager, intern):
        """Обычный менеджер получает 403 (только для админов)."""
        response = logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'count': '3',
        })
        assert response.status_code == 403
        data = json.loads(response.content)
        assert 'error' in data

    # --- Валидация параметров ---

    def test_missing_intern_id_returns_400(self, logged_in_admin):
        """Запрос без intern_id возвращает 400."""
        response = logged_in_admin.post(reverse(self.URL), {
            'week_start': '2025-01-06',
            'count': '3',
        })
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    def test_missing_week_start_returns_400(self, logged_in_admin, intern):
        """Запрос без week_start возвращает 400."""
        response = logged_in_admin.post(reverse(self.URL), {
            'intern_id': intern.id,
            'count': '3',
        })
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    def test_invalid_date_format_returns_400(self, logged_in_admin, intern):
        """Некорректный формат даты возвращает 400."""
        response = logged_in_admin.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': 'not-a-date',
            'count': '3',
        })
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    @pytest.mark.parametrize('count', ['-1', 'abc'])
    def test_invalid_count_value_returns_400(self, logged_in_admin, intern, count):
        """Отрицательное или нечисловое значение count возвращает 400."""
        response = logged_in_admin.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'count': count,
        })
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    def test_nonexistent_intern_returns_404(self, logged_in_admin):
        """Несуществующий intern_id возвращает 404."""
        response = logged_in_admin.post(reverse(self.URL), {
            'intern_id': 99999,
            'week_start': '2025-01-06',
            'count': '3',
        })
        assert response.status_code == 404
        data = json.loads(response.content)
        assert 'error' in data

    # --- Успешные операции ---

    def test_admin_can_create_weekly_status(self, logged_in_admin, intern):
        """Администратор может создать запись недельного статуса."""
        response = logged_in_admin.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'count': '5',
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['count'] == 5

        status = InternWeeklyStatus.objects.get(intern=intern, week_start=date(2025, 1, 6))
        assert status.manual_interview_count == 5

    def test_admin_can_update_existing_weekly_status(self, logged_in_admin, intern):
        """Администратор может обновить существующую запись."""
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=date(2025, 1, 6),
            manual_interview_count=2,
        )
        response = logged_in_admin.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'count': '7',
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['count'] == 7

        status = InternWeeklyStatus.objects.get(intern=intern, week_start=date(2025, 1, 6))
        assert status.manual_interview_count == 7

    def test_empty_count_removes_manual_count(self, logged_in_admin, intern):
        """Пустое значение count удаляет ручную корректировку (count=None)."""
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=date(2025, 1, 6),
            manual_interview_count=5,
        )
        response = logged_in_admin.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'count': '',
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['count'] is None

    def test_empty_count_deletes_record_if_no_absence(self, logged_in_admin, intern):
        """Пустой count без absence_status удаляет всю запись."""
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=date(2025, 1, 6),
            manual_interview_count=3,
        )
        logged_in_admin.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'count': '',
        })
        assert not InternWeeklyStatus.objects.filter(
            intern=intern, week_start=date(2025, 1, 6)
        ).exists()

    def test_empty_count_keeps_record_with_absence(self, logged_in_admin, intern):
        """Пустой count при наличии absence_status сохраняет запись."""
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=date(2025, 1, 6),
            manual_interview_count=3,
            absence_status='болеет',
        )
        logged_in_admin.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'count': '',
        })
        assert InternWeeklyStatus.objects.filter(
            intern=intern, week_start=date(2025, 1, 6)
        ).exists()

    def test_response_is_json(self, logged_in_admin, intern):
        """Ответ возвращается в формате JSON."""
        response = logged_in_admin.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'count': '2',
        })
        assert 'application/json' in response.get('Content-Type', '')

    def test_count_zero_is_valid(self, logged_in_admin, intern):
        """Значение count=0 является валидным."""
        response = logged_in_admin.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'count': '0',
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['count'] == 0


# ============================================================================
# SetManagerActiveView — POST /employees/api/set-manager-active/
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestSetManagerActiveView:
    """Тесты для SetManagerActiveView (POST /employees/api/set-manager-active/)."""

    URL = 'employees_set_manager_active'

    # --- Аутентификация и права ---

    def test_unauthenticated_returns_401(self, client, manager):
        """Неавторизованный запрос получает 401."""
        response = client.post(reverse(self.URL), {
            'manager_email': manager.email,
            'is_active': 'false',
        })
        assert response.status_code == 401

    def test_manager_cannot_set_active_returns_403(self, logged_in_manager, manager):
        """Обычный менеджер получает 403."""
        response = logged_in_manager.post(reverse(self.URL), {
            'manager_email': manager.email,
            'is_active': 'false',
        })
        assert response.status_code == 403
        data = json.loads(response.content)
        assert 'error' in data

    # --- Валидация параметров ---

    def test_missing_manager_email_returns_400(self, logged_in_admin):
        """Запрос без manager_email возвращает 400."""
        response = logged_in_admin.post(reverse(self.URL), {
            'is_active': 'false',
        })
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    def test_nonexistent_manager_returns_404(self, logged_in_admin):
        """Несуществующий email менеджера возвращает 404."""
        response = logged_in_admin.post(reverse(self.URL), {
            'manager_email': 'nonexistent@example.com',
            'is_active': 'false',
        })
        assert response.status_code == 404
        data = json.loads(response.content)
        assert 'error' in data

    # --- Успешные операции ---

    def test_admin_can_deactivate_manager(self, logged_in_admin, manager):
        """Администратор может деактивировать менеджера."""
        manager.is_active = True
        manager.save()

        response = logged_in_admin.post(reverse(self.URL), {
            'manager_email': manager.email,
            'is_active': 'false',
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['is_active'] is False

        manager.refresh_from_db()
        assert manager.is_active is False

    def test_admin_can_activate_manager(self, logged_in_admin, manager):
        """Администратор может активировать менеджера."""
        manager.is_active = False
        manager.save()

        response = logged_in_admin.post(reverse(self.URL), {
            'manager_email': manager.email,
            'is_active': 'true',
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['is_active'] is True

        manager.refresh_from_db()
        assert manager.is_active is True

    def test_response_contains_manager_info(self, logged_in_admin, manager):
        """Ответ содержит информацию о менеджере."""
        response = logged_in_admin.post(reverse(self.URL), {
            'manager_email': manager.email,
            'is_active': 'false',
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'email' in data
        assert 'is_active' in data
        assert 'full_name' in data
        assert data['email'] == manager.email
        assert data['full_name'] == manager.full_name

    def test_response_is_json(self, logged_in_admin, manager):
        """Ответ возвращается в формате JSON."""
        response = logged_in_admin.post(reverse(self.URL), {
            'manager_email': manager.email,
            'is_active': 'false',
        })
        assert 'application/json' in response.get('Content-Type', '')

    def test_default_is_active_false(self, logged_in_admin, manager):
        """Без явного is_active по умолчанию используется 'false'."""
        manager.is_active = True
        manager.save()

        response = logged_in_admin.post(reverse(self.URL), {
            'manager_email': manager.email,
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['is_active'] is False


# ============================================================================
# UpdateWeekAbsenceStatusView — POST /employees/api/update-week-absence/
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestUpdateWeekAbsenceStatusView:
    """Тесты для UpdateWeekAbsenceStatusView (POST /employees/api/update-week-absence/)."""

    URL = 'employees_update_week_absence'

    # --- Аутентификация ---

    def test_unauthenticated_returns_401(self, client, intern):
        """Неавторизованный запрос получает 401."""
        response = client.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': 'болеет',
        })
        assert response.status_code == 401

    def test_manager_can_access(self, logged_in_manager, intern):
        """Авторизованный менеджер может устанавливать статус отсутствия."""

        response = logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': 'болеет',
        })
        assert response.status_code == 200

    def test_admin_can_access(self, logged_in_admin, intern):
        """Авторизованный администратор может устанавливать статус отсутствия."""

        response = logged_in_admin.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': 'болеет',
        })
        assert response.status_code == 200

    # --- Валидация параметров ---

    def test_missing_intern_id_returns_400(self, logged_in_manager):
        """Запрос без intern_id возвращает 400."""
        response = logged_in_manager.post(reverse(self.URL), {
            'week_start': '2025-01-06',
            'absence_status': 'болеет',
        })
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    def test_missing_week_start_returns_400(self, logged_in_manager, intern):
        """Запрос без week_start возвращает 400."""
        response = logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'absence_status': 'болеет',
        })
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    def test_invalid_absence_status_returns_400(self, logged_in_manager, intern):
        """Недопустимый статус отсутствия возвращает 400."""
        response = logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': 'invalid_status',
        })
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    def test_invalid_date_format_returns_400(self, logged_in_manager, intern):
        """Некорректный формат даты возвращает 400."""
        response = logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': 'not-a-date',
            'absence_status': 'болеет',
        })
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data

    def test_nonexistent_intern_returns_404(self, logged_in_manager):
        """Несуществующий intern_id возвращает 404."""
        response = logged_in_manager.post(reverse(self.URL), {
            'intern_id': 99999,
            'week_start': '2025-01-06',
            'absence_status': 'болеет',
        })
        assert response.status_code == 404
        data = json.loads(response.content)
        assert 'error' in data

    # --- Допустимые статусы ---

    @pytest.mark.parametrize('status', ['болеет', 'отпуск', 'уехал', 'другое'])
    def test_valid_absence_statuses(self, logged_in_manager, intern, status):
        """Все допустимые статусы принимаются."""
        response = logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': status,
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['absence_status'] == status

    # --- Создание / обновление записи ---

    def test_creates_weekly_status_record(self, logged_in_manager, intern):
        """Запрос создаёт запись InternWeeklyStatus."""
        logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': 'отпуск',
        })
        assert InternWeeklyStatus.objects.filter(
            intern=intern,
            week_start=date(2025, 1, 6),
            absence_status='отпуск',
        ).exists()

    def test_updates_existing_record(self, logged_in_manager, intern):
        """Повторный запрос обновляет существующую запись."""
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=date(2025, 1, 6),
            absence_status='болеет',
        )
        logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': 'отпуск',
        })
        status = InternWeeklyStatus.objects.get(intern=intern, week_start=date(2025, 1, 6))
        assert status.absence_status == 'отпуск'

    def test_saves_absence_notes(self, logged_in_manager, intern):
        """Примечание к отсутствию сохраняется."""
        logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': 'другое',
            'absence_notes': 'Командировка в другой город',
        })
        status = InternWeeklyStatus.objects.get(intern=intern, week_start=date(2025, 1, 6))
        assert status.absence_notes == 'Командировка в другой город'

    def test_response_contains_display_status(self, logged_in_manager, intern):
        """Ответ содержит человекочитаемый статус отсутствия."""
        response = logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': 'болеет',
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'absence_status_display' in data
        assert data['absence_status_display'] == 'Болеет'

    # --- Удаление статуса ---

    def test_empty_absence_status_removes_it(self, logged_in_manager, intern):
        """Пустой absence_status удаляет статус отсутствия."""
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=date(2025, 1, 6),
            absence_status='болеет',
        )
        response = logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': '',
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['absence_status'] is None

    def test_empty_absence_status_deletes_record_if_no_manual_count(self, logged_in_manager, intern):
        """Удаление absence_status при отсутствии manual_count удаляет всю запись."""
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=date(2025, 1, 6),
            absence_status='болеет',
        )
        logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': '',
        })
        assert not InternWeeklyStatus.objects.filter(
            intern=intern, week_start=date(2025, 1, 6)
        ).exists()

    def test_empty_absence_status_keeps_record_with_manual_count(self, logged_in_manager, intern):
        """Удаление absence_status при наличии manual_count сохраняет запись."""
        InternWeeklyStatus.objects.create(
            intern=intern,
            week_start=date(2025, 1, 6),
            absence_status='болеет',
            manual_interview_count=3,
        )
        logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': '',
        })
        assert InternWeeklyStatus.objects.filter(
            intern=intern, week_start=date(2025, 1, 6)
        ).exists()

    def test_no_record_empty_status_returns_200(self, logged_in_manager, intern):
        """Удаление absence_status при отсутствующей записи возвращает 200."""
        response = logged_in_manager.post(reverse(self.URL), {
            'intern_id': intern.id,
            'week_start': '2025-01-06',
            'absence_status': '',
        })
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True


# ============================================================================
# InternWeeklyStatusViewSet — /api/employees/weekly-statuses/ (DRF)
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternWeeklyStatusViewSetAuth:
    """Тесты аутентификации и прав доступа к /api/employees/weekly-statuses/."""

    def test_unauthenticated_returns_403(self, api_client):
        """Неаутентифицированный запрос получает 403."""
        response = api_client.get('/api/employees/weekly-statuses/')
        assert response.status_code in (401, 403)

    def test_manager_can_access_list(self, api_client, api_manager_user):
        """Менеджер имеет доступ к списку."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/employees/weekly-statuses/')
        assert response.status_code == 200

    def test_admin_can_access_list(self, api_client, api_admin_user):
        """Администратор имеет доступ к списку."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/employees/weekly-statuses/')
        assert response.status_code == 200

    def test_user_without_groups_gets_403(self, api_client, api_anon_user):
        """Пользователь без групп получает 403."""
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.get('/api/employees/weekly-statuses/')
        assert response.status_code == 403

    def test_response_content_type_is_json(self, api_client, api_admin_user):
        """Ответ возвращается в формате JSON."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/employees/weekly-statuses/')
        assert 'application/json' in response['Content-Type']


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternWeeklyStatusViewSetList:
    """Тесты GET /api/employees/weekly-statuses/ — список и фильтры."""

    def test_admin_sees_all_statuses(
        self, api_client, api_admin_user, weekly_status, weekly_status_other
    ):
        """Администратор видит все недельные статусы."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/employees/weekly-statuses/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert weekly_status.id in ids
        assert weekly_status_other.id in ids

    def test_manager_sees_only_own_interns_statuses(
        self, api_client, api_manager_user, weekly_status, weekly_status_other
    ):
        """Менеджер видит статусы только своих студентов (manager_email=manager@example.com)."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get('/api/employees/weekly-statuses/')
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert weekly_status.id in ids
        assert weekly_status_other.id not in ids

    def test_filter_by_intern_id(
        self, api_client, api_admin_user, intern, weekly_status, weekly_status_other
    ):
        """Фильтр по intern_id возвращает только статусы указанного студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/employees/weekly-statuses/', {'intern_id': intern.id})
        assert response.status_code == 200
        results = get_api_results(response)
        ids = [item['id'] for item in results]
        assert weekly_status.id in ids
        assert weekly_status_other.id not in ids

    def test_filter_by_week_start(
        self, api_client, api_admin_user, intern, intern_other
    ):
        """Фильтр по week_start возвращает только статусы за эту неделю."""
        InternWeeklyStatus.objects.create(intern=intern, week_start=date(2025, 1, 6), manual_interview_count=1)
        InternWeeklyStatus.objects.create(intern=intern, week_start=date(2025, 1, 13), manual_interview_count=2)

        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/employees/weekly-statuses/', {'week_start': '2025-01-06'})
        assert response.status_code == 200
        results = get_api_results(response)
        week_starts = [item['week_start'] for item in results]
        assert all(ws == '2025-01-06' for ws in week_starts)

    def test_filter_by_absence_status(
        self, api_client, api_admin_user, weekly_status, weekly_status_other
    ):
        """Фильтр по absence_status возвращает только статусы с этим отсутствием."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/employees/weekly-statuses/', {'absence_status': 'болеет'})
        assert response.status_code == 200
        results = get_api_results(response)
        assert all(item['absence_status'] == 'болеет' for item in results)

    def test_empty_list_when_no_data(self, api_client, api_admin_user):
        """Пустой список при отсутствии данных."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/employees/weekly-statuses/')
        assert response.status_code == 200
        results = get_api_results(response)
        assert results == []

    def test_filter_by_invalid_intern_id_ignored(self, api_client, api_admin_user, weekly_status):
        """Невалидный intern_id (строка) игнорируется и возвращаются все данные."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/employees/weekly-statuses/', {'intern_id': 'invalid'})
        assert response.status_code == 200
        results = get_api_results(response)
        assert len(results) == 1


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternWeeklyStatusViewSetRetrieve:
    """Тесты GET /api/employees/weekly-statuses/{id}/."""

    def test_admin_can_retrieve_any_status(
        self, api_client, api_admin_user, weekly_status
    ):
        """Администратор может получить любой недельный статус."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        assert response.status_code == 200
        assert response.data['id'] == weekly_status.id

    def test_manager_can_retrieve_own_intern_status(
        self, api_client, api_manager_user, weekly_status
    ):
        """Менеджер может получить статус своего студента."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        assert response.status_code == 200

    def test_manager_cannot_retrieve_other_intern_status(
        self, api_client, api_manager_user, weekly_status_other
    ):
        """Менеджер не может получить статус чужого студента."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.get(f'/api/employees/weekly-statuses/{weekly_status_other.id}/')
        assert response.status_code == 404

    def test_retrieve_nonexistent_returns_404(self, api_client, api_admin_user):
        """Запрос несуществующего статуса возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get('/api/employees/weekly-statuses/99999/')
        assert response.status_code == 404

    def test_retrieve_response_has_required_fields(
        self, api_client, api_admin_user, weekly_status
    ):
        """Ответ содержит все обязательные поля."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        assert response.status_code == 200
        expected_fields = {
            'id', 'intern', 'intern_name', 'week_start',
            'manual_interview_count', 'absence_status', 'absence_notes',
            'created_at', 'updated_at',
        }
        assert expected_fields == set(response.data.keys())


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternWeeklyStatusViewSetCreate:
    """Тесты POST /api/employees/weekly-statuses/ — создание записи."""

    def test_admin_can_create_status(self, api_client, api_admin_user, intern):
        """Администратор может создать запись недельного статуса."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post('/api/employees/weekly-statuses/', {
            'intern': intern.id,
            'week_start': '2025-02-03',
            'manual_interview_count': 4,
        }, format='json')
        assert response.status_code == 201
        assert InternWeeklyStatus.objects.filter(intern=intern, week_start='2025-02-03').exists()

    def test_manager_can_create_status_for_own_intern(
        self, api_client, api_manager_user, intern
    ):
        """Менеджер может создать статус для своего студента."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post('/api/employees/weekly-statuses/', {
            'intern': intern.id,
            'week_start': '2025-02-10',
            'absence_status': 'болеет',
        }, format='json')
        assert response.status_code == 201

    def test_manager_cannot_create_with_manual_interview_count(
        self, api_client, api_manager_user, intern
    ):
        """Ручное число собесов задаёт только администратор."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post('/api/employees/weekly-statuses/', {
            'intern': intern.id,
            'week_start': '2025-02-17',
            'manual_interview_count': 3,
        }, format='json')
        assert response.status_code == 400
        assert 'manual_interview_count' in response.data

    def test_create_with_all_fields(self, api_client, api_admin_user, intern):
        """Создание записи со всеми полями."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post('/api/employees/weekly-statuses/', {
            'intern': intern.id,
            'week_start': '2025-03-03',
            'manual_interview_count': 2,
            'absence_status': 'уехал',
            'absence_notes': 'Командировка',
        }, format='json')
        assert response.status_code == 201
        status = InternWeeklyStatus.objects.get(intern=intern, week_start='2025-03-03')
        assert status.manual_interview_count == 2
        assert status.absence_status == 'уехал'
        assert status.absence_notes == 'Командировка'

    def test_unauthenticated_cannot_create(self, api_client, intern):
        """Неаутентифицированный пользователь не может создать статус."""
        response = api_client.post('/api/employees/weekly-statuses/', {
            'intern': intern.id,
            'week_start': '2025-02-03',
            'manual_interview_count': 4,
        }, format='json')
        assert response.status_code in (401, 403)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternWeeklyStatusViewSetUpdate:
    """Тесты PATCH /api/employees/weekly-statuses/{id}/ — частичное обновление."""

    def test_admin_can_patch_status(self, api_client, api_admin_user, weekly_status):
        """Администратор может частично обновить запись."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.patch(
            f'/api/employees/weekly-statuses/{weekly_status.id}/',
            {'manual_interview_count': 10},
            format='json',
        )
        assert response.status_code == 200
        weekly_status.refresh_from_db()
        assert weekly_status.manual_interview_count == 10

    def test_manager_can_patch_own_intern_status(
        self, api_client, api_manager_user, weekly_status
    ):
        """Менеджер может обновить статус своего студента."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/employees/weekly-statuses/{weekly_status.id}/',
            {'absence_status': 'отпуск'},
            format='json',
        )
        assert response.status_code == 200

    def test_manager_cannot_patch_manual_interview_count(
        self, api_client, api_manager_user, weekly_status
    ):
        """Менеджер не может менять ручное число собеседований."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/employees/weekly-statuses/{weekly_status.id}/',
            {'manual_interview_count': 7},
            format='json',
        )
        assert response.status_code == 400
        assert 'manual_interview_count' in response.data

    def test_manager_cannot_patch_other_intern_status(
        self, api_client, api_manager_user, weekly_status_other
    ):
        """Менеджер не может обновить статус чужого студента."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/employees/weekly-statuses/{weekly_status_other.id}/',
            {'manual_interview_count': 5},
            format='json',
        )
        assert response.status_code == 404


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternWeeklyStatusViewSetDelete:
    """Тесты DELETE /api/employees/weekly-statuses/{id}/ — удаление."""

    def test_admin_can_delete_status(
        self, api_client, api_admin_user, weekly_status
    ):
        """Администратор может удалить запись недельного статуса."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        assert response.status_code == 204
        assert not InternWeeklyStatus.objects.filter(id=weekly_status.id).exists()

    def test_manager_cannot_delete_status(
        self, api_client, api_manager_user, weekly_status
    ):
        """Обычный менеджер не может удалить запись (только для админа)."""
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.delete(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        assert response.status_code == 403

    def test_unauthenticated_cannot_delete(self, api_client, weekly_status):
        """Неаутентифицированный пользователь не может удалить запись."""
        response = api_client.delete(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        assert response.status_code in (401, 403)

    def test_delete_nonexistent_returns_404(self, api_client, api_admin_user):
        """Удаление несуществующей записи возвращает 404."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.delete('/api/employees/weekly-statuses/99999/')
        assert response.status_code == 404


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternWeeklyStatusSerializer:
    """Тесты сериализации полей InternWeeklyStatusSerializer."""

    def test_id_is_integer(self, api_client, api_admin_user, weekly_status):
        """id совпадает с id записи."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        assert response.data['id'] == weekly_status.id

    def test_intern_name_is_filled(self, api_client, api_admin_user, weekly_status, intern):
        """intern_name содержит имя студента."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        assert response.data['intern_name'] == intern.full_name

    def test_week_start_format(self, api_client, api_admin_user, weekly_status):
        """week_start возвращается в формате YYYY-MM-DD."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        week_start = response.data['week_start']
        assert week_start == '2025-01-06'

    def test_manual_interview_count_is_integer_or_null(
        self, api_client, api_admin_user, weekly_status
    ):
        """manual_interview_count равен значению, заданному при создании."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        assert response.data['manual_interview_count'] == 3

    def test_absence_status_can_be_null(
        self, api_client, api_admin_user, weekly_status
    ):
        """absence_status равен None, если не был задан."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        assert response.data['absence_status'] is None

    def test_created_at_and_updated_at_present(
        self, api_client, api_admin_user, weekly_status
    ):
        """created_at и updated_at присутствуют в ответе."""
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.get(f'/api/employees/weekly-statuses/{weekly_status.id}/')
        assert 'created_at' in response.data
        assert 'updated_at' in response.data
        assert response.data['created_at'] is not None
        assert response.data['updated_at'] is not None
