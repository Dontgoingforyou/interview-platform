"""
Тесты для сериализаторов приложения vector_search.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД (если требуется)
"""
import pytest

from vector_search.serializers import (
    SemanticSearchRequestSerializer,
    SemanticSearchResultSerializer,
    SemanticSearchResponseSerializer,
    SimilarEntitiesRequestSerializer,
    VectorEmbeddingSerializer,
    SearchLogSerializer,
)


class TestSemanticSearchRequestSerializer:
    """Тесты для SemanticSearchRequestSerializer."""

    def test_valid_minimal_data(self):
        """Проверка валидации минимальных данных."""
        data = {'query': 'test query'}
        serializer = SemanticSearchRequestSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data['query'] == 'test query'

    def test_valid_full_data(self):
        """Проверка валидации полных данных."""
        data = {
            'query': 'test query',
            'entity_type': 'interview',
            'top_k': 20,
            'min_score': 0.5,
            'direction_id': 1,
            'manager_email': 'manager@example.com',
            'interview_type': 'tech',
            'status': 'active'
        }
        serializer = SemanticSearchRequestSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data['query'] == 'test query'
        assert serializer.validated_data['entity_type'] == 'interview'
        assert serializer.validated_data['top_k'] == 20
        assert serializer.validated_data['min_score'] == 0.5

    def test_missing_required_query(self):
        """Проверка обязательности поля query."""
        data = {'entity_type': 'interview'}
        serializer = SemanticSearchRequestSerializer(data=data)

        assert not serializer.is_valid()
        assert 'query' in serializer.errors

    def test_invalid_entity_type(self):
        """Проверка валидации типа сущности."""
        data = {
            'query': 'test',
            'entity_type': 'invalid_type'
        }
        serializer = SemanticSearchRequestSerializer(data=data)

        assert not serializer.is_valid()
        assert 'entity_type' in serializer.errors

    def test_top_k_out_of_range_low(self):
        """Проверка минимального значения top_k."""
        data = {
            'query': 'test',
            'top_k': 0
        }
        serializer = SemanticSearchRequestSerializer(data=data)

        assert not serializer.is_valid()
        assert 'top_k' in serializer.errors

    def test_top_k_out_of_range_high(self):
        """Проверка максимального значения top_k."""
        data = {
            'query': 'test',
            'top_k': 200
        }
        serializer = SemanticSearchRequestSerializer(data=data)

        assert not serializer.is_valid()
        assert 'top_k' in serializer.errors

    def test_min_score_out_of_range_low(self):
        """Проверка минимального значения min_score."""
        data = {
            'query': 'test',
            'min_score': -0.1
        }
        serializer = SemanticSearchRequestSerializer(data=data)

        assert not serializer.is_valid()
        assert 'min_score' in serializer.errors

    def test_min_score_out_of_range_high(self):
        """Проверка максимального значения min_score."""
        data = {
            'query': 'test',
            'min_score': 1.5
        }
        serializer = SemanticSearchRequestSerializer(data=data)

        assert not serializer.is_valid()
        assert 'min_score' in serializer.errors

    @pytest.mark.parametrize('entity_type', [
        'interview', 'intern', 'offer', 'debt', 'sad_intern', 'manager', 'company',
        'direction', 'intern_weekly_status',
    ])
    def test_valid_entity_types(self, entity_type):
        """Проверка всех валидных типов сущностей."""
        data = {'query': 'test', 'entity_type': entity_type}
        serializer = SemanticSearchRequestSerializer(data=data)
        assert serializer.is_valid()


class TestSemanticSearchResultSerializer:
    """Тесты для SemanticSearchResultSerializer."""

    def test_serialize_result(self):
        """Проверка сериализации результата поиска."""
        data = {
            'entity_type': 'interview',
            'entity_id': 1,
            'text_content': 'Test content',
            'similarity_score': 0.95,
            'metadata': {'direction_id': 1}
        }
        serializer = SemanticSearchResultSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data['entity_type'] == 'interview'
        assert serializer.validated_data['similarity_score'] == 0.95


