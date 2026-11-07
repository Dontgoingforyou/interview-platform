import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from interviews.models import Interview

# Символы, недопустимые в имени файла в Windows и часто проблемные в Unix
_INVALID_FILENAME_CHARS = re.compile(r'[\x00-\x1f\\\/:*?"<>|]+')

# Максимальная длина имени без расширения (запас под .txt и ОС)
_MAX_STEM_LENGTH = 180


def _sanitize_segment(raw: str) -> str:
    """Очищает фрагмент имени файла; пустая строка, если нечего оставить."""
    if raw is None:
        return ''
    s = _INVALID_FILENAME_CHARS.sub('_', str(raw).strip())
    s = s.strip(' .')
    while '__' in s:
        s = s.replace('__', '_')
    return s.strip('_')


def build_interview_transcription_download_filename(interview: 'Interview') -> str:
    """
    Собирает имя файла: ФИО (full_name)_тип_компания_дата.txt.
    Пустые сегменты пропускаются; при полном отсутствии данных — Транскрипция_{pk}.txt.
    """
    segments: list[str] = []

    intern = getattr(interview, 'intern', None)
    if intern is not None:
        part = _sanitize_segment(getattr(intern, 'full_name', None) or '')
        if part:
            segments.append(part)

    part = _sanitize_segment(interview.get_interview_type_display() or '')
    if part:
        segments.append(part)

    company = getattr(interview, 'company', None)
    if company is not None:
        part = _sanitize_segment(str(company) or '')
        if part:
            segments.append(part)

    if interview.date:
        segments.append(interview.date.strftime('%d.%m.%Y'))

    if segments:
        stem = '_'.join(segments)
    else:
        stem = f'Транскрипция_{interview.pk}'

    if not stem or not stem.strip():
        stem = f'Транскрипция_{interview.pk}'

    if len(stem) > _MAX_STEM_LENGTH:
        stem = stem[:_MAX_STEM_LENGTH].rstrip(' ._')

    if not stem.endswith('.txt'):
        stem = f'{stem}.txt'

    return stem
