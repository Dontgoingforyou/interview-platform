"""
Общие валидаторы проекта.

Telegram-валидаторы используются в interviews, sad_intern, interns, debts и в шаблонах (core).
Валидатор даты рождения — в моделях interns (здесь для единой точки импорта).
"""
import re
from datetime import date
from django.core.exceptions import ValidationError

# Строгое совпадение: вся строка — один @username (4–31 символ).
TELEGRAM_RE = re.compile(r'^@[a-zA-Z0-9_]{4,31}$')
# Поиск первого @username в тексте (для «Tr: @user», «email, @user» и т.п.).
TELEGRAM_IN_TEXT_RE = re.compile(r'@[a-zA-Z0-9_]{4,31}')


def parse_telegram_contact(value):
    """
    Извлекает первый валидный Telegram-контакт из строки.

    Поддерживает:
    - целиком: @user, https://t.me/user, t.me/user;
    - внутри текста: «Tr: @LisanDanilovna», «контакт @username» и т.п.
    Возвращает @username или None, если ничего подходящего нет.
    """
    if not value:
        return None
    s = value.strip()
    if not s:
        return None
    # Сначала проверяем t.me/ — извлекаем username из пути
    if 't.me/' in s:
        part = s.split('t.me/')[-1].strip('/').split('?')[0].strip('/')
        match = re.match(r'^([a-zA-Z0-9_]{4,31})(?:/|$)', part)
        if match:
            return '@' + match.group(1)
    # Иначе ищем первое вхождение @username в строке
    found = TELEGRAM_IN_TEXT_RE.search(s)
    if found:
        return found.group(0)
    return None


def normalize_telegram_username(value):
    """
    Нормализует значение к одному @username (для полей «только Telegram»).

    Принимает: @user, user, https://t.me/user, t.me/user.
    Возвращает @username или исходное значение/пустую строку.
    """
    if not value:
        return value
    value = value.strip()
    if 't.me/' in value:
        part = value.split('t.me/')[-1].strip('/').split('?')[0].strip('/')
        value = '@' + part
    if value and not value.startswith('@'):
        value = '@' + value
    return value


def validate_telegram_username(value):
    """
    Валидатор формата Telegram-username (целиком одно значение).
    Пустое значение пропускается.
    """
    if not value:
        return
    normalized = normalize_telegram_username(value)
    if not TELEGRAM_RE.match(normalized):
        raise ValidationError(
            'Telegram-аккаунт должен быть в формате @username '
            '(от 5 до 32 символов, допустимы буквы, цифры и _).'
        )


def is_valid_telegram_contact(value):
    """Есть ли в строке хотя бы один валидный Telegram-контакт (для ссылки)."""
    return parse_telegram_contact(value) is not None


def get_telegram_tme_url(value):
    """URL для перехода в личку (https://t.me/username) или None."""
    username = parse_telegram_contact(value)
    if not username:
        return None
    return f'https://t.me/{username.lstrip("@")}'


def validate_hr_contacts_telegram(value):
    """
    Валидатор для поля «Контакты HR»: если значение похоже на Telegram
    (начинается с @ или содержит t.me/), проверяет формат. Иначе не проверяется (email и др.).
    """
    if not value:
        return
    value = value.strip()
    if not (value.startswith('@') or 't.me/' in value):
        return
    parsed = parse_telegram_contact(value)
    if parsed and TELEGRAM_RE.match(parsed):
        return
    # Если не удалось извлечь валидный контакт, проверяем как «целиком одно значение»
    normalized = normalize_telegram_username(value)
    validate_telegram_username(normalized)


def validate_date_of_birth(value):
    """Валидатор даты рождения (используется в моделях interns)."""
    if not value:
        return

    today = date.today()

    if value > today:
        raise ValidationError('Дата рождения не может быть в будущем.')

    age = today.year - value.year
    if (today.month, today.day) < (value.month, value.day):
        age -= 1

    if age > 100:
        raise ValidationError('Возраст не может быть больше 100 лет.')
