from urllib.parse import quote

from django.http import HttpResponse
from django.shortcuts import redirect

from .demo_users import authenticate_demo
from .sso_user import complete_local_login_session, spa_path_after_pkce_login

PORTAL_LOGIN_PATH = '/login'


def _is_safe_next_url(url: str) -> bool:
    if not url or not url.startswith('/') or url.startswith('//'):
        return False
    unsafe_prefixes = ('/login', '/logout', '/accounts/login', '/accounts/logout', '/no-access')
    return not any(url.startswith(prefix) for prefix in unsafe_prefixes)


def _portal_login_redirect(next_url: str):
    """Единственное окно входа — страница портала."""
    if next_url and _is_safe_next_url(next_url):
        return redirect(f'{PORTAL_LOGIN_PATH}?next={quote(next_url, safe="/")}')
    return redirect(PORTAL_LOGIN_PATH)


def logout_view(request):
    """Выход: очистка сессии и возврат на страницу входа портала."""
    request.session.flush()
    return redirect(PORTAL_LOGIN_PATH)


def logout_beacon_view(request):
    """Выход при закрытии вкладки. Только очищает сессию и возвращает 204."""
    request.session.flush()
    return HttpResponse(status=204)


def login_view(request):
    """Старый адрес входа. Окно одно: страница портала /login."""
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if request.method == 'POST':
        account = authenticate_demo(
            request.POST.get('username', ''),
            request.POST.get('password', ''),
        )
        if account is not None:
            payload = complete_local_login_session(request, account)
            if next_url and _is_safe_next_url(next_url):
                return redirect(next_url)
            return redirect(spa_path_after_pkce_login(payload['groups']))
    return _portal_login_redirect(next_url)
