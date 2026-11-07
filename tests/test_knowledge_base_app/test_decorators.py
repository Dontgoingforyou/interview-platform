"""Тесты knowledge_base_app.decorators."""
import json

import pytest
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse
from django.test import RequestFactory

from knowledge_base_app.decorators import admin_required, admin_required_api


@pytest.mark.django_db(databases=['default'])
class TestAdminRequired:
    def test_non_admin_redirects_with_message(self):
        class View:
            @admin_required(redirect_to='interview_list')
            def get(self, request):
                return HttpResponse('ok', status=200)

        request = RequestFactory().get('/')
        request.session = {'manager_role': 'manager'}
        setattr(request, '_messages', FallbackStorage(request))
        response = View().get(request)

        assert response.status_code == 302
        msgs = list(get_messages(request))
        assert len(msgs) == 1
        assert 'прав' in str(msgs[0]).lower()

    def test_admin_calls_view(self):
        class View:
            @admin_required()
            def get(self, request):
                return HttpResponse('ok', status=200)

        request = RequestFactory().get('/')
        request.session = {'manager_role': 'admin'}
        response = View().get(request)

        assert response.status_code == 200
        assert response.content == b'ok'


@pytest.mark.django_db(databases=['default'])
class TestAdminRequiredApi:
    def test_non_admin_returns_403_json(self):
        class View:
            @admin_required_api
            def get(self, request):
                return HttpResponse('ok', status=200)

        request = RequestFactory().get('/')
        request.session = {'manager_role': 'manager'}
        response = View().get(request)

        assert response.status_code == 403
        data = json.loads(response.content)
        assert data['success'] is False
        assert 'прав' in data['error'].lower()

    def test_admin_calls_view(self):
        class View:
            @admin_required_api
            def get(self, request):
                return HttpResponse('ok', status=200)

        request = RequestFactory().get('/')
        request.session = {'manager_role': 'admin'}
        response = View().get(request)

        assert response.status_code == 200
