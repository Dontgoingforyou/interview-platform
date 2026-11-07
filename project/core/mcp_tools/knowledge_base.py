"""MCP-тулы: база знаний."""
from __future__ import annotations

from typing import Any

from knowledge_base_app.managers import KnowledgeBaseManager
from knowledge_base_app.serializers import (
    KBArticleCreateSerializer,
    KBArticleDetailSerializer,
    KBArticleListItemSerializer,
    KBArticleUpdateSerializer,
    KBSearchResultSerializer,
    KBSectionCreateSerializer,
    KBSectionReadSerializer,
    KBSectionUpdateSerializer,
)

from core.mcp_tools._common import deny, is_admin_user, tool_text, validation_error


def tool_list_kb_sections(request, arguments: dict[str, Any]) -> dict[str, Any]:
    kb = KnowledgeBaseManager()
    sections = kb.get_sections()
    return tool_text({'results': KBSectionReadSerializer(sections, many=True).data})


def tool_get_kb_article(request, arguments: dict[str, Any]) -> dict[str, Any]:
    section_id = arguments.get('section_id')
    filename = arguments.get('filename')
    if not section_id or not filename:
        return tool_text({'error': 'Нужны section_id и filename'}, is_error=True)
    kb = KnowledgeBaseManager()
    article = kb.get_article(str(section_id), str(filename))
    if not article:
        return tool_text({'error': 'Статья не найдена'}, is_error=True)
    return tool_text(KBArticleDetailSerializer(article).data)


def tool_search_kb(request, arguments: dict[str, Any]) -> dict[str, Any]:
    query = arguments.get('q') or ''
    kb = KnowledgeBaseManager()
    results = kb.search_articles(str(query))
    return tool_text({'results': KBSearchResultSerializer(results, many=True).data})


def tool_list_kb_articles(request, arguments: dict[str, Any]) -> dict[str, Any]:
    section_id = arguments.get('section_id')
    if not section_id:
        return tool_text({'error': 'Нужен section_id'}, is_error=True)
    kb = KnowledgeBaseManager()
    articles = kb.get_articles(str(section_id))
    return tool_text({'results': KBArticleListItemSerializer(articles, many=True).data})


