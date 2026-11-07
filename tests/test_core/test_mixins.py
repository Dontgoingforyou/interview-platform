"""
Тесты для core/mixins.py.

Покрывает:
- ManagerRequiredMixin: редирект на логин без SSO-сессии, пропуск с SSO
- AdminRequiredMixin: редирект на логин без SSO, редирект для не-админа, пропуск для админа
- ManagerRequiredAPIView: JsonResponse 401 без SSO, пропуск с SSO
- RoleBasedAccessMixin.get_queryset: admin видит всё, manager — только своё;
  модель без поля manager_email — фильтрация не применяется
- ExternalReferencesMixin: get_manager (найден/не найден/нет email),
  get_manager_info (базовая/из сессии/нет email), manager cached_property
"""
import json

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse
from django.views import View
from unittest.mock import MagicMock

from core.mixins import (
    AdminRequiredDispatchMixin,
    AdminRequiredMixin,
    ExternalReferencesMixin,
    InterviewTranscriptionReadDispatchMixin,
    ManagerRequiredAPIView,
    ManagerRequiredMixin,
    RoleBasedAccessMixin,
)


class _OkView(View):
    """Минимальный View для проверки dispatch-цепочки."""

    def get(self, request, *args, **kwargs):
        return HttpResponse('OK')


class _ManagerView(ManagerRequiredMixin, _OkView):
    pass


class _AdminView(AdminRequiredMixin, _OkView):
    pass


class _APIView(ManagerRequiredAPIView, _OkView):
    pass


def _make_request(*, has_sso=True, role='manager', manager_email='manager@example.com'):
    """Создаёт GET-запрос с нужными параметрами сессии."""
    request = RequestFactory().get('/')
    session = {'manager_role': role, 'manager_email': manager_email}
    if has_sso:
        session['keycloak_user'] = True
        session['keycloak_id'] = 'test-keycloak-id'
    request.session = session
    return request


class TestManagerRequiredMixin:
    """Тесты для ManagerRequiredMixin."""

    def test_no_sso_redirects_to_login(self):
        """Без SSO-сессии → 302 на login."""
        request = _make_request(has_sso=False)
        response = _ManagerView.as_view()(request)
        assert response.status_code == 302
        assert response['Location'] == reverse('login')

    def test_with_sso_passes_through(self):
        """С SSO-сессией → 200."""
        request = _make_request(has_sso=True)
        response = _ManagerView.as_view()(request)
        assert response.status_code == 200


class TestAdminRequiredMixin:
    """Тесты для AdminRequiredMixin."""

    def test_no_sso_redirects_to_login(self):
        """Без SSO-сессии → 302 на login."""
        request = _make_request(has_sso=False)
        response = _AdminView.as_view()(request)
        assert response.status_code == 302
        assert response['Location'] == reverse('login')

    def test_non_admin_role_redirects_to_employees(self):
        """SSO есть, роль 'manager' → 302 на employees_list."""
        request = _make_request(has_sso=True, role='manager')
        response = _AdminView.as_view()(request)
        assert response.status_code == 302
        assert response['Location'] == '/employees/'

    def test_admin_role_passes_through(self):
        """SSO есть, роль 'admin' → 200."""
        request = _make_request(has_sso=True, role='admin')
        response = _AdminView.as_view()(request)
        assert response.status_code == 200


class TestManagerRequiredAPIView:
    """Тесты для ManagerRequiredAPIView."""

    def test_no_sso_returns_401(self):
        """Без SSO-сессии → JsonResponse 401 с полем error."""
        request = _make_request(has_sso=False)
        response = _APIView.as_view()(request)
        assert response.status_code == 401
        data = json.loads(response.content)
        assert 'error' in data

    def test_with_sso_returns_200(self):
        """С SSO-сессией → 200."""
        request = _make_request(has_sso=True)
        response = _APIView.as_view()(request)
        assert response.status_code == 200


@pytest.mark.django_db(databases=['default'])
class TestRoleBasedAccessMixin:
    """Тесты для RoleBasedAccessMixin.get_queryset."""

    def _make_view(self, *, role='manager', manager_email='manager@example.com', model=None):
        """Создаёт экземпляр view с заданной сессией и моделью."""
        from interns.models import Intern

        request = RequestFactory().get('/')
        request.session = {
            'keycloak_user': True,
            'keycloak_id': 'test-id',
            'manager_role': role,
            'manager_email': manager_email,
        }

        class _RoleView(RoleBasedAccessMixin):
            pass

        view = _RoleView()
        view.request = request
        view.model = model or Intern
        return view

    def test_admin_sees_all_objects(self, intern, intern_other):
        """Роль admin → queryset содержит всех студентов (нет фильтрации по manager_email)."""
        view = self._make_view(role='admin')
        assert view.get_queryset().count() == 2

    def test_manager_sees_only_own_objects(self, intern, intern_other):
        """Роль manager → queryset содержит только объекты своего менеджера."""
        view = self._make_view(role='manager', manager_email='manager@example.com')
        qs = view.get_queryset()
        assert qs.count() == 1
        assert qs.first().email == intern.email

    def test_model_without_manager_email_not_filtered(self, direction):
        """Модель без поля manager_email → фильтрация по роли не применяется."""
        from directions.models import Direction
        view = self._make_view(role='manager', model=Direction)
        assert view.get_queryset().count() == Direction.objects.count()

    def test_hr_sees_all_objects(self, intern, intern_other):
        """Роль hr → queryset содержит всех (как у админа, без фильтра по manager_email)."""
        view = self._make_view(role='hr')
        assert view.get_queryset().count() == 2

    def test_outstaff_sees_all_objects(self, intern, intern_other):
        view = self._make_view(role='outstaff')
        assert view.get_queryset().count() == 2


