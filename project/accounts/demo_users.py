"""
Демо-учётки локального входа.

Пароли публичные: это локальные демо-учётки.
"""
import secrets
from typing import TypedDict


class DemoAccount(TypedDict):
    username: str
    password: str
    email: str
    full_name: str
    groups: list[str]


DEMO_USERS: tuple[DemoAccount, ...] = (
    {
        'username': 'admin',
        'password': 'demo-admin',
        'email': 'anna.ivanova@example.com',
        'full_name': 'Анна Иванова',
        'groups': ['role_admin'],
    },
    {
        'username': 'manager',
        'password': 'demo-manager',
        'email': 'ivan.petrov@example.com',
        'full_name': 'Иван Петров',
        'groups': ['employment-managers'],
    },
    {
        'username': 'student',
        'password': 'demo-student',
        'email': 'student@example.com',
        'full_name': 'Студент Демонов',
        'groups': ['students'],
    },
)


def authenticate_demo(username: str, password: str) -> DemoAccount | None:
    """Возвращает демо-учётку или None."""
    login = (username or '').strip()
    secret = password or ''
    for account in DEMO_USERS:
        if account['username'] != login:
            continue
        if secrets.compare_digest(account['password'], secret):
            return account
        return None
    return None
