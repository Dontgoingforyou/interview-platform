import logging
from celery import shared_task

from vector_search.models import VectorEmbedding
from vector_search.services import EmbeddingService
from vector_search.utils import (
    ENTITY_COMPANY,
    ENTITY_DEBT,
    ENTITY_DIRECTION,
    ENTITY_INTERN,
    ENTITY_INTERN_WEEKLY_STATUS,
    ENTITY_INTERVIEW,
    ENTITY_INTERVIEW_TRANSCRIPTION,
    ENTITY_KB_ARTICLE,
    ENTITY_MANAGER,
    ENTITY_OFFER,
    ENTITY_SAD_INTERN,
    extract_metadata,
    extract_text_from_entity,
)

logger = logging.getLogger(__name__)

# Исключения, при которых имеет смысл повторять попытку (сетевые ошибки OpenAI, временные сбои БД)
_RETRY_EXCEPTIONS = (Exception,)
_RETRY_KWARGS = {
    'autoretry_for': _RETRY_EXCEPTIONS,
    'max_retries': 3,
    'retry_backoff': True,
    'retry_backoff_max': 60,
    'retry_jitter': True,
    'soft_time_limit': 55,
    'time_limit': 60,
}


@shared_task(name='vector_search.update_embedding', **_RETRY_KWARGS)
def update_embedding_task(entity_type: str, entity_id: str):
    """
    Обновляет эмбеддинг для конкретной сущности.

    Args:
        entity_type: Тип сущности (interview, intern, etc.)
        entity_id: ID сущности
    """
    try:
        # Получаем объект из БД
        obj = get_object_by_type(entity_type, entity_id)

        if not obj:
            logger.warning(f'Объект не найден: {entity_type}#{entity_id}')
            return

        # Извлекаем текст и метаданные
        text = extract_text_from_entity(entity_type, obj)
        metadata = extract_metadata(obj, entity_type)

        # Генерируем эмбеддинг
        embedding = EmbeddingService.generate_embedding(text)

        # Сохраняем/обновляем в основной БД
        VectorEmbedding.objects.update_or_create(
            entity_type=entity_type,
            entity_id=entity_id,
            defaults={
                'text_content': text,
                'embedding': embedding,
                'metadata': metadata
            }
        )

        logger.info(f'✓ Обновлен эмбеддинг: {entity_type}#{entity_id}')

    except Exception as e:
        logger.error(f'Ошибка обновления эмбеддинга {entity_type}#{entity_id}: {e}', exc_info=True)
        raise


@shared_task(name='vector_search.delete_embedding', **_RETRY_KWARGS)
def delete_embedding_task(entity_type: str, entity_id: str):
    """
    Удаляет эмбеддинг для удаленной сущности.

    Args:
        entity_type: Тип сущности
        entity_id: ID сущности
    """
    try:
        deleted_count, _ = VectorEmbedding.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id
        ).delete()

        if deleted_count > 0:
            logger.info(f'✓ Удален эмбеддинг: {entity_type}#{entity_id}')

    except Exception as e:
        logger.error(f'Ошибка удаления эмбеддинга {entity_type}#{entity_id}: {e}', exc_info=True)
        raise


@shared_task(name='vector_search.reindex_all', soft_time_limit=3600, time_limit=3660)
def reindex_all_task(entity_type: str = None):
    """
    Переиндексирует все данные (или конкретный тип).

    Args:
        entity_type: Тип сущности (опционально)
    """
    from django.core.management import call_command

    try:
        if entity_type:
            logger.info(f'Начинаю переиндексацию: {entity_type}')
            call_command('vectorize_data', '--entity-type', entity_type, '--force')
        else:
            logger.info('Начинаю полную переиндексацию')
            call_command('vectorize_data', '--all', '--force')

        logger.info('✓ Переиндексация завершена')

    except Exception as e:
        logger.error(f'Ошибка переиндексации: {e}', exc_info=True)
        raise


