import logging
import os
import sys
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import Http404, JsonResponse, HttpResponseForbidden
from celery.result import AsyncResult
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.views import (
    SpectacularSwaggerView,
    SpectacularAPIView,
    SpectacularRedocView,
)
from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from .mixins import ManagerRequiredMixin, ManagerRequiredAPIView
from core.constants import KEYCLOAK_MANAGER_GROUPS, KEYCLOAK_ROLE_ADMIN
from core.import_tasks import get_import_task_owner
from core.intern_utils import transliterate_name_to_cyrillic
from interns.models import Intern
from managers.models import Manager

logger = logging.getLogger(__name__)

# Группы, наличие которых даёт право на доступ к документации API (согласовано с InternPortalRequiredMixin)
API_DOCS_MANAGER_GROUPS = KEYCLOAK_MANAGER_GROUPS

API_DOCS_FORBIDDEN_MESSAGE = (
    'Доступ к документации API разрешён только менеджерам и администраторам.'
)


def _is_manager_or_admin(request):
    """Проверяет по сессии, что пользователь — менеджер или администратор (не только студент)."""
    if request.session.get('manager_role') == KEYCLOAK_ROLE_ADMIN:
        return True
    groups = set(request.session.get('manager_groups', []))
    return bool(groups & API_DOCS_MANAGER_GROUPS)


def _ensure_api_docs_debug():
    """Swagger, ReDoc и OpenAPI отдаются только при DEBUG=True."""
    if not settings.DEBUG:
        raise Http404


@extend_schema_view(
    get=extend_schema(
        tags=['Документация API'],
        summary='Интерактивная документация (Swagger UI)',
    ),
)
class ProtectedSwaggerView(SpectacularSwaggerView):
    """
    Swagger UI с защитой локальной сессией.

    Отдаётся только при DEBUG=True. Иначе 404, в том числе для менеджера.
    Доступ только для менеджеров и администраторов. Студенты (interns_portal) получают 403.
    Незалогиненные пользователи перенаправляются на страницу входа.

    authentication_classes содержат DRF-слой аутентификации (defense-in-depth).
    permission_classes = [] — намеренно: кастомный get() реализует редирект на логин
    вместо стандартного DRF 403, что даёт лучший UX для браузерных пользователей.
    """

    authentication_classes = list(API_VIEW_AUTHENTICATION_CLASSES)
    permission_classes = []

    def get(self, request, *args, **kwargs):
        _ensure_api_docs_debug()
        has_sso_auth = request.session.get('keycloak_user')
        if not has_sso_auth:
            return redirect(f"/login?next={request.path}")
        if not _is_manager_or_admin(request):
            return HttpResponseForbidden(API_DOCS_FORBIDDEN_MESSAGE)
        return super().get(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        tags=['Документация API'],
        summary='Схема OpenAPI',
    ),
)
class ProtectedSchemaView(SpectacularAPIView):
    """
    OpenAPI-схема с защитой локальной сессией.

    Отдаётся только при DEBUG=True. Иначе 404, в том числе для менеджера.
    Доступ только для менеджеров и администраторов. Студенты получают 403.
    При доступе без сессии возвращает 401 (для API-клиентов без браузера).

    authentication_classes — DRF-слой (defense-in-depth).
    permission_classes = [] — намеренно: кастомный get() возвращает 401 JSON
    вместо DRF-редиректа, что удобно для программных клиентов Swagger UI.
    """

    authentication_classes = list(API_VIEW_AUTHENTICATION_CLASSES)
    permission_classes = []

    def get(self, request, *args, **kwargs):
        _ensure_api_docs_debug()
        has_sso_auth = request.session.get('keycloak_user')
        if not has_sso_auth:
            return JsonResponse({'error': 'Требуется вход'}, status=401)
        if not _is_manager_or_admin(request):
            return JsonResponse({'error': API_DOCS_FORBIDDEN_MESSAGE}, status=403)
        return super().get(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        tags=['Документация API'],
        summary='Документация ReDoc',
    ),
)
class ProtectedRedocView(SpectacularRedocView):
    """
    ReDoc с защитой локальной сессией.

    Отдаётся только при DEBUG=True. Иначе 404, в том числе для менеджера.
    Доступ только для менеджеров и администраторов. Студенты получают 403.
    Логика как у ProtectedSwaggerView: нет сессии — редирект на логин; не менеджер/админ — 403.

    authentication_classes — DRF-слой (defense-in-depth).
    permission_classes = [] — намеренно: редирект в кастомном get().
    """

    authentication_classes = list(API_VIEW_AUTHENTICATION_CLASSES)
    permission_classes = []

    def get(self, request, *args, **kwargs):
        _ensure_api_docs_debug()
        has_sso_auth = request.session.get('keycloak_user')
        if not has_sso_auth:
            return redirect(f"/login?next={request.path}")
        if not _is_manager_or_admin(request):
            return HttpResponseForbidden(API_DOCS_FORBIDDEN_MESSAGE)
        return super().get(request, *args, **kwargs)


