"""Тесты interns.serializers."""
import pytest
from rest_framework.test import APIRequestFactory

from interns.serializers import (
    InternCreateUpdateSerializer,
    InternDetailSerializer,
    InternListSerializer,
    build_manager_display_map,
)
from managers.models import Manager
from tests.helpers import make_keycloak_user


@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestBuildManagerDisplayMap:
    def test_empty_emails_returns_empty_dict(self):
        assert build_manager_display_map(set()) == {}

    def test_maps_active_manager_emails_to_display_names(self, manager):
        result = build_manager_display_map({manager.email})
        assert result[manager.email] == manager.full_name


@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestInternListSerializer:
    def test_serializes_intern(self, intern, direction):
        intern.direction = direction
        intern.save(update_fields=['direction_id'])
        data = InternListSerializer(intern).data
        assert data['id'] == intern.pk
        assert 'full_name' in data

    def test_direction_name_none_when_no_direction(self, intern):
        serializer = InternListSerializer()
        obj = type('InternStub', (), {'direction': None})()
        assert serializer.get_direction_name(obj) is None

    def test_manager_display_name_from_context(self, intern, manager):
        context = {'manager_display_map': {manager.email: 'Отображаемое имя'}}
        data = InternListSerializer(intern, context=context).data
        assert data['manager_display_name'] == 'Отображаемое имя'

    def test_manager_display_name_none_without_email(self, intern):
        intern.manager_email = ''
        data = InternListSerializer(intern).data
        assert data['manager_display_name'] is None


@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestInternDetailSerializer:
    def test_serializes_expected_fields(self, intern, direction):
        intern.direction = direction
        intern.save(update_fields=['direction_id'])
        data = InternDetailSerializer(intern).data
        assert data['id'] == intern.pk
        assert data['full_name'] == intern.full_name
        assert data['direction_name'] == direction.name

    def test_direction_name_none_when_no_direction(self, intern):
        serializer = InternDetailSerializer()
        obj = type('InternStub', (), {'direction': None})()
        assert serializer.get_direction_name(obj) is None


@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestInternCreateUpdateSerializer:
    def _valid_data(self, direction, manager_email='manager@example.com'):
        return {
            'full_name': 'Новый Студент',
            'email': 'new@example.com',
            'telegram_username': '@valid_user',
            'direction_id': direction.pk,
            'hiring_hr': 'HR1',
            'responsible_hr': 'HR2',
            'group': 'GR1',
            'type_of_training': 'internal',
            'manager_email': manager_email,
        }

    def test_invalid_telegram_username_raises_validation_error(self, direction, intern_api_request, manager):
        data = self._valid_data(direction)
        data['telegram_username'] = '@ab'
        serializer = InternCreateUpdateSerializer(data=data, context={'request': intern_api_request})
        assert not serializer.is_valid()
        assert 'telegram_username' in serializer.errors

    def test_normalizes_telegram_username(self, direction, intern_api_request, manager):
        data = self._valid_data(direction)
        data['telegram_username'] = 'valid_user'
        serializer = InternCreateUpdateSerializer(data=data, context={'request': intern_api_request})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['telegram_username'] == '@valid_user'

    def test_empty_telegram_username_allowed(self, direction, intern_api_request, manager):
        data = self._valid_data(direction)
        data['telegram_username'] = ''
        serializer = InternCreateUpdateSerializer(data=data, context={'request': intern_api_request})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['telegram_username'] == ''

    def test_admin_can_assign_active_manager(self, direction, intern_api_request, manager2):
        data = self._valid_data(direction, manager_email=manager2.email)
        serializer = InternCreateUpdateSerializer(data=data, context={'request': intern_api_request})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['manager_email'] == manager2.email

    def test_manager_forced_to_own_email(self, direction, intern_api_request_manager, manager):
        data = self._valid_data(direction, manager_email='other@example.com')
        serializer = InternCreateUpdateSerializer(
            data=data,
            context={'request': intern_api_request_manager},
        )
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['manager_email'] == manager.email

    def test_manager_without_email_raises_validation_error(self, direction):
        req = APIRequestFactory().post('/api/interns/')
        req.user = make_keycloak_user(email='')
        data = self._valid_data(direction, manager_email='manager@example.com')
        serializer = InternCreateUpdateSerializer(data=data, context={'request': req})
        assert not serializer.is_valid()
        assert 'manager_email' in serializer.errors

    def test_inactive_manager_email_rejected(self, direction, intern_api_request, db):
        Manager.objects.create(
            email='inactive@example.com',
            full_name='Неактивный Менеджер',
            username='inactive',
            groups=['employment-managers'],
            is_active=False,
        )
        data = self._valid_data(direction, manager_email='inactive@example.com')
        serializer = InternCreateUpdateSerializer(data=data, context={'request': intern_api_request})
        assert not serializer.is_valid()
        assert 'manager_email' in serializer.errors

    def test_empty_manager_email_allowed_for_admin(self, direction, intern_api_request):
        data = self._valid_data(direction, manager_email='')
        serializer = InternCreateUpdateSerializer(data=data, context={'request': intern_api_request})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['manager_email'] == ''
