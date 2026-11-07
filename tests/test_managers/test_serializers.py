"""
Тесты сериализаторов приложения managers.

Покрывают:
- ManagerListSerializer  — полные данные менеджера с computed-полями
- ManagerUpdateSerializer — частичное обновление менеджера

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.serializers - для группировки тестов
"""
import pytest

from managers.models import Manager
from managers.serializers import ManagerListSerializer, ManagerUpdateSerializer


# ============================================================================
# ManagerListSerializer
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestManagerListSerializer:
    """Тесты ManagerListSerializer."""

    def test_serializes_all_expected_fields(self, manager):
        """Сериализатор включает все необходимые поля."""
        serializer = ManagerListSerializer(manager)
        expected_fields = {
            'email', 'full_name', 'username', 'groups', 'is_active',
            'is_admin', 'is_employment_manager', 'is_cv_manager',
            'is_education_manager', 'created_at', 'updated_at',
        }
        assert expected_fields == set(serializer.data.keys())

    def test_email_is_primary_key(self, manager):
        """email — первичный ключ, присутствует в ответе с корректным значением."""
        serializer = ManagerListSerializer(manager)
        assert serializer.data['email'] == manager.email

    def test_full_name_matches_db(self, manager):
        """full_name соответствует данным в БД."""
        serializer = ManagerListSerializer(manager)
        assert serializer.data['full_name'] == manager.full_name

    def test_username_matches_db(self, manager):
        """username соответствует данным в БД."""
        serializer = ManagerListSerializer(manager)
        assert serializer.data['username'] == manager.username

    def test_groups_is_list(self, manager):
        """groups возвращается как список."""
        serializer = ManagerListSerializer(manager)
        assert isinstance(serializer.data['groups'], list)

    @pytest.mark.parametrize('is_active_val, expected', [
        (True, True),
        (False, False),
    ])
    def test_is_active_serialized(self, is_active_val, expected):
        """is_active корректно сериализуется для активного и неактивного менеджера."""
        m = Manager.objects.create(
            email=f'active-{is_active_val}@example.com',
            full_name='Тестовый Менеджер',
            username=f'active_{is_active_val}',
            groups=['employment-managers'],
            is_active=is_active_val,
        )
        serializer = ManagerListSerializer(m)
        assert serializer.data['is_active'] is expected

    @pytest.mark.parametrize('groups, field, expected', [
        (['role_admin', 'employment-managers'], 'is_admin',              True),
        (['employment-managers'],                       'is_admin',              False),
        (['employment-managers'],                       'is_employment_manager', True),
        (['cv-managers'],                               'is_employment_manager', False),
        (['cv-managers'],                               'is_cv_manager',         True),
        (['employment-managers'],                       'is_cv_manager',         False),
        (['education'],                                 'is_education_manager',  True),
        (['employment-managers'],                       'is_education_manager',  False),
    ])
    def test_role_field_serialized(self, groups, field, expected):
        """Поле роли корректно сериализуется в зависимости от групп менеджера."""
        m = Manager.objects.create(
            email=f'ser-{field}-{str(expected).lower()}@example.com',
            full_name='Тестовый Менеджер',
            username=f'ser_{field}_{str(expected).lower()}',
            groups=groups,
        )
        serializer = ManagerListSerializer(m)
        assert serializer.data[field] is expected

    def test_admin_has_all_roles_true(self, admin_manager):
        """Администратор с несколькими группами имеет соответствующие флаги ролей."""
        serializer = ManagerListSerializer(admin_manager)
        assert serializer.data['is_admin'] is True
        assert serializer.data['is_employment_manager'] is True

    def test_created_at_is_present(self, manager):
        """created_at присутствует в ответе."""
        serializer = ManagerListSerializer(manager)
        assert serializer.data['created_at'] is not None

    def test_updated_at_is_present(self, manager):
        """updated_at присутствует в ответе."""
        serializer = ManagerListSerializer(manager)
        assert serializer.data['updated_at'] is not None

    def test_serializes_multiple_managers(self, manager, manager2):
        """Сериализатор корректно работает со списком менеджеров."""
        managers = Manager.objects.filter(email__in=[manager.email, manager2.email])
        serializer = ManagerListSerializer(managers, many=True)
        assert len(serializer.data) == 2
        emails = [item['email'] for item in serializer.data]
        assert manager.email in emails
        assert manager2.email in emails


# ============================================================================
# ManagerUpdateSerializer
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestManagerUpdateSerializer:
    """Тесты ManagerUpdateSerializer."""

    def test_contains_only_allowed_fields(self, manager):
        """Сериализатор содержит только поля full_name, username, is_active."""
        serializer = ManagerUpdateSerializer(manager)
        assert set(serializer.fields.keys()) == {'full_name', 'username', 'is_active'}

    def test_update_full_name(self, manager):
        """Сериализатор обновляет full_name."""
        serializer = ManagerUpdateSerializer(manager, data={'full_name': 'Новое Имя'}, partial=True)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        manager.refresh_from_db()
        assert manager.full_name == 'Новое Имя'

    def test_update_username(self, manager):
        """Сериализатор обновляет username."""
        serializer = ManagerUpdateSerializer(manager, data={'username': 'new_user'}, partial=True)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        manager.refresh_from_db()
        assert manager.username == 'new_user'

    @pytest.mark.parametrize('initial, target', [
        (True, False),
        (False, True),
    ])
    def test_update_is_active(self, manager, initial, target):
        """Сериализатор обновляет is_active в обе стороны."""
        manager.is_active = initial
        manager.save()
        serializer = ManagerUpdateSerializer(manager, data={'is_active': target}, partial=True)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        manager.refresh_from_db()
        assert manager.is_active is target

    def test_partial_update_does_not_reset_other_fields(self, manager):
        """Частичное обновление не сбрасывает не переданные поля."""
        original_username = manager.username
        original_active = manager.is_active
        serializer = ManagerUpdateSerializer(manager, data={'full_name': 'Только Имя'}, partial=True)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        manager.refresh_from_db()
        assert manager.username == original_username
        assert manager.is_active == original_active

    def test_update_all_fields_at_once(self, manager):
        """Сериализатор обновляет все допустимые поля одновременно."""
        data = {'full_name': 'Полное Обновление', 'username': 'full_update', 'is_active': False}
        serializer = ManagerUpdateSerializer(manager, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        manager.refresh_from_db()
        assert manager.full_name == 'Полное Обновление'
        assert manager.username == 'full_update'
        assert manager.is_active is False

    def test_email_field_not_in_serializer(self, manager):
        """Поле email отсутствует в сериализаторе обновления."""
        serializer = ManagerUpdateSerializer(manager)
        assert 'email' not in serializer.fields

    def test_groups_field_not_in_serializer(self, manager):
        """Поле groups отсутствует в сериализаторе обновления."""
        serializer = ManagerUpdateSerializer(manager)
        assert 'groups' not in serializer.fields

    def test_validated_data_is_valid_with_all_fields(self, manager):
        """is_valid() возвращает True для всех допустимых полей."""
        data = {'full_name': 'Валидное Имя', 'username': 'valid_user', 'is_active': True}
        serializer = ManagerUpdateSerializer(manager, data=data)
        assert serializer.is_valid()

    def test_empty_data_is_valid_for_partial(self, manager):
        """Пустые данные валидны при partial=True (ничего не обновляется)."""
        serializer = ManagerUpdateSerializer(manager, data={}, partial=True)
        assert serializer.is_valid()
