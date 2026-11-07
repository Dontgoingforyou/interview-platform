from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from accounts.permissions import IsAdminRole, IsManagerOrAdmin
from core.logging_mixins import ApiCRUDLoggingMixin
from ..models import Manager
from ..serializers import ManagerForFilterSerializer, ManagerListSerializer, ManagerUpdateSerializer


@extend_schema_view(
    create=extend_schema(exclude=True),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
    destroy=extend_schema(exclude=True),
)
class ManagerViewSet(ApiCRUDLoggingMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра менеджеров.

    Список и детали — только для администраторов.
    Эндпоинт /me/ доступен любому аутентифицированному пользователю.
    """
    serializer_class = ManagerListSerializer
    permission_classes = [IsAdminRole]
    lookup_field = 'email'
    lookup_value_regex = r'[^/]+'

    def get_queryset(self):
        qs = Manager.objects.all()

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1', 'yes'))

        group_filter = self.request.query_params.get('group')
        if group_filter:
            qs = qs.filter(groups__contains=[group_filter])

        return qs

    @extend_schema(
        summary='Список менеджеров',
        description=(
            'Возвращает список всех менеджеров системы. Только для администраторов.\n\n'
            '**Фильтры:**\n'
            '- `is_active` — активен ли менеджер (true/false)\n'
            '- `group` — фильтр по названию группы Keycloak'
        ),
        tags=['Менеджеры'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Детали менеджера',
        description='Возвращает информацию о менеджере по email. Только для администраторов.',
        tags=['Менеджеры'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Менеджеры для фильтров списков',
        description='Активные менеджеры (email + ФИО) для фильтра на странице собеседований и др.',
        tags=['Менеджеры'],
    )
    @action(
        detail=False,
        methods=['get'],
        url_path='for-filters',
        permission_classes=[IsManagerOrAdmin],
    )
    def for_filters(self, request):
        """Список менеджеров для выпадающих фильтров (не только admin)."""
        qs = Manager.objects.filter(is_active=True).order_by('full_name')
        serializer = ManagerForFilterSerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Профиль текущего пользователя',
        description='Возвращает профиль текущего аутентифицированного пользователя.',
        tags=['Менеджеры'],
    )
    @action(
        detail=False,
        methods=['get'],
        url_path='me',
        permission_classes=[IsManagerOrAdmin],
    )
    def me(self, request):
        """Возвращает профиль текущего пользователя."""
        user = request.user
        email = getattr(user, 'email', None)
        if not email:
            return Response({'detail': 'Email не найден в токене.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            manager = Manager.objects.get(email=email)
            serializer = ManagerListSerializer(manager)
            return Response(serializer.data)
        except Manager.DoesNotExist:
            return Response({
                'email': user.email,
                'full_name': getattr(user, 'full_name', ''),
                'username': getattr(user, 'username', ''),
                'groups': getattr(user, 'groups', []),
                'is_admin': getattr(user, 'is_admin', False),
                'note': 'Менеджер не найден в локальной БД (только токен Keycloak).',
            })

    @extend_schema(
        summary='Обновить менеджера',
        description='Обновляет данные менеджера. Только для администраторов.',
        request=ManagerUpdateSerializer,
        tags=['Менеджеры'],
    )
    @action(
        detail=True,
        methods=['patch'],
        url_path='update',
        permission_classes=[IsAdminRole],
    )
    def update_manager(self, request, email=None):
        """Частичное обновление менеджера (только admin)."""
        manager = self.get_object()
        serializer = ManagerUpdateSerializer(manager, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ManagerListSerializer(manager).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
