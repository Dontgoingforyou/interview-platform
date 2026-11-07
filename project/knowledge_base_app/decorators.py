"""
Декораторы для приложения База знаний
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .utils import json_error, is_admin


def admin_required(redirect_to='knowledge_base:index'):
    """
    Декоратор для проверки прав администратора (для обычных view)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            if not is_admin(request):
                messages.error(request, 'У вас нет прав для выполнения этого действия')
                return redirect(redirect_to)
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required_api(view_func):
    """
    Декоратор для проверки прав администратора (для API view)
    Возвращает JSON ответ с ошибкой
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not is_admin(request):
            return json_error('Недостаточно прав', status=403)
        return view_func(self, request, *args, **kwargs)
    return wrapper
