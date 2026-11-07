"""Юнит-тесты accounts.sso_user: нормализация групп Keycloak, редирект после PKCE."""

import pytest

from accounts.sso_user import (
    compute_manager_role,
    normalize_keycloak_groups,
    spa_path_after_pkce_login,
)
from core.constants import (
    KEYCLOAK_GROUP_STUDENTS,
    KEYCLOAK_ROLE_MENTOR,
    KEYCLOAK_ROLE_NO_ACCESS,
    KEYCLOAK_ROLE_STUDENT,
)


@pytest.mark.parametrize(
    ('raw', 'expected_contains_students'),
    [
        (['students'], True),
        (['/students'], True),
        (['/realm/students'], True),
        (['/students/cohort-2024'], True),
        (['/students/batch/2025'], True),
        ([{'path': '/students'}], True),
        ([{'name': 'students'}], True),
        (['employment-managers'], False),
    ],
)
def test_normalize_keycloak_groups_students_detection(raw, expected_contains_students):
    groups = normalize_keycloak_groups(raw)
    assert (KEYCLOAK_GROUP_STUDENTS in groups) is expected_contains_students


def test_compute_manager_role_pure_student():
    role, is_admin, is_manager, is_hr, is_outstaff, is_mentor = compute_manager_role(['students'])
    assert role == KEYCLOAK_ROLE_STUDENT
    assert not is_admin
    assert not is_manager
    assert not is_hr
    assert not is_outstaff
    assert not is_mentor


def test_compute_manager_role_pure_mentor():
    role, is_admin, is_manager, is_hr, is_outstaff, is_mentor = compute_manager_role(['mentors'])
    assert role == KEYCLOAK_ROLE_MENTOR
    assert not is_admin
    assert not is_manager
    assert not is_hr
    assert not is_outstaff
    assert is_mentor


def test_compute_manager_role_mentor_with_employment_gets_manager():
    role, _, is_manager, _, _, is_mentor = compute_manager_role(
        ['mentors', 'employment-managers'],
    )
    assert role == 'manager'
    assert is_manager
    assert is_mentor


def test_spa_path_after_pkce_login_mentor():
    assert spa_path_after_pkce_login(['mentors']) == '/interviews-database'


def test_compute_manager_role_no_access_empty_groups():
    role, *_ = compute_manager_role([])
    assert role == KEYCLOAK_ROLE_NO_ACCESS


def test_compute_manager_role_no_access_unknown_groups_only():
    role, *_ = compute_manager_role(['only-unknown-group'])
    assert role == KEYCLOAK_ROLE_NO_ACCESS


def test_spa_path_after_pkce_login_no_access():
    assert spa_path_after_pkce_login([]) == '/no-access'


def test_spa_path_after_pkce_login_student():
    assert spa_path_after_pkce_login(['students']) == '/interns-portal'


def test_spa_path_after_pkce_login_manager():
    assert spa_path_after_pkce_login(['employment-managers']) == '/interviews'
