import logging

logger = logging.getLogger('interns_portal')

UPLOAD_SENTINEL = '__uploading__'


def portal_upload_log(level: str, phase: str, interview_id: int, **extra) -> None:
    """Единый формат для Loki: phase, interview_id и опциональные поля."""
    parts = [f'[PORTAL_UPLOAD] phase={phase} interview_id={interview_id}']
    for key, value in extra.items():
        parts.append(f'{key}={value}')
    getattr(logger, level)(' '.join(parts))


def portal_user_label(user) -> str:
    """Обезличенный идентификатор пользователя (без email)."""
    return (
        getattr(user, 'full_name', None)
        or getattr(user, 'email', None)
        or 'unknown'
    )
