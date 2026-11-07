from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminRole, IsManagerOrAdmin, IsReadOnlyHROutstaff
from core.intern_utils import transliterate_name_to_cyrillic
from core.logging_mixins import ApiCRUDLoggingMixin
from managers.models import Manager
from sad_intern.drf_list_query import (
    GROUPS_PER_PAGE,
    PER_GROUP_PAGINATE_BY,
    apply_list_filters,
    build_grouped_payload,
    build_on_project_page,
    sad_intern_role_scoped_qs,
)
from sad_intern.serializers import (
    SadInternCreateUpdateSerializer,
    SadInternDetailSerializer,
    SadInternListSerializer,
)


def _intern_manager_display_map(instances):
    emails = set()
    for o in instances:
        if o.intern_id and o.intern and o.intern.manager_email:
            emails.add(o.intern.manager_email)
    if not emails:
        return {}
    out = {}
    for m in Manager.objects.filter(email__in=emails, is_active=True):
        raw = m.full_name or ''
        out[m.email] = transliterate_name_to_cyrillic(raw) or raw
    return out


class SadInternViewSet(ApiCRUDLoggingMixin, viewsets.ModelViewSet):
    """
    CRUD «грустят», группировка по направлениям, блок on_project.
    """

    api_logger_name = 'sad_intern.sadintern'

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminRole()]
        return [IsManagerOrAdmin(), IsReadOnlyHROutstaff()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SadInternDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return SadInternCreateUpdateSerializer
        return SadInternListSerializer

    def _base_role_qs(self):
        return sad_intern_role_scoped_qs(self.request.user)

    def get_queryset(self):
        user = self.request.user
        qs = self._base_role_qs()

        if self.action in ('grouped',):
            return qs
        if self.action in ('on_project_list',):
            return qs

        params = self.request.query_params
        if self.action == 'list':
            raw_exclude = params.get('exclude_on_project', '').lower()
            if raw_exclude in ('false', '0', 'no'):
                qs = qs.exclude_left_interns()
            else:
                qs = qs.for_main_waiting_list()
            if params.get('status'):
                qs = qs.filter(status=params['status'])
            if getattr(user, 'is_admin', False):
                me = params.get('manager_email')
                if me:
                    qs = qs.filter(manager_email=me)
            return qs

        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.action == 'list':
            qs = self.filter_queryset(self.get_queryset())
            ctx['intern_manager_display'] = _intern_manager_display_map(list(qs))
        return ctx

    def perform_create(self, serializer):
        serializer.save()

    @extend_schema(
        summary='Детали записи «грустящего» студента',
        tags=['Грустящие студенты'],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        ctx = self.get_serializer_context()
        ctx['intern_manager_display'] = _intern_manager_display_map([instance])
        serializer = self.get_serializer(instance, context=ctx)
        return Response(serializer.data)

    @extend_schema(
        summary='Обновить запись (PUT)',
        description='Менеджер может менять только записи со своим `manager_email`.',
        tags=['Грустящие студенты'],
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        if not getattr(user, 'is_admin', False):
            email = getattr(user, 'email', None)
            if instance.manager_email != email:
                return Response(
                    {'detail': 'Нет прав для редактирования этой записи.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Частично обновить запись',
        description='Менеджер может менять только записи со своим `manager_email`.',
        tags=['Грустящие студенты'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary='Список с группировкой по направлениям',
        description=(
            'Основной список ожидания (без on_project, с exclude_left_interns). '
            'Параметры: `directions_offset`, `page_<direction_id|none>`, `q`, `status`, `direction`, '
            '`order_by`, `order_dir`, `manager_email` (только admin).'
        ),
        parameters=[
            OpenApiParameter('directions_offset', OpenApiTypes.INT),
            OpenApiParameter('q', OpenApiTypes.STR),
            OpenApiParameter('status', OpenApiTypes.STR),
            OpenApiParameter('direction', OpenApiTypes.INT),
            OpenApiParameter('order_by', OpenApiTypes.STR),
            OpenApiParameter('order_dir', OpenApiTypes.STR),
            OpenApiParameter('manager_email', OpenApiTypes.STR),
        ],
        tags=['Грустящие студенты'],
    )
    @action(detail=False, methods=['get'], url_path='grouped')
    def grouped(self, request):
        user = request.user
        allow_mgr = getattr(user, 'is_admin', False)
        qs = apply_list_filters(
            self._base_role_qs(),
            request.query_params,
            waiting=True,
            allow_manager_email_filter=allow_mgr,
        )
        params = request.query_params
        payload = build_grouped_payload(
            qs,
            params,
            groups_per_page=GROUPS_PER_PAGE,
            per_group=PER_GROUP_PAGINATE_BY,
        )
        all_rows = []
        for g in payload['groups']:
            all_rows.extend(g['results'])
        mgr_map = _intern_manager_display_map(all_rows)
        ctx = {**self.get_serializer_context(), 'intern_manager_display': mgr_map}

        groups_out = []
        for g in payload['groups']:
            ser = SadInternListSerializer(g['results'], many=True, context=ctx)
            groups_out.append(
                {
                    'direction_id': g['direction_id'],
                    'direction_name': g['direction_name'],
                    'page': g['page'],
                    'total_pages': g['total_pages'],
                    'total_count': g['total_count'],
                    'per_page': g['per_page'],
                    'pagination_key': g['pagination_key'],
                    'results': ser.data,
                }
            )

        return Response(
            {
                'groups': groups_out,
                'has_more_directions': payload['has_more_directions'],
                'next_directions_offset': payload['next_directions_offset'],
                'total_directions': payload['total_directions'],
                'directions_offset': payload['directions_offset'],
            }
        )

    @extend_schema(
        summary='Вышли на проект',
        description='Пагинированный список со статусом on_project (`on_project_page`).',
        parameters=[
            OpenApiParameter('on_project_page', OpenApiTypes.INT),
            OpenApiParameter('q', OpenApiTypes.STR),
            OpenApiParameter('status', OpenApiTypes.STR),
            OpenApiParameter('direction', OpenApiTypes.INT),
        ],
        tags=['Грустящие студенты'],
    )
    @action(detail=False, methods=['get'], url_path='on-project')
    def on_project_list(self, request):
        user = request.user
        allow_mgr = getattr(user, 'is_admin', False)
        qs = apply_list_filters(
            self._base_role_qs(),
            request.query_params,
            waiting=False,
            allow_manager_email_filter=allow_mgr,
        )
        page_data = build_on_project_page(qs, request.query_params)
        mgr_map = _intern_manager_display_map(page_data['results'])
        ctx = {**self.get_serializer_context(), 'intern_manager_display': mgr_map}
        ser = SadInternListSerializer(page_data['results'], many=True, context=ctx)
        return Response(
            {
                'count': page_data['count'],
                'page': page_data['page'],
                'total_pages': page_data['total_pages'],
                'results': ser.data,
            }
        )

    @extend_schema(
        summary='Список «грустящих» студентов',
        description=(
            'Плоский список как на сайте: по умолчанию без `on_project`, без студентов со статусами «Оффер»/«Ушёл». '
            'Параметр `exclude_on_project=false` (или `0`, `no`) расширяет выдачу записями со статусом '
            '`on_project` (по-прежнему без студентов со статусами оффер/ушёл).\n\n'
            'Менеджер — только свои; HR/outstaff/admin — все (в рамках роли).\n\n'
            '**Фильтры:** `status`, `manager_email` (только admin), `exclude_on_project`.'
        ),
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR),
            OpenApiParameter('manager_email', OpenApiTypes.STR),
            OpenApiParameter(
                'exclude_on_project',
                OpenApiTypes.BOOL,
                description='По умолчанию скрыть on_project; false/0/no — показать',
            ),
        ],
        tags=['Грустящие студенты'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Добавить студента в список ожидания',
        description='Менеджер или администратор. Логика назначения менеджера как в веб-форме.',
        tags=['Грустящие студенты'],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Удалить запись',
        description='Только администратор.',
        tags=['Грустящие студенты'],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
