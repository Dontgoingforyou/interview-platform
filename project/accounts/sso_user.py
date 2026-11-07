"""Группы, роль и сессия после локального входа."""
import logging
from typing import Any

from django.db import transaction
from django.http import HttpRequest

from core.constants import (
    KEYCLOAK_APP_KNOWN_GROUPS,
    KEYCLOAK_GROUP_ADMIN,
    KEYCLOAK_GROUP_HR,
    KEYCLOAK_GROUP_MENTORS,
    KEYCLOAK_GROUP_OUTSTAFF,
    KEYCLOAK_GROUP_STUDENTS,
    KEYCLOAK_MANAGER_GROUPS,
    KEYCLOAK_ROLE_ADMIN,
    KEYCLOAK_ROLE_HR,
    KEYCLOAK_ROLE_MENTOR,
    KEYCLOAK_ROLE_NO_ACCESS,
    KEYCLOAK_ROLE_OUTSTAFF,
    KEYCLOAK_ROLE_STUDENT,
)

logger = logging.getLogger(__name__)


def normalize_keycloak_groups(groups: Any) -> list[str]:
    """
    Приводит список групп от SSO к списку строк (имена групп).
    Поддерживает формат ['role_admin', 'hrs'] и [{'name': 'role_admin'}, ...].
    Для путей Keycloak (/students, realm/students) добавляет последний сегмент, чтобы совпадало с KEYCLOAK_GROUP_STUDENTS.
    """
    if not groups:
        return []
    result: list[str] = []
    seen: set[str] = set()

    def add_token(s: str) -> None:
        raw = str(s).strip()
        if not raw:
            return
        tokens = [raw]
        if '/' in raw:
            # Извлекаем все непустые сегменты пути, чтобы /students/cohort-2024
            # давал и 'students', и 'cohort-2024', а не только последний сегмент.
            segments = [seg.strip() for seg in raw.split('/') if seg.strip()]
            tokens.extend(s for s in segments if s != raw)
        for t in tokens:
            if t and t not in seen:
                seen.add(t)
                result.append(t)

    for g in groups:
        if isinstance(g, str):
            add_token(g)
        elif isinstance(g, dict):
            name = g.get('name') or g.get('path') or g.get('id')
            if name:
                add_token(str(name))
        else:
            add_token(str(g))
    return result


def compute_manager_role(groups: list[str]) -> tuple[str, bool, bool, bool, bool, bool]:
    """
    Возвращает (manager_role, is_admin, is_manager, is_hr, is_outstaff, is_mentor).
    Нет ни одной известной группы приложения → no_access.
    Иначе приоритет: админ > менеджер > HR > outstaff > mentor > student; иначе 'manager'.
    """
    if not (set(groups) & KEYCLOAK_APP_KNOWN_GROUPS):
        return KEYCLOAK_ROLE_NO_ACCESS, False, False, False, False, False
    is_admin = KEYCLOAK_GROUP_ADMIN in groups
    is_hr = KEYCLOAK_GROUP_HR in groups
    is_manager = bool(set(groups) & KEYCLOAK_MANAGER_GROUPS)
    is_outstaff = KEYCLOAK_GROUP_OUTSTAFF in groups
    is_mentor = KEYCLOAK_GROUP_MENTORS in groups
    if is_admin:
        manager_role = KEYCLOAK_ROLE_ADMIN
    elif is_manager:
        manager_role = 'manager'
    elif is_hr:
        manager_role = KEYCLOAK_ROLE_HR
    elif is_outstaff:
        manager_role = KEYCLOAK_ROLE_OUTSTAFF
    elif is_mentor:
        manager_role = KEYCLOAK_ROLE_MENTOR
    elif KEYCLOAK_GROUP_STUDENTS in groups:
        manager_role = KEYCLOAK_ROLE_STUDENT
    else:
        manager_role = 'manager'
    return manager_role, is_admin, is_manager, is_hr, is_outstaff, is_mentor


def spa_path_after_pkce_login(groups: list[str]) -> str:
    """
    Первый экран React после обмена code на токены (как callback_view для Django-редиректа).
    Параметры auth_next / login_next обрабатываются на клиенте и имеют приоритет.
    """
    role, is_admin, is_manager, is_hr, is_outstaff, is_mentor = compute_manager_role(groups)
    if role == KEYCLOAK_ROLE_NO_ACCESS:
        return '/no-access'
    if is_mentor and role == KEYCLOAK_ROLE_MENTOR:
        return '/interviews-database'
    if is_admin or is_manager or is_hr or is_outstaff:
        return '/interviews'
    if KEYCLOAK_GROUP_STUDENTS in groups:
        return '/interns-portal'
    return '/interviews'


