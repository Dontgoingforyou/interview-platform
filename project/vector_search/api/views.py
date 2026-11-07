import logging

from django.db.models import Count
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsManagerOrAdmin
from core.constants import KEYCLOAK_ROLE_ADMIN, KEYCLOAK_ROLE_HR, KEYCLOAK_ROLE_OUTSTAFF
from vector_search.models import SearchLog, VectorEmbedding
from vector_search.serializers import (
    SemanticSearchRequestSerializer,
    SemanticSearchResponseSerializer,
    SimilarEntitiesRequestSerializer,
    SemanticSearchResultSerializer,
)
from vector_search.services import EmbeddingService
from vector_search.utils import ENTITY_KB_ARTICLE

logger = logging.getLogger(__name__)


def _vector_user_label(request) -> str:
    from core.logging_mixins import get_user_label_for_log

    return get_user_label_for_log(request)


def _vector_search_unrestricted_by_manager_email(manager_role: str) -> bool:
    """
    Не сужать выборку по manager_email.

    Администратор — отдельная ветка; HR и outstaff — отдельно (read-only обзор без привязки к своему email).
    """
    if manager_role == KEYCLOAK_ROLE_ADMIN:
        return True
    if manager_role in (KEYCLOAK_ROLE_HR, KEYCLOAK_ROLE_OUTSTAFF):
        return True
    return False


def _manager_role_for_vector_api(request):
    """Роль из сессии (браузер) или из KeycloakUser (Bearer)."""
    mr = request.session.get('manager_role')
    if mr:
        return mr
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return 'manager'
    if getattr(user, 'is_admin', False):
        return 'admin'
    if getattr(user, 'is_hr', False):
        return KEYCLOAK_ROLE_HR
    if getattr(user, 'is_outstaff', False):
        return KEYCLOAK_ROLE_OUTSTAFF
    return 'manager'


