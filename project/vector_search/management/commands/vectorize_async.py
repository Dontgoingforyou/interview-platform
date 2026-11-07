"""
Management команда для асинхронной векторизации данных через Celery.

Использование:
    python manage.py vectorize_async --all
    python manage.py vectorize_async --entity-type interview
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from vector_search.tasks import vectorize_batch_task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Асинхронная векторизация данных через Celery'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Векторизовать все типы сущностей'
        )

        parser.add_argument(
            '--entity-type',
            type=str,
            choices=[
                'interview', 'intern', 'offer', 'debt', 'sad_intern', 'manager', 'company',
                'direction', 'intern_weekly_status'
            ],
            help='Векторизовать конкретный тип сущности'
        )

        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Размер батча для отправки в Celery (по умолчанию: 100)'
        )

    def handle(self, *args, **options):
        all_entities = options['all']
        entity_type = options['entity_type']
        batch_size = options['batch_size']

        if not all_entities and not entity_type:
            raise CommandError('Укажите --all или --entity-type')

        # Определяем, какие типы обрабатывать
        if all_entities:
            entity_types = [
                'interview', 'intern', 'offer', 'debt', 'sad_intern', 'manager', 'company',
                'direction', 'intern_weekly_status'
            ]
        else:
            entity_types = [entity_type]

        self.stdout.write(self.style.SUCCESS(f'Запускаю асинхронную векторизацию: {", ".join(entity_types)}'))
        self.stdout.write(f'Batch size: {batch_size}')

        total_tasks = 0

        for etype in entity_types:
            self.stdout.write(self.style.NOTICE(f'\n=== Обработка: {etype} ==='))
            tasks_count = self.schedule_vectorization(etype, batch_size)
            total_tasks += tasks_count
            self.stdout.write(self.style.SUCCESS(f'✓ Запланировано задач для {etype}: {tasks_count}'))

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Всего запланировано задач: {total_tasks}')
        )
        self.stdout.write(
            self.style.WARNING('\nЗадачи выполняются в фоне. Проверить статус: docker compose logs -f celery_worker')
        )

    def schedule_vectorization(self, entity_type: str, batch_size: int) -> int:
        """
        Планирует задачи векторизации для типа сущности.

        Args:
            entity_type: Тип сущности
            batch_size: Размер батча

        Returns:
            Количество запланированных задач
        """
        # Получаем все объекты
        objects = self.get_objects_by_type(entity_type)

        if not objects:
            self.stdout.write(self.style.WARNING(f'  Объектов не найдено для {entity_type}'))
            return 0

        self.stdout.write(f'  Найдено объектов: {len(objects)}')

        # Разбиваем на батчи и отправляем в Celery
        tasks_count = 0
        for i in range(0, len(objects), batch_size):
            batch_ids = objects[i:i + batch_size]

            # Запускаем Celery задачу
            vectorize_batch_task.delay(entity_type, batch_ids, batch_size=32)
            tasks_count += 1

        return tasks_count

    def get_objects_by_type(self, entity_type: str):
        """
        Получает все объекты определенного типа из БД.

        Args:
            entity_type: Тип сущности

        Returns:
            Список объектов
        """
        if entity_type == 'interview':
            from interviews.models import Interview
            return list(Interview.objects.all().values_list('pk', flat=True))

        elif entity_type == 'intern':
            from interns.models import Intern
            return list(Intern.objects.all().values_list('pk', flat=True))

        elif entity_type == 'offer':
            from offers.models import Offer
            return list(Offer.objects.all().values_list('pk', flat=True))

        elif entity_type == 'debt':
            from debts.models import Debt
            return list(Debt.objects.all().values_list('pk', flat=True))

        elif entity_type == 'sad_intern':
            from sad_intern.models import SadIntern
            return list(SadIntern.objects.all().values_list('pk', flat=True))

        elif entity_type == 'manager':
            from managers.models import Manager
            return list(Manager.objects.all().values_list('email', flat=True))

        elif entity_type == 'company':
            from companies.models import Company
            return list(Company.objects.all().values_list('pk', flat=True))

        elif entity_type == 'direction':
            from directions.models import Direction
            return list(Direction.objects.all().values_list('pk', flat=True))

        elif entity_type == 'intern_weekly_status':
            from employees.models import InternWeeklyStatus
            return list(InternWeeklyStatus.objects.all().values_list('pk', flat=True))

        return []