class GetInternDataView(ManagerRequiredAPIView, View):
    """
    Универсальное представление для получения данных студента по ID.
    Возвращает все доступные данные о студенте.
    """

    def get(self, request, *args, **kwargs):
        intern_id = request.GET.get('intern_id')
        if not intern_id:
            return JsonResponse({'error': 'ID студента не передан'}, status=400)

        try:
            intern = get_object_or_404(Intern.objects.select_related('direction'), id=intern_id)
        except Http404:
            return JsonResponse({'error': 'Студент не найден'}, status=404)

        from core.constants import KEYCLOAK_ROLE_ADMIN

        if request.session.get('manager_role') != KEYCLOAK_ROLE_ADMIN:
            session_email = request.session.get('manager_email')
            if not session_email or intern.manager_email != session_email:
                return JsonResponse({'error': 'Нет доступа к данным этого студента'}, status=403)

        direction_id = intern.direction_id
        direction_name = intern.direction.name if intern.direction else None

        manager_email = intern.manager_email
        manager_name = None
        if manager_email:
            try:
                manager = Manager.objects.get(email=manager_email)
                raw = manager.full_name or ''
                manager_name = transliterate_name_to_cyrillic(raw) or raw
            except Manager.DoesNotExist:
                pass

        # Форматируем real_interview_date в формат YYYY-MM-DD для HTML5 date input
        real_interview_date = None
        if intern.real_interview_date:
            real_interview_date = intern.real_interview_date.strftime('%Y-%m-%d')

        data = {
            'direction_id': direction_id,
            'direction_name': direction_name,
            'telegram_username': intern.telegram_username or '',
            'email': intern.email or '',
            'manager_email': manager_email,
            'manager_name': manager_name,
            'real_interview_date': real_interview_date,
        }
        return JsonResponse(data)


class ImportTaskStatusView(ManagerRequiredMixin, View):
    """
    Универсальное представление для проверки статуса задачи импорта.
    Возвращает текущий прогресс выполнения задачи Celery.
    Используется всеми модулями с асинхронным импортом.
    Требует авторизации для защиты от несанкционированного доступа.
    """

    def get(self, request, task_id):
        """
        Возвращает статус задачи импорта.

        Args:
            task_id: ID задачи Celery

        Returns:
            JsonResponse с информацией о прогрессе
        """
        task_owner = get_import_task_owner(task_id)
        if task_owner is not None:
            user_email = request.session.get('manager_email', '')
            if task_owner != user_email:
                logger.warning(
                    'Попытка доступа к чужой задаче импорта %s пользователем %s',
                    task_id,
                    user_email,
                )
                return JsonResponse({'error': 'Нет доступа к этой задаче импорта'}, status=403)

        task = AsyncResult(task_id)

        try:
            task_state = task.state
        except ValueError as e:
            # Обработка ошибки десериализации для старых задач с некорректным форматом
            logger.warning(f"Ошибка при получении статуса задачи {task_id}: {e}")
            response = {
                'state': 'FAILURE',
                'status': 'Задача завершена с устаревшим форматом данных. Попробуйте запустить импорт заново.',
                'current': 0,
                'total': 100
            }
            return JsonResponse(response)

        if task_state == 'PENDING':
            # Задача еще не начала выполняться
            response = {
                'state': task.state,
                'status': 'Ожидание начала импорта...',
                'current': 0,
                'total': 100
            }
        elif task_state == 'PROGRESS':
            # Задача выполняется
            response = {
                'state': task_state,
                'status': task.info.get('status', ''),
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 100)
            }
        elif task_state == 'SUCCESS':
            # Задача успешно завершена
            result = task.result
            response = {
                'state': task_state,
                'status': 'Импорт завершен успешно',
                'current': 100,
                'total': 100,
                'result': result
            }
        elif task_state == 'FAILURE':
            # Произошла ошибка
            response = {
                'state': task_state,
                'status': str(task.info),
                'current': 0,
                'total': 100
            }
        else:
            # Другие состояния
            response = {
                'state': task_state,
                'status': str(task.info) if task.info else 'Неизвестное состояние',
                'current': 0,
                'total': 100
            }

        return JsonResponse(response)


@method_decorator(ensure_csrf_cookie, name='get')
class ReactSPAView(View):
    """Отдаёт React SPA для всех маршрутов, не обработанных Django.

    Аналог catch-all в nginx: всё что не совпало с Django URL-паттернами
    перенаправляется в React Router, который сам разберётся какой компонент показать.

    ensure_csrf_cookie — выставляет куку csrftoken при первом GET, чтобы axios мог слать
    X-CSRFToken на POST к API (иначе 403 от CsrfViewMiddleware).
    """

    def get(self, request, *args, **kwargs):
        is_testing = os.getenv('DJANGO_TESTING') == '1' or 'test' in sys.argv or 'pytest' in sys.modules
        return render(request, 'spa.html', {'is_testing': is_testing})
