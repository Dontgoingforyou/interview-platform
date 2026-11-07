"""
Общая логика транскрипции собеседования для Django views и DRF API.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from interviews.models import Interview
from transcriptions.constants import (
    TRANSCRIPTION_PENDING_COOLDOWN_MINUTES,
    TRANSCRIPTION_PROCESSING_STALE_MINUTES,
)
from transcriptions.models import InterviewTranscription, TranscriptionStatus
from transcriptions.transcription_download_filename import build_interview_transcription_download_filename

logger = logging.getLogger(__name__)


def transcribe_interview_payload(pk: int, *, log_user_label: str):
    """
    Запуск транскрипции. Возвращает (payload: dict, status_code: int).
    """
    interview = get_object_or_404(Interview, pk=pk)

    if not interview.transcription_media_url:
        return {'error': 'Нет подходящей ссылки на видео для транскрипции'}, 400

    from transcriptions.tasks import transcribe_interview

    cooldown = timedelta(minutes=TRANSCRIPTION_PENDING_COOLDOWN_MINUTES)
    now = timezone.now()
    scheduled = False

    with transaction.atomic():
        row = (
            InterviewTranscription.objects.select_for_update()
            .filter(interview_id=interview.pk)
            .first()
        )
        if row is None:
            row = InterviewTranscription.objects.create(
                interview=interview,
                status=TranscriptionStatus.PENDING,
            )
            tid = row.pk
            scheduled = True
        else:
            if row.status == TranscriptionStatus.PROCESSING:
                return {'status': row.status, 'message': 'Уже выполняется'}, 200
            if row.status == TranscriptionStatus.PENDING and row.updated_at >= now - cooldown:
                return {'status': 'pending', 'message': 'Уже в очереди'}, 200

            InterviewTranscription.objects.filter(pk=row.pk).update(
                status=TranscriptionStatus.PENDING,
                error_message=None,
                updated_at=timezone.now(),
            )
            tid = row.pk
            scheduled = True

        if scheduled:
            transaction.on_commit(lambda: transcribe_interview.delay(tid))

    logger.info(
        '[ТРАНСКРИПЦИЯ] Запущена вручную администратором %s для собеседования #%s',
        log_user_label,
        pk,
    )
    return {'status': 'pending', 'message': 'Транскрипция поставлена в очередь'}, 200


def transcription_status_payload(pk: int):
    """Статус транскрипции. Всегда 200, тело — dict (как у legacy JSON)."""
    try:
        transcription = InterviewTranscription.objects.only(
            'status', 'error_message', 'updated_at'
        ).get(interview_id=pk)
    except InterviewTranscription.DoesNotExist:
        return {'status': 'none', 'error_message': ''}, 200

    if transcription.status == TranscriptionStatus.PROCESSING:
        stale_threshold = timezone.now() - timedelta(minutes=TRANSCRIPTION_PROCESSING_STALE_MINUTES)
        if transcription.updated_at < stale_threshold:
            msg = (
                'Задача прервана. '
                'Запустите транскрипцию заново.'
            )
            logger.warning(
                '[ТРАНСКРИПЦИЯ] Собеседование #%s: processing без обновления дольше %s мин. — помечаем failed',
                pk,
                TRANSCRIPTION_PROCESSING_STALE_MINUTES,
            )
            InterviewTranscription.objects.filter(pk=transcription.pk).update(
                status=TranscriptionStatus.FAILED,
                error_message=msg[:500],
                updated_at=timezone.now(),
            )
            return {'status': 'failed', 'error_message': msg}, 200

    return {
        'status': transcription.status,
        'error_message': transcription.error_message or '',
    }, 200


def transcription_text_payload(pk: int):
    """Текст транскрипции. (payload, status_code)."""
    try:
        transcription = InterviewTranscription.objects.select_related(
            'interview__intern',
            'interview__company',
        ).get(
            interview_id=pk,
            status=TranscriptionStatus.COMPLETED,
        )
    except InterviewTranscription.DoesNotExist:
        return {'error': 'Транскрипция не найдена или ещё не завершена'}, 404

    interview = transcription.interview
    filename = build_interview_transcription_download_filename(interview)
    return {'text': transcription.text or '', 'filename': filename}, 200