def sync_manager_if_eligible(
    user_info: dict,
    groups: list[str],
    is_admin: bool,
    is_manager: bool,
    is_hr: bool,
    is_outstaff: bool,
) -> None:
    """Создаёт или обновляет запись Manager, если пользователь в допустимых группах."""
    if not (is_admin or is_manager or is_hr or is_outstaff):
        logger.warning(
            'Пользователь %s не добавлен в таблицу менеджеров: нет admin/manager/hr/outstaff. groups=%s',
            user_info.get('email'),
            groups,
        )
        return

    from managers.models import Manager

    try:
        with transaction.atomic():
            manager, created = Manager.objects.update_or_create(
                email=user_info.get('email'),
                defaults={
                    'full_name': user_info.get('full_name', 'Менеджер'),
                    'username': user_info.get('username', ''),
                    'groups': groups,
                    'is_active': True,
                },
            )
        action = 'создан' if created else 'обновлён'
        if is_admin:
            reason = 'admin'
        elif is_outstaff:
            reason = KEYCLOAK_ROLE_OUTSTAFF
        elif is_hr:
            reason = KEYCLOAK_ROLE_HR
        else:
            reason = 'manager'
        logger.info(
            '✓ Менеджер %s %s в локальной БД (причина: %s, groups: %s)',
            user_info.get('email'),
            action,
            reason,
            groups,
        )
    except Exception as e:
        logger.error(
            '✗ Ошибка при создании/обновлении менеджера %s: %s',
            user_info.get('email'),
            e,
            exc_info=True,
        )


def apply_tokens_to_session(request: HttpRequest, tokens: dict[str, Any]) -> None:
    import time

    request.session['access_token'] = tokens['access_token']
    request.session.pop('refresh_token', None)
    request.session['token_expires_in'] = tokens.get('expires_in', 1800)
    request.session['token_timestamp'] = time.time()


def apply_user_info_to_session(
    request: HttpRequest,
    user_info: dict[str, Any],
    groups: list[str],
    manager_role: str,
) -> None:
    request.session['manager_email'] = user_info.get('email')
    request.session['manager_username'] = user_info.get('username')
    request.session['manager_name'] = user_info.get('full_name', 'Пользователь')
    request.session['manager_role'] = manager_role
    request.session['manager_groups'] = groups
    request.session['keycloak_user'] = True


def user_payload_for_client(
    user_info: dict[str, Any],
    groups: list[str],
    manager_role: str,
) -> dict[str, Any]:
    """Срез пользователя для ответа SPA (роли для ProtectedRoute)."""
    return {
        'email': user_info.get('email') or '',
        'username': user_info.get('username') or '',
        'full_name': user_info.get('full_name', 'Пользователь'),
        'manager_role': manager_role,
        'groups': groups,
    }


def complete_local_login_session(request: HttpRequest, account: dict) -> dict[str, Any]:
    """Заполняет сессию из демо-учётки, без внешнего токена."""
    user_info = {
        'email': account['email'],
        'username': account['username'],
        'full_name': account['full_name'],
        'groups': account['groups'],
    }
    groups = normalize_keycloak_groups(account.get('groups', []))
    manager_role, is_admin, is_manager, is_hr, is_outstaff, _is_mentor = compute_manager_role(groups)
    apply_user_info_to_session(request, user_info, groups, manager_role)
    sync_manager_if_eligible(user_info, groups, is_admin, is_manager, is_hr, is_outstaff)
    return user_payload_for_client(user_info, groups, manager_role)


def complete_sso_login_session(
    request: HttpRequest,
    tokens: dict[str, Any],
    user_info: dict[str, Any],
) -> dict[str, Any]:
    """
    Заполняет сессию Django после получения токенов и user_info.
    Возвращает user_payload (для единообразия с API).
    """
    groups = normalize_keycloak_groups(user_info.get('groups', []))
    manager_role, is_admin, is_manager, is_hr, is_outstaff, _is_mentor = compute_manager_role(groups)
    apply_tokens_to_session(request, tokens)
    apply_user_info_to_session(request, user_info, groups, manager_role)
    logger.info(
        'Проверка групп пользователя %s: %s (role=%s)',
        user_info.get('email'),
        groups,
        manager_role,
    )
    sync_manager_if_eligible(user_info, groups, is_admin, is_manager, is_hr, is_outstaff)
    return user_payload_for_client(user_info, groups, manager_role)
