import logging
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
from django.urls import reverse
from django.db import DatabaseError
from django.utils.functional import cached_property
from core.constants import (
    KEYCLOAK_GROUP_STUDENTS,
    KEYCLOAK_MANAGER_GROUPS,
    KEYCLOAK_ROLE_ADMIN,
    KEYCLOAK_ROLE_HR,
    KEYCLOAK_ROLE_OUTSTAFF,
)

logger = logging.getLogger(__name__)


class ExternalReferencesMixin:
    """
    Миксин для безопасного получения связанных объектов (Manager) из БД.

    Использует @cached_property для предотвращения дублирующихся запросов
    в рамках одного request/объекта.
    """

    def get_manager(self):
        """
        Получает Manager из основной БД по manager_email.
        """
        if hasattr(self, 'manager_email') and self.manager_email:
            from managers.models import Manager
            try:
                return Manager.objects.get(email=self.manager_email)
            except Manager.DoesNotExist:
                return None
            except (DatabaseError, Exception) as e:
                logger.error('Ошибка получения менеджера (manager_email в контексте view): %s', e)
                return None
        return None

    def get_manager_info(self, request=None):
        """
        Получает информацию о менеджере из сессии.

        Args:
            request: HTTP request для получения данных из сессии

        Returns:
            dict с полями: email, name, role, username
        """
        if hasattr(self, 'manager_email') and self.manager_email:
            # Если передан request, пытаемся взять данные из сессии
            if request and request.session.get('keycloak_user'):
                session_email = request.session.get('manager_email')
                # Если email совпадает с текущим пользователем - берем из сессии
                if session_email == self.manager_email:
                    return {
                        'email': self.manager_email,
                        'name': request.session.get('manager_name', 'Менеджер'),
                        'role': request.session.get('manager_role', 'manager'),
                        'username': request.session.get('manager_username', ''),
                    }

            # Если request не передан или email не совпадает, возвращаем базовую инфо
            return {
                'email': self.manager_email,
                'name': self.manager_email.split('@')[0].replace('.', ' ').title(),
                'role': 'manager',
            }

        return None

    @cached_property
    def manager(self):
        """Cached property для получения Manager."""
        return self.get_manager()


class InternPortalRequiredMixin:
    """Требует сессию входа и группу students.
    Админы и менеджеры не допускаются — редирект в основное приложение."""

    def dispatch(self, request, *args, **kwargs):
        has_sso_auth = request.session.get('keycloak_user')
        is_student = KEYCLOAK_GROUP_STUDENTS in (request.session.get('manager_groups') or [])
        if not (has_sso_auth and is_student):
            return redirect('login')
        # Админ или менеджер не должны видеть портал студента
        if request.session.get('manager_role') == KEYCLOAK_ROLE_ADMIN:
            return redirect('interview_list')
        groups = set(request.session.get('manager_groups', []))
        if groups & KEYCLOAK_MANAGER_GROUPS:
            return redirect('interview_list')
        return super().dispatch(request, *args, **kwargs)


class ManagerRequiredMixin:
    """Требует локальный вход в сессии."""

    def dispatch(self, request, *args, **kwargs):
        # Проверяем наличие сессии входа
        has_sso_auth = request.session.get('keycloak_user')

        if not has_sso_auth:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin:
    """Требует прав администратора (демо-роль admin)."""

    def dispatch(self, request, *args, **kwargs):
        has_sso_auth = request.session.get('keycloak_user')
        if not has_sso_auth:
            return redirect('login')
        if request.session.get('manager_role') != KEYCLOAK_ROLE_ADMIN:
            return redirect('/employees/')
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredDispatchMixin:
    """
    Проверка сессии и роли admin для dispatch.
    Редирект при отсутствии прав — через get_admin_redirect_url().
    """
    admin_required_message = 'Доступ только для администратора'

    def get_admin_redirect_url(self, request):
        """URL для редиректа при отсутствии прав админа. Переопределяется в подклассах."""
        return '/employees/'

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('keycloak_user'):
            return redirect('login')
        if request.session.get('manager_role') != KEYCLOAK_ROLE_ADMIN:
            messages.error(request, self.admin_required_message)
            return redirect(self.get_admin_redirect_url(request))
        return super().dispatch(request, *args, **kwargs)


class InterviewTranscriptionReadDispatchMixin:
    """
    Сессия и dispatch для транскрипции в браузере.

    Администратор, HR и outstaff — любое собеседование по id (как в API).
    Менеджер из групп KEYCLOAK_MANAGER_GROUPS — только своё (manager_email / intern.manager_email).
    """
    admin_required_message = (
        'Транскрипция доступна администратору, HR, outstaff или менеджеру (только свои собеседования).'
    )

    def get_admin_redirect_url(self, request):
        return '/employees/'

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('keycloak_user'):
            return redirect('login')
        pk = kwargs.get('pk')
        try:
            pk_int = int(pk)
        except (TypeError, ValueError):
            messages.error(request, 'Некорректный идентификатор собеседования.')
            return redirect(self.get_admin_redirect_url(request))

        role = request.session.get('manager_role')
        if role == KEYCLOAK_ROLE_ADMIN:
            return super().dispatch(request, *args, **kwargs)
        if role in (KEYCLOAK_ROLE_HR, KEYCLOAK_ROLE_OUTSTAFF):
            return super().dispatch(request, *args, **kwargs)
        if role == 'manager':
            groups = set(request.session.get('manager_groups') or [])
            if not (groups & KEYCLOAK_MANAGER_GROUPS):
                messages.error(request, self.admin_required_message)
                return redirect(self.get_admin_redirect_url(request))
            from interviews.utils import session_may_access_interview_transcription
            if not session_may_access_interview_transcription(request, pk_int):
                messages.error(request, 'Нет доступа к транскрипции этого собеседования.')
                return redirect(reverse('interview_list'))
            return super().dispatch(request, *args, **kwargs)

        messages.error(request, self.admin_required_message)
        return redirect(self.get_admin_redirect_url(request))


class ManagerRequiredAPIView:
    """Требует локальный вход для API."""

    def dispatch(self, request, *args, **kwargs):
        # Проверяем наличие сессии входа
        has_sso_auth = bool(request.session.get('keycloak_user'))

        if not has_sso_auth:
            return JsonResponse({'error': 'Требуется авторизация'}, status=401)
        return super().dispatch(request, *args, **kwargs)


class RoleBasedAccessMixin(ManagerRequiredMixin):
    """
    Фильтрует queryset: админ — все, менеджер — только свои.

    Автоматически проверяет наличие поля manager_email у модели.
    Если поля нет - не применяет фильтрацию.
    """

    def get_queryset(self):
        qs = super().get_queryset() if hasattr(super(), 'get_queryset') else self.model.objects.all()

        # Проверяем наличие полей в модели
        if not hasattr(self, 'model') or not hasattr(self.model, '_meta'):
            return qs

        field_names = [f.name for f in self.model._meta.get_fields()]

        # Если у модели нет manager_email, возвращаем queryset без фильтрации
        if 'manager_email' not in field_names:
            return qs

        # Стандартная фильтрация по ролям
        role = self.request.session.get('manager_role', 'manager')

        if role == KEYCLOAK_ROLE_ADMIN:
            return qs
        if role in (KEYCLOAK_ROLE_HR, KEYCLOAK_ROLE_OUTSTAFF):
            return qs

        # Фильтруем по manager_email для обычных менеджеров
        manager_email = self.request.session.get('manager_email')
        if manager_email:
            qs = qs.filter(manager_email=manager_email)

        return qs
