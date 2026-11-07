"""
Сохранение загруженного файла для асинхронного импорта (CSV/XLSX/XLS).
Используется API-импортом собеседований и студентов.
"""
import os
import uuid

from django.conf import settings

ALLOWED_IMPORT_EXTENSIONS = ('.csv', '.xlsx', '.xls')


def validate_import_filename(filename: str) -> bool:
    name = (filename or '').lower()
    return name.endswith(ALLOWED_IMPORT_EXTENSIONS)


def save_import_upload_file(uploaded_file, filename_prefix: str) -> tuple[str | None, str | None]:
    """
    Сохраняет файл в media/imports.

    Returns:
        (tmp_path, error_message) — при успехе error_message is None.
    """
    media_root = getattr(settings, 'MEDIA_ROOT', None) or os.path.join(settings.BASE_DIR, 'media')
    imports_dir = os.path.join(media_root, 'imports')
    os.makedirs(imports_dir, exist_ok=True)
    ext = os.path.splitext(uploaded_file.name)[1] or '.xlsx'
    tmp_name = f'{filename_prefix}_{uuid.uuid4().hex}{ext}'
    tmp_path = os.path.join(imports_dir, tmp_name)
    try:
        with open(tmp_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
    except OSError as e:
        return None, f'Ошибка сохранения файла: {e!s}'
    return tmp_path, None
