"""Форма локального входа и выход."""
import pytest


@pytest.mark.django_db
def test_login_page_redirects_to_portal(client):
    response = client.get('/accounts/login/')
    assert response.status_code == 302
    assert response['Location'] == '/login'


@pytest.mark.django_db
def test_login_post_admin_redirects(client):
    response = client.post('/accounts/login/', {'username': 'admin', 'password': 'demo-admin'})
    assert response.status_code == 302
    assert response['Location'].endswith('/interviews')
    assert client.session['manager_role'] == 'admin'


@pytest.mark.django_db
def test_login_post_bad_password(client):
    response = client.post('/accounts/login/', {'username': 'admin', 'password': 'bad'})
    assert response.status_code == 302
    assert response['Location'] == '/login'


@pytest.mark.django_db
def test_logout_clears_session(client):
    client.post('/accounts/login/', {'username': 'manager', 'password': 'demo-manager'})
    response = client.get('/accounts/logout/')
    assert response.status_code == 302
    assert 'manager_email' not in client.session


@pytest.mark.django_db
def test_logout_beacon_returns_204(client):
    client.post('/accounts/login/', {'username': 'manager', 'password': 'demo-manager'})
    response = client.post('/accounts/logout-beacon/')
    assert response.status_code == 204
    assert 'manager_email' not in client.session
