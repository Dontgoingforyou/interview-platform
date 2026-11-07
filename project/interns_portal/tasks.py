import logging
import os

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from core.s3_video_storage import (
    S3VideoStorageError,
    build_object_key,
    upload_file_to_s3,
    user_friendly_storage_error,
)

from interviews.models import Interview

from .upload_logging import portal_upload_log

logger = logging.getLogger('interns_portal')

UPLOAD_PROGRESS_START = 5
UPLOAD_PROGRESS_END = 95


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def upload_video_to_s3(self, interview_id: int, file_path: str, filename: str):
    """
    Загружает видеофайл в S3 и сохраняет стабильный URL в Interview.video_link.

    Просмотр по кнопке — через presigned URL при отдаче API (см. resolve_video_play_url).
    """
    object_key = build_object_key(filename)
    tmp_basename = os.path.basename(file_path)
    file_exists = os.path.isfile(file_path)
    size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2) if file_exists else 0

    portal_upload_log(
        'info',
        'worker_start',
        interview_id,
        tmp_basename=tmp_basename,
        file_exists=file_exists,
        size_mb=size_mb,
        object_key=object_key,
    )

    if not file_exists:
        portal_upload_log(
            'error',
            'worker_start',
            interview_id,
            reason='file_not_found',
            tmp_basename=tmp_basename,
        )
        raise FileNotFoundError(
            f'Временный файл не найден (interview_id={interview_id}, tmp_basename={tmp_basename})'
        )

    # Явный task_id: Callback boto3 вызывается из фонового потока, где request.id недоступен.
    celery_task_id = self.request.id

    def _update_progress(uploaded: int, total: int):
        if not celery_task_id or total <= 0:
            return
        pct = UPLOAD_PROGRESS_START + int(
            (uploaded / total) * (UPLOAD_PROGRESS_END - UPLOAD_PROGRESS_START)
        )
        try:
            self.update_state(
                task_id=celery_task_id,
                state='PROGRESS',
                meta={'current': pct, 'status': 'Загрузка в облачное хранилище...'},
            )
        except Exception:
            logger.debug(
                '[PORTAL_UPLOAD] phase=progress_update_skipped interview_id=%s',
                interview_id,
                exc_info=True,
            )

    try:
        if celery_task_id:
            self.update_state(
                task_id=celery_task_id,
                state='PROGRESS',
                meta={
                    'current': UPLOAD_PROGRESS_START,
                    'status': 'Загрузка в облачное хранилище...',
                },
            )
        stable_url = upload_file_to_s3(
            file_path,
            object_key,
            progress_callback=_update_progress if celery_task_id else None,
        )
        portal_upload_log('info', 'worker_s3_upload', interview_id, object_key=object_key)

        interview = Interview.objects.filter(pk=interview_id).first()
        if interview is None:
            portal_upload_log(
                'warning',
                'worker_done',
                interview_id,
                reason='interview_not_found',
            )
        else:
            interview.video_link = stable_url
            interview.upload_task_id = None
            interview.save(update_fields=['video_link', 'upload_task_id'])
            portal_upload_log('info', 'worker_done', interview_id, object_key=object_key)

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(
                '[PORTAL_UPLOAD] phase=tmp_removed interview_id=%s tmp_basename=%s',
                interview_id,
                tmp_basename,
            )

    except Exception as exc:
        exc_type = type(exc).__name__
        portal_upload_log(
            'warning',
            'worker_retry',
            interview_id,
            exc_type=exc_type,
            retry=self.request.retries,
        )
        logger.exception(
            '[PORTAL_UPLOAD] phase=worker_error interview_id=%s exc_type=%s',
            interview_id,
            exc_type,
        )
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            friendly = user_friendly_storage_error(exc)
            portal_upload_log(
                'error',
                'worker_failed_final',
                interview_id,
                exc_type=exc_type,
                reason=friendly[:200],
            )
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(
                    '[PORTAL_UPLOAD] phase=tmp_removed_after_failure interview_id=%s tmp_basename=%s',
                    interview_id,
                    tmp_basename,
                )
            raise S3VideoStorageError(friendly) from exc
