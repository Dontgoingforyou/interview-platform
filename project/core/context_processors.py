"""Контекст-процессоры для шаблонов."""

from core.constants import (
    KEYCLOAK_ROLE_ADMIN,
    KEYCLOAK_ROLE_HR,
    KEYCLOAK_ROLE_MENTOR,
    KEYCLOAK_ROLE_NO_ACCESS,
    KEYCLOAK_ROLE_OUTSTAFF,
    KEYCLOAK_ROLE_STUDENT,
)


def student_session(request):
    """
    Добавляет is_student: True, если пользователь в группе students (Keycloak).
    Используется для выхода при закрытии вкладки и других ограничений для студентов.
    """
    groups = request.session.get('manager_groups') or []
    return {'is_student': 'students' in groups}


def can_write(request):
    """
    Добавляет can_write: False для ролей HR и outstaff (только просмотр и фильтрация).
    Админ и менеджеры всегда имеют can_write=True.
    Используется в шаблонах для скрытия кнопок «Добавить», «Редактировать», «Удалить», «Импорт».
    """
    role = request.session.get('manager_role', 'manager')
    if role in (
        KEYCLOAK_ROLE_HR,
        KEYCLOAK_ROLE_OUTSTAFF,
        KEYCLOAK_ROLE_MENTOR,
        KEYCLOAK_ROLE_STUDENT,
        KEYCLOAK_ROLE_NO_ACCESS,
    ):
        return {'can_write': False}
    return {'can_write': role in (KEYCLOAK_ROLE_ADMIN, 'manager')}
