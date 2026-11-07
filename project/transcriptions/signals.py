import logging
from datetime import timedelta

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from core.logging_mixins import log_signal
from interviews.models import INTERVIEW_TRANSCRIPTION_URL_FIELDS, Interview
from transcriptions.constants import TRANSCRIPTION_PENDING_COOLDOWN_MINUTES
from transcriptions.models import InterviewTranscription, TranscriptionStatus

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Interview)
@log_signal('post_save', 'transcriptions.signals')
def on_interview_video_link_saved(sender, instance, created, update_fields, **kwargs):
    """
    Запускает транскрипцию при появлении или изменении полей с URL для транскрипции у Interview.
    Не срабатывает если сохранение не затрагивало video_link / link / interview_link.
    """
    if not created and update_fields is not None:
        if not set(update_fields) & INTERVIEW_TRANSCRIPTION_URL_FIELDS:
            return

    if not instance.transcription_media_url:
        return

    from transcriptions.tasks import transcribe_interview

    obj, created = InterviewTranscription.objects.get_or_create(interview=instance)

    if obj.status == TranscriptionStatus.PROCESSING:
        logger.info(
            f'[ТРАНСКРИПЦИЯ] Пропуск для собеседования #{instance.pk}: статус {obj.status}'
        )
        return
    if obj.status == TranscriptionStatus.COMPLETED:
        logger.info(
            f'[ТРАНСКРИПЦИЯ] Пропуск для собеседования #{instance.pk}: статус {obj.status}'
        )
        return

    cooldown = timedelta(minutes=TRANSCRIPTION_PENDING_COOLDOWN_MINUTES)
    if (
        not created
        and obj.status == TranscriptionStatus.PENDING
        and obj.updated_at >= timezone.now() - cooldown
    ):
        logger.info(
            f'[ТРАНСКРИПЦИЯ] Пропуск дубля очереди для собеседования #{instance.pk}: уже pending'
        )
        return

    InterviewTranscription.objects.filter(pk=obj.pk).update(
        status=TranscriptionStatus.PENDING,
        error_message=None,
    )
    transaction.on_commit(lambda pk=obj.pk: transcribe_interview.delay(pk))
    logger.info(f'[ТРАНСКРИПЦИЯ] Задача поставлена в очередь для собеседования #{instance.pk}')
