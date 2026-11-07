"""
Тесты для сервисов приложения vector_search.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.services - для группировки тестов сервисов
"""
import pytest
from unittest.mock import MagicMock, Mock, patch

from vector_search.services import EmbeddingService
from vector_search.models import VectorEmbedding

# Сохраняем оригинальный get_client для тестов инициализации (conftest мокирует его).
_original_get_client = EmbeddingService.get_client


@pytest.mark.django_db(databases=['default'])
@pytest.mark.services
class TestEmbeddingService:
    """Тесты для EmbeddingService."""

    def test_generate_embedding_with_mock(self, mock_openai_embedding):
        """Проверка генерации эмбеддинга."""
        text = 'Test text for embedding'
        embedding = EmbeddingService.generate_embedding(text)

        assert embedding == [0.1] * 1536
        mock_openai_embedding.embeddings.create.assert_called_once()

    def test_generate_embedding_empty_text(self):
        """Проверка генерации эмбеддинга для пустого текста."""
        # Для пустого текста должен вернуться нулевой вектор
        embedding = EmbeddingService.generate_embedding('')

        assert embedding is not None
        assert len(embedding) == 1536
        assert all(x == 0.0 for x in embedding)

    def test_generate_embedding_whitespace_text(self):
        """Проверка генерации эмбеддинга для текста из пробелов."""
        embedding = EmbeddingService.generate_embedding('   ')

        assert embedding is not None
        assert len(embedding) == 1536
        assert all(x == 0.0 for x in embedding)

    def test_generate_embedding_long_text(self, mock_openai_embedding):
        """Проверка обрезания длинного текста."""
        long_text = 'a' * 50000  # Больше лимита
        embedding = EmbeddingService.generate_embedding(long_text)

        assert embedding is not None
        # Проверяем что API был вызван с обрезанным текстом
        call_args = mock_openai_embedding.embeddings.create.call_args
        assert len(call_args[1]['input']) <= 30000

    def test_generate_embeddings_batch_with_mock(self, mock_openai_embedding):
        """Проверка батчевой генерации эмбеддингов."""
        texts = ['Text 1', 'Text 2', 'Text 3']

        # Мокируем response для батча
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536),
            Mock(embedding=[0.2] * 1536),
            Mock(embedding=[0.3] * 1536),
        ]
        mock_openai_embedding.embeddings.create.return_value = mock_response

        embeddings = EmbeddingService.generate_embeddings_batch(texts, batch_size=10)

        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)

    def test_generate_embeddings_batch_empty_list(self):
        """Проверка батчевой генерации для пустого списка."""
        embeddings = EmbeddingService.generate_embeddings_batch([])
        assert embeddings == []

    def test_cosine_similarity_identical_vectors(self):
        """Проверка косинусного сходства идентичных векторов."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]

        similarity = EmbeddingService.cosine_similarity(vec1, vec2)

        assert abs(similarity - 1.0) < 0.0001  # Должно быть близко к 1

    def test_cosine_similarity_opposite_vectors(self):
        """Проверка косинусного сходства противоположных векторов."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]

        similarity = EmbeddingService.cosine_similarity(vec1, vec2)

        assert abs(similarity - (-1.0)) < 0.0001  # Должно быть близко к -1

    def test_cosine_similarity_orthogonal_vectors(self):
        """Проверка косинусного сходства ортогональных векторов."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        similarity = EmbeddingService.cosine_similarity(vec1, vec2)

        assert abs(similarity) < 0.0001  # Должно быть близко к 0

    def test_cosine_similarity_zero_vector(self):
        """Проверка косинусного сходства с нулевым вектором."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]

        similarity = EmbeddingService.cosine_similarity(vec1, vec2)

        assert similarity == 0.0

    def test_enrich_kb_article_semantic_results_fills_section_and_filename(self):
        """Пустые section_id/filename в metadata дополняются из KBArticle."""
        from knowledge_base_app.models import KBArticle, KBSection

        section = KBSection.objects.create(
            section_id='skills',
            title='Навыки',
            description='',
            icon='📄',
            order=0,
        )
        article = KBArticle.objects.create(
            section=section,
            filename='resume.md',
            title='Резюме',
            content='Текст',
        )
        results = [
            {
                'entity_type': 'kb_article',
                'entity_id': str(article.pk),
                'text_content': 'заголовок',
                'metadata': {'entity_type': 'kb_article'},
                'similarity_score': 0.85,
            }
        ]
        enriched = EmbeddingService.enrich_kb_article_semantic_results(results)

        assert enriched[0]['metadata']['section_id'] == 'skills'
        assert enriched[0]['metadata']['filename'] == 'resume.md'
        assert enriched[0]['metadata']['title'] == 'Резюме'

    def test_enrich_kb_article_semantic_results_skips_complete_metadata(self):
        """Если section_id и filename уже есть — строка результата не меняется."""
        from knowledge_base_app.models import KBArticle, KBSection

        section = KBSection.objects.create(
            section_id='a',
            title='A',
            description='',
            icon='📄',
            order=0,
        )
        article = KBArticle.objects.create(
            section=section,
            filename='x.md',
            title='Old title',
            content='',
        )
        original_meta = {'section_id': 'legacy', 'filename': 'keep.md', 'title': 'T'}
        row = {
            'entity_type': 'kb_article',
            'entity_id': str(article.pk),
            'text_content': '',
            'metadata': original_meta,
            'similarity_score': 0.5,
        }
        enriched = EmbeddingService.enrich_kb_article_semantic_results([row])

        assert enriched[0]['metadata'] == original_meta

    @patch('vector_search.services.EmbeddingService.generate_embedding')
    def test_semantic_search_basic(self, mock_generate, vector_embedding_interview, interview):
        """Проверка базового семантического поиска."""
        # Мокируем генерацию эмбеддинга для запроса
        mock_generate.return_value = [0.1] * 1536

        results, search_time = EmbeddingService.semantic_search(
            query='test query',
            top_k=10,
            min_score=0.0
        )

        assert len(results) == 1

    @patch('vector_search.services.EmbeddingService.generate_embedding')
    def test_semantic_search_with_entity_type_filter(
        self,
        mock_generate,
        vector_embedding_interview,
        vector_embedding_intern
    ):
        """Проверка семантического поиска с фильтром по типу сущности."""
        mock_generate.return_value = [0.1] * 1536

        results, _ = EmbeddingService.semantic_search(
            query='test',
            entity_type='interview',
            top_k=10,
            min_score=0.0
        )

        # Проверяем что все результаты - интервью
        assert all(result['entity_type'] == 'interview' for result in results)

    @patch('vector_search.services.EmbeddingService.generate_embedding')
    def test_semantic_search_with_metadata_filters(
        self,
        mock_generate,
        vector_embedding_interview,
        interview
    ):
        """Проверка семантического поиска с фильтрами по метаданным."""
        mock_generate.return_value = [0.1] * 1536

        results, _ = EmbeddingService.semantic_search(
            query='test',
            filters={'direction_id': interview.direction_id},
            top_k=10,
            min_score=0.0
        )

        # Проверяем что все результаты соответствуют фильтру
        assert all(result['metadata'].get('direction_id') == interview.direction_id for result in results)

    @patch('vector_search.services.EmbeddingService.generate_embedding')
    def test_semantic_search_min_score_filter(self, mock_generate, vector_embedding_interview):
        """Проверка фильтрации по минимальному score."""
        mock_generate.return_value = [0.1] * 1536

        # С высоким порогом результатов может не быть
        results, _ = EmbeddingService.semantic_search(
            query='test',
            min_score=0.99,
            top_k=10
        )

        # Проверяем что все результаты имеют score >= min_score
        assert all(result['similarity_score'] >= 0.99 for result in results)

    @patch('vector_search.services.EmbeddingService.generate_embedding')
    def test_semantic_search_top_k_limit(self, mock_generate):
        """Проверка ограничения количества результатов."""
        # Создаём несколько эмбеддингов с уникальными entity_id
        base_id = 2000
        for i in range(5):
            VectorEmbedding.objects.create(
                entity_type='test',
                entity_id=base_id + i,
                text_content=f'Test {i}',
                embedding=[0.1] * 1536,
                metadata={}
            )

        mock_generate.return_value = [0.1] * 1536

        results, _ = EmbeddingService.semantic_search(
            query='test',
            top_k=3,
            min_score=0.0
        )

        # Не больше чем top_k
        assert len(results) <= 3

    def test_get_similar_entities_success(self, vector_embedding_interview, interview):
        """Проверка поиска похожих сущностей."""
        # Создаём ещё один похожий эмбеддинг с уникальным entity_id
        similar_id = 3000
        VectorEmbedding.objects.create(
            entity_type='interview',
            entity_id=similar_id,
            text_content='Similar interview',
            embedding=[0.11] * 1536,  # Похожий вектор
            metadata={}
        )

        results = EmbeddingService.get_similar_entities(
            entity_type='interview',
            entity_id=interview.id,
            top_k=5
        )

        assert isinstance(results, list)
        # Не должна включать саму себя
        assert all(result['entity_id'] != interview.id for result in results)

    def test_get_similar_entities_nonexistent(self):
        """Проверка поиска похожих для несуществующей сущности."""
        results = EmbeddingService.get_similar_entities(
            entity_type='interview',
            entity_id=99999,
            top_k=5
        )

        assert results == []

    def test_get_similar_entities_same_type_only(
        self,
        vector_embedding_interview,
        vector_embedding_intern,
        interview
    ):
        """Проверка что возвращаются только сущности того же типа."""
        results = EmbeddingService.get_similar_entities(
            entity_type='interview',
            entity_id=interview.id,
            top_k=10
        )

        # Не должно быть intern в результатах
        assert all(result['entity_type'] == 'interview' for result in results)

    def test_get_client_openai(self, mock_openai_embedding):
        """Проверка что get_client возвращает клиент (мокирован через conftest)."""
        client = EmbeddingService.get_client()
        assert client is not None

    @patch('vector_search.services.settings')
    def test_generate_embedding_truncates_long_text(self, mock_settings, mock_openai_embedding):
        """Проверка что длинный текст обрезается."""
        mock_settings.EMBEDDING_DIMENSION = 1536
        mock_settings.EMBEDDING_MODEL_NAME = 'text-embedding-3-small'

        # Очень длинный текст
        long_text = 'a' * 35000

        EmbeddingService.generate_embedding(long_text)

        # Проверяем что был вызван с обрезанным текстом
        call_args = mock_openai_embedding.embeddings.create.call_args
        input_text = call_args[1]['input']
        assert len(input_text) <= 30000

    def test_generate_embedding_api_exception_reraises(self, mock_openai_embedding):
        """При ошибке API исключение пробрасывается."""
        mock_openai_embedding.embeddings.create.side_effect = Exception('API error')
        with pytest.raises(Exception, match='API error'):
            EmbeddingService.generate_embedding('some text')

    def test_generate_embedding_wrong_dimension_raises(self, mock_openai_embedding):
        """Вектор чужой размерности не возвращается: в базе колонка 1536."""
        mock_openai_embedding.embeddings.create.return_value.data = [
            Mock(embedding=[0.5] * 100)
        ]
        with pytest.raises(ValueError, match='1536'):
            EmbeddingService.generate_embedding('text')

    def test_get_client_passes_base_url(self):
        """Реальный get_client передаёт адрес API эмбеддингов."""
        with patch.object(EmbeddingService, '_client', None):
            with patch('vector_search.services.settings') as mock_settings:
                mock_settings.OPENAI_API_KEY = 'test-embedding-key'
                mock_settings.OPENAI_BASE_URL = 'https://api.openai.com/v1'
                mock_settings.EMBEDDING_MODEL_NAME = 'text-embedding-3-small'
                with patch(
                    'vector_search.services.EmbeddingService.get_client',
                    _original_get_client,
                ):
                    with patch('openai.OpenAI') as mock_openai:
                        mock_openai.return_value = Mock()
                        EmbeddingService.get_client()
                        mock_openai.assert_called_once_with(
                            api_key='test-embedding-key',
                            base_url='https://api.openai.com/v1',
                        )

    def test_generate_embeddings_batch_exception_reraises(self, mock_openai_embedding):
        """При ошибке в батче исключение пробрасывается."""
        mock_openai_embedding.embeddings.create.side_effect = Exception('Batch API error')
        with pytest.raises(Exception, match='Batch API error'):
            EmbeddingService.generate_embeddings_batch(['a', 'b'], batch_size=10)

    def test_get_client_raises_when_openai_api_key_missing(self):
        """get_client поднимает ValueError, если OPENAI_API_KEY не задан."""
        with patch.object(EmbeddingService, '_client', None):
            with patch('vector_search.services.settings') as mock_settings:
                mock_settings.OPENAI_API_KEY = None
                mock_settings.EMBEDDING_MODEL_NAME = 'text-embedding-3-small'
                with patch(
                    'vector_search.services.EmbeddingService.get_client',
                    _original_get_client,
                ):
                    with pytest.raises(
                        ValueError,
                        match='OPENAI_API_KEY не установлен в настройках',
                    ):
                        EmbeddingService.get_client()

    def test_get_client_reraises_exception_from_openai_init(self):
        """Исключение при создании OpenAI-клиента пробрасывается."""
        with patch.object(EmbeddingService, '_client', None):
            with patch('vector_search.services.settings') as mock_settings:
                mock_settings.OPENAI_API_KEY = 'sk-test'
                mock_settings.EMBEDDING_MODEL_NAME = 'text-embedding-3-small'
                with patch(
                    'vector_search.services.EmbeddingService.get_client',
                    _original_get_client,
                ):
                    with patch('openai.OpenAI') as mock_openai:
                        mock_openai.side_effect = RuntimeError('OpenAI init failed')
                        with pytest.raises(RuntimeError, match='OpenAI init failed'):
                            EmbeddingService.get_client()

    @patch('os.environ.get')
    @patch('os.environ.get')
    @patch('vector_search.services.EmbeddingService.generate_embedding')
    def test_semantic_search_pgvector_branch_returns_mocked_results(
        self, mock_generate, mock_env_get, mock_openai_embedding
    ):
        """Ветка pgvector: при DJANGO_TESTING != '1' выполняется SQL и возвращаются результаты."""
        mock_env_get.return_value = None
        mock_generate.return_value = [0.1] * 1536
        fake_rows = [
            ('interview', '42', 'Текст', {'key': 'val'}, 0.95),
        ]
        mock_cursor = MagicMock()
        mock_cursor.description = [
            ('entity_type',), ('entity_id',), ('text_content',),
            ('metadata',), ('similarity_score',),
        ]
        mock_cursor.fetchall.return_value = fake_rows
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False
        with patch('vector_search.services.connections') as mock_connections:
            mock_connections.__getitem__.return_value = mock_conn
            results, search_time = EmbeddingService.semantic_search(
                query='test', top_k=5, min_score=0.0
            )
        assert len(results) == 1
        assert results[0]['entity_type'] == 'interview'
        assert results[0]['entity_id'] == '42'
        assert results[0]['text_content'] == 'Текст'
        assert results[0]['metadata'] == {'key': 'val'}
        assert results[0]['similarity_score'] == 0.95

    def test_get_similar_entities_with_manager_email_filter(
        self, vector_embedding_interview, interview
    ):
        """Фильтр manager_email оставляет только студентов с этим менеджером."""
        VectorEmbedding.objects.create(
            entity_type='interview',
            entity_id=9999,
            text_content='Other',
            embedding=[0.1] * 1536,
            metadata={'manager_email': 'other@example.com'},
        )
        VectorEmbedding.objects.create(
            entity_type='interview',
            entity_id=8888,
            text_content='Same manager',
            embedding=[0.11] * 1536,
            metadata={'manager_email': interview.manager_email},
        )
        results = EmbeddingService.get_similar_entities(
            entity_type='interview',
            entity_id=interview.id,
            top_k=10,
            manager_email=interview.manager_email,
        )
        assert len(results) == 1
        assert results[0]['entity_id'] == '8888'
        assert results[0]['metadata'].get('manager_email') == interview.manager_email

    @patch('os.environ.get')
    def test_get_similar_entities_pgvector_branch_returns_mocked_results(
        self, mock_env_get, vector_embedding_interview, interview
    ):
        """Ветка pgvector в get_similar_entities: мок cursor возвращает результаты."""
        mock_env_get.return_value = None
        fake_rows = [
            ('interview', '100', 'Similar', {'manager_email': 'm@ex.com'}, 0.88),
        ]
        mock_cursor = MagicMock()
        mock_cursor.description = [
            ('entity_type',), ('entity_id',), ('text_content',),
            ('metadata',), ('similarity_score',),
        ]
        mock_cursor.fetchall.return_value = fake_rows
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False
        with patch('vector_search.services.connections') as mock_connections:
            mock_connections.__getitem__.return_value = mock_conn
            results = EmbeddingService.get_similar_entities(
                entity_type='interview',
                entity_id=interview.id,
                top_k=5,
            )
        assert len(results) == 1
        assert results[0]['entity_type'] == 'interview'
        assert results[0]['entity_id'] == '100'
        assert results[0]['similarity_score'] == 0.88
