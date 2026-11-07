"""
HTTP MCP пет-проекта.

POST /mcp принимает JSON-RPC: initialize, tools/list, tools/call.
Клиент ходит с сессией локального входа.
"""
from __future__ import annotations

import logging
from typing import Any

from core.mcp_tools import TOOLS
from core.mcp_tools._common import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    require_tool_access,
    tool_visible_for_user,
)

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = '2025-03-26'
SERVER_NAME = 'imp'


def jsonrpc_result(req_id: Any, result: Any) -> dict[str, Any]:
    return {'jsonrpc': '2.0', 'id': req_id, 'result': result}


def jsonrpc_error(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {'jsonrpc': '2.0', 'id': req_id, 'error': {'code': code, 'message': message}}


def list_tool_specs(user: Any = None) -> list[dict[str, Any]]:
    specs = []
    for name, spec in TOOLS.items():
        if user is not None and not tool_visible_for_user(name, user):
            continue
        specs.append({
            'name': name,
            'description': spec['description'],
            'inputSchema': spec['inputSchema'],
        })
    return specs


def handle_mcp_request(request, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get('jsonrpc') != '2.0':
        return jsonrpc_error(None, -32600, 'Invalid Request')

    req_id = payload.get('id')
    method = payload.get('method')
    params = payload.get('params') or {}
    if not isinstance(params, dict):
        params = {}

    if method == 'initialize':
        return jsonrpc_result(
            req_id,
            {
                'protocolVersion': PROTOCOL_VERSION,
                'capabilities': {'tools': {}},
                'serverInfo': {'name': SERVER_NAME, 'version': '1.0.0'},
            },
        )
    if method == 'notifications/initialized':
        return jsonrpc_result(req_id, {})
    if method == 'ping':
        return jsonrpc_result(req_id, {})
    if method == 'tools/list':
        return jsonrpc_result(req_id, {'tools': list_tool_specs(request.user)})
    if method == 'tools/call':
        name = params.get('name')
        arguments = params.get('arguments') or {}
        if not isinstance(arguments, dict):
            arguments = {}
        spec = TOOLS.get(name)
        if spec is None:
            return jsonrpc_error(req_id, -32602, f'Unknown tool: {name}')
        denied = require_tool_access(name, request.user)
        if denied is not None:
            return jsonrpc_result(req_id, denied)
        try:
            return jsonrpc_result(req_id, spec['handler'](request, arguments))
        except Exception:
            logger.exception('Ошибка MCP tools/call name=%s', name)
            return jsonrpc_error(req_id, -32603, 'Internal error')
    return jsonrpc_error(req_id, -32601, f'Method not found: {method}')


# Совместимость имён констант
__all__ = [
    'PROTOCOL_VERSION',
    'SERVER_NAME',
    'DEFAULT_PAGE_SIZE',
    'MAX_PAGE_SIZE',
    'TOOLS',
    'handle_mcp_request',
    'list_tool_specs',
    'jsonrpc_result',
    'jsonrpc_error',
]
