import logging
import time
from typing import List, Dict, Any, Optional
import numpy as np

from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)

# Лимит символов для эмбеддинга: ~7000 токенов при русском тексте (≈2.14 симв/токен),
# безопасный запас до лимита модели в 8192 токена.
_MAX_TEXT_CHARS = 15000


def _require_embedding_dimension(embedding: List[float]) -> List[float]:
    """Отклоняет вектор чужой размерности: запасная text-embedding-3-large — 3072, колонка — 1536."""
    expected = settings.EMBEDDING_DIMENSION
    if len(embedding) != expected:
        raise ValueError(
            f'Размерность эмбеддинга ({len(embedding)}) не равна {expected}. '
            'Вектор в базу не пишется.'
        )
    return embedding


class EmbeddingService:
    """Сервис векторных эмбеддингов через внешний LLM API."""

    _client = None

    @classmethod
    def get_client(cls):
        """Возвращает OpenAI клиент (singleton, ленивая инициализация)."""
        if cls._client is None:
            try:
                from openai import OpenAI
                api_key = getattr(settings, 'OPENAI_API_KEY', None)
                if not api_key:
                    raise ValueError(
                        'OPENAI_API_KEY не установлен в настройках. '
                        'Добавьте его в .env файл.'
                    )
                cls._client = OpenAI(
                    api_key=api_key,
                    base_url=settings.OPENAI_BASE_URL,
                )
                logger.info(
                    f'OpenAI клиент инициализирован. Модель: {settings.EMBEDDING_MODEL_NAME}, '
                    f'адрес: {settings.OPENAI_BASE_URL}'
                )
            except Exception:
                logger.exception('Ошибка инициализации клиента LLM API')
                raise
        return cls._client

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """
        Генерирует эмбеддинг для одного текста.

        Args:
            text: Текст для векторизации

        Returns:
            Список чисел (вектор) размерности EMBEDDING_DIMENSION
        """
        if not text or not text.strip():
            # Возвращаем нулевой вектор для пустого текста
            return [0.0] * settings.EMBEDDING_DIMENSION

        try:
            client = cls.get_client()

            # Обрезаем текст до разумного размера
            if len(text) > _MAX_TEXT_CHARS:
                text = text[:_MAX_TEXT_CHARS]
                logger.warning(f'Текст обрезан до {_MAX_TEXT_CHARS} символов')

            response = client.embeddings.create(
                input=text,
                model=settings.EMBEDDING_MODEL_NAME
            )
            embedding = response.data[0].embedding
            return _require_embedding_dimension(embedding)

        except Exception:
            logger.exception('Ошибка генерации эмбеддинга')
            raise

    @classmethod
    def generate_embeddings_batch(cls, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """
        Генерирует эмбеддинги для списка текстов (батчами).

        Args:
            texts: Список текстов
            batch_size: Размер батча (по умолчанию из settings)

        Returns:
            Список векторов
        """
        if not texts:
            return []

        batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        client = cls.get_client()

        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Обрезаем длинные тексты
            batch_processed = [text[:_MAX_TEXT_CHARS] if len(text) > _MAX_TEXT_CHARS else text for text in batch]

            logger.info(f'Генерация эмбеддингов для батча {i // batch_size + 1} ({len(batch)} текстов)')

            try:
                response = client.embeddings.create(
                    input=batch_processed,
                    model=settings.EMBEDDING_MODEL_NAME
                )
                embeddings.extend(
                    _require_embedding_dimension(item.embedding) for item in response.data
                )

                # Небольшая задержка между батчами для соблюдения rate limits
                if i + batch_size < len(texts):
                    time.sleep(0.1)

            except Exception:
                logger.exception('Ошибка генерации батча эмбеддингов')
                raise

        return embeddings

    @classmethod
    def cosine_similarity(cls, vec1: List[float], vec2: List[float]) -> float:
        """
        Вычисляет косинусное сходство между двумя векторами.

        Args:
            vec1: Первый вектор
            vec2: Второй вектор

        Returns:
            Значение от -1 до 1 (1 = полное совпадение)
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0

        return float(dot_product / (norm_v1 * norm_v2))

    @classmethod
    def semantic_search(
        cls,
        query: str,
        entity_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None
    ) -> tuple[List[Dict[str, Any]], float]:
        """
        Семантический поиск по эмбеддингам.

        Args:
            query: Поисковый запрос
            entity_type: Фильтр по типу сущности (interview, intern, etc.)
            filters: Дополнительные фильтры по метаданным
            top_k: Количество результатов (по умолчанию из settings)
            min_score: Минимальный score (по умолчанию из settings)

        Returns:
            Кортеж (список результатов, время выполнения в мс)
        """
        import os

        top_k = top_k or settings.SEMANTIC_SEARCH_TOP_K
        min_score = min_score or settings.SEMANTIC_SEARCH_MIN_SCORE

        # Генерируем эмбеддинг для запроса
        query_embedding = cls.generate_embedding(query)
        start_time = time.time()

        # Проверяем, используем ли мы тестовую среду (SQLite)
        is_testing = os.environ.get('DJANGO_TESTING') == '1'

        if is_testing:
            # Для тестов используем Python-вычисление (SQLite не поддерживает pgvector)
            from vector_search.models import VectorEmbedding

            # Получаем все эмбеддинги с фильтрами
            queryset = VectorEmbedding.objects.all()

            if entity_type:
                queryset = queryset.filter(entity_type=entity_type)

            # Применяем фильтры по метаданным
            if filters:
                for key, value in filters.items():
                    queryset = queryset.filter(**{f'metadata__{key}': str(value)})

            # Вычисляем косинусное сходство в Python
            results = []
            for embedding in queryset:
                similarity = cls.cosine_similarity(query_embedding, embedding.embedding)

                if similarity >= min_score:
                    results.append({
                        'entity_type': embedding.entity_type,
                        'entity_id': embedding.entity_id,
                        'text_content': embedding.text_content,
                        'metadata': embedding.metadata,
                        'similarity_score': similarity
                    })

            # Сортируем и ограничиваем количество
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            results = results[:top_k]

        else:
            # pgvector
            query_embedding_array = np.array(query_embedding, dtype=np.float32)

            sql_query = """
                SELECT
                    entity_type,
                    entity_id,
                    text_content,
                    metadata,
                    1 - (embedding <=> %s) AS similarity_score
                FROM vector_embeddings
                WHERE 1=1
            """
            params = [query_embedding_array]

            # Добавляем фильтр по типу сущности
            if entity_type:
                sql_query += " AND entity_type = %s"
                params.append(entity_type)

            # Добавляем фильтры по метаданным (JSON)
            if filters:
                for key, value in filters.items():
                    sql_query += " AND metadata->>%s = %s"
                    params.extend([key, str(value)])

            # Фильтруем по минимальному score
            sql_query += " AND 1 - (embedding <=> %s) >= %s"
            params.extend([query_embedding_array, min_score])

            # Сортируем по similarity и ограничиваем количество
            sql_query += " ORDER BY similarity_score DESC LIMIT %s"
            params.append(top_k)

            # Выполняем запрос в основной БД
            with connections['default'].cursor() as cursor:
                # Регистрируем адаптер pgvector для этого подключения
                try:
                    from pgvector.psycopg2 import register_vector
                    register_vector(cursor.connection)
                except Exception as e:
                    logger.debug(
                        f'pgvector register_vector: {e} (адаптер уже зарегистрирован или недоступен)'
                    )

                cursor.execute(sql_query, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        search_time = (time.time() - start_time) * 1000  # в миллисекундах

        logger.info(
            f'Семантический поиск: "{query}" | '
            f'Найдено: {len(results)} | '
            f'Время: {search_time:.2f}ms'
        )

        return results, search_time

    @staticmethod
    def enrich_kb_article_semantic_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Дополняет metadata у kb_article из БД, если в записи эмбеддинга нет section_id/filename
        (старые индексы или частичные метаданные).
        """
        from knowledge_base_app.models import KBArticle

        from vector_search.utils import ENTITY_KB_ARTICLE, extract_metadata

        to_fix: List[tuple[int, int]] = []
        pks: set[int] = set()
        for i, row in enumerate(results):
            if row.get('entity_type') != ENTITY_KB_ARTICLE:
                continue
            meta = row.get('metadata')
            if not isinstance(meta, dict):
                meta = {}
            if meta.get('section_id') and meta.get('filename'):
                continue
            eid = row.get('entity_id')
            try:
                pk = int(eid)
            except (TypeError, ValueError):
                continue
            to_fix.append((i, pk))
            pks.add(pk)

        if not pks:
            return results

        articles = {
            a.pk: a
            for a in KBArticle.objects.select_related('section').filter(pk__in=pks)
        }

        out = list(results)
        for i, pk in to_fix:
            article = articles.get(pk)
            if not article:
                continue
            row = dict(out[i])
            raw_meta = row.get('metadata')
            meta = dict(raw_meta) if isinstance(raw_meta, dict) else {}
            fresh = extract_metadata(article, ENTITY_KB_ARTICLE)
            for key in ('section_id', 'filename', 'title'):
                if not meta.get(key) and fresh.get(key):
                    meta[key] = fresh[key]
            row['metadata'] = meta
            out[i] = row
        return out

    @classmethod
    def get_similar_entities(
        cls,
        entity_type: str,
        entity_id: int,
        top_k: int = 5,
        manager_email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Находит похожие сущности на основе их эмбеддингов.

        Args:
            entity_type: Тип сущности
            entity_id: ID сущности
            top_k: Количество похожих результатов
            manager_email: Email менеджера для фильтрации (опционально)

        Returns:
            Список похожих сущностей
        """
        import os
        from vector_search.models import VectorEmbedding

        try:
            # Получаем эмбеддинг целевой сущности
            target = VectorEmbedding.objects.get(
                entity_type=entity_type,
                entity_id=entity_id
            )

            # Проверяем, используем ли мы тестовую среду (SQLite)
            is_testing = os.environ.get('DJANGO_TESTING') == '1'

            if is_testing:
                # Для тестов используем Python-вычисление (SQLite не поддерживает pgvector)
                queryset = VectorEmbedding.objects.filter(
                    entity_type=entity_type
                ).exclude(
                    entity_id=entity_id
                )

                # Фильтрация по manager_email
                if manager_email:
                    queryset = queryset.filter(metadata__manager_email=manager_email)

                # Вычисляем косинусное сходство в Python
                results = []
                for embedding in queryset:
                    similarity = cls.cosine_similarity(target.embedding, embedding.embedding)

                    results.append({
                        'entity_type': embedding.entity_type,
                        'entity_id': embedding.entity_id,
                        'text_content': embedding.text_content,
                        'metadata': embedding.metadata,
                        'similarity_score': similarity
                    })

                # Сортируем и ограничиваем количество
                results.sort(key=lambda x: x['similarity_score'], reverse=True)
                results = results[:top_k]

            else:
                # pgvector
                target_embedding_array = np.array(target.embedding, dtype=np.float32)

                sql_query = """
                    SELECT
                        entity_type,
                        entity_id,
                        text_content,
                        metadata,
                        1 - (embedding <=> %s) AS similarity_score
                    FROM vector_embeddings
                    WHERE entity_type = %s
                      AND entity_id != %s
                """
                params = [target_embedding_array, entity_type, entity_id]

                # Добавляем фильтр по manager_email
                if manager_email:
                    sql_query += " AND metadata->>%s = %s"
                    params.extend(['manager_email', manager_email])

                sql_query += """
                    ORDER BY similarity_score DESC
                    LIMIT %s
                """
                params.append(top_k)

                with connections['default'].cursor() as cursor:
                    # Регистрируем адаптер pgvector для этого подключения
                    try:
                        from pgvector.psycopg2 import register_vector
                        register_vector(cursor.connection)
                    except Exception as e:
                        logger.debug(
                            f'pgvector register_vector: {e} (адаптер уже зарегистрирован или недоступен)'
                        )

                    cursor.execute(sql_query, params)
                    columns = [col[0] for col in cursor.description]
                    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return results

        except VectorEmbedding.DoesNotExist:
            logger.warning(f'Эмбеддинг не найден: {entity_type}#{entity_id}')
            return []
