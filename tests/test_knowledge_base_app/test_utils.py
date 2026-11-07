"""Тесты knowledge_base_app.utils."""
import json

import pytest
from django.test import RequestFactory

from knowledge_base_app.utils import get_section_by_id, is_admin, json_error, json_success


class TestJsonHelpers:
    def test_json_success_minimal(self):
        response = json_success()
        data = json.loads(response.content)
        assert data['success'] is True
        assert response.status_code == 200

    def test_json_success_with_message_and_data(self):
        response = json_success(message='Готово', data={'id': 1}, extra='x')
        data = json.loads(response.content)
        assert data['message'] == 'Готово'
        assert data['id'] == 1
        assert data['extra'] == 'x'

    def test_json_error_default_status(self):
        response = json_error('Ошибка')
        data = json.loads(response.content)
        assert data['success'] is False
        assert data['error'] == 'Ошибка'
        assert response.status_code == 400

    def test_json_error_custom_status_and_kwargs(self):
        response = json_error('Forbidden', status=403, code='no_access')
        data = json.loads(response.content)
        assert response.status_code == 403
        assert data['code'] == 'no_access'


class TestGetSectionById:
    def test_found_returns_section(self):
        sections = [{'id': 'a', 'title': 'A'}, {'id': 'b', 'title': 'B'}]
        assert get_section_by_id(sections, 'b') == {'id': 'b', 'title': 'B'}

    def test_missing_returns_none(self):
        assert get_section_by_id([{'id': 'a'}], 'z') is None


@pytest.mark.django_db(databases=['default'])
class TestIsAdmin:
    def test_admin_session(self):
        request = RequestFactory().get('/')
        request.session = {'manager_role': 'admin'}
        assert is_admin(request) is True

    def test_manager_session(self):
        request = RequestFactory().get('/')
        request.session = {'manager_role': 'manager'}
        assert is_admin(request) is False
