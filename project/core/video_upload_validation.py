"""Проверка загружаемых видеофайлов (портал студента)."""

# Сигнатуры контейнеров: MP4/MOV (ftyp), WebM, AVI, MKV, FLV, WMV
_VIDEO_MAGIC = (
    (b'ftyp', 4, 'mp4/mov'),
    (b'\x1a\x45\xdf\xa3', 0, 'webm/mkv'),
    (b'RIFF', 0, 'avi'),
    (b'FLV\x01', 0, 'flv'),
)


def validate_video_upload_size(size) -> str | None:
    """None если размер допустим, иначе текст ошибки."""
    if size is None:
        return 'Не удалось определить размер файла.'
    return None


def validate_video_magic_header(header: bytes, ext: str) -> str | None:
    """
    Проверка magic bytes по началу файла.
    None — ок, иначе сообщение об ошибке.
    """
    if len(header) < 12:
        return 'Файл слишком мал или повреждён.'

    ext = ext.lower()
    if ext in ('.mp4', '.mov'):
        if header[4:8] != b'ftyp':
            return 'Содержимое файла не соответствует формату MP4/MOV.'
        return None

    if ext == '.webm':
        if not header.startswith(b'\x1a\x45\xdf\xa3'):
            return 'Содержимое файла не соответствует формату WebM.'
        return None

    if ext == '.mkv':
        if not header.startswith(b'\x1a\x45\xdf\xa3'):
            return 'Содержимое файла не соответствует формату MKV.'
        return None

    if ext == '.avi':
        if not header.startswith(b'RIFF') or header[8:12] != b'AVI ':
            return 'Содержимое файла не соответствует формату AVI.'
        return None

    if ext == '.flv':
        if not header.startswith(b'FLV'):
            return 'Содержимое файла не соответствует формату FLV.'
        return None

    if ext == '.wmv':
        if header[:4] != b'\x30\x26\xb2\x75':
            return 'Содержимое файла не соответствует формату WMV.'
        return None

    return None
