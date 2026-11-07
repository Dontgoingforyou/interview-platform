import logging
import threading

from celery import shared_task
from django.core.cache import cache
from django.db import close_old_connections
from django.utils import timezone

from transcriptions.constants import TRANSCRIPTION_PROCESSING_HEARTBEAT_SECONDS

logger = logging.getLogger(__name__)

_BALANCE_EXHAUSTED_CACHE_KEY = 'deepgram_balance_exhausted'
_BALANCE_EXHAUSTED_MSG = (
    'Баланс Deepgram исчерпан. Пополните счёт и сбросьте флаг: '
    'python manage.py transcribe_interviews --reset-balance-flag'
)

# Ошибки, при которых повтор Celery не поможет (та же ссылка, тот же ответ Яндекс/Deepgram)
_TERMINAL_ERROR_MARKERS = (
    'капч',
    'unsupported media',
    '400',
    '408',
    '415',
    'text/html',
    'remote server failed',
    'disknotfound',
    'resource not found',
    'не удалось найти запрошенный ресурс',
    'asr_payment_required',
    'payment required',
)


def _should_fail_without_retry(exc: BaseException) -> bool:
    """True — сразу FAILED в БД, без retry (капча, битая ссылка, 415, нулевой баланс)."""
    msg = str(exc).lower()
    return any(marker in msg for marker in _TERMINAL_ERROR_MARKERS)


def _is_balance_exhausted(exc: BaseException) -> bool:
    """True — ошибка 402/ASR_PAYMENT_REQUIRED от Deepgram (нулевой баланс)."""
    msg = str(exc).lower()
    return '402' in msg or 'asr_payment_required' in msg or 'payment required' in msg


def _touch_processing_updated_at(transcription_id: int) -> None:
    """Обновляет updated_at у processing, чтобы watchdog статуса не сбрасывал долгие задачи."""
    from transcriptions.models import InterviewTranscription, TranscriptionStatus

    close_old_connections()
    try:
        InterviewTranscription.objects.filter(
            pk=transcription_id,
            status=TranscriptionStatus.PROCESSING,
        ).update(updated_at=timezone.now())
    finally:
        close_old_connections()


def _start_processing_heartbeat(transcription_id: int) -> tuple[threading.Event, threading.Thread]:
    stop = threading.Event()

    def _loop() -> None:
        while not stop.wait(TRANSCRIPTION_PROCESSING_HEARTBEAT_SECONDS):
            try:
                _touch_processing_updated_at(transcription_id)
            except Exception:
                logger.exception(
                    '[ТРАНСКРИПЦИЯ] Heartbeat не удался для transcription_id=%s',
                    transcription_id,
                )

    thread = threading.Thread(target=_loop, name=f'tr-hb-{transcription_id}', daemon=True)
    thread.start()
    return stop, thread


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit='30/m',
    name='transcriptions.tasks.transcribe_interview',
)
def transcribe_interview(self, transcription_id: int) -> None:
    """
    Celery-задача транскрипции видео собеседования через Deepgram API.

    Args:
        transcription_id: PK записи InterviewTranscription
    """
    from transcriptions.models import InterviewTranscription, TranscriptionStatus
    from transcriptions.services import TranscriptionService

    if cache.get(_BALANCE_EXHAUSTED_CACHE_KEY):
        InterviewTranscription.objects.filter(pk=transcription_id).update(
            status=TranscriptionStatus.FAILED,
            error_message=_BALANCE_EXHAUSTED_MSG,
        )
        logger.warning(
            '[ТРАНСКРИПЦИЯ] Задача #%d пропущена: баланс Deepgram исчерпан', transcription_id
        )
        return

    try:
        transcription = InterviewTranscription.objects.select_related('interview').get(
            pk=transcription_id
        )
    except InterviewTranscription.DoesNotExist:
        logger.warning(f'[ТРАНСКРИПЦИЯ] InterviewTranscription #{transcription_id} не найдена, задача пропущена')
        return

    interview = transcription.interview
    media_url = interview.transcription_media_url
    if not media_url:
        logger.warning(
            f'[ТРАНСКРИПЦИЯ] Собеседование #{interview.pk} не имеет URL для транскрипции '
            f'(video_link / link / interview_link), задача пропущена'
        )
        return

    logger.info(f'[ТРАНСКРИПЦИЯ] Начало транскрипции для собеседования #{interview.pk}')

    InterviewTranscription.objects.filter(pk=transcription_id).update(
        status=TranscriptionStatus.PROCESSING,
        error_message=None,
        updated_at=timezone.now(),
    )

    stop_heartbeat, _hb_thread = _start_processing_heartbeat(transcription_id)
    try:
        text = TranscriptionService.transcribe_from_url(media_url)

        InterviewTranscription.objects.filter(pk=transcription_id).update(
            status=TranscriptionStatus.COMPLETED,
            text=text,
            error_message=None,
        )
        logger.info(
            f'[ТРАНСКРИПЦИЯ] Успешно завершена для собеседования #{interview.pk}, '
            f'длина текста: {len(text)} символов'
        )

        _trigger_vector_embedding(transcription_id)

    except Exception as exc:
        if _is_balance_exhausted(exc):
            cache.set(_BALANCE_EXHAUSTED_CACHE_KEY, True, timeout=None)
            InterviewTranscription.objects.filter(pk=transcription_id).update(
                status=TranscriptionStatus.FAILED,
                error_message=_BALANCE_EXHAUSTED_MSG,
            )
            logger.error(
                '[ТРАНСКРИПЦИЯ] Баланс Deepgram исчерпан (собеседование #%d). '
                'Все последующие задачи будут остановлены автоматически.',
                interview.pk,
            )
            return

        if _should_fail_without_retry(exc):
            error_msg = str(exc)[:500]
            InterviewTranscription.objects.filter(pk=transcription_id).update(
                status=TranscriptionStatus.FAILED,
                error_message=error_msg,
            )
            logger.error(
                f'[ТРАНСКРИПЦИЯ] Ошибка без повторов для собеседования #{interview.pk}: {error_msg}'
            )
            return

        logger.warning(
            f'[ТРАНСКРИПЦИЯ] Ошибка для собеседования #{interview.pk} '
            f'(попытка {self.request.retries + 1}/{self.max_retries + 1}): {exc}'
        )
        try:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            error_msg = str(exc)[:500]
            InterviewTranscription.objects.filter(pk=transcription_id).update(
                status=TranscriptionStatus.FAILED,
                error_message=error_msg,
            )
            logger.error(
                f'[ТРАНСКРИПЦИЯ] Исчерпаны попытки для собеседования #{interview.pk}: {error_msg}'
            )
    finally:
        stop_heartbeat.set()


def _trigger_vector_embedding(transcription_id: int) -> None:
    """Запускает обновление векторного эмбеддинга для транскрипции."""
    try:
        from vector_search.tasks import update_embedding_task
        update_embedding_task.delay('interview_transcription', transcription_id)
        logger.info(f'[ТРАНСКРИПЦИЯ] Запущена векторизация для transcription #{transcription_id}')
    except Exception as e:
        logger.warning(f'[ТРАНСКРИПЦИЯ] Не удалось запустить векторизацию: {e}')
