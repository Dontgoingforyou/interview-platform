"""Синхронная векторизация. Большой объём лучше гонять через vectorize_async."""
import logging
from typing import List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from vector_search.models import VectorEmbedding
from vector_search.services import EmbeddingService
from vector_search.utils import VECTOR_ENTITY_TYPES, extract_metadata, extract_text_from_entity

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Векторизация данных из БД для семантического поиска'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Векторизовать все типы сущностей'
        )

        parser.add_argument(
            '--entity-type',
            type=str,
            choices=list(VECTOR_ENTITY_TYPES),
            help='Векторизовать конкретный тип сущности'
        )

        parser.add_argument(
            '--batch-size',
            type=int,
            default=32,
            help='Размер батча для генерации эмбеддингов (по умолчанию: 32)'
        )

        parser.add_argument(
            '--force',
            action='store_true',
            help='Перезаписать существующие эмбеддинги'
        )

    def handle(self, *args, **options):
        all_entities = options['all']
        entity_type = options['entity_type']
        batch_size = options['batch_size']
        force = options['force']

        if not all_entities and not entity_type:
            raise CommandError('Укажите --all или --entity-type')

        # Определяем, какие типы обрабатывать
        if all_entities:
            entity_types = list(VECTOR_ENTITY_TYPES)
        else:
            entity_types = [entity_type]

        self.stdout.write(self.style.SUCCESS(f'Начинаю векторизацию: {", ".join(entity_types)}'))
        self.stdout.write(f'Batch size: {batch_size}')

        total_processed = 0

        for etype in entity_types:
            self.stdout.write(self.style.NOTICE(f'\n=== Обработка: {etype} ==='))
            processed = self.vectorize_entity_type(etype, batch_size, force)
            total_processed += processed
            self.stdout.write(self.style.SUCCESS(f'✓ Обработано {etype}: {processed} записей'))

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Всего обработано: {total_processed} записей')
        )

    @staticmethod
    def _get_entity_id(entity_type: str, obj) -> str:
        """
        Возвращает правильный entity_id для объекта.

        Для Manager используется email (уникальный и стабильный идентификатор),
        для остальных — строковое представление pk.
        """
        if entity_type == 'manager':
            return obj.email
        return str(obj.pk)

    def vectorize_entity_type(self, entity_type: str, batch_size: int, force: bool) -> int:
        """
        Векторизует все объекты определенного типа.

        Args:
            entity_type: Тип сущности
            batch_size: Размер батча
            force: Перезаписать существующие

        Returns:
            Количество обработанных записей
        """
        # Получаем все объекты из БД
        objects = self.get_objects_by_type(entity_type)

        if not objects:
            self.stdout.write(self.style.WARNING(f'  Объектов не найдено для {entity_type}'))
            return 0

        self.stdout.write(f'  Найдено объектов: {len(objects)}')

        if force:
            # Удаляем ВСЕ существующие эмбеддинги этого типа (включая устаревшие с другими ID)
            deleted_count, _ = VectorEmbedding.objects.filter(entity_type=entity_type).delete()
            if deleted_count:
                self.stdout.write(f'  Удалено устаревших эмбеддингов: {deleted_count}')
        else:
            # Исключаем уже обработанные
            existing_ids = set(
                VectorEmbedding.objects.filter(entity_type=entity_type)
                .values_list('entity_id', flat=True)
            )
            objects = [obj for obj in objects if self._get_entity_id(entity_type, obj) not in existing_ids]
            self.stdout.write(f'  Новых для обработки: {len(objects)}')

        if not objects:
            return 0

        # Извлекаем тексты и генерируем эмбеддинги по частям
        self.stdout.write('  Генерация и сохранение эмбеддингов...')
        saved_count = 0
        PROCESS_BATCH_SIZE = 100  # Обрабатываем по 100 объектов за раз

        for i in range(0, len(objects), PROCESS_BATCH_SIZE):
            batch_objects = objects[i:i + PROCESS_BATCH_SIZE]

            # Извлекаем тексты для батча
            texts = []
            metadata_list = []
            for obj in batch_objects:
                text = extract_text_from_entity(entity_type, obj)
                metadata = extract_metadata(obj, entity_type)
                texts.append(text)
                metadata_list.append(metadata)

            # Генерируем эмбеддинги для батча
            embeddings = EmbeddingService.generate_embeddings_batch(texts, batch_size)

            # Сохраняем в БД с транзакцией
            with transaction.atomic():
                for obj, text, embedding, metadata in zip(batch_objects, texts, embeddings, metadata_list):
                    entity_id = self._get_entity_id(entity_type, obj)
                    VectorEmbedding.objects.update_or_create(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        defaults={
                            'text_content': text,
                            'embedding': embedding,
                            'metadata': metadata,
                        }
                    )
                    saved_count += 1

            if saved_count % 100 == 0:
                self.stdout.write(f'    Сохранено: {saved_count}/{len(objects)}')

        return saved_count

    def get_objects_by_type(self, entity_type: str) -> List:
        """
        Получает все объекты определенного типа из БД.

        Args:
            entity_type: Тип сущности

        Returns:
            Список объектов
        """
        if entity_type == 'interview':
            from interviews.models import Interview
            return list(Interview.objects.select_related('intern', 'company', 'direction').all())

        elif entity_type == 'intern':
            from interns.models import Intern
            return list(Intern.objects.select_related('direction').all())

        elif entity_type == 'offer':
            from offers.models import Offer
            return list(Offer.objects.select_related('intern', 'direction').all())

        elif entity_type == 'debt':
            from debts.models import Debt
            return list(Debt.objects.select_related('intern', 'direction').all())

        elif entity_type == 'sad_intern':
            from sad_intern.models import SadIntern
            return list(SadIntern.objects.select_related('intern').all())

        elif entity_type == 'manager':
            from managers.models import Manager
            return list(Manager.objects.all())

        elif entity_type == 'company':
            from companies.models import Company
            return list(Company.objects.all())

        elif entity_type == 'direction':
            from directions.models import Direction
            return list(Direction.objects.all())

        elif entity_type == 'intern_weekly_status':
            from employees.models import InternWeeklyStatus
            return list(InternWeeklyStatus.objects.select_related('intern').all())

        elif entity_type == 'kb_article':
            from knowledge_base_app.models import KBArticle
            return list(KBArticle.objects.select_related('section').all())

        elif entity_type == 'interview_transcription':
            from transcriptions.models import InterviewTranscription
            return list(
                InterviewTranscription.objects.select_related(
                    'interview', 'interview__direction', 'interview__intern',
                ).all()
            )

        return []
