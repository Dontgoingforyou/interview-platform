from django import template
from core.constants import MONTH_NAMES
from core.intern_utils import transliterate_name_to_cyrillic
from core.validators import get_telegram_tme_url, is_valid_telegram_contact

register = template.Library()


@register.filter
def transliterate_name(value):
    """
    Транслитерирует имя (ФИО) из латиницы в кириллицу для отображения.
    Фоллбэк: при пустом/некорректном результате возвращается исходное значение.
    """
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return value
    result = transliterate_name_to_cyrillic(value)
    if not result or not result.strip():
        return value
    return result


@register.filter
def get_item(dictionary, key):
    """
    Универсальный фильтр для получения значения из словаря по ключу.
    Если значение - объект с атрибутом name, возвращает obj.name.
    Иначе возвращает само значение.
    """
    if not dictionary or not key:
        return None

    obj = dictionary.get(key)
    if obj is None:
        return None

    # Если объект имеет атрибут name (например, модель Direction, Company, Manager)
    if hasattr(obj, 'name'):
        return obj.name

    return obj


@register.filter
def get_month_name(index):
    """Возвращает название месяца по его номеру (1-12)."""
    try:
        return MONTH_NAMES[int(index) - 1]
    except (IndexError, ValueError, TypeError):
        return "—"


@register.filter
def starts_with_page_prefix(value):
    """Проверяет, начинается ли строка с 'page_'."""
    return isinstance(value, str) and value.startswith('page_')


@register.filter
def get_range(value):
    """Фильтр для цикла по диапазону чисел."""
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return []


@register.filter
def aliases_preview(aliases_list, char_limit=80):
    """
    Возвращает превью псевдонимов: показывает столько псевдонимов,
    сколько умещается в char_limit символов, остальные заменяет «+ ещё N».
    """
    from django.utils.html import format_html, escape

    if not aliases_list:
        return ''

    visible = []
    total_len = 0
    for alias in aliases_list:
        sep_len = 2 if visible else 0  # длина ', ' перед следующим элементом
        if visible and total_len + sep_len + len(alias) > char_limit:
            break
        visible.append(alias)
        total_len += sep_len + len(alias)

    remaining = len(aliases_list) - len(visible)
    text = escape(', '.join(visible))
    if remaining > 0:
        return format_html('{} <em>+ ещё {}</em>', text, remaining)
    return text


@register.filter
def is_telegram_contact(value):
    """Проверяет, является ли значение валидным Telegram-контактом (для отображения ссылки)."""
    return bool(value and is_valid_telegram_contact(value))


@register.filter
def telegram_tme_url(value):
    """Возвращает URL t.me для личных сообщений или пустую строку."""
    url = get_telegram_tme_url(value) if value else None
    return url or ''


@register.filter
def metric_percent(value):
    """Форматирует число как процент с одним знаком после запятой (для SSR метрик)."""
    if value is None:
        return '—'
    try:
        return f'{float(value):.1f}%'
    except (TypeError, ValueError):
        return '—'


@register.filter
def metric_percent_ratio(value):
    """Доля 0–1 в проценты с одним знаком (для success_rate и т.п.). 0.45 -> «45.0%»."""
    if value is None:
        return '—'
    try:
        return f'{float(value) * 100:.1f}%'
    except (TypeError, ValueError):
        return '—'


@register.filter
def format_subtitle_count(value, suffix):
    """Форматирует подпись метрики: число + суффикс в скобках. 5, «интервью за 30 дней» -> «(5 интервью за 30 дней)»."""
    if value is None:
        return ''
    try:
        n = int(value)
        return f'({n} {suffix})'
    except (TypeError, ValueError):
        return ''


@register.filter
def format_days(value):
    """Для подписи «X дн.» (например, fastest-direction-days)."""
    if value is None:
        return ''
    try:
        n = int(float(value))
        return f'{n} дн.'
    except (TypeError, ValueError):
        return ''


@register.filter
def decimal_dot(value, decimals=None):
    """Десятичное число с точкой (как в JS toFixed), без локали — чтобы не мигала запятая."""
    if value is None:
        return '—'
    try:
        n = int(decimals) if decimals is not None else 2
        return f'{float(value):.{n}f}'
    except (TypeError, ValueError):
        return '—'


@register.filter
def metric_currency(value):
    """Форматирует число как рубли для SSR метрик (средний оффер и т.п.)."""
    if value is None:
        return '—'
    try:
        n = int(float(value))
        return f'{n:,} ₽'.replace(',', ' ')
    except (TypeError, ValueError):
        return '—'


@register.filter
def is_active_url(url_name, url_names):
    """
    Проверяет, является ли текущий url_name одним из переданных значений.
    Используется для выделения вкладки в sidebar.html
    """
    if not url_name:
        return False
    url_list = [name.strip() for name in str(url_names).split(',')]
    return url_name in url_list


@register.filter
def interview_transcription_allowed_for_request(interview, request):
    """Показ кнопок транскрипции в таблицах: роли и владение собеседованием (см. session_may_access_interview_transcription)."""
    from interviews.utils import session_may_access_interview_transcription

    return session_may_access_interview_transcription(request, interview.pk)
