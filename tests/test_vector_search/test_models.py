"""
Тесты для моделей приложения vector_search.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.models - для группировки тестов моделей
"""
import pytest
from django.db import IntegrityError

from vector_search.models import VectorEmbedding, SearchLog


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestVectorEmbedding:
    """Тесты для модели VectorEmbedding."""

    def test_create_vector_embedding(self, interview):
        """Проверка создания векторного эмбеддинга."""
        embedding = VectorEmbedding.objects.create(
            entity_type='interview',
            entity_id=str(interview.id),
            text_content='Test content',
            embedding=[0.1] * 1536,
            metadata={'test': 'data'}
        )

        assert embedding.entity_type == 'interview'
        assert embedding.entity_id == str(interview.id)
        assert embedding.text_content == 'Test content'
        assert len(embedding.embedding) == 1536
        assert embedding.metadata == {'test': 'data'}

    def test_vector_embedding_str(self, vector_embedding_interview, interview):
        """Проверка строкового представления модели."""
        assert str(vector_embedding_interview) == f'interview#{interview.id}'

    def test_vector_embedding_unique_constraint(self, vector_embedding_interview, interview):
        """Проверка уникальности (entity_type, entity_id)."""
        with pytest.raises(IntegrityError, match='UNIQUE constraint'):
            VectorEmbedding.objects.create(
                entity_type='interview',
                entity_id=str(interview.id),
                text_content='Duplicate',
                embedding=[0.1] * 1536,
                metadata={}
            )

    def test_vector_embedding_metadata_default(self, interview):
        """Проверка дефолтного значения metadata."""
        embedding = VectorEmbedding.objects.create(
            entity_type='interview',
            entity_id=str(interview.id),
            text_content='Test',
            embedding=[0.1] * 1536
        )

        assert embedding.metadata == {}

    def test_vector_embedding_timestamps(self, vector_embedding_interview):
        """Проверка автоматического заполнения временных меток."""
        assert vector_embedding_interview.created_at is not None
        assert vector_embedding_interview.updated_at is not None

    def test_vector_embedding_update_timestamp(self, vector_embedding_interview):
        """Проверка обновления updated_at при изменении."""
        old_updated_at = vector_embedding_interview.updated_at

        vector_embedding_interview.text_content = 'Updated content'
        vector_embedding_interview.save()

        vector_embedding_interview.refresh_from_db()
        assert vector_embedding_interview.updated_at > old_updated_at

    def test_vector_embedding_different_entity_types(self, interview, intern):
        """Проверка создания эмбеддингов разных типов."""
        emb1 = VectorEmbedding.objects.create(
            entity_type='interview',
            entity_id=str(interview.id),
            text_content='Interview',
            embedding=[0.1] * 1536
        )

        emb2 = VectorEmbedding.objects.create(
            entity_type='intern',
            entity_id=str(intern.id),
            text_content='Intern',
            embedding=[0.2] * 1536
        )

        assert emb1.entity_type == 'interview'
        assert emb2.entity_type == 'intern'
        assert VectorEmbedding.objects.count() == 2


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestSearchLog:
    """Тесты для модели SearchLog."""

    def test_create_search_log(self):
        """Проверка создания лога поиска."""
        log = SearchLog.objects.create(
            query='test query',
            entity_type='interview',
            results_count=10,
            search_time_ms=150.5,
            user_email='test@example.com',
            filters={'direction_id': 1}
        )

        assert log.query == 'test query'
        assert log.entity_type == 'interview'
        assert log.results_count == 10
        assert log.search_time_ms == 150.5
        assert log.user_email == 'test@example.com'
        assert log.filters == {'direction_id': 1}

    def test_search_log_str(self, search_log):
        """Проверка строкового представления модели."""
        assert str(search_log) == 'тестовый запрос (5 рез.)'

    def test_search_log_str_truncation(self):
        """Проверка обрезания длинного запроса в __str__."""
        long_query = 'a' * 100
        log = SearchLog.objects.create(
            query=long_query,
            entity_type='interview',
            results_count=5,
            search_time_ms=100.0
        )

        str_repr = str(log)
        # 50 символов + " (5 рез.)" = 59
        assert len(str_repr) <= 65

    def test_search_log_nullable_fields(self):
        """Проверка необязательных полей."""
        log = SearchLog.objects.create(
            query='test',
            results_count=0,
            search_time_ms=50.0
        )

        assert log.entity_type is None
        assert log.user_email is None
        assert log.filters == {}

    def test_search_log_ordering(self):
        """Проверка сортировки логов по дате (newest first)."""
        log1 = SearchLog.objects.create(
            query='first',
            results_count=1,
            search_time_ms=10.0
        )

        log2 = SearchLog.objects.create(
            query='second',
            results_count=2,
            search_time_ms=20.0
        )

        logs = list(SearchLog.objects.all())
        assert logs[0].id == log2.id  # Newest first
        assert logs[1].id == log1.id

    def test_search_log_created_at(self, search_log):
        """Проверка автоматического заполнения created_at."""
        assert search_log.created_at is not None