class TestSemanticSearchResponseSerializer:
    """Тесты для SemanticSearchResponseSerializer."""

    def test_serialize_response(self):
        """Проверка сериализации ответа поиска."""
        data = {
            'query': 'test query',
            'results': [
                {
                    'entity_type': 'interview',
                    'entity_id': 1,
                    'text_content': 'Test',
                    'similarity_score': 0.95,
                    'metadata': {}
                }
            ],
            'total_found': 1,
            'search_time_ms': 123.45
        }
        serializer = SemanticSearchResponseSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data['query'] == 'test query'
        assert serializer.validated_data['total_found'] == 1
        assert len(serializer.validated_data['results']) == 1


class TestSimilarEntitiesRequestSerializer:
    """Тесты для SimilarEntitiesRequestSerializer."""

    def test_valid_minimal_data(self):
        """Проверка валидации минимальных данных."""
        data = {
            'entity_type': 'interview',
            'entity_id': 1
        }
        serializer = SimilarEntitiesRequestSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data['entity_type'] == 'interview'
        assert serializer.validated_data['entity_id'] == 1
        assert serializer.validated_data['top_k'] == 5  # default

    def test_valid_with_top_k(self):
        """Проверка валидации с указанным top_k."""
        data = {
            'entity_type': 'interview',
            'entity_id': 1,
            'top_k': 10
        }
        serializer = SimilarEntitiesRequestSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data['top_k'] == 10

    def test_missing_entity_type(self):
        """Проверка обязательности поля entity_type."""
        data = {'entity_id': 1}
        serializer = SimilarEntitiesRequestSerializer(data=data)

        assert not serializer.is_valid()
        assert 'entity_type' in serializer.errors

    def test_missing_entity_id(self):
        """Проверка обязательности поля entity_id."""
        data = {'entity_type': 'interview'}
        serializer = SimilarEntitiesRequestSerializer(data=data)

        assert not serializer.is_valid()
        assert 'entity_id' in serializer.errors

    def test_invalid_entity_type(self):
        """Проверка валидации типа сущности."""
        data = {
            'entity_type': 'invalid',
            'entity_id': 1
        }
        serializer = SimilarEntitiesRequestSerializer(data=data)

        assert not serializer.is_valid()
        assert 'entity_type' in serializer.errors

    @pytest.mark.parametrize('top_k', [0, 100])
    def test_top_k_out_of_range(self, top_k):
        """Проверка граничных значений top_k (слишком мало и слишком много)."""
        data = {
            'entity_type': 'interview',
            'entity_id': 1,
            'top_k': top_k,
        }
        serializer = SimilarEntitiesRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'top_k' in serializer.errors


@pytest.mark.django_db(databases=['default'])
class TestVectorEmbeddingSerializer:
    """Тесты для VectorEmbeddingSerializer."""

    def test_serialize_vector_embedding(self, vector_embedding_interview):
        """Проверка сериализации векторного эмбеддинга."""
        serializer = VectorEmbeddingSerializer(vector_embedding_interview)
        data = serializer.data

        assert data['entity_type'] == 'interview'
        assert data['entity_id'] == vector_embedding_interview.entity_id
        assert data['text_content'] == vector_embedding_interview.text_content
        assert 'metadata' in data
        assert 'created_at' in data
        assert 'updated_at' in data
        # Вектор не должен быть в данных
        assert 'embedding' not in data

    def test_serialize_excludes_embedding_vector(self, vector_embedding_intern):
        """Проверка что сам вектор не сериализуется."""
        serializer = VectorEmbeddingSerializer(vector_embedding_intern)
        data = serializer.data

        # Проверяем что вектор (который очень большой) не включён
        assert 'embedding' not in data


@pytest.mark.django_db(databases=['default'])
class TestSearchLogSerializer:
    """Тесты для SearchLogSerializer."""

    def test_serialize_search_log(self, search_log):
        """Проверка сериализации лога поиска."""
        serializer = SearchLogSerializer(search_log)
        data = serializer.data

        assert data['query'] == search_log.query
        assert data['entity_type'] == search_log.entity_type
        assert data['results_count'] == search_log.results_count
        assert data['search_time_ms'] == search_log.search_time_ms
        assert data['user_email'] == search_log.user_email
        assert data['filters'] == search_log.filters

    def test_serialize_all_fields(self, search_log):
        """Проверка что все поля включены в сериализацию."""
        serializer = SearchLogSerializer(search_log)
        data = serializer.data

        assert 'id' in data
        assert 'query' in data
        assert 'entity_type' in data
        assert 'results_count' in data
        assert 'search_time_ms' in data
        assert 'user_email' in data
        assert 'filters' in data
        assert 'created_at' in data
