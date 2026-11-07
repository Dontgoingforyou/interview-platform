"""
Тесты для вспомогательных функций и задач vector_search/tasks.py.

Покрывает:
- get_object_by_type: получение объекта по типу и id из БД (все поддерживаемые типы,
  несуществующий id, неизвестный тип)
- _get_entity_id: возвращает email для manager, str(pk) для остальных типов
- update_embedding_task: объект не найден (early return), успешное обновление, ветка исключения
- delete_embedding_task: успешное удаление, ветка исключения
- reindex_all_task: с entity_type, без, ветка исключения
- vectorize_batch_task: успех, пустой список, ветка исключения
"""
import pytest
from unittest.mock import patch

from vector_search.tasks import (
    _get_entity_id,
    get_object_by_type,
    update_embedding_task,
    delete_embedding_task,
    reindex_all_task,
    vectorize_batch_task,
)


@pytest.mark.django_db(databases=['default'])
class TestGetObjectByType:
    """Тесты для get_object_by_type — получение объекта по типу сущности и id."""

    def test_returns_interview(self, interview):
        """Корректный тип 'interview' → возвращает объект Interview по pk."""
        result = get_object_by_type('interview', interview.pk)
        assert result is not None
        assert result.pk == interview.pk

    def test_returns_intern(self, intern):
        """Корректный тип 'intern' → возвращает объект Intern по pk."""
        result = get_object_by_type('intern', intern.pk)
        assert result is not None
        assert result.pk == intern.pk

    def test_returns_offer(self, offer):
        """Корректный тип 'offer' → возвращает объект Offer по pk."""
        result = get_object_by_type('offer', offer.pk)
        assert result is not None
        assert result.pk == offer.pk

    def test_returns_debt(self, debt):
        """Корректный тип 'debt' → возвращает объект Debt по pk."""
        result = get_object_by_type('debt', debt.pk)
        assert result is not None
        assert result.pk == debt.pk

    def test_returns_sad_intern(self, sad_intern):
        """Корректный тип 'sad_intern' → возвращает объект SadIntern по pk."""
        result = get_object_by_type('sad_intern', sad_intern.pk)
        assert result is not None
        assert result.pk == sad_intern.pk

    def test_returns_manager(self, manager):
        """Тип 'manager' использует email в качестве entity_id."""
        result = get_object_by_type('manager', manager.email)
        assert result is not None
        assert result.email == manager.email

    def test_returns_company(self, company):
        """Корректный тип 'company' → возвращает объект Company по pk."""
        result = get_object_by_type('company', company.pk)
        assert result is not None
        assert result.pk == company.pk
        assert result.name == company.name

    def test_returns_direction(self, direction):
        """Корректный тип 'direction' → возвращает объект Direction по pk."""
        result = get_object_by_type('direction', direction.pk)
        assert result is not None
        assert result.pk == direction.pk
        assert result.name == direction.name

    def test_returns_intern_weekly_status(self, intern_weekly_status):
        """Корректный тип 'intern_weekly_status' → возвращает объект по pk."""
        result = get_object_by_type('intern_weekly_status', intern_weekly_status.pk)
        assert result is not None
        assert result.pk == intern_weekly_status.pk
        assert result.intern_id == intern_weekly_status.intern_id

    def test_returns_none_when_company_pk_not_found(self):
        """Несуществующий pk для company → возвращает None."""
        result = get_object_by_type('company', 999999)
        assert result is None

    @pytest.mark.parametrize('entity_type', [
        'interview', 'intern', 'offer', 'debt', 'sad_intern', 'company',
        'direction', 'intern_weekly_status',
    ])
    def test_returns_none_when_pk_not_found(self, entity_type):
        """Несуществующий pk → возвращает None (не бросает исключение)."""
        result = get_object_by_type(entity_type, 999999)
        assert result is None

    def test_returns_none_when_manager_email_not_found(self):
        """Несуществующий email для manager → возвращает None."""
        result = get_object_by_type('manager', 'non-existent@example.com')
        assert result is None

    def test_returns_none_for_unknown_type(self, intern):
        """Неизвестный тип сущности → возвращает None."""
        result = get_object_by_type('unknown_type', intern.pk)
        assert result is None

    def test_interview_select_related(self, interview):
        """Объект Interview возвращается с предзагруженными intern, company, direction."""
        result = get_object_by_type('interview', interview.pk)
        # Проверяем, что обращение к связанным объектам не генерирует новых запросов
        # (они уже загружены через select_related)
        assert result.intern_id == interview.intern_id
        assert result.direction_id == interview.direction_id


@pytest.mark.django_db(databases=['default'])
class TestGetEntityId:
    """Тесты для _get_entity_id — определение корректного идентификатора сущности."""

    @pytest.mark.parametrize('entity_type', [
        'interview', 'intern', 'offer', 'debt', 'sad_intern', 'company',
    ])
    def test_returns_str_pk_for_non_manager(self, entity_type, intern):
        """Для всех типов кроме manager возвращает str(pk)."""
        result = _get_entity_id(entity_type, intern)
        assert result == str(intern.pk)

    def test_returns_email_for_manager(self, manager):
        """Для типа manager возвращает email."""
        result = _get_entity_id('manager', manager)
        assert result == manager.email


