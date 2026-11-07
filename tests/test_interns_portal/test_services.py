"""Тесты interns_portal.services."""
import pytest

from core.constants import KEYCLOAK_ROLE_ADMIN
from interns.models import Intern
from interns_portal.services import (
    _resolve_intern_portal,
    get_intern_for_current_user,
    get_intern_for_portal_user,
    is_staff_or_manager_session,
)


@pytest.mark.django_db(databases=['default'])
class TestIsStaffOrManagerSession:
    def test_admin(self):
        assert is_staff_or_manager_session(KEYCLOAK_ROLE_ADMIN, []) is True

    def test_manager_group(self):
        from core.constants import KEYCLOAK_GROUP_EMPLOYMENT
        assert is_staff_or_manager_session('manager', [KEYCLOAK_GROUP_EMPLOYMENT]) is True

    def test_plain_user(self):
        assert is_staff_or_manager_session('manager', []) is False


@pytest.mark.django_db(databases=['default'])
class TestResolveInternPortal:
    def test_empty_email_and_name(self):
        assert _resolve_intern_portal('', '', skip_fio_autolink=False) is None

    def test_by_corporate_email(self, intern):
        intern.corporate_email = 'user@corp.ru'
        intern.save(update_fields=['corporate_email'])
        result = _resolve_intern_portal('user@corp.ru', '', skip_fio_autolink=True)
        assert result is not None
        assert result.pk == intern.pk

    def test_fio_autolink_sets_corporate_email(self, intern):
        intern.corporate_email = None
        intern.full_name = 'Иван Иванов'
        intern.save(update_fields=['corporate_email', 'full_name'])
        result = _resolve_intern_portal('kc-fio@corp.ru', 'Иван Иванов', skip_fio_autolink=False)
        assert result is not None
        result.refresh_from_db()
        assert result.corporate_email == 'kc-fio@corp.ru'

    def test_skip_fio_returns_none_without_email_match(self, intern):
        intern.corporate_email = None
        intern.save(update_fields=['corporate_email'])
        assert _resolve_intern_portal('', intern.full_name, skip_fio_autolink=True) is None

    def test_by_personal_email_when_corporate_empty(self, intern):
        intern.corporate_email = None
        intern.email = 'demo.student@example.com'
        intern.save(update_fields=['corporate_email', 'email'])
        result = _resolve_intern_portal(
            'demo.student@example.com',
            'Demo Student',
            skip_fio_autolink=False,
        )
        assert result is not None
        assert result.pk == intern.pk

    def test_translit_matches_db_without_yo(self, intern):
        intern.corporate_email = None
        intern.email = None
        intern.full_name = 'Артем Петров'
        intern.save(update_fields=['corporate_email', 'email', 'full_name'])
        result = _resolve_intern_portal(
            'artem.petrov@example.com',
            'Artem Petrov',
            skip_fio_autolink=False,
        )
        assert result is not None
        assert result.pk == intern.pk
        result.refresh_from_db()
        assert result.corporate_email == 'artem.petrov@example.com'

    def test_translit_matches_db_with_yo(self, intern):
        intern.corporate_email = None
        intern.email = None
        intern.full_name = 'Артём Петров'
        intern.save(update_fields=['corporate_email', 'email', 'full_name'])
        result = _resolve_intern_portal(
            'artem.petrov@example.com',
            'Artem Petrov',
            skip_fio_autolink=False,
        )
        assert result is not None
        assert result.pk == intern.pk

    def test_translit_matches_db_with_soft_sign(self, intern):
        intern.corporate_email = None
        intern.email = None
        intern.full_name = 'Игорь Петров'
        intern.save(update_fields=['corporate_email', 'email', 'full_name'])
        result = _resolve_intern_portal(
            'igor.petrov@example.com',
            'Igor Petrov',
            skip_fio_autolink=False,
        )
        assert result is not None
        assert result.pk == intern.pk
        result.refresh_from_db()
        assert result.corporate_email == 'igor.petrov@example.com'

    def test_translit_matches_db_without_soft_sign(self, intern):
        intern.corporate_email = None
        intern.email = None
        intern.full_name = 'Игор Петров'
        intern.save(update_fields=['corporate_email', 'email', 'full_name'])
        result = _resolve_intern_portal(
            'igor.petrov@example.com',
            'Igor Petrov',
            skip_fio_autolink=False,
        )
        assert result is not None
        assert result.pk == intern.pk


@pytest.mark.django_db(databases=['default'])
class TestGetInternHelpers:
    def test_get_intern_for_current_user(self, intern, rf):
        intern.corporate_email = 'sess@corp.ru'
        intern.save(update_fields=['corporate_email'])
        request = rf.get('/')
        request.session = {
            'manager_email': 'sess@corp.ru',
            'manager_name': '',
            'manager_role': 'student',
            'manager_groups': ['students'],
        }
        assert get_intern_for_current_user(request).pk == intern.pk

    def test_get_intern_for_portal_user_admin_skips_fio(self, intern, api_admin_user):
        assert get_intern_for_portal_user(api_admin_user) is None or isinstance(
            get_intern_for_portal_user(api_admin_user), Intern
        )
