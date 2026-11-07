"""Общие хелперы для HTTP MCP-тулов."""
from __future__ import annotations

import json
from typing import Any

from accounts.sso_user import compute_manager_role
from core.constants import (
    KEYCLOAK_MANAGER_GROUPS,
    KEYCLOAK_ROLE_HR,
    KEYCLOAK_ROLE_MENTOR,
    KEYCLOAK_ROLE_OUTSTAFF,
    KEYCLOAK_ROLE_STUDENT,
    KEYCLOAK_ROLE_NO_ACCESS,
)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50

# Тулы только для admin (как «нет в меню» у менеджера/HR).
ADMIN_ONLY_TOOLS = frozenset({
    'list_offers',
    'get_offer',
    'create_offer',
    'update_offer',
    'delete_offer',
    'list_debts',
    'get_debt',
    'create_debt',
    'update_debt',
    'delete_debt',
    'add_debt_payment',
    'get_managers_kpi',
    'get_admin_developers',
    'create_kb_section',
    'update_kb_section',
    'delete_kb_section',
    'create_kb_article',
    'update_kb_article',
    'delete_kb_article',
    'update_intern',
    'delete_intern',
    'delete_company',
    'delete_sad_intern',
})

# Mentor (не admin): продуктовый allowlist.
MENTOR_ALLOWLIST = frozenset({
    'list_interviews_database',
    'get_interview',
    'get_transcription_status',
    'get_transcription_text',
    'start_transcription',
})


def tool_text(payload: Any, *, is_error: bool = False) -> dict[str, Any]:
    return {
        'content': [{'type': 'text', 'text': json.dumps(payload, ensure_ascii=False, default=str)}],
        'isError': is_error,
    }


def page_bounds(arguments: dict[str, Any]) -> tuple[int, int]:
    try:
        page = max(int(arguments.get('page') or 1), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(arguments.get('page_size') or DEFAULT_PAGE_SIZE)
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    start = (page - 1) * page_size
    return start, page_size


def deny(message: str = 'Недостаточно прав') -> dict[str, Any]:
    return tool_text({'error': message}, is_error=True)


def validation_error(errors: Any) -> dict[str, Any]:
    return tool_text({'error': 'Ошибка валидации', 'details': errors}, is_error=True)


def is_admin_user(user: Any) -> bool:
    return bool(getattr(user, 'is_admin', False) or getattr(user, 'is_superuser', False))


def is_hr_or_outstaff(user: Any) -> bool:
    return bool(getattr(user, 'is_hr', False) or getattr(user, 'is_outstaff', False))


def is_mentor_only(user: Any) -> bool:
    """Ментор без админских прав."""
    return bool(getattr(user, 'is_mentor', False) and not is_admin_user(user))


def can_interview_write(user: Any) -> bool:
    if is_admin_user(user):
        return True
    groups = list(getattr(user, 'groups', None) or [])
    role, _, _, _, _, _ = compute_manager_role(groups)
    if role in (
        KEYCLOAK_ROLE_HR,
        KEYCLOAK_ROLE_OUTSTAFF,
        KEYCLOAK_ROLE_MENTOR,
        KEYCLOAK_ROLE_STUDENT,
        KEYCLOAK_ROLE_NO_ACCESS,
    ):
        return False
    return role in ('admin', 'manager') or bool(set(groups) & KEYCLOAK_MANAGER_GROUPS)


def can_company_edit(user: Any) -> bool:
    if is_admin_user(user):
        return True
    if is_hr_or_outstaff(user):
        return False
    user_groups = set(getattr(user, 'groups', []) or [])
    return bool(user_groups & KEYCLOAK_MANAGER_GROUPS)


def can_transcribe(user: Any) -> bool:
    return is_admin_user(user) or bool(getattr(user, 'is_mentor', False))


def tool_visible_for_user(name: str, user: Any) -> bool:
    if is_admin_user(user):
        return True
    if name in ADMIN_ONLY_TOOLS:
        return False
    if is_mentor_only(user):
        return name in MENTOR_ALLOWLIST
    return True


def require_tool_access(name: str, user: Any) -> dict[str, Any] | None:
    """None если доступ есть, иначе ответ isError."""
    if tool_visible_for_user(name, user):
        return None
    return deny('Тул недоступен для вашей роли')
