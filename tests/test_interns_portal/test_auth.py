"""
Тесты для InternPortalRequiredMixin.

Покрывает:
- Редирект на логин без SSO-сессии.
- Редирект на логин с SSO, но без группы students.
- Доступ разрешён при наличии SSO + группа students.
"""
from django.http import HttpResponse
from django.test import RequestFactory
from django.views import View

from core.mixins import InternPortalRequiredMixin


class _OkView(InternPortalRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('OK', status=200)


def _make_request(*, has_sso=True, groups=None, manager_role=None):
    """Создаёт GET-запрос с нужными параметрами сессии."""
    request = RequestFactory().get('/')
    groups = groups or []
    session = {'manager_groups': groups}
    if manager_role is not None:
        session['manager_role'] = manager_role
    else:
        session['manager_role'] = 'admin' if 'role_admin' in groups else 'manager'
    if has_sso:
        session['keycloak_user'] = True
        session['keycloak_id'] = 'test-keycloak-id'
    request.session = session
    return request


class TestInternPortalRequiredMixin:
    """Тесты InternPortalRequiredMixin."""

    def test_redirects_without_sso(self):
        """Без SSO — редирект на логин."""
        request = _make_request(has_sso=False, groups=['students'])
        response = _OkView.as_view()(request)
        assert response.status_code == 302
        assert '/accounts/login/' in response['Location'] or response['Location'].endswith('/login/')

    def test_redirects_with_sso_but_no_student_group(self):
        """SSO есть, но пользователь не в группе students — редирект."""
        request = _make_request(has_sso=True, groups=['employment-managers'])
        response = _OkView.as_view()(request)
        assert response.status_code == 302

    def test_redirects_with_empty_groups(self):
        """SSO есть, группы пустые — редирект."""
        request = _make_request(has_sso=True, groups=[])
        response = _OkView.as_view()(request)
        assert response.status_code == 302

    def test_allows_student(self):
        """Студент с группой students — доступ разрешён."""
        request = _make_request(has_sso=True, groups=['students'])
        response = _OkView.as_view()(request)
        assert response.status_code == 200
        assert response.content == b'OK'

    def test_allows_student_with_multiple_groups(self):
        """Студент с несколькими группами — доступ разрешён."""
        request = _make_request(has_sso=True, groups=['students', 'some-other'])
        response = _OkView.as_view()(request)
        assert response.status_code == 200

    def test_redirects_admin_with_students_group(self):
        """Админ с группой students редиректится в основное приложение, не на портал."""
        from django.urls import reverse

        request = _make_request(has_sso=True, groups=['students', 'role_admin'])
        response = _OkView.as_view()(request)
        assert response.status_code == 302
        assert response['Location'] == reverse('interview_list')

    def test_redirects_manager_with_students_group(self):
        """Менеджер (employment-managers) с группой students редиректится в основное приложение."""
        from django.urls import reverse

        request = _make_request(has_sso=True, groups=['students', 'employment-managers'])
        response = _OkView.as_view()(request)
        assert response.status_code == 302
        assert response['Location'] == reverse('interview_list')
