import logging
import re
from typing import TYPE_CHECKING, Any

from core.constants import KEYCLOAK_MANAGER_GROUPS, KEYCLOAK_ROLE_ADMIN
from core.intern_utils import find_intern_by_name, transliterate_name_to_cyrillic
from interns.models import Intern

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger('interns_portal')


def is_staff_or_manager_session(
    manager_role: str | None,
    manager_groups: list | None,
) -> bool:
    """Админ или менеджер — без автосвязки по ФИО."""
    if manager_role == KEYCLOAK_ROLE_ADMIN:
        return True
    groups = set(manager_groups or [])
    return bool(groups & KEYCLOAK_MANAGER_GROUPS)


def _intern_by_sso_email(email: str) -> Intern | None:
    """Сначала почта входа на портал, затем личный email из карточки intern."""
    by_corporate = Intern.objects.filter(corporate_email__iexact=email).first()
    if by_corporate:
        return by_corporate
    return Intern.objects.filter(email__iexact=email).first()


def _collapse_cyr_fio(value: str) -> str:
    """Сравнение ФИО без ё/ь/ъ: Артём ↔ Артем, Игорь ↔ Игор."""
    return value.lower().replace('ё', 'е').replace('ь', '').replace('ъ', '')


def _collapsed_lookup_token(part: str) -> str:
    """Токен для SQL: «Игорь» → «Игор», чтобы найти и запись без мягкого знака."""
    collapsed = _collapse_cyr_fio(part)
    if not collapsed:
        return part
    return collapsed[:1].upper() + collapsed[1:]


def _intern_by_collapsed_fio(full_name_ru: str) -> Intern | None:
    parts = [p for p in re.split(r'[\s\-]+', full_name_ru.strip()) if p]
    if len(parts) < 2:
        return None
    hits: list[Intern] = []
    for intern in Intern.objects.filter(full_name__icontains=_collapsed_lookup_token(parts[0])):
        hay = _collapse_cyr_fio(intern.full_name)
        if all(_collapse_cyr_fio(p) in hay for p in parts):
            hits.append(intern)
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        logger.warning(f'InternPortal: несколько студентов по ФИО без ь/ё: {full_name_ru!r}')
    return None


def _intern_by_fio_variants(full_name: str) -> Intern | None:
    """Поиск по ФИО: как есть, транслит, без ё, без ь."""
    intern = find_intern_by_name(full_name)
    if intern:
        return intern
    name_no_spaces = full_name.replace(' ', '').replace('-', '')
    if not full_name or not name_no_spaces.isascii():
        return None
    full_name_ru = transliterate_name_to_cyrillic(full_name)
    if full_name_ru == full_name:
        return None
    intern = find_intern_by_name(full_name_ru)
    if intern:
        logger.info(
            f'InternPortal: автосвязка через транслитерацию: {full_name!r} → {full_name_ru!r}',
        )
        return intern
    without_yo = full_name_ru.replace('ё', 'е').replace('Ё', 'Е')
    if without_yo != full_name_ru:
        intern = find_intern_by_name(without_yo)
        if intern:
            logger.info(
                f'InternPortal: автосвязка через транслитерацию без ё: {full_name!r} → {without_yo!r}',
            )
            return intern
    intern = _intern_by_collapsed_fio(full_name_ru)
    if intern:
        logger.info(
            f'InternPortal: автосвязка через ФИО без ь/ё: {full_name!r} → {intern.full_name!r}',
        )
        return intern
    return None


def _resolve_intern_portal(
    manager_email: str,
    full_name_raw: str,
    *,
    skip_fio_autolink: bool,
) -> Intern | None:
    """
    Ядро привязки: corporate_email / email intern → ФИО (если не skip_fio_autolink).
    SSO больше не возвращает внешний id, поэтому используем email и ФИО.
    """
    email = (manager_email or '').strip()
    if email:
        by_email = _intern_by_sso_email(email)
        if by_email:
            logger.info(f'InternPortal: студент найден, id={by_email.pk}')
            return by_email

    if skip_fio_autolink:
        return None

    full_name = re.sub(r'\s+', ' ', (full_name_raw or '').strip()).strip()
    intern = _intern_by_fio_variants(full_name)

    if intern is None:
        logger.warning(
            f'InternPortal: студент с ФИО {full_name!r} не найден — автосвязка невозможна',
        )
        return None

    # Обновляем corporate_email если он был пустой
    if email and not intern.corporate_email:
        intern.corporate_email = email
        intern.save(update_fields=['corporate_email'])
        logger.info(f'InternPortal: добавлена почта входа для студента {intern.full_name!r}')

    return intern


def get_intern_for_current_user(request: 'HttpRequest') -> Intern | None:
    """Intern для текущего пользователя по данным Django-сессии SSO."""
    skip_fio = is_staff_or_manager_session(
        request.session.get('manager_role'),
        request.session.get('manager_groups'),
    )
    return _resolve_intern_portal(
        request.session.get('manager_email', ''),
        request.session.get('manager_name', ''),
        skip_fio_autolink=skip_fio,
    )


def get_intern_for_portal_user(user: Any) -> Intern | None:
    """
    Intern для пользователя сессии DRF.
    Админы и менеджеры — без автосвязки по ФИО.
    """
    skip_fio = bool(
        getattr(user, 'is_admin', False)
        or (set(getattr(user, 'groups', []) or []) & KEYCLOAK_MANAGER_GROUPS)
    )
    return _resolve_intern_portal(
        getattr(user, 'email', '') or '',
        getattr(user, 'full_name', '') or '',
        skip_fio_autolink=skip_fio,
    )
