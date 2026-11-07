"""
Тесты для валидаторов приложения interns.

Используются маркеры pytest:
- @pytest.mark.validators - для группировки тестов валидаторов
"""
import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError

from core.validators import (
    get_telegram_tme_url,
    is_valid_telegram_contact,
    normalize_telegram_username,
    parse_telegram_contact,
    validate_date_of_birth,
    validate_hr_contacts_telegram,
    validate_telegram_username,
)


@pytest.mark.validators
class TestValidateDateOfBirth:
    """Тесты для валидатора validate_date_of_birth."""

    @pytest.mark.parametrize('valid_date', [
        date.today() - timedelta(days=365),
        date.today(),
        date.today() - timedelta(days=36500),
        date(2000, 1, 1),
        None,
    ])
    def test_valid_dates_pass(self, valid_date):
        """Валидные значения не вызывают ValidationError."""
        validate_date_of_birth(valid_date)

    def test_future_date_raises(self):
        """Будущая дата вызывает ValidationError."""
        with pytest.raises(ValidationError, match='не может быть в будущем'):
            validate_date_of_birth(date.today() + timedelta(days=1))

    def test_too_old_date_raises(self):
        """Дата старше 100 лет вызывает ValidationError."""
        old_date = date(date.today().year - 101, 1, 1)
        with pytest.raises(ValidationError, match='больше 100 лет'):
            validate_date_of_birth(old_date)


@pytest.mark.validators
class TestNormalizeTelegramUsername:
    """Тесты для функции normalize_telegram_username."""

    @pytest.mark.parametrize('input_val, expected', [
        ('@vasya',                       '@vasya'),
        ('vasya',                        '@vasya'),
        ('https://t.me/vasya_pupkin',    '@vasya_pupkin'),
        ('t.me/vasya_pupkin',            '@vasya_pupkin'),
        ('https://t.me/vasya/',          '@vasya'),
        ('  @vasya  ',                   '@vasya'),
        ('  vasya  ',                    '@vasya'),
        ('user_123',                     '@user_123'),
        ('https://t.me/MyUser123',       '@MyUser123'),
        ('',                             ''),
        (None,                           None),
    ])
    def test_normalize(self, input_val, expected):
        """Нормализация username из различных форматов."""
        result = normalize_telegram_username(input_val)
        assert result == expected


@pytest.mark.validators
class TestValidateTelegramUsername:
    """Тесты для валидатора validate_telegram_username."""

    @pytest.mark.parametrize('valid_username', [
        '@vasya',
        '@user123',
        '@user_name',
        '@' + 'a' * 31,
        '',
        None,
    ])
    def test_valid_usernames_pass(self, valid_username):
        """Корректные значения не вызывают ValidationError."""
        validate_telegram_username(valid_username)

    @pytest.mark.parametrize('invalid_username', [
        '@abc',
        '@user name',
        '@user!name',
        '@пользователь',
        '@' + 'a' * 32,
        '@',
    ])
    def test_invalid_usernames_raise(self, invalid_username):
        """Некорректные username вызывают ValidationError."""
        with pytest.raises(ValidationError, match='формате @username'):
            validate_telegram_username(invalid_username)

    def test_normalize_then_validate(self):
        """Нормализованный username из ссылки проходит валидацию."""
        value = normalize_telegram_username('https://t.me/valid_user1')
        validate_telegram_username(value)


@pytest.mark.validators
class TestValidateHrContactsTelegram:
    """Тесты для валидатора validate_hr_contacts_telegram (Контакты HR)."""

    @pytest.mark.parametrize('value', ['', None, 'anna@company.com', 'тел. +7 999 123-45-67'])
    def test_non_telegram_passed(self, value):
        """Не-Telegram значения не проверяются и проходят."""
        validate_hr_contacts_telegram(value)

    @pytest.mark.parametrize('value', ['@valid_user', '@user123', 'https://t.me/valid_user1'])
    def test_valid_telegram_passed(self, value):
        """Корректный Telegram в Контактах HR проходит."""
        validate_hr_contacts_telegram(value)

    @pytest.mark.parametrize('value', ['@abc', 't.me/ab'])
    def test_invalid_telegram_raises(self, value):
        """Слишком короткий или невалидный Telegram в Контактах HR вызывает ValidationError."""
        with pytest.raises(ValidationError, match='формате @username'):
            validate_hr_contacts_telegram(value)

    @pytest.mark.parametrize('value', ['Tr: @LisanDanilovna', 'контакт @valid_user', 'https://t.me/okurr'])
    def test_telegram_inside_text_passed(self, value):
        """Telegram внутри текста (префикс, ссылка) проходит валидацию Контактов HR."""
        validate_hr_contacts_telegram(value)


@pytest.mark.validators
class TestParseTelegramContact:
    """Тесты для parse_telegram_contact — извлечение первого @username из строки."""

    @pytest.mark.parametrize('value, expected', [
        ('@vasya', '@vasya'),
        ('Tr: @LisanDanilovna', '@LisanDanilovna'),
        ('https://t.me/okurr', '@okurr'),
        ('контакт @user_123', '@user_123'),
        ('', None),
        (None, None),
        ('+79933661610', None),
        ('На xx', None),
    ])
    def test_parse(self, value, expected):
        """Извлекается первый валидный Telegram-контакт или None."""
        assert parse_telegram_contact(value) == expected

    @pytest.mark.parametrize('value', ['@vasya', 'Tr: @user', 'https://t.me/okurr'])
    def test_is_valid_and_url(self, value):
        """Если parse находит контакт, is_valid_telegram_contact и get_telegram_tme_url работают."""
        assert is_valid_telegram_contact(value) is True
        url = get_telegram_tme_url(value)
        assert url.startswith('https://t.me/')
        assert '@' not in url
