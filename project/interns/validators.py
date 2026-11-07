"""
Валидаторы приложения interns.

Реэкспорт из core.validators для совместимости с миграциями и существующим кодом.
Импорты из core.validators.
"""
from core.validators import (
    TELEGRAM_IN_TEXT_RE,
    TELEGRAM_RE,
    get_telegram_tme_url,
    is_valid_telegram_contact,
    normalize_telegram_username,
    parse_telegram_contact,
    validate_date_of_birth,
    validate_hr_contacts_telegram,
    validate_telegram_username,
)

__all__ = [
    'TELEGRAM_IN_TEXT_RE',
    'TELEGRAM_RE',
    'get_telegram_tme_url',
    'is_valid_telegram_contact',
    'normalize_telegram_username',
    'parse_telegram_contact',
    'validate_date_of_birth',
    'validate_hr_contacts_telegram',
    'validate_telegram_username',
]
