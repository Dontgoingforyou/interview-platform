import logging

from django.db import IntegrityError
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.db.models.deletion import ProtectedError
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsManagerOrAdmin
from core.logging_mixins import ApiCRUDLoggingMixin

from ..models import Company
from ..serializers import CompanyMergeSerializer, CompanySerializer
from ..services import MergeCompaniesService, compute_company_list_stats
from .permissions import CompanyViewSetPermissionMixin, IsCompanyEditor

logger = logging.getLogger('companies')


class CompanyStatsAPIView(APIView):
    """Агрегаты для шапки списка компаний."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            raise NotAuthenticated()

    @extend_schema(
        summary='Статистика по компаниям',
        description='Сводные числа: всего, бигтех, с/без собеседований.',
        tags=['Компании'],
        responses={200: OpenApiResponse(description='OK')},
    )
    def get(self, request):
        return Response(compute_company_list_stats())


class CompanyMergeAPIView(APIView):
    """Объединение дублей (аналог CompanyMergeView POST)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsCompanyEditor]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            raise NotAuthenticated()

    @extend_schema(
        summary='Объединить компании',
        description='Перенос собеседований на главную, слияние псевдонимов, удаление дублей.',
        request=CompanyMergeSerializer,
        tags=['Компании'],
        responses={
            200: OpenApiResponse(description='Успех'),
            400: OpenApiResponse(description='Ошибка валидации'),
        },
    )
    def post(self, request):
        ser = CompanyMergeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        primary_id = ser.validated_data['primary_id']
        dup_ids = list(dict.fromkeys(ser.validated_data['duplicate_ids']))

        primary = Company.objects.filter(pk=primary_id).first()
        if not primary:
            return Response({'detail': 'Главная компания не найдена.'}, status=status.HTTP_400_BAD_REQUEST)

        duplicates = list(Company.objects.filter(pk__in=dup_ids))
        found_ids = {c.pk for c in duplicates}
        if found_ids != set(dup_ids):
            return Response({'detail': 'Одна или несколько компаний не найдены.'}, status=status.HTTP_400_BAD_REQUEST)

        duplicates = [c for c in duplicates if c.pk != primary.pk]
        if not duplicates:
            return Response(
                {'detail': 'Не выбраны компании для объединения (или выбрана только главная).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        user_label = getattr(user, 'email', None) or getattr(user, 'username', 'unknown')

        try:
            result = MergeCompaniesService.execute(primary, duplicates)
        except IntegrityError:
            logger.exception(
                '[ОБЪЕДИНЕНИЕ - ОШИБКА] Пользователь %s — ошибка объединения (главная «%s» id=%s)',
                user_label,
                primary.name,
                primary.pk,
            )
            return Response(
                {'detail': 'Ошибка при сохранении данных. Попробуйте ещё раз.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            '[УДАЛЕНИЕ] Пользователь %s объединил компании через API. '
            'Главная: «%s» (id=%s). Удалены дубли id=%s: %s. Перенесено собеседований: %s.',
            user_label,
            result.primary_name,
            result.primary_id,
            result.duplicate_ids,
            result.duplicate_names,
            result.interviews_moved,
        )
        return Response(
            {
                'primary_id': result.primary_id,
                'primary_name': result.primary_name,
                'removed_ids': result.duplicate_ids,
                'removed_names': result.duplicate_names,
                'interviews_moved': result.interviews_moved,
            },
            status=status.HTTP_200_OK,
        )


class CompanyViewSet(CompanyViewSetPermissionMixin, ApiCRUDLoggingMixin, viewsets.ModelViewSet):
    """
    CRUD компаний: чтение — менеджеры/HR/outstaff; запись — менеджеры и админ; удаление — только админ.
    """

    api_logger_name = 'companies.company'
    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    serializer_class = CompanySerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            raise NotAuthenticated()

    def get_queryset(self):
        qs = Company.objects.annotate(
            interviews_count=Count('interview'),
            name_sort_key=Case(
                When(name__iregex=r'^[а-яёa-z]', then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        )
        q = self.request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(aliases__icontains=q))
        bigtech = self.request.query_params.get('is_bigtech')
        if bigtech is not None:
            low = str(bigtech).lower()
            if low in ('true', '1', 'yes'):
                qs = qs.filter(is_bigtech=True)
            elif low in ('false', '0', 'no'):
                qs = qs.filter(is_bigtech=False)
        # Совместимость с шаблоном: bigtech=1 / пусто
        legacy_bt = self.request.query_params.get('bigtech')
        if legacy_bt == '1':
            qs = qs.filter(is_bigtech=True)

        sort = self.request.query_params.get('sort', 'interviews')
        if sort == '-interviews':
            qs = qs.order_by('interviews_count', 'name_sort_key', 'name')
        elif sort == '-name':
            qs = qs.order_by('name_sort_key', '-name')
        elif sort == 'name':
            qs = qs.order_by('name_sort_key', 'name')
        else:
            qs = qs.order_by('-interviews_count', 'name_sort_key', 'name')

        return qs

    @extend_schema(
        summary='Удалить компанию',
        description='Только администратор. Нельзя удалить компанию со связанными собеседованиями.',
        tags=['Компании'],
        responses={204: OpenApiResponse(description='Удалено'), 409: OpenApiResponse(description='Конфликт')},
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete()
        except ProtectedError:
            return Response(
                {
                    'detail': (
                        'Нельзя удалить компанию: с ней связаны собеседования. '
                        'Сначала измените компанию в собеседованиях.'
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )
        self._get_api_logger().info(
            'API [УДАЛЕНИЕ] id=%s — %s',
            instance.pk,
            self._get_api_user_label(request),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary='Список компаний',
        description=(
            'Пагинированный список.\n\n'
            '**Фильтры:** `q`, `is_bigtech` (true/false), `bigtech=1` (только бигтех).\n'
            '**Сортировка:** `sort` — interviews, -interviews, name, -name (по умолчанию interviews).'
        ),
        tags=['Компании'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Создать компанию',
        tags=['Компании'],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Детали компании',
        tags=['Компании'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Изменить компанию',
        tags=['Компании'],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Частично изменить компанию',
        tags=['Компании'],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
