"""
Тесты для сериализаторов приложения sad_intern.

Покрывают:
- SadInternListSerializer   — поля, read_only, вычисляемые значения
- SadInternDetailSerializer — поля, read_only, manager_email
- SadInternCreateUpdateSerializer — валидация, сохранение

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.serializers - для группировки тестов сериализаторов
"""
import pytest
from rest_framework.test import APIRequestFactory

from sad_intern.models import SadIntern
from sad_intern.serializers import (
    SadInternListSerializer,
    SadInternDetailSerializer,
    SadInternCreateUpdateSerializer,
)


@pytest.fixture
def sad_api_request(api_admin_user):
    """POST-запрос с пользователем-админом для сериализатора создания."""
    req = APIRequestFactory().post('/api/sad-interns/')
    req.user = api_admin_user
    return req


@pytest.fixture
def sad_api_request_manager(api_manager_user):
    """PATCH-запрос с пользователем-менеджером для частичного обновления."""
    req = APIRequestFactory().patch('/api/sad-interns/1/')
    req.user = api_manager_user
    return req


# ============================================================================
# SadInternListSerializer
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestSadInternListSerializer:
    """Тесты для SadInternListSerializer."""

    def test_contains_expected_fields(self, sad_intern):
        """Сериализатор содержит все ожидаемые поля."""
        serializer = SadInternListSerializer(sad_intern)
        data = serializer.data
        expected_fields = {
            'id', 'intern', 'intern_name', 'date_added', 'waiting_since',
            'days_waiting', 'telegram_username', 'manager_email', 'status', 'note',
            'real_interview_date', 'direction_id', 'direction_name', 'status_display',
            'intern_manager_name',
        }
        assert expected_fields == set(data.keys())

    def test_intern_name_is_full_name(self, sad_intern):
        """Поле intern_name содержит full_name студента."""
        serializer = SadInternListSerializer(sad_intern)
        assert serializer.data['intern_name'] == sad_intern.intern.full_name

    def test_id_is_read_only(self, sad_intern, intern):
        """Поле id является read_only."""
        data = {
            'id': 9999,
            'intern': intern.pk,
            'waiting_since': '2025-12-01',
        }
        serializer = SadInternListSerializer(sad_intern, data=data, partial=True)
        assert serializer.is_valid()
        # id не должен измениться
        assert serializer.validated_data.get('id') is None

    def test_date_added_is_read_only(self, sad_intern, intern):
        """Поле date_added является read_only."""
        data = {
            'intern': intern.pk,
            'waiting_since': '2025-12-01',
            'date_added': '2000-01-01',
        }
        serializer = SadInternListSerializer(sad_intern, data=data, partial=True)
        assert serializer.is_valid()
        assert 'date_added' not in serializer.validated_data

    def test_days_waiting_is_read_only(self, sad_intern, intern):
        """Поле days_waiting является read_only."""
        data = {
            'intern': intern.pk,
            'waiting_since': '2025-12-01',
            'days_waiting': 9999,
        }
        serializer = SadInternListSerializer(sad_intern, data=data, partial=True)
        assert serializer.is_valid()
        assert 'days_waiting' not in serializer.validated_data

    def test_status_field_value(self, sad_intern):
        """Поле status содержит корректное значение."""
        serializer = SadInternListSerializer(sad_intern)
        assert serializer.data['status'] == sad_intern.status

    def test_telegram_username_field(self, sad_intern):
        """Поле telegram_username содержит корректное значение."""
        serializer = SadInternListSerializer(sad_intern)
        assert serializer.data['telegram_username'] == sad_intern.telegram_username

    def test_manager_email_field(self, sad_intern):
        """Поле manager_email содержит корректное значение."""
        serializer = SadInternListSerializer(sad_intern)
        assert serializer.data['manager_email'] == sad_intern.manager_email

    def test_note_field(self, sad_intern):
        """Поле note содержит корректное значение."""
        serializer = SadInternListSerializer(sad_intern)
        assert serializer.data['note'] == sad_intern.note

    def test_days_waiting_is_non_negative(self, sad_intern):
        """Поле days_waiting содержит неотрицательное значение."""
        serializer = SadInternListSerializer(sad_intern)
        assert serializer.data['days_waiting'] >= 0

    def test_serializes_multiple_objects(self, sad_intern, sad_intern_other):
        """Сериализатор корректно сериализует список объектов."""
        qs = SadIntern.objects.filter(pk__in=[sad_intern.pk, sad_intern_other.pk])
        serializer = SadInternListSerializer(qs, many=True)
        assert len(serializer.data) == 2