class _AdminDispatchView(AdminRequiredDispatchMixin, _OkView):
    pass


class TestAdminRequiredDispatchMixin:
    def test_manager_redirected(self):
        from django.contrib.messages.storage.fallback import FallbackStorage

        request = _make_request(has_sso=True, role='manager')
        setattr(request, '_messages', FallbackStorage(request))
        response = _AdminDispatchView.as_view()(request)
        assert response.status_code == 302


class _TranscriptionView(InterviewTranscriptionReadDispatchMixin, _OkView):
    pass


@pytest.mark.django_db(databases=['default'])
class TestInterviewTranscriptionReadDispatchMixin:
    def test_hr_allowed(self, interview):
        request = _make_request(has_sso=True, role='hr')
        request.session['manager_role'] = 'hr'
        response = _TranscriptionView.as_view()(request, pk=interview.pk)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# ExternalReferencesMixin
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
class TestExternalReferencesMixin:
    """Тесты для ExternalReferencesMixin."""

    def _make_mixin(self, email=None):
        mixin = ExternalReferencesMixin()
        mixin.manager_email = email
        return mixin

    def test_get_manager_returns_manager_object_by_email(self, manager):
        """get_manager по email → объект Manager из БД."""
        mixin = self._make_mixin(email=manager.email)
        result = mixin.get_manager()
        assert result is not None
        assert result.email == manager.email

    def test_get_manager_without_email_returns_none(self):
        """get_manager без manager_email → None."""
        mixin = self._make_mixin(email=None)
        assert mixin.get_manager() is None

    def test_get_manager_nonexistent_email_returns_none(self, db):
        """get_manager с несуществующим email → None (Manager.DoesNotExist)."""
        mixin = self._make_mixin(email='nobody@nowhere.com')
        assert mixin.get_manager() is None

    def test_get_manager_info_without_email_returns_none(self):
        """get_manager_info без manager_email → None."""
        mixin = self._make_mixin(email=None)
        assert mixin.get_manager_info() is None

    def test_get_manager_info_with_email_returns_dict(self):
        """get_manager_info с email → dict с обязательными ключами."""
        mixin = self._make_mixin(email='some@example.com')
        result = mixin.get_manager_info()
        assert result is not None
        assert result['email'] == 'some@example.com'
        assert 'name' in result
        assert 'role' in result

    def test_get_manager_info_derives_name_from_email(self):
        """Без запроса имя строится из части email до @."""
        mixin = self._make_mixin(email='ivan.petrov@example.com')
        result = mixin.get_manager_info()
        assert result['name'] == 'Ivan Petrov'

    def test_get_manager_info_with_matching_session_uses_session_data(self):
        """Если session manager_email совпадает → данные берутся из сессии."""
        mixin = self._make_mixin(email='user@example.com')
        request = MagicMock()
        request.session = {
            'keycloak_user': 'token',
            'manager_email': 'user@example.com',
            'manager_name': 'Иван Тестов',
            'manager_role': 'admin',
            'manager_username': 'ivantestov',
        }
        result = mixin.get_manager_info(request=request)
        assert result['name'] == 'Иван Тестов'
        assert result['role'] == 'admin'
        assert result['username'] == 'ivantestov'

    def test_get_manager_info_with_mismatched_session_returns_basic_info(self):
        """Если session email не совпадает → возвращается базовая информация."""
        mixin = self._make_mixin(email='other@example.com')
        request = MagicMock()
        request.session = {
            'keycloak_user': 'token',
            'manager_email': 'different@example.com',
            'manager_name': 'Другой Пользователь',
        }
        result = mixin.get_manager_info(request=request)
        assert result['email'] == 'other@example.com'
        assert result['role'] == 'manager'

    def test_manager_cached_property_returns_manager(self, manager):
        """manager cached_property возвращает объект Manager."""
        mixin = self._make_mixin(email=manager.email)
        assert mixin.manager is not None
        assert mixin.manager.email == manager.email

    def test_manager_cached_property_is_cached(self, manager):
        """manager cached_property возвращает тот же объект при повторном обращении."""
        mixin = self._make_mixin(email=manager.email)
        result1 = mixin.manager
        result2 = mixin.manager
        assert result1 == result2
