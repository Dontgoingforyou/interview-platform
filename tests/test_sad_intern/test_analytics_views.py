"""
Тесты для sad_intern/analytics_views.py.

Покрывают эндпоинт GET /sad_intern/api/analytics/sad_intern/:
- Аутентификация через декоратор @manager_required_api (сессионная, keycloak)
- Структура JSON-ответа
- Метрики при пустой БД
- Метрика total (учёт on_project, интернов оффер/ушёл)
- Метрика with_contact (telegram username)
- Метрика avg_wait (среднее и округление)
- Метрики longest_wait_days / longest_wait_name
"""
import pytest
from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone

from interns.models import Intern
from sad_intern.models import SadIntern


# ---------------------------------------------------------------------------
# Вспомогательная фабрика — Intern + SadIntern для for_main_waiting_list()
# ---------------------------------------------------------------------------

def _make_active_sad_intern(direction, waiting_days, full_name, telegram=None, manager_email='manager@example.com'):
    """Создаёт Intern и SadIntern для метрик for_main_waiting_list() (без on_project, интерн не оффер/ушёл)."""
    today = timezone.now().date()

    intern = Intern.objects.create(
        full_name=full_name,
        direction=direction,
        manager_email=manager_email,
        date_of_receipt=date(2025, 1, 1),
        date_of_birth=date(2000, 1, 1),
        hiring_hr='HR1',
        responsible_hr='HR2',
        group='GR1',
        type_of_training='internal',
    )
    sad = SadIntern.objects.create(
        intern=intern,
        waiting_since=today - timedelta(days=waiting_days),
        telegram_username=telegram,
        manager_email=manager_email,
        status='rejected',
    )
    return sad


# ============================================================================
# Аутентификация
# ============================================================================

@pytest.mark.django_db(databases=['default'])
class TestSadInternAnalyticsApiAuth:
    """Тесты аутентификации эндпоинта аналитики."""

    def test_unauthenticated_returns_401(self, client):
        """Запрос без сессии возвращает 401."""
        url = reverse('api_sad_intern_analytics')
        response = client.get(url)
        assert response.status_code == 401

    def test_authenticated_manager_returns_200(self, logged_in_manager):
        """Авторизованный менеджер получает 200."""
        url = reverse('api_sad_intern_analytics')
        response = logged_in_manager.get(url)
        assert response.status_code == 200

    def test_authenticated_admin_returns_200(self, logged_in_admin):
        """Авторизованный администратор получает 200."""
        url = reverse('api_sad_intern_analytics')
        response = logged_in_admin.get(url)
        assert response.status_code == 200


# ============================================================================
# Структура ответа
# ============================================================================

@pytest.mark.django_db(databases=['default'])
class TestSadInternAnalyticsApiStructure:
    """Тесты структуры JSON-ответа."""

    def test_response_content_type_is_json(self, logged_in_manager):
        """Ответ возвращается с Content-Type application/json."""
        url = reverse('api_sad_intern_analytics')
        response = logged_in_manager.get(url)
        assert 'application/json' in response['Content-Type']

    def test_response_has_all_required_keys(self, logged_in_manager):
        """Ответ содержит все обязательные ключи верхнего уровня."""
        url = reverse('api_sad_intern_analytics')
        response = logged_in_manager.get(url)
        data = response.json()
        required_keys = {'total', 'with_contact', 'avg_wait', 'longest_wait_days', 'longest_wait_name', 'tooltips'}
        assert required_keys.issubset(data.keys())

    def test_tooltips_contain_all_expected_keys(self, logged_in_manager):
        """Поле tooltips содержит ключи для всех четырёх метрик."""
        url = reverse('api_sad_intern_analytics')
        response = logged_in_manager.get(url)
        tooltips = response.json()['tooltips']
        expected_keys = {'total', 'with-contact', 'avg-wait', 'longest'}
        assert expected_keys.issubset(tooltips.keys())

    @pytest.mark.parametrize('tooltip_key', ['total', 'with-contact', 'avg-wait', 'longest'])
    def test_tooltip_value_is_non_empty_string(self, logged_in_manager, tooltip_key):
        """Каждая подсказка содержит непустой текст."""
        url = reverse('api_sad_intern_analytics')
        tooltips = logged_in_manager.get(url).json()['tooltips']
        val = tooltips[tooltip_key]
        assert isinstance(val, str) and val.strip()


