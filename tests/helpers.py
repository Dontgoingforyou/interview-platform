"""
Вспомогательные утилиты для тестов.

Не содержит фикстур pytest — только вспомогательные функции и фабрики,
которые можно импортировать напрямую в любой тестовый модуль.
"""
from accounts.authentication import KeycloakUser


def get_list_table_body(html_content):
    """Извлекает содержимое первого <tbody> из HTML (список/таблица).

    Используется, когда нужно проверить отсутствие строки в списке, но имя
    может присутствовать в других блоках страницы (метрики, подзаголовки).
    Если таблицы нет (пустой список) — возвращает пустую строку.
    """
    if '<tbody>' not in html_content or '</tbody>' not in html_content:
        return ''
    parts = html_content.split('<tbody>', 1)
    if len(parts) != 2:
        return ''
    return parts[1].split('</tbody>', 1)[0]


def get_api_results(response):
    """Возвращает список результатов из API-ответа.

    Поддерживает пагинированный ответ {'results': [...]} и плоский список.
    """
    data = response.data
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    return data


def make_keycloak_user(
    email='manager@example.com',
    groups=None,
    is_admin=False,
    *,
    full_name=None,
):
    """Создаёт KeycloakUser с указанными параметрами.

    Устанавливает атрибут pk (используется DRF UserRateThrottle для кэш-ключа).

    Args:
        email: email пользователя
        groups: список групп Keycloak; если None — определяется по is_admin
        is_admin: True → добавляет группу role_admin и роль admin
        full_name: необязательное ФИО
    """
    if groups is None:
        groups = ['role_admin', 'employment-managers'] if is_admin else ['employment-managers']
    info = {
        'email': email,
        'username': 'testuser',
        'full_name': full_name if full_name is not None else 'Тест Тестов',
        'groups': groups,
    }
    user = KeycloakUser(info)
    user.pk = email
    return user
