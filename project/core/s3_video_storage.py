"""
S3-хранилище видеозаписей собеседований (FirstVDS и совместимые провайдеры).

В БД (Interview.video_link) хранится стабильный path-style HTTPS URL без подписи.
При отдаче API и для транскрипции генерируется presigned GET (TTL — S3_PRESIGNED_EXPIRES).
"""
from __future__ import annotations

import logging
from functools import lru_cache
from urllib.parse import quote, unquote, urlparse

from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


class S3VideoStorageError(Exception):
    """Ошибка загрузки или доступа к видео в S3 с понятным сообщением для UI."""


def _s3_endpoint_host() -> str:
    return (urlparse(settings.S3_ENDPOINT_URL).netloc or '').lower()


@lru_cache(maxsize=1)
def get_s3_client():
    """Клиент boto3 S3 с path-style addressing (FirstVDS)."""
    return __import__('boto3').client(
        's3',
        endpoint_url=settings.S3_ENDPOINT_URL,
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
    )


_CONTENT_TYPES = {
    '.mp4': 'video/mp4',
    '.mov': 'video/quicktime',
    '.avi': 'video/x-msvideo',
    '.mkv': 'video/x-matroska',
    '.webm': 'video/webm',
    '.flv': 'video/x-flv',
    '.wmv': 'video/x-ms-wmv',
}


def _content_type_for_key(key: str) -> str:
    ext = __import__('os').path.splitext(key)[1].lower()
    return _CONTENT_TYPES.get(ext, 'application/octet-stream')


def build_object_key(filename: str) -> str:
    """
    Ключ объекта в бакете: плоский путь в корне (или под S3_VIDEO_PREFIX).

    Уникальность имён обеспечивается суффиксом [id N] в build_video_object_filename.
    """
    name = filename.lstrip('/')
    extra_prefix = (settings.S3_VIDEO_PREFIX or '').strip().strip('/')
    if extra_prefix:
        return f'{extra_prefix}/{name}'
    return name


def build_stable_video_url(bucket: str, key: str) -> str:
    """Стабильный HTTPS URL для записи в video_link (без query-подписи)."""
    endpoint = settings.S3_ENDPOINT_URL.rstrip('/')
    key = key.lstrip('/')
    encoded_key = quote(key, safe='/')
    return f'{endpoint}/{bucket}/{encoded_key}'


def parse_s3_video_url(url: str) -> tuple[str, str] | None:
    """
    Разбирает стабильный URL видео → (bucket, key).
    Возвращает None, если хост не совпадает с S3_ENDPOINT_URL.
    """
    if not url or not isinstance(url, str):
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme not in ('http', 'https'):
        return None
    host = (parsed.netloc or '').lower()
    if host != _s3_endpoint_host():
        return None
    path = unquote(parsed.path or '').strip('/')
    if '/' not in path:
        return None
    bucket, key = path.split('/', 1)
    if not bucket or not key:
        return None
    return bucket, key


def is_s3_video_url(url: str | None) -> bool:
    return parse_s3_video_url(url or '') is not None


def presigned_get_url(
    stored_url: str,
    expires: int | None = None,
    *,
    inline: bool = True,
) -> str:
    """Временная подписанная ссылка для просмотра (inline) или скачивания private-объекта."""
    parsed = parse_s3_video_url(stored_url)
    if not parsed:
        return stored_url
    bucket, key = parsed
    ttl = expires if expires is not None else settings.S3_PRESIGNED_EXPIRES
    params = {
        'Bucket': bucket,
        'Key': key,
        'ResponseContentType': _content_type_for_key(key),
    }
    if inline:
        basename = __import__('os').path.basename(key)
        params['ResponseContentDisposition'] = f'inline; filename="{quote(basename)}"'
    try:
        return get_s3_client().generate_presigned_url(
            'get_object',
            Params=params,
            ExpiresIn=ttl,
        )
    except (ClientError, BotoCoreError) as exc:
        logger.warning('Не удалось сгенерировать presigned URL: %s', type(exc).__name__)
        return stored_url


def resolve_video_play_url(stored_url: str | None) -> str | None:
    """
    URL для кнопки «Смотреть запись»: presigned для S3, иначе исходная ссылка (Я.Диск и др.).
    """
    if not stored_url:
        return None
    url = stored_url.strip()
    if not url:
        return None
    if is_s3_video_url(url):
        return presigned_get_url(url)
    return url


def user_friendly_storage_error(exc: BaseException) -> str:
    """Короткое сообщение для Celery FAILURE / UI."""
    if isinstance(exc, S3VideoStorageError):
        return str(exc)
    if isinstance(exc, ClientError):
        code = exc.response.get('Error', {}).get('Code', '')
        if code in ('QuotaExceeded', 'EntityTooLarge', 'SlowDown'):
            return 'Недостаточно места или превышена квота хранилища. Обратитесь к администратору.'
        if code in ('AccessDenied', 'InvalidAccessKeyId', 'SignatureDoesNotMatch'):
            return 'Ошибка доступа к хранилищу S3. Обратитесь к администратору.'
        if code == 'NoSuchBucket':
            return 'Бакет видео не найден в S3. Обратитесь к администратору.'
    name = type(exc).__name__
    if 'InsufficientStorage' in name or 'Quota' in name:
        return 'Недостаточно места в хранилище. Обратитесь к администратору.'
    return 'Ошибка загрузки видео в облачное хранилище. Попробуйте позже.'


def upload_file_to_s3(
    file_path: str,
    object_key: str,
    *,
    progress_callback=None,
) -> str:
    """
    Загружает файл в S3_VIDEO_BUCKET. Возвращает стабильный video_link URL.

    progress_callback(bytes_transferred, total_bytes) — опционально для Celery.
    """
    bucket = settings.S3_VIDEO_BUCKET
    total = 0
    try:
        total = __import__('os').path.getsize(file_path)
    except OSError:
        pass

    uploaded = 0

    def _boto_callback(bytes_amount):
        nonlocal uploaded
        uploaded += bytes_amount
        if progress_callback and total > 0:
            progress_callback(uploaded, total)

    try:
        get_s3_client().upload_file(
            file_path,
            bucket,
            object_key,
            Callback=_boto_callback if progress_callback else None,
        )
    except (ClientError, BotoCoreError) as exc:
        raise S3VideoStorageError(user_friendly_storage_error(exc)) from exc

    return build_stable_video_url(bucket, object_key)
