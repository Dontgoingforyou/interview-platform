"""POST /api/auth/login/"""
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_login_admin_sets_session():
    client = APIClient()
    response = client.post(
        '/api/auth/login/',
        {'username': 'admin', 'password': 'demo-admin'},
        format='json',
    )
    assert response.status_code == 200
    body = response.data
    assert body['user']['email'] == 'anna.ivanova@example.com'
    assert body['user']['manager_role'] == 'admin'
    assert client.session['manager_email'] == 'anna.ivanova@example.com'
    assert 'access_token' not in client.session


@pytest.mark.django_db
def test_login_wrong_password():
    client = APIClient()
    response = client.post(
        '/api/auth/login/',
        {'username': 'admin', 'password': 'nope'},
        format='json',
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_student_role():
    client = APIClient()
    response = client.post(
        '/api/auth/login/',
        {'username': 'student', 'password': 'demo-student'},
        format='json',
    )
    assert response.status_code == 200
    assert response.data['user']['manager_role'] == 'student'
    assert response.data['redirect_after_login'] == '/interns-portal'
