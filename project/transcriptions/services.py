import ipaddress
import logging
from urllib.parse import urlparse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Разрешённые домены для загрузки медиафайлов транскрипции (защита от SSRF)
_ALLOWED_TRANSCRIPTION_DOMAINS: frozenset[str] = frozenset({
    'yandex.ru',
    'yandex.net',
    'disk.yandex.ru',
    'disk.yandex.net',
    'downloader.disk.yandex.ru',
    'cloud-api.yandex.net',
    'yadi.sk',
    'getfile.dokpub.com',
    'googleapis.com',
    'storage.googleapis.com',
    'deepgram.com',
    'api.deepgram.com',
})


def _is_allowed_transcription_url(url: str) -> bool:
    """
    Проверяет, что URL принадлежит разрешённому домену и не ведёт на приватный/локальный адрес.
    Защита от SSRF: video_link из БД не должен позволять запрашивать внутренние ресурсы.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        host = parsed.hostname or ''
        try:
            addr = ipaddress.ip_address(host)
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
                return False
        except ValueError:
            pass
        domains = _ALLOWED_TRANSCRIPTION_DOMAINS
        endpoint_host = (urlparse(settings.S3_ENDPOINT_URL or '').hostname or '').lower()
        if endpoint_host:
            domains = domains | {endpoint_host}
        return any(host == domain or host.endswith('.' + domain) for domain in domains)
    except Exception:
        logger.exception('Проверка URL транскрипции завершилась ошибкой')
        return False


# Deepgram Nova-2 модель с поддержкой русского языка
_DEEPGRAM_MODEL = 'nova-2'
_DEEPGRAM_LANGUAGE = 'ru'
_DEEPGRAM_TRANSCRIBE_URL = 'https://api.deepgram.com/v1/listen'
_DEEPGRAM_BALANCE_URL = 'https://api.deepgram.com/v1/projects/{project_id}/balances'

# Таймаут запроса к Deepgram при URL-режиме (Deepgram сам скачивает файл)
_URL_REQUEST_TIMEOUT = 300
# Таймаут скачивания файла с Яндекс.Диска в RAM при fallback
_DOWNLOAD_TIMEOUT = 600
# Таймаут отправки бинарных данных в Deepgram при fallback
_UPLOAD_TIMEOUT = 600
# Размер чанка при потоковом скачивании в RAM (байт)
_DOWNLOAD_CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB

# Маркеры ответа Deepgram, означающие что он не смог скачать файл по URL
_SLOW_UPLOAD_MARKERS = ('slow_upload', 'request upload timeout')
# Маркеры Content-Type → расширение файла для отправки в Deepgram
_CONTENT_TYPE_EXT_MAP = {
    'webm': '.webm',
    'ogg': '.ogg',
    'opus': '.ogg',
    'mpeg': '.mp3',
    'mp3': '.mp3',
    'wav': '.wav',
}
_MIME_MAP = {
    '.mp4': 'video/mp4',
    '.webm': 'video/webm',
    '.ogg': 'audio/ogg',
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
}


def _is_slow_upload_error(exc: BaseException) -> bool:
    """True — Deepgram вернул 408 SLOW_UPLOAD (не успел скачать файл по URL)."""
    msg = str(exc).lower()
    return '408' in msg and any(m in msg for m in _SLOW_UPLOAD_MARKERS)


# Эвристика: очень короткая вставка между двумя репликами одного спикера — часто ошибка
# диризации при перебивании («меня» между двумя репликами одного человека).
# Слишком широкий порог сливает настоящие короткие ответы («Привет.»).
_SHORT_SANDWICH_1WORD_MAX_CHARS = 6
_SHORT_SANDWICH_2WORDS_MAX_CHARS = 10


def _normalize_speaker_id(raw) -> int:
    if isinstance(raw, int):
        return raw
    return 0


def _merge_consecutive_utterances(utterances: list) -> list[tuple[int, str]]:
    """Склеивает подряд идущие utterances одного спикера в [(speaker_id, text), ...]."""
    blocks: list[tuple[int, str]] = []
    current_speaker = None
    current_parts: list[str] = []
    for u in utterances:
        speaker_num = _normalize_speaker_id(u.get('speaker', 0))
        text = (u.get('transcript') or '').strip()
        if not text:
            continue
        if speaker_num == current_speaker:
            current_parts.append(text)
        else:
            if current_parts:
                blocks.append((current_speaker, ' '.join(current_parts)))
            current_speaker = speaker_num
            current_parts = [text]
    if current_parts:
        blocks.append((current_speaker, ' '.join(current_parts)))
    return blocks


def _is_short_sandwich_fragment(text: str) -> bool:
    """Очень короткая вставка — кандидат на слияние с соседними репликами того же спикера."""
    t = text.strip()
    if not t:
        return False
    parts = t.split()
    if len(parts) == 1:
        return len(t) <= _SHORT_SANDWICH_1WORD_MAX_CHARS
    if len(parts) == 2:
        return len(t) <= _SHORT_SANDWICH_2WORDS_MAX_CHARS
    return False


def _merge_sandwiched_short_fragments(blocks: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """
    Паттерн: спикер A, короткая реплика B, снова A — объединяем в одну реплику A.
    Снижает артефакты вроде «Спикер 1: Раз-раз.» / «Спикер 2: меня» / «Спикер 1: слышно?».
    """
    if len(blocks) < 3:
        return blocks
    out: list[tuple[int, str]] = []
    i = 0
    while i < len(blocks):
        if i + 2 < len(blocks):
            sp_a, t_a = blocks[i]
            sp_b, t_b = blocks[i + 1]
            sp_c, t_c = blocks[i + 2]
            if sp_a == sp_c and sp_a != sp_b and _is_short_sandwich_fragment(t_b):
                merged = f'{t_a} {t_b} {t_c}'.strip()
                out.append((sp_a, merged))
                i += 3
                continue
        out.append(blocks[i])
        i += 1
    return out


def _blocks_to_transcript_text(blocks: list[tuple[int, str]]) -> str:
    parts = []
    for sp_id, text in blocks:
        label = f'Спикер {sp_id + 1}'
        parts.append(f'{label}: {text}')
    return '\n\n'.join(parts) if parts else ''


class TranscriptionService:
    """Сервис транскрипции видео/аудио через Deepgram API."""

    @classmethod
    def _get_api_key(cls) -> str:
        api_key = getattr(settings, 'DEEPGRAM_API_KEY', '')
        if not api_key:
            raise ValueError('DEEPGRAM_API_KEY не установлен в настройках')
        return api_key

    @classmethod
    def _resolve_media_url(cls, media_url: str) -> str:
        """
        Прямой URL для скачивания: presigned для S3, API Я.Диска для публичных шаров.
        """
        from core.s3_video_storage import is_s3_video_url, presigned_get_url

        if is_s3_video_url(media_url):
            if not _is_allowed_transcription_url(media_url):
                raise ValueError(f'URL для транскрипции не разрешён (SSRF-защита): {media_url[:80]}')
            # Дольше стандартного UI-TTL: задача транскрипции может идти несколько минут
            direct = presigned_get_url(media_url, expires=7200)
            if not _is_allowed_transcription_url(direct):
                raise ValueError(f'Presigned URL не прошёл SSRF-проверку: {direct[:80]}')
            return direct
        return cls._resolve_yandex_disk_url(media_url)

    @classmethod
    def _resolve_yandex_disk_url(cls, public_url: str) -> str:
        """
        Преобразует публичную ссылку Яндекс Диска в прямую download-ссылку.
        Использует API Яндекс Диска для получения прямого URL.
        """
        if not _is_allowed_transcription_url(public_url):
            raise ValueError(f'URL для транскрипции не разрешён (SSRF-защита): {public_url[:80]}')
        try:
            import yadisk
            client = yadisk.Client(token=settings.YANDEX_DISK_TOKEN)
            with client:
                meta = client.get_public_meta(public_url)
                download_link = client.get_public_download_link(public_url)
                logger.info(f'Resolved Яндекс Диск URL для файла: {getattr(meta, "name", "unknown")}')
                return download_link
        except ValueError:
            raise
        except Exception as e:
            logger.warning(f'Не удалось резолвить URL через yadisk API ({e}), используем прямой redirect')
            # Fallback: resolve redirect вручную
            resp = requests.head(public_url, allow_redirects=True, timeout=30)
            resolved = resp.url
            if not _is_allowed_transcription_url(resolved):
                raise ValueError(f'Редирект ведёт на запрещённый URL (SSRF-защита): {resolved[:80]}')
            return resolved

    @classmethod
    def _download_to_tempfile(cls, url: str) -> tuple[str, str]:
        """
        Скачивает файл по URL во временный файл на диске (потоком, чанками — RAM не нагружается).

        Returns:
            (tmp_path, content_type) — путь к файлу и MIME-тип.
            Caller обязан удалить файл после использования.
        """
        import os
        import tempfile
        logger.info(f'[ТРАНСКРИПЦИЯ] Скачивание файла на диск: {url[:80]}...')
        resp = requests.get(url, stream=True, timeout=_DOWNLOAD_TIMEOUT)
        if resp.status_code != 200:
            raise RuntimeError(
                f'Не удалось скачать файл с Яндекс.Диска: HTTP {resp.status_code}'
            )
        content_type = resp.headers.get('Content-Type', 'video/mp4')
        ct_lower = content_type.lower()
        ext = next(
            (v for k, v in _CONTENT_TYPE_EXT_MAP.items() if k in ct_lower),
            '.mp4',
        )
        fd, tmp_path = tempfile.mkstemp(suffix=ext, prefix='transcription_')
        try:
            total = 0
            with os.fdopen(fd, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=_DOWNLOAD_CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
            logger.info(f'[ТРАНСКРИПЦИЯ] Скачано на диск: {total / 1024 / 1024:.1f} МБ -> {tmp_path}')
        except Exception:
            os.unlink(tmp_path)
            raise
        return tmp_path, content_type

    @classmethod
    def _transcribe_via_url(cls, api_key: str, direct_url: str) -> str:
        """Отправляет URL в Deepgram — Deepgram сам скачивает файл."""
        params = cls._deepgram_params()
        headers = {'Authorization': f'Token {api_key}', 'Content-Type': 'application/json'}
        response = requests.post(
            _DEEPGRAM_TRANSCRIBE_URL,
            json={'url': direct_url},
            headers=headers,
            params=params,
            timeout=_URL_REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f'Deepgram вернул ошибку {response.status_code}: {response.text[:300]}'
            )
        return cls._parse_deepgram_response(response.json())

    @classmethod
    def _transcribe_via_tempfile(cls, api_key: str, direct_url: str) -> str:
        """
        Fallback: скачивает файл на диск и отправляет потоком в Deepgram.
        Используется когда Deepgram не может скачать файл по URL (408 SLOW_UPLOAD).
        Не нагружает RAM — файл читается с диска при отправке.
        """
        import os
        tmp_path, raw_content_type = cls._download_to_tempfile(direct_url)
        try:
            ct_lower = raw_content_type.lower()
            ext = next(
                (v for k, v in _CONTENT_TYPE_EXT_MAP.items() if k in ct_lower),
                '.mp4',
            )
            mime = _MIME_MAP.get(ext, 'video/mp4')
            logger.info(f'[ТРАНСКРИПЦИЯ] Отправка файла с диска в Deepgram (тип: {mime})')
            params = cls._deepgram_params()
            headers = {'Authorization': f'Token {api_key}', 'Content-Type': mime}
            with open(tmp_path, 'rb') as f:
                response = requests.post(
                    _DEEPGRAM_TRANSCRIBE_URL,
                    data=f,
                    headers=headers,
                    params=params,
                    timeout=_UPLOAD_TIMEOUT,
                )
            if response.status_code != 200:
                raise RuntimeError(
                    f'Deepgram вернул ошибку {response.status_code}: {response.text[:300]}'
                )
            return cls._parse_deepgram_response(response.json())
        finally:
            try:
                os.unlink(tmp_path)
                logger.info(f'[ТРАНСКРИПЦИЯ] Временный файл удалён: {tmp_path}')
            except OSError as e:
                logger.warning(f'[ТРАНСКРИПЦИЯ] Не удалось удалить временный файл {tmp_path}: {e}')

    @classmethod
    def _deepgram_params(cls) -> dict:
        return {
            'model': _DEEPGRAM_MODEL,
            'language': _DEEPGRAM_LANGUAGE,
            'punctuate': 'true',
            'diarize': 'true',
            'utterances': 'true',
            'smart_format': 'true',
        }

    @classmethod
    def transcribe_from_url(cls, video_url: str) -> str:
        """
        Транскрибирует видео/аудио по URL через Deepgram API.

        Стратегия двух попыток:
        1. Отправляет URL в Deepgram — он сам скачивает файл (быстро, без RAM).
        2. Если Deepgram вернул 408 SLOW_UPLOAD (не смог скачать с Яндекс.Диска) —
           скачивает файл в RAM на нашем сервере и отправляет бинарные данные напрямую.

        Args:
            video_url: Публичная ссылка на видео (Яндекс Диск)

        Returns:
            Текст транскрипции

        Raises:
            ValueError: Если API-ключ не настроен
            RuntimeError: Если обе попытки завершились ошибкой
        """
        api_key = cls._get_api_key()
        direct_url = cls._resolve_media_url(video_url)

        lowered = direct_url.lower()
        if 'showcaptcha' in lowered or '/captcha' in lowered:
            raise RuntimeError(
                'Не удалось получить прямую ссылку на файл: Яндекс.Диск вернул страницу с капчей '
                'или ресурс недоступен (проверьте публичную ссылку и токен YA_TOKEN).'
            )

        try:
            return cls._transcribe_via_url(api_key, direct_url)
        except RuntimeError as exc:
            if not _is_slow_upload_error(exc):
                raise
            logger.warning(
                '[ТРАНСКРИПЦИЯ] 408 SLOW_UPLOAD от Deepgram — fallback: скачиваем файл на диск'
            )

        return cls._transcribe_via_tempfile(api_key, direct_url)

    @classmethod
    def _parse_deepgram_response(cls, data: dict) -> str:
        """Извлекает текст транскрипции из ответа Deepgram API."""
        results = data.get('results') or {}

        utterances = results.get('utterances')
        if utterances:
            blocks = _merge_consecutive_utterances(utterances)
            while True:
                merged = _merge_sandwiched_short_fragments(blocks)
                if merged == blocks:
                    break
                blocks = merged
            transcript = _blocks_to_transcript_text(blocks)
        else:
            try:
                transcript = results['channels'][0]['alternatives'][0]['transcript']
            except (KeyError, IndexError) as e:
                raise RuntimeError(f'Неожиданный формат ответа Deepgram: {e}') from e

        logger.info(f'[ТРАНСКРИПЦИЯ] Транскрипция получена, длина текста: {len(transcript)} символов')
        return transcript

    @classmethod
    def get_balance(cls) -> dict:
        """
        Возвращает текущий баланс проекта Deepgram.

        Returns:
            dict с ключами: amount (float), units (str)

        Raises:
            ValueError: Если ключ или project_id не настроены
            RuntimeError: Если API вернул ошибку
        """
        api_key = cls._get_api_key()
        project_id = getattr(settings, 'DEEPGRAM_PROJECT_ID', '')
        if not project_id:
            raise ValueError('DEEPGRAM_PROJECT_ID не установлен в настройках')

        url = _DEEPGRAM_BALANCE_URL.format(project_id=project_id)
        headers = {'Authorization': f'Token {api_key}'}

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise RuntimeError(
                f'Deepgram balance API вернул {response.status_code}: {response.text[:200]}'
            )

        data = response.json()
        balances = data.get('balances', [])
        if not balances:
            return {'amount': 0.0, 'units': 'usd'}

        balance = balances[0]
        return {
            'amount': balance.get('amount', 0.0),
            'units': balance.get('units', 'usd'),
        }