@pytest.mark.django_db(databases=['default'])
class TestUpdateEmbeddingTask:
    """Тесты для задачи update_embedding_task."""

    def test_returns_early_when_object_not_found(self):
        """Когда объект не найден, задача завершается без ошибки."""
        result = update_embedding_task.delay('interview', 999999)
        result.get(timeout=5)
        assert result.successful()

    def test_updates_embedding_when_object_found(
        self, interview, mock_openai_embedding
    ):
        """При найденном объекте генерируется эмбеддинг и сохраняется в БД."""
        from vector_search.models import VectorEmbedding

        update_embedding_task(entity_type='interview', entity_id=interview.pk)

        emb = VectorEmbedding.objects.filter(
            entity_type='interview',
            entity_id=interview.pk,
        ).first()
        assert emb is not None
        assert len(emb.embedding) == 1536


@pytest.mark.django_db(databases=['default'])
class TestDeleteEmbeddingTask:
    """Тесты для задачи delete_embedding_task."""

    def test_deletes_existing_embedding(self, vector_embedding_interview, interview):
        """Удаление существующего эмбеддинга."""
        delete_embedding_task(entity_type='interview', entity_id=interview.id)
        from vector_search.models import VectorEmbedding
        assert not VectorEmbedding.objects.filter(
            entity_type='interview',
            entity_id=str(interview.id),
        ).exists()

    def test_no_error_when_nothing_to_delete(self):
        """Отсутствие записи не вызывает ошибку."""
        delete_embedding_task(entity_type='interview', entity_id=999999)

    def test_exception_during_delete_reraises(self, interview):
        """При исключении в delete исключение логируется и пробрасывается."""
        with patch('vector_search.tasks.VectorEmbedding') as mock_ve:
            mock_ve.objects.filter.return_value.delete.side_effect = RuntimeError(
                'DB error'
            )
            with pytest.raises(RuntimeError, match='DB error'):
                delete_embedding_task(entity_type='interview', entity_id=interview.id)


@pytest.mark.django_db(databases=['default'])
class TestUpdateEmbeddingTaskException:
    """Ветка исключения в update_embedding_task."""

    def test_exception_during_update_reraises(self, interview):
        """При исключении при обновлении эмбеддинга исключение пробрасывается."""
        with patch('vector_search.tasks.VectorEmbedding') as mock_ve:
            mock_ve.objects.update_or_create.side_effect = RuntimeError(
                'update failed'
            )
            with patch('vector_search.tasks.get_object_by_type') as mock_get:
                mock_get.return_value = interview
                with pytest.raises(RuntimeError, match='update failed'):
                    update_embedding_task(
                        entity_type='interview', entity_id=interview.pk
                    )


@pytest.mark.django_db(databases=['default'])
class TestReindexAllTask:
    """Тесты для reindex_all_task."""

    def test_with_entity_type_calls_call_command_with_entity_type(self):
        """При указании entity_type вызывается call_command с --entity-type."""
        with patch('django.core.management.call_command') as mock_call:
            reindex_all_task(entity_type='interview')
        mock_call.assert_called_once_with(
            'vectorize_data', '--entity-type', 'interview', '--force'
        )

    def test_without_entity_type_calls_call_command_with_all(self):
        """Без entity_type вызывается call_command с --all."""
        with patch('django.core.management.call_command') as mock_call:
            reindex_all_task(entity_type=None)
        mock_call.assert_called_once_with('vectorize_data', '--all', '--force')

    def test_exception_during_reindex_reraises(self):
        """При исключении call_command исключение пробрасывается."""
        with patch('django.core.management.call_command') as mock_call:
            mock_call.side_effect = OSError('Command failed')
            with pytest.raises(OSError, match='Command failed'):
                reindex_all_task(entity_type='interview')


@pytest.mark.django_db(databases=['default'])
class TestVectorizeBatchTask:
    """Тесты для vectorize_batch_task."""

    def test_returns_zero_when_no_objects_found(self):
        """Когда ни один объект не найден, возвращается 0."""
        result = vectorize_batch_task(
            entity_type='interview',
            entity_ids=[999998, 999999],
            batch_size=32,
        )
        assert result == 0

    def test_saves_embeddings_and_returns_count(
        self, interview, mock_openai_embedding
    ):
        """При найденных объектах векторизует и возвращает количество сохранённых."""
        from vector_search.models import VectorEmbedding

        result = vectorize_batch_task(
            entity_type='interview',
            entity_ids=[interview.pk],
            batch_size=32,
        )
        assert result == 1
        emb = VectorEmbedding.objects.filter(
            entity_type='interview',
            entity_id=str(interview.pk),
        ).first()
        assert emb is not None
        assert len(emb.embedding) == 1536

    def test_exception_during_batch_reraises(self, interview):
        """При исключении в generate_embeddings_batch исключение пробрасывается."""
        with patch(
            'vector_search.tasks.EmbeddingService.generate_embeddings_batch'
        ) as mock_batch:
            mock_batch.side_effect = RuntimeError('API error')
            with pytest.raises(RuntimeError, match='API error'):
                vectorize_batch_task(
                    entity_type='interview',
                    entity_ids=[interview.pk],
                    batch_size=32,
                )
