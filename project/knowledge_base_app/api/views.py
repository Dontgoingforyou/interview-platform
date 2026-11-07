import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsAdminRole, IsManagerOrAdmin

from ..managers import KnowledgeBaseManager
from ..serializers import (
    KBArticleCreateSerializer,
    KBArticleDetailSerializer,
    KBArticleListItemSerializer,
    KBArticleUpdateSerializer,
    KBSectionCreateSerializer,
    KBSectionReadSerializer,
    KBSectionUpdateSerializer,
    KBSearchResultSerializer,
)

logger = logging.getLogger('knowledge_base')


def _require_authenticated_user(request):
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        raise NotAuthenticated()


def _kb_user_label(request) -> str:
    from core.logging_mixins import get_user_label_for_log

    return get_user_label_for_log(request)


class KnowledgeBaseSearchAPIView(APIView):
    """Полнотекстовый поиск по статьям (параметр `q`)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        _require_authenticated_user(request)

    @extend_schema(
        summary='Поиск по базе знаний',
        description='Поиск по заголовку и содержимому статей. Пустой `q` — первые результаты в пределе лимита.',
        tags=['База знаний'],
        responses={200: KBSearchResultSerializer(many=True)},
    )
    def get(self, request):
        query = request.query_params.get('q', '')
        try:
            kb = KnowledgeBaseManager()
            results = kb.search_articles(query)
        except Exception as exc:
            logger.exception('Ошибка поиска в БЗ: %s', exc)
            return Response(
                {'detail': 'Ошибка выполнения поиска.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        ser = KBSearchResultSerializer(results, many=True)
        return Response(ser.data)


class KnowledgeBaseSectionListCreateAPIView(APIView):
    """Список разделов и создание (только админ)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminRole()]
        return [IsManagerOrAdmin()]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        _require_authenticated_user(request)

    @extend_schema(
        summary='Список разделов базы знаний',
        tags=['База знаний'],
        responses={200: KBSectionReadSerializer(many=True)},
    )
    def get(self, request):
        kb = KnowledgeBaseManager()
        sections = kb.get_sections()
        ser = KBSectionReadSerializer(sections, many=True)
        return Response(ser.data)

    @extend_schema(
        summary='Создать раздел',
        tags=['База знаний'],
        request=KBSectionCreateSerializer,
        responses={
            201: OpenApiResponse(description='Создано'),
            400: OpenApiResponse(description='Ошибка валидации'),
        },
    )
    def post(self, request):
        ser = KBSectionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        kb = KnowledgeBaseManager()
        try:
            kb.create_section(
                data['section_id'],
                data['title'],
                data.get('description') or '',
                data.get('icon') or '📁',
            )
        except ValueError as e:
            raise ValidationError({'detail': str(e)}) from e
        except Exception as exc:
            logger.exception('Ошибка создания раздела БЗ: %s', exc)
            return Response({'detail': 'Не удалось создать раздел.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info(
            '[СОЗДАНИЕ] API пользователь %s создал раздел «%s» (id=%s)',
            _kb_user_label(request),
            data['title'],
            data['section_id'],
        )
        return Response(
            {'section_id': data['section_id'], 'title': data['title']},
            status=status.HTTP_201_CREATED,
        )


class KnowledgeBaseSectionDetailAPIView(APIView):
    """Детали раздела, обновление и удаление."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsManagerOrAdmin()]
        return [IsAdminRole()]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        _require_authenticated_user(request)

    def _get_section_payload(self, section_id: str) -> dict:
        kb = KnowledgeBaseManager()
        for s in kb.get_sections():
            if s['id'] == section_id:
                return s
        return None

    @extend_schema(
        summary='Детали раздела',
        tags=['База знаний'],
        responses={200: KBSectionReadSerializer, 404: OpenApiResponse(description='Не найден')},
    )
    def get(self, request, section_id):
        payload = self._get_section_payload(section_id)
        if not payload:
            raise NotFound('Раздел не найден')
        return Response(KBSectionReadSerializer(payload).data)

    @extend_schema(
        summary='Обновить раздел',
        tags=['База знаний'],
        request=KBSectionUpdateSerializer,
        responses={200: OpenApiResponse(description='OK')},
    )
    def patch(self, request, section_id):
        ser = KBSectionUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = {k: v for k, v in ser.validated_data.items() if v is not None}
        kb = KnowledgeBaseManager()
        try:
            kb.update_section(
                section_id,
                title=data.get('title'),
                description=data.get('description'),
                icon=data.get('icon'),
            )
        except ValueError as e:
            if 'не найден' in str(e).lower():
                raise NotFound(str(e)) from e
            raise ValidationError({'detail': str(e)}) from e
        logger.info(
            '[ОБНОВЛЕНИЕ] API пользователь %s обновил раздел %s',
            _kb_user_label(request),
            section_id,
        )
        payload = self._get_section_payload(section_id)
        return Response(KBSectionReadSerializer(payload).data)

    @extend_schema(
        summary='Удалить раздел',
        tags=['База знаний'],
        responses={204: OpenApiResponse(description='Удалено')},
    )
    def delete(self, request, section_id):
        kb = KnowledgeBaseManager()
        try:
            kb.delete_section(section_id)
        except ValueError as e:
            if 'не найден' in str(e).lower():
                raise NotFound(str(e)) from e
            raise ValidationError({'detail': str(e)}) from e
        logger.info(
            '[УДАЛЕНИЕ] API пользователь %s удалил раздел %s',
            _kb_user_label(request),
            section_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class KnowledgeBaseArticleListCreateAPIView(APIView):
    """Список статей раздела и создание статьи."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminRole()]
        return [IsManagerOrAdmin()]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        _require_authenticated_user(request)

    @extend_schema(
        summary='Список статей раздела',
        tags=['База знаний'],
        responses={200: KBArticleListItemSerializer(many=True)},
    )
    def get(self, request, section_id):
        kb = KnowledgeBaseManager()
        articles = kb.get_articles(section_id)
        if not articles and not any(s['id'] == section_id for s in kb.get_sections()):
            raise NotFound('Раздел не найден')
        return Response(KBArticleListItemSerializer(articles, many=True).data)

    @extend_schema(
        summary='Создать статью в разделе',
        tags=['База знаний'],
        request=KBArticleCreateSerializer,
        responses={201: OpenApiResponse(description='Создано')},
    )
    def post(self, request, section_id):
        ser = KBArticleCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        title = ser.validated_data['title']
        content = ser.validated_data.get('content') or ''
        kb = KnowledgeBaseManager()
        try:
            filename = kb.create_article(section_id, title, content)
        except ValueError as e:
            if 'не найден' in str(e).lower():
                raise NotFound(str(e)) from e
            raise ValidationError({'detail': str(e)}) from e
        except Exception as exc:
            logger.exception('Ошибка создания статьи БЗ: %s', exc)
            return Response({'detail': 'Не удалось создать статью.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info(
            '[СОЗДАНИЕ] API пользователь %s создал статью «%s» в разделе %s, файл %s',
            _kb_user_label(request),
            title,
            section_id,
            filename,
        )
        return Response({'filename': filename, 'title': title}, status=status.HTTP_201_CREATED)


class KnowledgeBaseArticleDetailAPIView(APIView):
    """Чтение, обновление и удаление статьи."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsManagerOrAdmin()]
        return [IsAdminRole()]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        _require_authenticated_user(request)

    @extend_schema(
        summary='Детали статьи',
        tags=['База знаний'],
        responses={200: KBArticleDetailSerializer, 404: OpenApiResponse(description='Не найдена')},
    )
    def get(self, request, section_id, filename):
        kb = KnowledgeBaseManager()
        article = kb.get_article(section_id, filename)
        if not article:
            raise NotFound('Статья не найдена')
        return Response(KBArticleDetailSerializer(article).data)

    @extend_schema(
        summary='Обновить статью',
        tags=['База знаний'],
        request=KBArticleUpdateSerializer,
        responses={200: KBArticleDetailSerializer},
    )
    def patch(self, request, section_id, filename):
        ser = KBArticleUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        title = ser.validated_data.get('title')
        content = ser.validated_data.get('content')
        if title is None and content is None:
            raise ValidationError({'detail': 'Укажите title и/или content.'})

        kb = KnowledgeBaseManager()
        if content is not None:
            ok = kb.save_article(section_id, filename, content, title=title)
        elif title is not None:
            existing = kb.get_article(section_id, filename)
            if not existing:
                raise NotFound('Статья не найдена')
            ok = kb.save_article(section_id, filename, existing['markdown'], title=title)
        else:
            ok = False

        if not ok:
            raise NotFound('Статья или раздел не найдены')

        logger.info(
            '[ОБНОВЛЕНИЕ] API пользователь %s обновил статью %s/%s',
            _kb_user_label(request),
            section_id,
            filename,
        )
        article = kb.get_article(section_id, filename)
        return Response(KBArticleDetailSerializer(article).data)

    @extend_schema(
        summary='Удалить статью',
        tags=['База знаний'],
        responses={204: OpenApiResponse(description='Удалено')},
    )
    def delete(self, request, section_id, filename):
        kb = KnowledgeBaseManager()
        deleted = kb.delete_article(section_id, filename)
        if not deleted:
            raise NotFound('Статья не найдена')
        logger.info(
            '[УДАЛЕНИЕ] API пользователь %s удалил статью %s/%s',
            _kb_user_label(request),
            section_id,
            filename,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
