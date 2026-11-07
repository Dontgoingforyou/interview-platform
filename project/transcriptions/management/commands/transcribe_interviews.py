import logging
from datetime import date as date_type

from django.core.management.base import BaseCommand
from django.db.models import F, Q

from interviews.models import Interview
from transcriptions.models import InterviewTranscription, TranscriptionStatus

logger = logging.getLogger(__name__)

# Стоимость Deepgram Nova-2 за минуту аудио (USD)
_DEEPGRAM_PRICE_PER_MINUTE = 0.0043
# Средняя длина собеседования в минутах для оценки стоимости
_AVG_INTERVIEW_MINUTES = 45
# Rate limit задачи transcribe_interview (задач/минуту) — должен совпадать с tasks.py
_TASK_RATE_LIMIT_PER_MINUTE = 30


def _loose_transcription_media_q() -> Q:
    """Грубый отбор кандидатов; точное соответствие — через Interview.transcription_media_url."""
    return (
        (Q(video_link__isnull=False) & ~Q(video_link=''))
        | Q(link__icontains='disk.yandex')
        | Q(link__icontains='yadi.sk')
        | Q(link__icontains='360.yandex')
        | Q(interview_link__icontains='disk.yandex')
        | Q(interview_link__icontains='yadi.sk')
        | Q(interview_link__icontains='360.yandex')
    )


class Command(BaseCommand):
    help = (
        'Пакетная транскрипция видеозаписей собеседований через Deepgram API.\n'
        'По умолчанию добавляет в очередь все необработанные записи.\n'
        '\n'
        'Примеры:\n'
        '  python manage.py transcribe_interviews --dry-run\n'
        '  python manage.py transcribe_interviews --from-year=2025 --dry-run\n'
        '  python manage.py transcribe_interviews --from-year=2025 --batch-size=50\n'
        '  python manage.py transcribe_interviews --limit=100\n'
        '  python manage.py transcribe_interviews --reset-balance-flag\n'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Показать количество записей и примерную стоимость без запуска задач',
        )
        parser.add_argument(
            '--from-year',
            type=int,
            default=None,
            help='Транскрибировать только собесы с датой >= 1 января указанного года (например, 2025)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Максимальное количество записей для обработки',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Размер батча для постановки задач в очередь (по умолчанию 50)',
        )
        parser.add_argument(
            '--retry-failed',
            action='store_true',
            default=False,
            help='Включить в обработку записи со статусом failed (по умолчанию — нет)',
        )
        parser.add_argument(
            '--reset-balance-flag',
            action='store_true',
            default=False,
            help='Сбросить флаг остановки из-за нулевого баланса Deepgram и продолжить работу',
        )

    def handle(self, *args, **options):
        from django.core.cache import cache
        from transcriptions.tasks import _BALANCE_EXHAUSTED_CACHE_KEY

        dry_run = options['dry_run']
        from_year = options['from_year']
        limit = options['limit']
        batch_size = options['batch_size']
        retry_failed = options['retry_failed']
        reset_balance_flag = options['reset_balance_flag']

        if reset_balance_flag:
            cache.delete(_BALANCE_EXHAUSTED_CACHE_KEY)
            self.stdout.write(self.style.SUCCESS(
                'Флаг остановки из-за нулевого баланса Deepgram сброшен. Транскрипция доступна.'
            ))
            if not dry_run:
                return

        if cache.get(_BALANCE_EXHAUSTED_CACHE_KEY):
            self.stdout.write(self.style.ERROR(
                '\n[СТОП] Баланс Deepgram исчерпан — транскрипция заблокирована.\n'
                'Пополните счёт на https://console.deepgram.com/ и затем выполните:\n'
                '  python manage.py transcribe_interviews --reset-balance-flag'
            ))
            return

        qs = Interview.objects.filter(_loose_transcription_media_q())
        if from_year:
            qs = qs.filter(date__gte=date_type(from_year, 1, 1))

        eligible_pks = []
        for inv in (
            qs
            .only('id', 'video_link', 'link', 'interview_link')
            .order_by(F('date').desc(nulls_last=True), '-pk')
            .iterator(chunk_size=500)
        ):
            if inv.transcription_media_url:
                eligible_pks.append(inv.pk)

        already_completed_ids = set(
            InterviewTranscription.objects.filter(
                status=TranscriptionStatus.COMPLETED,
                interview_id__in=eligible_pks,
            ).values_list('interview_id', flat=True)
        )
        in_progress_ids = set(
            InterviewTranscription.objects.filter(
                status=TranscriptionStatus.PROCESSING,
                interview_id__in=eligible_pks,
            ).values_list('interview_id', flat=True)
        )
        if not retry_failed:
            failed_ids = set(
                InterviewTranscription.objects.filter(
                    status=TranscriptionStatus.FAILED,
                    interview_id__in=eligible_pks,
                ).values_list('interview_id', flat=True)
            )
        else:
            failed_ids = set()

        filtered_pks = [
            pk
            for pk in eligible_pks
            if pk not in already_completed_ids
            and pk not in in_progress_ids
            and (retry_failed or pk not in failed_ids)
        ]

        total = len(filtered_pks)

        if limit:
            filtered_pks = filtered_pks[:limit]
        count = len(filtered_pks)

        estimated_minutes = count * _AVG_INTERVIEW_MINUTES
        estimated_hours = estimated_minutes / 60
        estimated_cost = estimated_minutes * _DEEPGRAM_PRICE_PER_MINUTE
        estimated_queue_minutes = count / _TASK_RATE_LIMIT_PER_MINUTE

        year_label = f' (с {from_year} года)' if from_year else ''
        self.stdout.write(self.style.HTTP_INFO(
            f'\n=== Транскрипция собеседований{year_label} ==='
        ))
        self.stdout.write(f'Всего необработанных записей с URL для транскрипции: {total}')
        self.stdout.write(f'Будет обработано: {count}')
        self.stdout.write(
            f'Примерное время обработки: ~{estimated_hours:.1f} ч. '
            f'(при {_AVG_INTERVIEW_MINUTES} мин./собесе) — оценка стоимости'
        )
        self.stdout.write(
            f'Примерное время очереди: ~{estimated_queue_minutes:.0f} мин. '
            f'(rate_limit={_TASK_RATE_LIMIT_PER_MINUTE}/мин)'
        )
        self.stdout.write(
            f'Примерная стоимость (Deepgram Nova-2): ~${estimated_cost:.2f}'
        )

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\n[dry-run] Задачи не запущены. Уберите --dry-run для реального запуска.'
            ))
            return

        if count == 0:
            self.stdout.write(self.style.SUCCESS('Нет записей для обработки.'))
            return

        from transcriptions.tasks import transcribe_interview

        enqueued = 0
        interview_ids = filtered_pks

        for i in range(0, len(interview_ids), batch_size):
            batch = interview_ids[i:i + batch_size]
            for interview_id in batch:
                obj, _ = InterviewTranscription.objects.get_or_create(
                    interview_id=interview_id
                )
                InterviewTranscription.objects.filter(pk=obj.pk).update(
                    status=TranscriptionStatus.PENDING,
                    error_message=None,
                )
                transcribe_interview.delay(obj.pk)
                enqueued += 1

            self.stdout.write(f'  Поставлено в очередь: {enqueued}/{count}...')

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово: {enqueued} задач поставлено в очередь Celery.'
        ))
        logger.info(
            '[ТРАНСКРИПЦИЯ] Management command: поставлено в очередь %d задач', enqueued
        )
