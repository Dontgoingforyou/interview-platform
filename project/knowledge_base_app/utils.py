"""
Вспомогательные функции для приложения База знаний
"""
from django.http import JsonResponse
from typing import Dict, Any, Optional


def json_success(message: str = None, data: Dict[str, Any] = None, **kwargs) -> JsonResponse:
    """
    Создать успешный JSON ответ
    """
    response: dict[str, Any] = {'success': True}

    if message:
        response['message'] = message

    if data:
        response.update(data)

    if kwargs:
        response.update(kwargs)

    return JsonResponse(response)


def json_error(error: str, status: int = 400, **kwargs) -> JsonResponse:
    """
    Создать JSON ответ с ошибкой
    """
    response = {
        'success': False,
        'error': error
    }

    if kwargs:
        response.update(kwargs)

    return JsonResponse(response, status=status)


def get_section_by_id(sections: list, section_id: str) -> Optional[Dict[str, Any]]:
    """
    Найти раздел по ID в списке разделов
    """
    for section in sections:
        if section['id'] == section_id:
            return section
    return None


def is_admin(request) -> bool:
    """
    Проверить, является ли пользователь администратором
    """
    return request.session.get('manager_role') == 'admin'