class SemanticSearchAPIView(APIView):
    """
    API для семантического поиска по всей БД.

    Принимает запрос на естественном языке и возвращает
    наиболее релевантные результаты из векторизованной БД.

    Права доступа:
    - Администратор: все результаты (без фильтра по manager_email)
    - HR и outstaff: полный обзор в рамках read-only ролей
    - Менеджер: только свои данные (по manager_email)
    """

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    @extend_schema(
        summary='Семантический поиск',
        description='Поиск по естественному языку с использованием векторных эмбеддингов',
        request=SemanticSearchRequestSerializer,
        responses={200: SemanticSearchResponseSerializer},
        tags=['Векторный поиск'],
    )
    def post(self, request):
        serializer = SemanticSearchRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': 'Некорректные параметры', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        query = data['query']
        entity_type = data.get('entity_type')
        top_k = data.get('top_k')
        min_score = data.get('min_score')

        # Роль и email: из сессии (браузер/SSO) или из request.user (API Bearer)
        manager_role = _manager_role_for_vector_api(request)
        manager_email = request.session.get('manager_email') or getattr(request.user, 'email', None)
        logger.info('[ПОИСК] %s — семантический поиск: "%s"', _vector_user_label(request), query)

        # Формируем фильтры по метаданным
        filters = {}
        for key in ['direction_id', 'manager_email', 'interview_type', 'status']:
            if key in data and data[key]:
                filters[key] = data[key]

        # Фильтр по manager_email только для менеджеров (не админ, не HR/outstaff).
        # Статьи базы знаний — общие для всех менеджеров, без привязки к email.
        if (
            entity_type != ENTITY_KB_ARTICLE
            and not _vector_search_unrestricted_by_manager_email(manager_role)
            and manager_email
        ):
            # Если в фильтрах уже указан manager_email, проверяем что он совпадает
            if 'manager_email' in filters and filters['manager_email'] != manager_email:
                logger.warning(
                    f'Менеджер {manager_email} пытается искать данные другого менеджера: '
                    f'{filters["manager_email"]}'
                )
                return Response(
                    {'error': 'Доступ запрещен', 'details': 'Вы можете искать только свои данные'},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Устанавливаем фильтр по email менеджера
            filters['manager_email'] = manager_email
            logger.info(f'Применен фильтр по manager_email для менеджера: {manager_email}')

        try:
            # Выполняем семантический поиск
            results, search_time = EmbeddingService.semantic_search(
                query=query,
                entity_type=entity_type,
                filters=filters if filters else None,
                top_k=top_k,
                min_score=min_score,
            )

            if entity_type == ENTITY_KB_ARTICLE:
                results = EmbeddingService.enrich_kb_article_semantic_results(results)

            # Логируем запрос
            user_email = manager_email
            SearchLog.objects.create(
                query=query,
                entity_type=entity_type,
                results_count=len(results),
                search_time_ms=search_time,
                user_email=user_email,
                filters=filters,
            )

            # Формируем ответ
            response_data = {
                'query': query,
                'results': results,
                'total_found': len(results),
                'search_time_ms': search_time,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Ошибка семантического поиска: {e}', exc_info=True)
            return Response(
                {'error': 'Ошибка выполнения поиска', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SimilarEntitiesAPIView(APIView):
    """
    API для поиска похожих сущностей.

    Находит похожие объекты на основе их векторных представлений.

    Права доступа:
    - Администратор: похожие по любым сущностям
    - HR и outstaff: без ограничения по чужому manager_email
    - Менеджер: только свои сущности
    """

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    @extend_schema(
        summary='Поиск похожих сущностей',
        description='Находит похожие объекты того же типа',
        request=SimilarEntitiesRequestSerializer,
        responses={200: SemanticSearchResultSerializer(many=True)},
        tags=['Векторный поиск'],
    )
    def post(self, request):
        serializer = SimilarEntitiesRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': 'Некорректные параметры', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        entity_type = data['entity_type']
        entity_id = data['entity_id']
        top_k = data.get('top_k', 5)

        # Роль и email: из сессии (браузер/SSO) или из request.user (API Bearer)
        manager_role = _manager_role_for_vector_api(request)
        manager_email = request.session.get('manager_email') or getattr(request.user, 'email', None)
        logger.info(
            '[ПОИСК] %s — поиск похожих: %s#%s',
            _vector_user_label(request),
            entity_type,
            entity_id,
        )

        if (
            entity_type != ENTITY_KB_ARTICLE
            and not _vector_search_unrestricted_by_manager_email(manager_role)
            and manager_email
        ):
            # Проверяем, принадлежит ли запрашиваемая сущность менеджеру
            try:
                target_embedding = VectorEmbedding.objects.get(
                    entity_type=entity_type,
                    entity_id=entity_id,
                )

                # Проверяем manager_email в метаданных
                entity_manager_email = target_embedding.metadata.get('manager_email')

                if entity_manager_email != manager_email:
                    logger.warning(
                        f'Менеджер {manager_email} пытается получить доступ к сущности '
                        f'{entity_type}#{entity_id}, принадлежащей {entity_manager_email}'
                    )
                    return Response(
                        {'error': 'Доступ запрещен', 'details': 'Вы можете искать только свои данные'},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            except VectorEmbedding.DoesNotExist:
                return Response(
                    {'error': 'Сущность не найдена'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        try:
            # Ищем похожие сущности (статьи БЗ — без фильтра по manager_email)
            if entity_type == ENTITY_KB_ARTICLE:
                similar_manager_filter = None
            else:
                similar_manager_filter = (
                    manager_email if not _vector_search_unrestricted_by_manager_email(manager_role) else None
                )
            results = EmbeddingService.get_similar_entities(
                entity_type=entity_type,
                entity_id=entity_id,
                top_k=top_k,
                manager_email=similar_manager_filter,
            )

            return Response(results, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Ошибка поиска похожих сущностей: {e}', exc_info=True)
            return Response(
                {'error': 'Ошибка выполнения поиска', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VectorStatsAPIView(APIView):
    """
    API для получения статистики векторизации.

    Права доступа:
    - Администратор: статистика по всем данным
    - HR и outstaff: по всем данным (read-only роли)
    - Менеджер: только по своим данным
    """

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    @extend_schema(
        summary='Статистика векторизации',
        description='Возвращает информацию о количестве векторизованных объектов',
        tags=['Векторный поиск'],
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'total_embeddings': {'type': 'integer'},
                        'by_type': {'type': 'object', 'additionalProperties': True},
                        'last_updated': {'type': 'string', 'nullable': True},
                        'embedding_dimension': {'type': 'integer'},
                        'role': {'type': 'string'},
                    },
                },
                description='Сводка по эмбеддингам',
            ),
            500: OpenApiResponse(description='Внутренняя ошибка'),
        },
    )
    def get(self, request):
        try:
            # Роль и email: из сессии (браузер/SSO) или из request.user (API Bearer)
            manager_role = _manager_role_for_vector_api(request)
            manager_email = request.session.get('manager_email') or getattr(request.user, 'email', None)
            logger.info('[ПОИСК] %s — запрос статистики векторизации', _vector_user_label(request))

            # Базовый queryset
            queryset = VectorEmbedding.objects.all()

            if not _vector_search_unrestricted_by_manager_email(manager_role) and manager_email:
                # Фильтруем по metadata->manager_email
                queryset = queryset.filter(
                    metadata__manager_email=manager_email,
                )

            # Подсчитываем количество по типам
            stats = queryset.values('entity_type').annotate(
                count=Count('id'),
            )

            stats_dict = {item['entity_type']: item['count'] for item in stats}

            total = sum(stats_dict.values())

            # Последнее обновление (из доступных данных)
            latest = queryset.order_by('-updated_at').first()
            last_updated = latest.updated_at.isoformat() if latest else None

            return Response(
                {
                    'total_embeddings': total,
                    'by_type': stats_dict,
                    'last_updated': last_updated,
                    'embedding_dimension': 1536,  # OpenAI text-embedding-3-small
                    'role': manager_role,  # Показываем роль для отладки
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f'Ошибка получения статистики: {e}', exc_info=True)
            return Response(
                {'error': 'Ошибка получения статистики', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