# ============================================================================
# SadInternDetailSerializer
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestSadInternDetailSerializer:
    """Тесты для SadInternDetailSerializer."""

    def test_contains_expected_fields(self, sad_intern):
        """Сериализатор содержит все ожидаемые поля."""
        serializer = SadInternDetailSerializer(sad_intern)
        data = serializer.data
        expected_fields = {
            'id', 'intern', 'intern_name', 'date_added', 'waiting_since',
            'days_waiting', 'telegram_username', 'manager_email',
            'status', 'note',
            'real_interview_date', 'direction_id', 'direction_name', 'status_display',
            'intern_manager_name',
        }
        assert expected_fields == set(data.keys())

    def test_intern_name_is_full_name(self, sad_intern):
        """Поле intern_name содержит full_name студента."""
        serializer = SadInternDetailSerializer(sad_intern)
        assert serializer.data['intern_name'] == sad_intern.intern.full_name

    def test_read_only_fields(self, sad_intern, intern):
        """Поля id, date_added, days_waiting являются read_only."""
        data = {
            'intern': intern.pk,
            'waiting_since': '2025-12-01',
            'id': 9999,
            'date_added': '2000-01-01',
            'days_waiting': 9999,
        }
        serializer = SadInternDetailSerializer(sad_intern, data=data, partial=True)
        assert serializer.is_valid()
        assert 'id' not in serializer.validated_data
        assert 'date_added' not in serializer.validated_data
        assert 'days_waiting' not in serializer.validated_data

    def test_all_data_matches_model(self, sad_intern):
        """Все поля соответствуют значениям в модели."""
        serializer = SadInternDetailSerializer(sad_intern)
        data = serializer.data
        assert data['id'] == sad_intern.pk
        assert data['intern'] == sad_intern.intern.pk
        assert data['intern_name'] == sad_intern.intern.full_name
        assert data['manager_email'] == sad_intern.manager_email
        assert data['status'] == sad_intern.status
        assert data['note'] == sad_intern.note
        assert data['telegram_username'] == sad_intern.telegram_username
        assert data['days_waiting'] == sad_intern.days_waiting


# ============================================================================
# SadInternCreateUpdateSerializer
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestSadInternCreateUpdateSerializer:
    """Тесты для SadInternCreateUpdateSerializer."""

    def test_valid_data_creates_sad_intern(self, intern, sad_api_request):
        """Валидные данные позволяют создать запись через сериализатор."""
        data = {
            'intern': intern.pk,
            'waiting_since': '2025-11-01',
            'telegram_username': '@test',
            'manager_email': 'manager@example.com',
            'status': 'rejected',
            'note': 'Тест',
        }
        serializer = SadInternCreateUpdateSerializer(data=data, context={'request': sad_api_request})
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.pk is not None
        assert instance.intern == intern
        assert instance.status == 'rejected'

    def test_contains_expected_fields(self):
        """Сериализатор содержит ожидаемые поля для записи/обновления."""
        serializer = SadInternCreateUpdateSerializer()
        expected_fields = {
            'intern', 'waiting_since', 'telegram_username',
            'manager_email', 'status', 'note',
        }
        assert expected_fields == set(serializer.fields.keys())

    def test_intern_is_required(self):
        """Поле intern обязательно при создании."""
        data = {
            'waiting_since': '2025-11-01',
            'status': 'rejected',
        }
        serializer = SadInternCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'intern' in serializer.errors

    def test_waiting_since_optional_with_defaults(self, intern, sad_api_request):
        """Поле waiting_since можно не передавать — подставляется дата."""
        data = {
            'intern': intern.pk,
            'status': 'rejected',
        }
        serializer = SadInternCreateUpdateSerializer(data=data, context={'request': sad_api_request})
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.waiting_since is not None

    def test_optional_fields_can_be_omitted(self, intern, sad_api_request):
        """Необязательные поля можно не передавать."""
        data = {
            'intern': intern.pk,
            'waiting_since': '2025-11-01',
        }
        serializer = SadInternCreateUpdateSerializer(data=data, context={'request': sad_api_request})
        assert serializer.is_valid(), serializer.errors

    def test_partial_update_status(self, sad_intern, sad_api_request_manager):
        """Частичное обновление статуса работает корректно."""
        serializer = SadInternCreateUpdateSerializer(
            sad_intern,
            data={'status': 'accepted'},
            partial=True,
            context={'request': sad_api_request_manager},
        )
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.status == 'accepted'

    def test_partial_update_note(self, sad_intern, sad_api_request_manager):
        """Частичное обновление примечания работает корректно."""
        serializer = SadInternCreateUpdateSerializer(
            sad_intern,
            data={'note': 'Новое примечание'},
            partial=True,
            context={'request': sad_api_request_manager},
        )
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.note == 'Новое примечание'

    def test_partial_update_telegram_username(self, sad_intern, sad_api_request_manager):
        """Частичное обновление telegram_username работает корректно."""
        serializer = SadInternCreateUpdateSerializer(
            sad_intern,
            data={'telegram_username': '@new_tg'},
            partial=True,
            context={'request': sad_api_request_manager},
        )
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.telegram_username == '@new_tg'

    def test_invalid_waiting_since_format_returns_error(self, intern):
        """Невалидный формат waiting_since возвращает ошибку."""
        data = {
            'intern': intern.pk,
            'waiting_since': 'не-дата',
            'status': 'rejected',
        }
        serializer = SadInternCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'waiting_since' in serializer.errors

    def test_does_not_expose_id_and_date_added(self):
        """Сериализатор не содержит полей id и date_added (они в read_only из других)."""
        serializer = SadInternCreateUpdateSerializer()
        assert 'id' not in serializer.fields
        assert 'date_added' not in serializer.fields
        assert 'days_waiting' not in serializer.fields

    @pytest.mark.parametrize('status_val', ['rejected', 'accepted', 'offered', 'fired', 'on_project'])
    def test_create_with_all_statuses(self, intern, status_val, sad_api_request):
        """Сериализатор принимает каждый из допустимых статусов."""
        data = {
            'intern': intern.pk,
            'waiting_since': '2025-11-01',
            'status': status_val,
        }
        serializer = SadInternCreateUpdateSerializer(data=data, context={'request': sad_api_request})
        assert serializer.is_valid(), f'Статус {status_val} не прошёл валидацию: {serializer.errors}'
        instance = serializer.save()
        assert instance.status == status_val
