"""Тесты KeycloakUser и сессионной аутентификации."""
from unittest.mock import MagicMock

from accounts.authentication import KeycloakSessionAuthentication, KeycloakUser


def make_user_info(**kwargs):
    base = {
        'email': 'user@example.com',
        'username': 'testuser',
        'full_name': 'Тест Тестов',
        'role': 'manager',
        'groups': [],
    }
    base.update(kwargs)
    return base


class TestKeycloakUser:
    def test_basic_fields_populated(self):
        user = KeycloakUser(make_user_info())
        assert user.email == 'user@example.com'
        assert user.username == 'testuser'
        assert user.full_name == 'Тест Тестов'
        assert user.role == 'no_access'
        assert user.groups == []

    def test_default_values_for_missing_fields(self):
        user = KeycloakUser({})
        assert user.email == ''
        assert user.role == 'no_access'

    def test_drf_compat_flags(self):
        user = KeycloakUser(make_user_info())
        assert user.is_authenticated is True
        assert user.is_active is True

    def test_is_admin_when_in_admin_group(self):
        user = KeycloakUser(make_user_info(groups=['role_admin']))
        assert user.is_admin is True

    def test_is_employment_manager(self):
        user = KeycloakUser(make_user_info(groups=['employment-managers']))
        assert user.is_employment_manager is True

    def test_student_group_sets_role_student(self):
        user = KeycloakUser(make_user_info(groups=['students']))
        assert user.role == 'student'
        assert user.is_student is True

    def test_student_path_normalized(self):
        user = KeycloakUser(make_user_info(groups=['/students']))
        assert 'students' in user.groups
        assert user.role == 'student'

    def test_str_representation(self):
        user = KeycloakUser(make_user_info(full_name='Иван Иванов', email='ivan@test.com'))
        assert str(user) == 'Иван Иванов (ivan@test.com)'


class TestKeycloakSessionAuthentication:
    def _request(self, session):
        request = MagicMock()
        request.session = session
        return request

    def test_empty_session_returns_none(self):
        auth = KeycloakSessionAuthentication()
        assert auth.authenticate(self._request({})) is None

    def test_session_without_email_returns_none(self):
        auth = KeycloakSessionAuthentication()
        assert auth.authenticate(self._request({'keycloak_user': True})) is None

    def test_session_builds_user(self):
        auth = KeycloakSessionAuthentication()
        user, token = auth.authenticate(self._request({
            'keycloak_user': True,
            'manager_email': 'anna.ivanova@example.com',
            'manager_username': 'admin',
            'manager_name': 'Анна Иванова',
            'manager_groups': ['role_admin'],
        }))
        assert token is None
        assert user.is_admin is True
        assert user.email == 'anna.ivanova@example.com'
