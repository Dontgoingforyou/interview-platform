from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from accounts.permissions import (
    IsAdminRole,
    IsInterviewWriteRole,
    IsManagerOrAdmin,
    IsReadOnlyHROutstaff,
)
from core.constants import INTERN_VALID_STATUSES
from core.logging_mixins import ApiCRUDLoggingMixin

from ..list_filters import (
    apply_intern_list_ordering,
    apply_intern_manager_direction_group_filters,
    apply_intern_status_filters,
    apply_intern_text_search,
)
from ..models import Intern
from ..pagination import InternListPagination
from ..serializers import (
    InternCreateUpdateSerializer,
    InternDetailSerializer,
    InternListSerializer,
    build_manager_display_map,
)


class InternViewSet(ApiCRUDLoggingMixin, viewsets.ModelViewSet):
    """
    ViewSet для управления студентами.

    Менеджер видит только своих студентов.
    HR и outstaff видят всех на чтение (список, детали).
    Администратор видит всех.
    Создание: администратор (любой менеджер в теле) или менеджер (только с назначением на себя).
    Изменение и удаление — только для администраторов.
    """

    api_logger_name = 'interns.intern'
    pagination_class = InternListPagination

    # --- Вспомогательные методы ---

    def _build_list_serializer(self, items):
        """Собирает сериализатор списка с добавлением manager_display_map в контекст."""
        emails = {obj.manager_email for obj in items if obj.manager_email}
        ctx = {
            **self.get_serializer_context(),
            'manager_display_map': build_manager_display_map(emails),
        }
        return self.get_serializer(items, many=True, context=ctx)

    def get_permissions(self):
        action = getattr(self, 'action', None)
        if action == 'create':
            return [IsInterviewWriteRole()]
        if action in ('update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [IsManagerOrAdmin(), IsReadOnlyHROutstaff()]

    def perform_create(self, serializer):
        user = self.request.user
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_admin', False):
            serializer.save()
            return
        email = getattr(user, 'email', None)
        if not email:
            raise PermissionDenied('Не удалось определить email пользователя.')
        serializer.save(manager_email=email)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InternDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return InternCreateUpdateSerializer
        return InternListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Intern.objects.select_related('direction')

        if not getattr(user, 'is_admin', False):
            if not (
                getattr(user, 'is_hr', False)
                or getattr(user, 'is_outstaff', False)
            ):
                email = getattr(user, 'email', None)
                if email:
                    qs = qs.filter(manager_email=email)

        params = self.request.query_params
        manager = params.get('manager') or params.get('manager_email')
        direction_id = params.get('direction_id') or params.get('direction')
        qs = apply_intern_manager_direction_group_filters(
            qs,
            manager_email=manager,
            direction_id=direction_id,
            group=params.get('group'),
        )
        qs = apply_intern_status_filters(qs, status=params.get('status') or None)
        qs = apply_intern_text_search(qs, params.get('q'))
        qs = apply_intern_list_ordering(
            qs,
            params.get('order_by', 'id'),
            params.get('order_dir', 'desc'),
        )
        return qs

    @extend_schema(
        summary='Список студентов',
        description=(
            'Менеджер видит только своих студентов. Администратор, HR и outstaff — всех.\n\n'
            'Фильтры: `q`, `status`, `manager` / `manager_email`, '
            '`direction` / `direction_id`, `group`, `order_by`, `order_dir`.'
        ),
        parameters=[
            OpenApiParameter('q', OpenApiTypes.STR, description='Поиск: ФИО, email, группа, HR'),
            OpenApiParameter('status', OpenApiTypes.STR, description='Статус: активный, ушел, оффер'),
            OpenApiParameter('manager', OpenApiTypes.STR, description='Email менеджера'),
            OpenApiParameter('manager_email', OpenApiTypes.STR, description='Алиас manager'),
            OpenApiParameter('direction_id', OpenApiTypes.INT, description='ID направления'),
            OpenApiParameter('direction', OpenApiTypes.INT, description='Алиас direction_id'),
            OpenApiParameter('group', OpenApiTypes.STR, description='Группа (частичное совпадение)'),
            OpenApiParameter('order_by', OpenApiTypes.STR, description='Поле сортировки'),
            OpenApiParameter('order_dir', OpenApiTypes.STR, description='asc или desc'),
        ],
        tags=['Студенты'],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self._build_list_serializer(page).data)
        return Response(self._build_list_serializer(queryset).data)

    @extend_schema(
        summary='Детали студента',
        description='Возвращает полную информацию о студенте по ID.',
        tags=['Студенты'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Создать студента',
        description=(
            'Создаёт нового студента. Администратор задаёт любого менеджера; '
            'менеджер с ролью записи — студент всегда назначается на email из сессии (поле в теле игнорируется).'
        ),
        tags=['Студенты'],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Обновить студента (PUT)',
        description='Полное обновление студента. Только для администраторов.',
        tags=['Студенты'],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Частичное обновление студента',
        description='Обновляет указанные поля студента. Только для администраторов.',
        tags=['Студенты'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Смена статуса студента (раздел «Сотрудники»)',
        description=(
            'Обновляет поле manual_status. Доступно менеджерам и администраторам '
            '(аналог legacy POST /employees/api/update-status/).'
        ),
        request={
            'application/json': {
                'type': 'object',
                'properties': {'manual_status': {'type': 'string'}},
                'required': ['manual_status'],
            }
        },
        tags=['Студенты'],
    )
    @action(detail=True, methods=['patch'], url_path='manual-status')
    def patch_manual_status(self, request, pk=None):
        """Обновление manual_status только для своих студентов (или admin)."""
        intern = self.get_object()

        user = request.user
        if not getattr(user, 'is_admin', False) and not getattr(user, 'is_superuser', False):
            email = getattr(user, 'email', None)
            if intern.manager_email != email:
                raise PermissionDenied('Нет прав для изменения статуса этого студента.')

        new_status = request.data.get('manual_status')
        if not new_status:
            raise ValidationError({'manual_status': 'Укажите manual_status.'})
        if new_status not in INTERN_VALID_STATUSES:
            raise ValidationError({
                'manual_status': f'Допустимые значения: {", ".join(INTERN_VALID_STATUSES)}',
            })

        intern.manual_status = new_status
        intern.save(update_fields=['manual_status'])
        self._get_api_logger().info(
            'API [MANUAL_STATUS] id=%s manual_status=%s — %s',
            pk,
            new_status,
            self._get_api_user_label(request),
        )
        return Response({
            'success': True,
            'manual_status': new_status,
            'status_display': intern.status_display,
        })

    @extend_schema(
        summary='Удалить студента',
        description='Удаление студента. Только администратор.',
        tags=['Студенты'],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
