"""
API-представления для управления недельными статусами студентов.

Эндпоинты:
    GET    /api/employees/weekly-statuses/          — список статусов
    POST   /api/employees/weekly-statuses/          — создание/обновление статуса
    GET    /api/employees/weekly-statuses/{id}/     — детали статуса
    PATCH  /api/employees/weekly-statuses/{id}/     — обновление статуса
    DELETE /api/employees/weekly-statuses/{id}/     — удаление (только admin)

Доступ:
    - GET: любой аутентифицированный менеджер или администратор
    - POST/PATCH: менеджер (своих студентов) или администратор
    - DELETE: только администратор

Фильтры:
    - intern_id: ID студента
    - week_start: дата начала недели (YYYY-MM-DD)
    - absence_status: статус отсутствия
"""
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from rest_framework.exceptions import PermissionDenied

from accounts.permissions import IsAdminRole, IsManagerOrAdmin, IsReadOnlyHROutstaff
from core.logging_mixins import ApiCRUDLoggingMixin

from ..models import InternWeeklyStatus
from ..serializers import InternWeeklyStatusCreateUpdateSerializer, InternWeeklyStatusSerializer


class InternWeeklyStatusViewSet(ApiCRUDLoggingMixin, viewsets.ModelViewSet):
    """
    ViewSet для управления недельными статусами студентов.

    Менеджер видит/редактирует статусы только своих студентов.
    Администратор видит/редактирует всё.
    """

    api_logger_name = 'employees.intern_weekly_status'

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminRole()]
        return [IsManagerOrAdmin(), IsReadOnlyHROutstaff()]

    def perform_create(self, serializer):
        self._validate_intern_ownership(serializer.validated_data.get('intern'))
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._validate_intern_ownership(serializer.instance.intern)
        super().perform_update(serializer)

    def _validate_intern_ownership(self, intern):
        if intern is None:
            return
        user = self.request.user
        if getattr(user, 'is_admin', False) or getattr(user, 'is_superuser', False):
            return
        email = getattr(user, 'email', None)
        if not email or intern.manager_email != email:
            raise PermissionDenied('Нет прав для записи статуса этого студента.')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return InternWeeklyStatusCreateUpdateSerializer
        return InternWeeklyStatusSerializer

    def get_queryset(self):
        user = self.request.user
        qs = InternWeeklyStatus.objects.select_related('intern')

        if not getattr(user, 'is_admin', False):
            email = getattr(user, 'email', None)
            if email:
                qs = qs.filter(intern__manager_email=email)

        intern_id = self.request.query_params.get('intern_id')
        if intern_id:
            try:
                qs = qs.filter(intern_id=int(intern_id))
            except (ValueError, TypeError):
                pass

        week_start = self.request.query_params.get('week_start')
        if week_start:
            qs = qs.filter(week_start=week_start)

        absence_status = self.request.query_params.get('absence_status')
        if absence_status:
            qs = qs.filter(absence_status=absence_status)

        return qs

    @extend_schema(
        summary='Список недельных статусов',
        description=(
            'Возвращает список недельных статусов студентов.\n\n'
            'Менеджер видит только статусы своих студентов.\n\n'
            '**Фильтры:**\n'
            '- `intern_id` — ID студента\n'
            '- `week_start` — начало недели (YYYY-MM-DD)\n'
            '- `absence_status` — статус отсутствия (болеет / отпуск / уехал / другое)'
        ),
        tags=['Сотрудники'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Детали недельного статуса',
        description='Возвращает информацию о недельном статусе студента по ID.',
        tags=['Сотрудники'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Создать недельный статус',
        description='Создаёт запись о недельном статусе студента.',
        tags=['Сотрудники'],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Обновить недельный статус (PUT)',
        description='Полное обновление недельного статуса студента.',
        tags=['Сотрудники'],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Обновить недельный статус',
        description='Частичное обновление недельного статуса студента.',
        tags=['Сотрудники'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Удалить недельный статус',
        description='Удаляет запись о недельном статусе. Только для администраторов.',
        tags=['Сотрудники'],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
