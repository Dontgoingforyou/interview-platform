import logging
from django.db.models import Q

from core.constants import (
    COMPANY_OPTIONS,
    KEYCLOAK_MANAGER_GROUPS,
    KEYCLOAK_ROLE_ADMIN,
    KEYCLOAK_ROLE_HR,
    KEYCLOAK_ROLE_MENTOR,
    KEYCLOAK_ROLE_OUTSTAFF,
)
from core.date_utils import parse_datetime_for_interview  # noqa: F401

logger = logging.getLogger('interview_import')


def get_or_create_company(name):
    """
    Находит или создаёт компанию в основной БД и возвращает её ID.
    Нормализует название через map_company_name и устанавливает is_bigtech.
    """
    from companies.models import Company

    if not name or not isinstance(name, str):
        return None

    canonical_name = map_company_name(name)
    is_bigtech = canonical_name is not None
    effective_name = canonical_name if canonical_name else name

    if not effective_name.strip():
        return None

    company, created = Company.objects.get_or_create(
        name=effective_name,
        defaults={'is_bigtech': is_bigtech},
    )
    action = 'Создана' if created else 'Найдена'
    logger.info(f"{action} компания: '{effective_name}' (исходное: '{name}', ID: {company.id}, is_bigtech: {is_bigtech})")
    return company.id


def map_company_name(name):
    """
    Нормализует название компании к каноническому виду.

    Порядок поиска:
    1. Точное совпадение с Company.name в БД.
    2. Совпадение в COMPANY_OPTIONS (обратная совместимость со статичным словарём).
    3. Совпадение в Company.aliases в БД (псевдонимы, заданные администратором).

    Возвращает каноническое имя или None если совпадение не найдено.
    """
    if not name or not isinstance(name, str):
        return None
    name_clean = name.strip()
    if not name_clean:
        return None

    # 1. Точное совпадение с именем компании в БД
    from companies.models import Company
    try:
        company = Company.objects.get(name=name_clean)
        return company.name
    except Company.DoesNotExist:
        pass
    except Company.MultipleObjectsReturned:
        pass

    # 2. Поиск в статичном словаре COMPANY_OPTIONS
    for canonical, variants in COMPANY_OPTIONS.items():
        if name_clean in variants:
            return canonical

    # 3. Поиск среди псевдонимов компаний в БД
    for company in Company.objects.exclude(aliases=''):
        if name_clean in company.get_aliases_list():
            return company.name

    return None


def session_may_access_interview_transcription(request, interview_pk: int) -> bool:
    """
    Доступ к веб-эндпоинтам транскрипции (сессия SSO): админ и HR/outstaff/mentor — любой id;
    менеджер из KEYCLOAK_MANAGER_GROUPS — только «своё» собеседование.
    """
    if not getattr(request, 'session', None) or not request.session.get('keycloak_user'):
        return False
    role = request.session.get('manager_role')
    if role == KEYCLOAK_ROLE_ADMIN:
        return True
    if role in (KEYCLOAK_ROLE_HR, KEYCLOAK_ROLE_OUTSTAFF, KEYCLOAK_ROLE_MENTOR):
        return True
    if role != 'manager':
        return False
    groups = set(request.session.get('manager_groups') or [])
    if not (groups & KEYCLOAK_MANAGER_GROUPS):
        return False
    email = request.session.get('manager_email')
    if not email:
        return False
    from interviews.models import Interview

    return Interview.objects.filter(pk=interview_pk).filter(
        Q(manager_email=email) |
        Q(manager_email__isnull=True, intern__manager_email=email)
    ).exists()