# ============================================================================
# Пустая БД
# ============================================================================

@pytest.mark.django_db(databases=['default'])
class TestSadInternAnalyticsApiEmptyDB:
    """Тесты корректного поведения при отсутствии данных в БД."""

    def test_total_is_zero(self, logged_in_manager):
        """total == 0 при пустой БД."""
        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['total'] == 0

    def test_with_contact_is_zero(self, logged_in_manager):
        """with_contact == 0 при пустой БД."""
        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['with_contact'] == 0

    def test_avg_wait_is_zero(self, logged_in_manager):
        """avg_wait == 0 при пустой БД."""
        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['avg_wait'] == 0

    def test_longest_wait_days_is_zero(self, logged_in_manager):
        """longest_wait_days == 0 при пустой БД."""
        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['longest_wait_days'] == 0

    def test_longest_wait_name_is_dash(self, logged_in_manager):
        """longest_wait_name == '—' при пустой БД."""
        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['longest_wait_name'] == '—'


# ============================================================================
# Метрика total
# ============================================================================

@pytest.mark.django_db(databases=['default'])
class TestSadInternAnalyticsApiTotal:
    """Тесты метрики total — общее количество грустящих (без on_project, без ушедших)."""

    def test_total_counts_active_interns(self, logged_in_manager, direction):
        """Один активный студент учитывается в total."""
        _make_active_sad_intern(direction, waiting_days=10, full_name='Активный Студент')
        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['total'] == 1

    def test_total_excludes_on_project_status(self, logged_in_manager, direction, sad_intern_on_project):
        """Студент со статусом on_project не увеличивает total."""
        _make_active_sad_intern(direction, waiting_days=10, full_name='Активный Студент')
        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        # Активный (rejected) считается, sad_intern_on_project — нет
        assert data['total'] == 1

    def test_total_excludes_intern_with_manual_status_left(self, logged_in_manager, sad_intern, intern):
        """Студент с manual_status='ушел' не входит в total."""
        intern.manual_status = 'ушел'
        intern.save()

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['total'] == 0

    def test_total_excludes_intern_with_manual_status_offer(self, logged_in_manager, sad_intern, intern):
        """Студент с manual_status='оффер' не входит в total."""
        intern.manual_status = 'оффер'
        intern.save()

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['total'] == 0

    def test_total_multiple_active_interns(self, logged_in_manager, direction):
        """Все активные студенты (не on_project, не ушедшие) учитываются в total."""
        _make_active_sad_intern(direction, waiting_days=10, full_name='Первый Студент')
        _make_active_sad_intern(direction, waiting_days=20, full_name='Второй Студент')
        _make_active_sad_intern(direction, waiting_days=5, full_name='Третий Студент')

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['total'] == 3


# ============================================================================
# Метрика with_contact
# ============================================================================

@pytest.mark.django_db(databases=['default'])
class TestSadInternAnalyticsApiWithContact:
    """Тесты метрики with_contact — студенты с Telegram-ником."""

    def test_with_contact_counts_intern_with_telegram(self, logged_in_manager, sad_intern):
        """Студент с telegram_username учитывается в with_contact."""
        # sad_intern имеет telegram_username='@ivan_tg'
        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['with_contact'] == 1

    def test_with_contact_excludes_null_telegram(self, logged_in_manager, direction):
        """Студент с telegram_username=None не учитывается в with_contact."""
        _make_active_sad_intern(direction, waiting_days=10, full_name='Студент Без TG', telegram=None)

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['with_contact'] == 0

    def test_with_contact_excludes_empty_string_telegram(self, logged_in_manager, direction):
        """Студент с telegram_username='' не учитывается в with_contact."""
        _make_active_sad_intern(direction, waiting_days=10, full_name='Студент Без TG', telegram='')

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['with_contact'] == 0

    def test_with_contact_mixed_telegram(self, logged_in_manager, direction):
        """Из трёх студентов with_contact считает только тех, у кого есть Telegram."""
        _make_active_sad_intern(direction, waiting_days=10, full_name='С TG', telegram='@tg_user')
        _make_active_sad_intern(direction, waiting_days=15, full_name='Без TG Null', telegram=None)
        _make_active_sad_intern(direction, waiting_days=5, full_name='Без TG Пусто', telegram='')

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['total'] == 3
        assert data['with_contact'] == 1


