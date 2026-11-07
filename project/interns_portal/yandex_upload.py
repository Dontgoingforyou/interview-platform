import re

_UNSAFE_CHARS = re.compile(r'[\\/:*?"<>|]')


def safe_filename_part(value: str) -> str:
    """Убирает символы, недопустимые в именах файлов объектного хранилища."""
    return _UNSAFE_CHARS.sub('', str(value)).strip() or 'без названия'


def build_video_object_filename(interview, ext: str) -> str:
    """
    Имя объекта видео (S3 / legacy Я.Диск):
    «Направление. Фамилия Имя. Компания. Тип. Дата [id N].ext»
    """
    direction = safe_filename_part(interview.direction.name)
    full_name = safe_filename_part(interview.intern.full_name)
    company = safe_filename_part(interview.company.name) if interview.company_id else 'без компании'
    itype = safe_filename_part(interview.get_interview_type_display())
    date_str = interview.date.strftime('%d.%m.%Y') if interview.date else 'без даты'
    pk_part = f' [id {interview.pk}]' if getattr(interview, 'pk', None) else ''
    return f'{direction}. {full_name}. {company}. {itype}. {date_str}{pk_part}{ext}'


def build_ya_disk_filename(interview, ext: str) -> str:
    """Алиас для обратной совместимости импортов."""
    return build_video_object_filename(interview, ext)
