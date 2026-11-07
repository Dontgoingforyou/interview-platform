"""
Тесты для accounts/permissions.py

Покрывают все 6 классов разрешений:
- IsKeycloakAuthenticated
- IsAdminRole
- IsManagerOrAdmin
- IsEmploymentManager
- IsCVManager
- IsEducationManager
"""
import pytest
from unittest.mock import MagicMock

from accounts.permissions import (
    IsKeycloakAuthenticated,
    IsAdminRole,
    IsAdminOrMentorRole,
    IsManagerOrAdmin,
    IsEmploymentManager,
    IsCVManager,
    IsEducationManager,
)
from tests.helpers import make_keycloak_user


def make_request(user=None):
    request = MagicMock()
    request.user = user
    return request


def make_anon_request():
    """Запрос без пользователя (None)."""
    return make_request(user=None)


def make_plain_user():
    """Объект без атрибутов KeycloakUser (обычный Django AnonymousUser-like)."""
    user = MagicMock(spec=[])  # без атрибутов
    return user


# ---------------------------------------------------------------------------
# IsKeycloakAuthenticated
# ---------------------------------------------------------------------------

class TestIsKeycloakAuthenticated:
    perm = IsKeycloakAuthenticated()

    def test_authenticated_keycloak_user_allowed(self):
        user = make_keycloak_user()
        request = make_request(user=user)
        assert self.perm.has_permission(request, None) is True

    def test_none_user_denied(self):
        request = make_anon_request()
        assert self.perm.has_permission(request, None) is False

    def test_user_without_is_authenticated_attr_denied(self):
        request = make_request(user=make_plain_user())
        assert self.perm.has_permission(request, None) is False

    def test_user_with_is_authenticated_false_denied(self):
        user = MagicMock()
        user.is_authenticated = False
        request = make_request(user=user)
        assert self.perm.has_permission(request, None) is False

    def test_has_message(self):
        assert 'вход' in self.perm.message


# ---------------------------------------------------------------------------
# IsAdminRole
# ---------------------------------------------------------------------------

class TestIsAdminRole:
    perm = IsAdminRole()

    @pytest.mark.parametrize('groups, expected', [
        (['role_admin'], True),
        (['employment-managers'], False),
        ([], False),
    ])
    def test_group_based_permission(self, groups, expected):
        user = make_keycloak_user(groups=groups)
        assert self.perm.has_permission(make_request(user=user), None) is expected

    def test_none_user_denied(self):
        assert self.perm.has_permission(make_anon_request(), None) is False

    def test_user_without_is_admin_attr_denied(self):
        user = make_plain_user()
        assert self.perm.has_permission(make_request(user=user), None) is False


# ---------------------------------------------------------------------------
# IsAdminOrMentorRole
# ---------------------------------------------------------------------------

class TestIsAdminOrMentorRole:
    perm = IsAdminOrMentorRole()

    @pytest.mark.parametrize('groups, expected', [
        (['role_admin'], True),
        (['mentors'], True),
        (['employment-managers'], False),
        (['hrs'], False),
    ])
    def test_group_based_permission(self, groups, expected):
        user = make_keycloak_user(groups=groups)
        assert self.perm.has_permission(make_request(user=user), None) is expected


# ---------------------------------------------------------------------------
# IsManagerOrAdmin
# ---------------------------------------------------------------------------

class TestIsManagerOrAdmin:
    perm = IsManagerOrAdmin()

    @pytest.mark.parametrize('groups, expected', [
        (['role_admin'], True),
        (['employment-managers'], True),
        (['cv-managers'], True),
        (['education'], True),
        (['mentors'], True),
        (['role_admin', 'cv-managers'], True),
        (['some-unknown-group'], False),
        ([], False),
    ])
    def test_group_based_permission(self, groups, expected):
        user = make_keycloak_user(groups=groups)
        assert self.perm.has_permission(make_request(user=user), None) is expected

    def test_none_user_denied(self):
        assert self.perm.has_permission(make_anon_request(), None) is False

    def test_user_without_is_authenticated_attr_denied(self):
        request = make_request(user=make_plain_user())
        assert self.perm.has_permission(request, None) is False

    def test_user_not_authenticated_denied(self):
        user = MagicMock()
        user.is_authenticated = False
        request = make_request(user=user)
        assert self.perm.has_permission(request, None) is False


# ---------------------------------------------------------------------------
# IsEmploymentManager
# ---------------------------------------------------------------------------

class TestIsEmploymentManager:
    perm = IsEmploymentManager()

    @pytest.mark.parametrize('groups, expected', [
        (['employment-managers'], True),
        (['role_admin'], True),
        (['cv-managers'], False),
        (['education'], False),
    ])
    def test_group_based_permission(self, groups, expected):
        user = make_keycloak_user(groups=groups)
        assert self.perm.has_permission(make_request(user=user), None) is expected

    def test_none_user_denied(self):
        assert self.perm.has_permission(make_anon_request(), None) is False

    def test_user_without_attrs_denied(self):
        request = make_request(user=make_plain_user())
        assert self.perm.has_permission(request, None) is False

    def test_user_not_authenticated_denied(self):
        user = MagicMock()
        user.is_authenticated = False
        assert self.perm.has_permission(make_request(user=user), None) is False


# ---------------------------------------------------------------------------
# IsCVManager
# ---------------------------------------------------------------------------

class TestIsCVManager:
    perm = IsCVManager()

    @pytest.mark.parametrize('groups, expected', [
        (['cv-managers'], True),
        (['role_admin'], True),
        (['employment-managers'], False),
        (['education'], False),
    ])
    def test_group_based_permission(self, groups, expected):
        user = make_keycloak_user(groups=groups)
        assert self.perm.has_permission(make_request(user=user), None) is expected

    def test_none_user_denied(self):
        assert self.perm.has_permission(make_anon_request(), None) is False

    def test_user_without_attrs_denied(self):
        request = make_request(user=make_plain_user())
        assert self.perm.has_permission(request, None) is False

    def test_user_not_authenticated_denied(self):
        user = MagicMock()
        user.is_authenticated = False
        assert self.perm.has_permission(make_request(user=user), None) is False


# ---------------------------------------------------------------------------
# IsEducationManager
# ---------------------------------------------------------------------------

class TestIsEducationManager:
    perm = IsEducationManager()

    @pytest.mark.parametrize('groups, expected', [
        (['education'], True),
        (['role_admin'], True),
        (['employment-managers'], False),
        (['cv-managers'], False),
    ])
    def test_group_based_permission(self, groups, expected):
        user = make_keycloak_user(groups=groups)
        assert self.perm.has_permission(make_request(user=user), None) is expected

    def test_none_user_denied(self):
        assert self.perm.has_permission(make_anon_request(), None) is False

    def test_user_without_attrs_denied(self):
        request = make_request(user=make_plain_user())
        assert self.perm.has_permission(request, None) is False

    def test_user_not_authenticated_denied(self):
        user = MagicMock()
        user.is_authenticated = False
        assert self.perm.has_permission(make_request(user=user), None) is False
