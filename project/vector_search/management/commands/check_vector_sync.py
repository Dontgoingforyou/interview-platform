"""
Management команда для диагностики расхождений между БД и векторным индексом.

Показывает по каждому типу сущности:
  - сколько объектов в БД
  - сколько эмбеддингов в vector_embeddings
  - разница (пропущенные / устаревшие)

Использование:
    python manage.py check_vector_sync
    python manage.py check_vector_sync --entity-type intern
    python manage.py check_vector_sync --fix        # запускает переиндексацию пропущенных
"""
import logging
from django.core.management.base import BaseCommand

from vector_search.models import VectorEmbedding
from vector_search.utils import VECTOR_ENTITY_TYPES

logger = logging.getLogger(__name__)

ENTITY_TYPES = list(VECTOR_ENTITY_TYPES)


def _get_db_ids(entity_type: str) -> set:
    """Возвращает множество entity_id (строк) всех объектов данного типа из БД."""
    if entity_type == 'interview':
        from interviews.models import Interview
        return {str(pk) for pk in Interview.objects.values_list('pk', flat=True)}

    elif entity_type == 'intern':
        from interns.models import Intern
        return {str(pk) for pk in Intern.objects.values_list('pk', flat=True)}

    elif entity_type == 'offer':
        from offers.models import Offer
        return {str(pk) for pk in Offer.objects.values_list('pk', flat=True)}

    elif entity_type == 'debt':
        from debts.models import Debt
        return {str(pk) for pk in Debt.objects.values_list('pk', flat=True)}

    elif entity_type == 'sad_intern':
        from sad_intern.models import SadIntern
        return {str(pk) for pk in SadIntern.objects.values_list('pk', flat=True)}

    elif entity_type == 'manager':
        from managers.models import Manager
        return {str(email) for email in Manager.objects.values_list('email', flat=True)}

    elif entity_type == 'company':
        from companies.models import Company
        return {str(pk) for pk in Company.objects.values_list('pk', flat=True)}

    elif entity_type == 'direction':
        from directions.models import Direction
        return {str(pk) for pk in Direction.objects.values_list('pk', flat=True)}

    elif entity_type == 'intern_weekly_status':
        from employees.models import InternWeeklyStatus
        return {str(pk) for pk in InternWeeklyStatus.objects.values_list('pk', flat=True)}

    elif entity_type == 'interview_transcription':
        from transcriptions.models import InterviewTranscription
        return {str(pk) for pk in InterviewTranscription.objects.values_list('pk', flat=True)}

    elif entity_type == 'kb_article':
        from knowledge_base_app.models import KBArticle
        return {str(pk) for pk in KBArticle.objects.values_list('pk', flat=True)}

    return set()


class Command(BaseCommand):
    help = 'Диагностика расхождений между БД и векторным индексом'

    def add_arguments(self, parser):
        parser.add_argument(
            '--entity-type',
            type=str,
            choices=ENTITY_TYPES,
            help='Проверить только конкретный тип сущности'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Запустить переиндексацию пропущенных объектов после диагностики'
        )

    def handle(self, *args, **options):
        entity_type = options['entity_type']
        fix = options['fix']

        types_to_check = [entity_type] if entity_type else ENTITY_TYPES

        self.stdout.write(self.style.SUCCESS('=== Диагностика векторного индекса ===\n'))

        total_missing = 0
        total_orphaned = 0
        types_with_issues = []

        for etype in types_to_check:
            self.stdout.write(self.style.NOTICE(f'--- {etype} ---'))

            db_ids = _get_db_ids(etype)
            emb_ids = set(
                VectorEmbedding.objects.filter(entity_type=etype)
                .values_list('entity_id', flat=True)
            )

            missing = db_ids - emb_ids       # есть в БД, нет эмбеддинга
            orphaned = emb_ids - db_ids      # есть эмбеддинг, объект удалён

            self.stdout.write(f'  Объектов в БД:          {len(db_ids)}')
            self.stdout.write(f'  Эмбеддингов в индексе:  {len(emb_ids)}')

            if missing:
                self.stdout.write(self.style.ERROR(f'  Пропущено (нет эмбеддинга): {len(missing)}'))
                total_missing += len(missing)
                types_with_issues.append(etype)
            else:
                self.stdout.write(self.style.SUCCESS('  Пропущено: 0'))

            if orphaned:
                self.stdout.write(self.style.WARNING(f'  Устаревших (объект удалён): {len(orphaned)}'))
                total_orphaned += len(orphaned)
            else:
                self.stdout.write(self.style.SUCCESS('  Устаревших: 0'))

            self.stdout.write('')

        # Итог
        self.stdout.write('=== Итог ===')
        if total_missing == 0 and total_orphaned == 0:
            self.stdout.write(self.style.SUCCESS('✓ Расхождений нет. Индекс синхронизирован.'))
        else:
            if total_missing:
                self.stdout.write(self.style.ERROR(f'✗ Пропущено объектов (нет эмбеддинга): {total_missing}'))
            if total_orphaned:
                self.stdout.write(self.style.WARNING(f'⚠ Устаревших эмбеддингов (объект удалён): {total_orphaned}'))
            self.stdout.write('')
            self.stdout.write('Для исправления запустите:')
            if types_with_issues:
                for etype in types_with_issues:
                    self.stdout.write(f'  python manage.py vectorize_data --entity-type {etype} --force')
            self.stdout.write('  или: python manage.py vectorize_data --all --force')

        # --fix: отправляем пропущенные типы на переиндексацию через Celery (асинхронно)
        if fix:
            if not types_with_issues:
                self.stdout.write(self.style.SUCCESS('\n--fix: нечего исправлять, индекс актуален.'))
                return

            self.stdout.write(self.style.NOTICE('\n--fix: планирую асинхронную переиндексацию через Celery...'))
            from django.core.management import call_command
            for etype in types_with_issues:
                try:
                    call_command('vectorize_async', '--entity-type', etype)
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {etype}: задачи отправлены в Celery'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Ошибка планирования {etype}: {e}'))
                    logger.error(f'Ошибка планирования переиндексации {etype}: {e}', exc_info=True)
            self.stdout.write(self.style.WARNING('\nПереиндексация выполняется в фоне через Celery-воркер.'))
