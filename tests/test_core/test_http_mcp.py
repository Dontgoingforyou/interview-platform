"""Тесты HTTP MCP локального входа."""
import json
from unittest.mock import patch

import pytest

from core.mcp_tools import TOOLS
from core.mcp_tools._common import ADMIN_ONLY_TOOLS, MENTOR_ALLOWLIST


def _mcp(method, params=None, req_id=1):
    payload = {'jsonrpc': '2.0', 'id': req_id, 'method': method}
    if params is not None:
        payload['params'] = params
    return payload


def _call_payload(response):
    body = response.json()['result']
    return json.loads(body['content'][0]['text']), body.get('isError', False)


def _call(api_client, name, arguments=None):
    response = api_client.post(
        '/mcp',
        _mcp('tools/call', {'name': name, 'arguments': arguments or {}}),
        format='json',
    )
    assert response.status_code == 200
    return _call_payload(response)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestHttpMcpAuth:
    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.post('/mcp', _mcp('tools/list'), format='json')
        assert response.status_code == 401

    def test_user_without_role_returns_403(self, api_client, api_anon_user):
        api_client.force_authenticate(user=api_anon_user)
        response = api_client.post('/mcp', _mcp('tools/list'), format='json')
        assert response.status_code == 403


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestHttpMcpProtocol:
    def test_initialize_returns_server_info(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post(
            '/mcp',
            _mcp('initialize', {'protocolVersion': '2025-03-26'}),
            format='json',
        )
        assert response.status_code == 200
        body = response.json()
        assert body['jsonrpc'] == '2.0'
        assert body['result']['serverInfo']['name'] == 'imp'
        assert 'tools' in body['result']['capabilities']

    def test_tools_list_admin_sees_all_registered(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post('/mcp', _mcp('tools/list'), format='json')
        assert response.status_code == 200
        names = {tool['name'] for tool in response.json()['result']['tools']}
        assert names == set(TOOLS.keys())
        assert 'list_interviews' in names
        assert 'list_offers' in names
        assert 'vector_search' in names

    def test_vector_tool_absent_when_app_disabled(self):
        import importlib

        from django.conf import settings

        import core.mcp_tools as registry

        original_apps = list(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS = [app for app in original_apps if app != 'vector_search']
        try:
            importlib.reload(registry)
            assert 'vector_search' not in registry.TOOLS
        finally:
            settings.INSTALLED_APPS = original_apps
            importlib.reload(registry)
        assert 'vector_search' in registry.TOOLS

    def test_tools_list_manager_hides_admin_only(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post('/mcp', _mcp('tools/list'), format='json')
        names = {tool['name'] for tool in response.json()['result']['tools']}
        assert 'list_interviews' in names
        assert 'list_interns' in names
        assert names.isdisjoint(ADMIN_ONLY_TOOLS)

    def test_tools_list_mentor_allowlist(self, api_client, api_mentor_user):
        api_client.force_authenticate(user=api_mentor_user)
        response = api_client.post('/mcp', _mcp('tools/list'), format='json')
        names = {tool['name'] for tool in response.json()['result']['tools']}
        assert names == MENTOR_ALLOWLIST

    def test_unknown_method_is_jsonrpc_error(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        response = api_client.post('/mcp', _mcp('nope'), format='json')
        assert response.status_code == 200
        assert response.json()['error']['code'] == -32601


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestHttpMcpTools:
    def test_list_interviews_respects_manager_scope(
        self, api_client, api_manager_user, interview, interview_other
    ):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/mcp',
            _mcp('tools/call', {'name': 'list_interviews', 'arguments': {}}),
            format='json',
        )
        assert response.status_code == 200
        payload, is_error = _call_payload(response)
        assert is_error is False
        ids = [item['id'] for item in payload['results']]
        assert interview.id in ids
        assert interview_other.id not in ids

    def test_get_interview_returns_own_record(
        self, api_client, api_manager_user, interview
    ):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/mcp',
            _mcp(
                'tools/call',
                {'name': 'get_interview', 'arguments': {'id': interview.id}},
            ),
            format='json',
        )
        assert response.status_code == 200
        payload, is_error = _call_payload(response)
        assert is_error is False
        assert payload['id'] == interview.id

    def test_get_interview_hides_foreign_record(
        self, api_client, api_manager_user, interview_other
    ):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/mcp',
            _mcp(
                'tools/call',
                {'name': 'get_interview', 'arguments': {'id': interview_other.id}},
            ),
            format='json',
        )
        assert response.status_code == 200
        assert response.json()['result']['isError'] is True

    def test_list_interns_respects_manager_scope(
        self, api_client, api_manager_user, intern, intern_other
    ):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/mcp',
            _mcp('tools/call', {'name': 'list_interns', 'arguments': {}}),
            format='json',
        )
        assert response.status_code == 200
        payload, is_error = _call_payload(response)
        assert is_error is False
        ids = [item['id'] for item in payload['results']]
        assert intern.id in ids
        assert intern_other.id not in ids
        assert all('password_hh' not in item for item in payload['results'])

    def test_get_intern_returns_own_record(self, api_client, api_manager_user, intern):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/mcp',
            _mcp('tools/call', {'name': 'get_intern', 'arguments': {'id': intern.id}}),
            format='json',
        )
        assert response.status_code == 200
        payload, is_error = _call_payload(response)
        assert is_error is False
        assert payload['id'] == intern.id

    def test_manager_cannot_call_admin_only_offer(
        self, api_client, api_manager_user
    ):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/mcp',
            _mcp('tools/call', {'name': 'list_offers', 'arguments': {}}),
            format='json',
        )
        assert response.status_code == 200
        assert response.json()['result']['isError'] is True

    def test_hr_cannot_create_interview(self, api_client, api_hr_user, intern, direction):
        api_client.force_authenticate(user=api_hr_user)
        response = api_client.post(
            '/mcp',
            _mcp(
                'tools/call',
                {
                    'name': 'create_interview',
                    'arguments': {
                        'intern': intern.id,
                        'direction_id': direction.id,
                        'interview_type': 'tech',
                    },
                },
            ),
            format='json',
        )
        assert response.status_code == 200
        assert response.json()['result']['isError'] is True

    def test_manager_create_interview(
        self, api_client, api_manager_user, intern, direction, company
    ):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/mcp',
            _mcp(
                'tools/call',
                {
                    'name': 'create_interview',
                    'arguments': {
                        'intern': intern.id,
                        'direction_id': direction.id,
                        'company_id': company.id,
                        'interview_type': 'tech',
                    },
                },
            ),
            format='json',
        )
        assert response.status_code == 200
        payload, is_error = _call_payload(response)
        assert is_error is False
        assert payload['id']
        assert payload.get('intern') == intern.id

    def test_manager_cannot_update_intern(self, api_client, api_manager_user, intern):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/mcp',
            _mcp(
                'tools/call',
                {
                    'name': 'update_intern',
                    'arguments': {'id': intern.id, 'full_name': 'Новое Имя'},
                },
            ),
            format='json',
        )
        assert response.status_code == 200
        assert response.json()['result']['isError'] is True

    def test_list_companies(self, api_client, api_manager_user, company):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/mcp',
            _mcp('tools/call', {'name': 'list_companies', 'arguments': {}}),
            format='json',
        )
        payload, is_error = _call_payload(response)
        assert is_error is False
        assert any(row['id'] == company.id for row in payload['results'])

    def test_list_directions(self, api_client, api_manager_user, direction):
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.post(
            '/mcp',
            _mcp('tools/call', {'name': 'list_directions', 'arguments': {}}),
            format='json',
        )
        payload, is_error = _call_payload(response)
        assert is_error is False
        assert any(row['id'] == direction.id for row in payload['results'])

    def test_mentor_denied_list_interns(self, api_client, api_mentor_user):
        api_client.force_authenticate(user=api_mentor_user)
        response = api_client.post(
            '/mcp',
            _mcp('tools/call', {'name': 'list_interns', 'arguments': {}}),
            format='json',
        )
        assert response.json()['result']['isError'] is True


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestHttpMcpAdminPaths:
    """Счастливые пути тулов, которые иначе не попадают в прогон."""

    def test_reference_lists(self, api_client, api_admin_user, company, direction, manager):
        api_client.force_authenticate(user=api_admin_user)
        companies, err = _call(api_client, 'list_companies', {'q': 'Google', 'page': 'x', 'page_size': 'y'})
        assert err is False
        assert companies['results'][0]['id'] == company.id

        directions, err = _call(api_client, 'list_directions', {'q': 'Backend'})
        assert err is False
        assert directions['results'][0]['id'] == direction.id

        one, err = _call(api_client, 'get_direction', {'id': direction.id})
        assert err is False
        assert one['id'] == direction.id

        _metrics, err = _call(api_client, 'get_directions_metrics', {})
        assert err is False

        managers, err = _call(api_client, 'list_managers', {'q': 'Алексей'})
        assert err is False
        assert managers['results'][0]['email'] == manager.email

        _analytics, err = _call(api_client, 'get_managers_analytics', {})
        assert err is False

        developers, err = _call(api_client, 'get_developers_stats', {'direction_id': direction.id})
        assert err is False
        assert developers['count'] == len(developers['results'])

        employees, err = _call(api_client, 'list_employees_managers', {})
        assert err is False
        assert any(row['email'] == manager.email for row in employees['results'])

        board, err = _call(api_client, 'get_manager_board', {'email': manager.email})
        assert err is False
        assert board['manager']['email'] == manager.email

    def test_company_crud(self, api_client, api_admin_user, api_manager_user, api_hr_user):
        api_client.force_authenticate(user=api_hr_user)
        _payload, err = _call(api_client, 'update_company', {'id': 1, 'name': 'Нет'})
        assert err is True

        api_client.force_authenticate(user=api_manager_user)
        created, err = _call(api_client, 'create_company', {'name': 'MCP Company'})
        assert err is False
        company_id = created['id']

        updated, err = _call(api_client, 'update_company', {'id': company_id, 'name': 'MCP Company 2'})
        assert err is False
        assert updated['name'] == 'MCP Company 2'

        api_client.force_authenticate(user=api_admin_user)
        deleted, err = _call(api_client, 'delete_company', {'id': company_id})
        assert err is False
        assert deleted == {'deleted': True, 'id': company_id}

    def test_intern_offer_debt_and_sad(self, api_client, api_admin_user, direction, intern):
        api_client.force_authenticate(user=api_admin_user)
        created, err = _call(api_client, 'create_intern', {
            'full_name': 'MCP Студент',
            'direction_id': direction.id,
            'email': 'mcp-student@example.com',
            'hiring_hr': 'HR1',
            'responsible_hr': 'HR2',
            'group': 'GR-MCP',
            'type_of_training': 'internal',
        })
        assert err is False
        intern_id = created['id']

        updated, err = _call(api_client, 'update_intern', {'id': intern_id, 'full_name': 'MCP Студент 2'})
        assert err is False
        assert updated['full_name'] == 'MCP Студент 2'

        offer, err = _call(api_client, 'create_offer', {
            'intern': intern.id,
            'direction_id': direction.id,
            'month': 10,
            'year': 2026,
            'amount': '100000.00',
        })
        assert err is False
        offer_id = offer['id']
        offers, err = _call(api_client, 'list_offers', {})
        assert err is False
        assert any(row['id'] == offer_id for row in offers['results'])
        got, err = _call(api_client, 'get_offer', {'id': offer_id})
        assert err is False
        assert got['id'] == offer_id
        changed, err = _call(api_client, 'update_offer', {'id': offer_id, 'amount': '120000.00'})
        assert err is False
        assert str(changed['amount']) in ('120000.00', '120000')
        removed, err = _call(api_client, 'delete_offer', {'id': offer_id})
        assert err is False
        assert removed['id'] == offer_id

        debt, err = _call(api_client, 'create_debt', {
            'intern': intern.id,
            'direction_id': direction.id,
            'total_amount': '10000.00',
        })
        assert err is False
        debt_id = debt['id']
        debts, err = _call(api_client, 'list_debts', {})
        assert err is False
        assert any(row['id'] == debt_id for row in debts['results'])
        got_debt, err = _call(api_client, 'get_debt', {'id': debt_id})
        assert err is False
        assert got_debt['id'] == debt_id
        paid, err = _call(api_client, 'add_debt_payment', {
            'id': debt_id,
            'amount': '1000.00',
            'month': 10,
            'year': 2026,
        })
        assert err is False
        assert paid['debt_id'] == debt_id
        updated_debt, err = _call(api_client, 'update_debt', {'id': debt_id, 'paid_amount': '1000.00'})
        assert err is False
        assert updated_debt['id'] == debt_id
        deleted_debt, err = _call(api_client, 'delete_debt', {'id': debt_id})
        assert err is False
        assert deleted_debt['id'] == debt_id

        sad, err = _call(api_client, 'create_sad_intern', {'intern': intern.id, 'note': 'mcp'})
        assert err is False
        sad_id = sad['id']
        sad_list, err = _call(api_client, 'list_sad_interns', {})
        assert err is False
        assert any(row['id'] == sad_id for row in sad_list['results'])
        got_sad, err = _call(api_client, 'get_sad_intern', {'id': sad_id})
        assert err is False
        assert got_sad['id'] == sad_id
        edited, err = _call(api_client, 'update_sad_intern', {'id': sad_id, 'note': 'mcp-2'})
        assert err is False
        assert edited['note'] == 'mcp-2'
        deleted_sad, err = _call(api_client, 'delete_sad_intern', {'id': sad_id})
        assert err is False
        assert deleted_sad['id'] == sad_id

        deleted_intern, err = _call(api_client, 'delete_intern', {'id': intern_id})
        assert err is False
        assert deleted_intern['id'] == intern_id

    def test_interview_database_and_transcription(self, api_client, api_admin_user, interview):
        api_client.force_authenticate(user=api_admin_user)
        updated, err = _call(api_client, 'update_interview', {
            'id': interview.id,
            'interview_type': 'tech',
        })
        assert err is False
        assert updated['id'] == interview.id

        interview.link = 'https://example.com/rec'
        interview.save(update_fields=['link'])
        listed, err = _call(api_client, 'list_interviews_database', {})
        assert err is False
        assert any(row['id'] == interview.id for row in listed['results'])

        status, err = _call(api_client, 'get_transcription_status', {'id': interview.id})
        assert err is False
        assert status['status'] == 'none'

        _text, text_err = _call(api_client, 'get_transcription_text', {'id': interview.id})
        assert text_err is True

        _started, start_err = _call(api_client, 'start_transcription', {'id': interview.id})
        assert start_err is True

    def test_admin_reports(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        missing, err = _call(api_client, 'get_managers_kpi', {})
        assert err is True
        assert 'date_from' in missing['error']

        _bad, err = _call(api_client, 'get_managers_kpi', {'date_from': 'вчера', 'date_to': 'завтра'})
        assert err is True

        report, err = _call(api_client, 'get_managers_kpi', {
            'date_from': '2026-01-01',
            'date_to': '2026-01-31',
            'min_kpi': 3,
        })
        assert err is False
        assert report['date_from'] == '2026-01-01'
        assert report['results'] == []

        developers, err = _call(api_client, 'get_admin_developers', {'show_hidden': True})
        assert err is False
        assert developers['total_active'] == 0

    def test_knowledge_base_crud(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        section, err = _call(api_client, 'create_kb_section', {
            'section_id': 'mcp-cov',
            'title': 'MCP',
        })
        assert err is False
        assert section['section_id'] == 'mcp-cov'

        sections, err = _call(api_client, 'list_kb_sections', {})
        assert err is False
        assert any(row['id'] == 'mcp-cov' for row in sections['results'])

        renamed, err = _call(api_client, 'update_kb_section', {
            'section_id': 'mcp-cov',
            'title': 'MCP 2',
        })
        assert err is False
        assert renamed['title'] == 'MCP 2'

        article, err = _call(api_client, 'create_kb_article', {
            'section_id': 'mcp-cov',
            'title': 'Заметка',
            'content': 'mcp-note',
        })
        assert err is False
        filename = article['filename']

        articles, err = _call(api_client, 'list_kb_articles', {'section_id': 'mcp-cov'})
        assert err is False
        assert articles['results'][0]['filename'] == filename

        detail, err = _call(api_client, 'get_kb_article', {
            'section_id': 'mcp-cov',
            'filename': filename,
        })
        assert err is False
        assert detail['title'] == 'Заметка'

        found, err = _call(api_client, 'search_kb', {'q': 'mcp-note'})
        assert err is False
        assert any(row['title'] == 'Заметка' for row in found['results'])

        edited, err = _call(api_client, 'update_kb_article', {
            'section_id': 'mcp-cov',
            'filename': filename,
            'content': 'новый текст',
        })
        assert err is False
        assert 'новый текст' in edited['markdown']

        removed_article, err = _call(api_client, 'delete_kb_article', {
            'section_id': 'mcp-cov',
            'filename': filename,
        })
        assert err is False
        assert removed_article['deleted'] is True

        removed_section, err = _call(api_client, 'delete_kb_section', {'section_id': 'mcp-cov'})
        assert err is False
        assert removed_section['deleted'] is True

    def test_vector_search(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        with patch(
            'core.mcp_tools.vector_search.EmbeddingService.semantic_search',
            return_value=([], 12),
        ):
            payload, err = _call(api_client, 'vector_search', {'query': 'стажёр'})
        assert err is False
        assert payload['query'] == 'стажёр'
        assert payload['total_found'] == 0
        assert payload['search_time_ms'] == 12

        with patch(
            'core.mcp_tools.vector_search.EmbeddingService.semantic_search',
            side_effect=RuntimeError('поиск недоступен'),
        ):
            _payload, err = _call(api_client, 'vector_search', {'query': 'стажёр'})
        assert err is True