def tool_create_kb_section(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('Создание разделов БЗ доступно только администраторам')
    ser = KBSectionCreateSerializer(data=arguments)
    if not ser.is_valid():
        return validation_error(ser.errors)
    data = ser.validated_data
    kb = KnowledgeBaseManager()
    try:
        kb.create_section(
            data['section_id'],
            data['title'],
            data.get('description') or '',
            data.get('icon') or '📁',
        )
    except ValueError as exc:
        return tool_text({'error': str(exc)}, is_error=True)
    return tool_text({'section_id': data['section_id'], 'title': data['title']})


def tool_update_kb_section(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('Изменение разделов БЗ доступно только администраторам')
    section_id = arguments.get('section_id')
    if not section_id:
        return tool_text({'error': 'Нужен section_id'}, is_error=True)
    ser = KBSectionUpdateSerializer(data={k: v for k, v in arguments.items() if k != 'section_id'}, partial=True)
    if not ser.is_valid():
        return validation_error(ser.errors)
    data = {k: v for k, v in ser.validated_data.items() if v is not None}
    kb = KnowledgeBaseManager()
    try:
        kb.update_section(
            str(section_id),
            title=data.get('title'),
            description=data.get('description'),
            icon=data.get('icon'),
        )
    except ValueError as exc:
        return tool_text({'error': str(exc)}, is_error=True)
    for s in kb.get_sections():
        if s['id'] == section_id:
            return tool_text(KBSectionReadSerializer(s).data)
    return tool_text({'error': 'Раздел не найден'}, is_error=True)


def tool_delete_kb_section(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('Удаление разделов БЗ доступно только администраторам')
    section_id = arguments.get('section_id')
    if not section_id:
        return tool_text({'error': 'Нужен section_id'}, is_error=True)
    kb = KnowledgeBaseManager()
    try:
        kb.delete_section(str(section_id))
    except ValueError as exc:
        return tool_text({'error': str(exc)}, is_error=True)
    return tool_text({'deleted': True, 'section_id': section_id})


def tool_create_kb_article(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('Создание статей БЗ доступно только администраторам')
    section_id = arguments.get('section_id')
    if not section_id:
        return tool_text({'error': 'Нужен section_id'}, is_error=True)
    ser = KBArticleCreateSerializer(data=arguments)
    if not ser.is_valid():
        return validation_error(ser.errors)
    kb = KnowledgeBaseManager()
    try:
        filename = kb.create_article(
            str(section_id),
            ser.validated_data['title'],
            ser.validated_data.get('content') or '',
        )
    except ValueError as exc:
        return tool_text({'error': str(exc)}, is_error=True)
    return tool_text({'filename': filename, 'title': ser.validated_data['title']})


def tool_update_kb_article(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('Изменение статей БЗ доступно только администраторам')
    section_id = arguments.get('section_id')
    filename = arguments.get('filename')
    if not section_id or not filename:
        return tool_text({'error': 'Нужны section_id и filename'}, is_error=True)
    ser = KBArticleUpdateSerializer(
        data={k: v for k, v in arguments.items() if k not in ('section_id', 'filename')},
        partial=True,
    )
    if not ser.is_valid():
        return validation_error(ser.errors)
    title = ser.validated_data.get('title')
    content = ser.validated_data.get('content')
    if title is None and content is None:
        return tool_text({'error': 'Укажите title и/или content'}, is_error=True)
    kb = KnowledgeBaseManager()
    if content is not None:
        ok = kb.save_article(str(section_id), str(filename), content, title=title)
    else:
        existing = kb.get_article(str(section_id), str(filename))
        if not existing:
            return tool_text({'error': 'Статья не найдена'}, is_error=True)
        ok = kb.save_article(str(section_id), str(filename), existing.get('content') or '', title=title)
    if not ok:
        return tool_text({'error': 'Не удалось сохранить статью'}, is_error=True)
    article = kb.get_article(str(section_id), str(filename))
    return tool_text(KBArticleDetailSerializer(article).data)


def tool_delete_kb_article(request, arguments: dict[str, Any]) -> dict[str, Any]:
    if not is_admin_user(request.user):
        return deny('Удаление статей БЗ доступно только администраторам')
    section_id = arguments.get('section_id')
    filename = arguments.get('filename')
    if not section_id or not filename:
        return tool_text({'error': 'Нужны section_id и filename'}, is_error=True)
    kb = KnowledgeBaseManager()
    try:
        kb.delete_article(str(section_id), str(filename))
    except ValueError as exc:
        return tool_text({'error': str(exc)}, is_error=True)
    return tool_text({'deleted': True, 'section_id': section_id, 'filename': filename})


TOOLS: dict[str, dict[str, Any]] = {
    'list_kb_sections': {
        'description': 'Список разделов базы знаний портала.',
        'inputSchema': {'type': 'object', 'properties': {}},
        'handler': tool_list_kb_sections,
    },
    'list_kb_articles': {
        'description': 'Список статей раздела БЗ портала.',
        'inputSchema': {
            'type': 'object',
            'properties': {'section_id': {'type': 'string'}},
            'required': ['section_id'],
        },
        'handler': tool_list_kb_articles,
    },
    'get_kb_article': {
        'description': 'Статья базы знаний портала по разделу и filename.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'section_id': {'type': 'string'},
                'filename': {'type': 'string'},
            },
            'required': ['section_id', 'filename'],
        },
        'handler': tool_get_kb_article,
    },
    'search_kb': {
        'description': 'Полнотекстовый поиск по базе знаний портала.',
        'inputSchema': {
            'type': 'object',
            'properties': {'q': {'type': 'string'}},
        },
        'handler': tool_search_kb,
    },
    'create_kb_section': {
        'description': 'Создать раздел БЗ (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'section_id': {'type': 'string'},
                'title': {'type': 'string'},
                'description': {'type': 'string'},
                'icon': {'type': 'string'},
            },
            'required': ['section_id', 'title'],
        },
        'handler': tool_create_kb_section,
    },
    'update_kb_section': {
        'description': 'Обновить раздел БЗ (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'section_id': {'type': 'string'}},
            'required': ['section_id'],
        },
        'handler': tool_update_kb_section,
    },
    'delete_kb_section': {
        'description': 'Удалить раздел БЗ (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {'section_id': {'type': 'string'}},
            'required': ['section_id'],
        },
        'handler': tool_delete_kb_section,
    },
    'create_kb_article': {
        'description': 'Создать статью БЗ (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'section_id': {'type': 'string'},
                'title': {'type': 'string'},
                'content': {'type': 'string'},
            },
            'required': ['section_id', 'title'],
        },
        'handler': tool_create_kb_article,
    },
    'update_kb_article': {
        'description': 'Обновить статью БЗ (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'section_id': {'type': 'string'},
                'filename': {'type': 'string'},
                'title': {'type': 'string'},
                'content': {'type': 'string'},
            },
            'required': ['section_id', 'filename'],
        },
        'handler': tool_update_kb_article,
    },
    'delete_kb_article': {
        'description': 'Удалить статью БЗ (только администратор).',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'section_id': {'type': 'string'},
                'filename': {'type': 'string'},
            },
            'required': ['section_id', 'filename'],
        },
        'handler': tool_delete_kb_article,
    },
}