@shared_task(name='vector_search.vectorize_batch', soft_time_limit=600, time_limit=660)
def vectorize_batch_task(entity_type: str, entity_ids: list, batch_size: int = 32):
    """
    Векторизирует батч объектов определенного типа.

    Args:
        entity_type: Тип сущности
        entity_ids: Список ID объектов для векторизации
        batch_size: Размер батча для генерации эмбеддингов
    """
    from django.db import transaction

    try:
        logger.info(f'Начинаю векторизацию батча {entity_type}: {len(entity_ids)} объектов')

        # Получаем объекты
        objects = []
        for entity_id in entity_ids:
            obj = get_object_by_type(entity_type, entity_id)
            if obj:
                objects.append(obj)

        if not objects:
            logger.warning(f'Объекты не найдены для {entity_type}')
            return 0

        # Извлекаем тексты и метаданные
        texts = []
        metadata_list = []
        for obj in objects:
            text = extract_text_from_entity(entity_type, obj)
            metadata = extract_metadata(obj, entity_type)
            texts.append(text)
            metadata_list.append(metadata)

        # Генерируем эмбеддинги
        embeddings = EmbeddingService.generate_embeddings_batch(texts, batch_size)

        # Сохраняем в БД
        saved_count = 0
        with transaction.atomic():
            for obj, text, embedding, metadata in zip(objects, texts, embeddings, metadata_list):
                entity_id = _get_entity_id(entity_type, obj)
                VectorEmbedding.objects.update_or_create(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    defaults={
                        'text_content': text,
                        'embedding': embedding,
                        'metadata': metadata
                    }
                )
                saved_count += 1

        logger.info(f'✓ Векторизировано {saved_count} объектов {entity_type}')
        return saved_count

    except Exception as e:
        logger.error(f'Ошибка векторизации батча {entity_type}: {e}', exc_info=True)
        raise


def _get_entity_id(entity_type: str, obj) -> str:
    """
    Возвращает правильный entity_id для объекта.

    Для Manager используется email (уникальный и стабильный идентификатор),
    для остальных — строковое представление pk.
    """
    if entity_type == ENTITY_MANAGER:
        return obj.email
    return str(obj.pk)


def get_object_by_type(entity_type: str, entity_id):
    """
    Получает объект по типу и ID.

    Args:
        entity_type: Тип сущности
        entity_id: ID (для manager — email, для остальных — pk)

    Returns:
        Объект модели или None
    """
    try:
        if entity_type == ENTITY_INTERVIEW:
            from interviews.models import Interview
            return Interview.objects.select_related('intern', 'company', 'direction').get(pk=entity_id)

        elif entity_type == ENTITY_INTERN:
            from interns.models import Intern
            return Intern.objects.select_related('direction').get(pk=entity_id)

        elif entity_type == ENTITY_OFFER:
            from offers.models import Offer
            return Offer.objects.select_related('intern', 'direction').get(pk=entity_id)

        elif entity_type == ENTITY_DEBT:
            from debts.models import Debt
            return Debt.objects.select_related('intern', 'direction').get(pk=entity_id)

        elif entity_type == ENTITY_SAD_INTERN:
            from sad_intern.models import SadIntern
            return SadIntern.objects.select_related('intern').get(pk=entity_id)

        elif entity_type == ENTITY_MANAGER:
            from managers.models import Manager
            return Manager.objects.get(email=entity_id)

        elif entity_type == ENTITY_COMPANY:
            from companies.models import Company
            return Company.objects.get(pk=entity_id)

        elif entity_type == ENTITY_DIRECTION:
            from directions.models import Direction
            return Direction.objects.get(pk=entity_id)

        elif entity_type == ENTITY_INTERN_WEEKLY_STATUS:
            from employees.models import InternWeeklyStatus
            return InternWeeklyStatus.objects.select_related('intern').get(pk=entity_id)

        elif entity_type == ENTITY_INTERVIEW_TRANSCRIPTION:
            from transcriptions.models import InterviewTranscription
            return InterviewTranscription.objects.select_related(
                'interview', 'interview__direction', 'interview__intern'
            ).get(pk=entity_id)

        elif entity_type == ENTITY_KB_ARTICLE:
            from knowledge_base_app.models import KBArticle
            return KBArticle.objects.select_related('section').get(pk=entity_id)

    except Exception as e:
        logger.warning('Не удалось получить сущность %s#%s: %s', entity_type, entity_id, e)
        return None

    return None