# ============================================================================
# Метрика avg_wait
# ============================================================================

@pytest.mark.django_db(databases=['default'])
class TestSadInternAnalyticsApiAvgWait:
    """Тесты метрики avg_wait — среднее количество дней ожидания."""

    def test_avg_wait_single_intern_equals_its_days_waiting(self, logged_in_manager, direction):
        """При одном студенте avg_wait равен его days_waiting."""
        sad = _make_active_sad_intern(direction, waiting_days=20, full_name='Один Студент')

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['avg_wait'] == sad.days_waiting

    def test_avg_wait_multiple_interns_correct_mean(self, logged_in_manager, direction):
        """avg_wait корректно вычисляет среднее по нескольким студентам."""
        s1 = _make_active_sad_intern(direction, waiting_days=10, full_name='Студент А')
        s2 = _make_active_sad_intern(direction, waiting_days=20, full_name='Студент Б')
        expected_avg = round((s1.days_waiting + s2.days_waiting) / 2, 2)

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['avg_wait'] == expected_avg

    def test_avg_wait_is_rounded_to_two_decimal_places(self, logged_in_manager, direction):
        """avg_wait округлён до двух знаков: (10 + 11 + 13) / 3 = 11.33."""
        _make_active_sad_intern(direction, waiting_days=10, full_name='Студент 1')
        _make_active_sad_intern(direction, waiting_days=11, full_name='Студент 2')
        _make_active_sad_intern(direction, waiting_days=13, full_name='Студент 3')

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['avg_wait'] == round((10 + 11 + 13) / 3, 2)

    def test_avg_wait_excludes_on_project_from_calculation(self, logged_in_manager, direction, sad_intern_on_project):
        """on_project студенты не учитываются при вычислении avg_wait."""
        s1 = _make_active_sad_intern(direction, waiting_days=10, full_name='Активный Студент')

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        # avg вычисляется только по активным, не по on_project
        assert data['avg_wait'] == s1.days_waiting


# ============================================================================
# Метрики longest_wait_days и longest_wait_name
# ============================================================================

@pytest.mark.django_db(databases=['default'])
class TestSadInternAnalyticsApiLongestWait:
    """Тесты метрик longest_wait_days и longest_wait_name."""

    def test_longest_wait_days_returns_max(self, logged_in_manager, direction):
        """longest_wait_days равен максимальному days_waiting среди активных студентов."""
        s_short = _make_active_sad_intern(direction, waiting_days=10, full_name='Короткое Ожидание')
        s_long = _make_active_sad_intern(direction, waiting_days=30, full_name='Долгое Ожидание')

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['longest_wait_days'] == s_long.days_waiting

    def test_longest_wait_name_matches_intern_full_name(self, logged_in_manager, direction):
        """longest_wait_name — полное имя студента с максимальным ожиданием."""
        _make_active_sad_intern(direction, waiting_days=10, full_name='Короткое Ожидание')
        _make_active_sad_intern(direction, waiting_days=30, full_name='Долгое Ожидание')

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['longest_wait_name'] == 'Долгое Ожидание'

    def test_longest_wait_excludes_on_project(self, logged_in_manager, direction, sad_intern_on_project):
        """on_project студенты не участвуют в определении longest_wait."""
        s_active = _make_active_sad_intern(direction, waiting_days=15, full_name='Активный Долгожитель')

        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        # Только активный студент учитывается
        assert data['longest_wait_days'] == s_active.days_waiting
        assert data['longest_wait_name'] == 'Активный Долгожитель'

    def test_longest_wait_single_intern(self, logged_in_manager, sad_intern):
        """При одном студенте longest_wait совпадает с его данными."""
        url = reverse('api_sad_intern_analytics')
        data = logged_in_manager.get(url).json()
        assert data['longest_wait_days'] == sad_intern.days_waiting
        assert data['longest_wait_name'] == sad_intern.intern.full_name
