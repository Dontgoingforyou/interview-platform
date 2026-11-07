import logging
from typing import Dict, Any

from core.intern_utils import transliterate_name_to_cyrillic

logger = logging.getLogger(__name__)

ENTITY_INTERVIEW = 'interview'
ENTITY_INTERN = 'intern'
ENTITY_OFFER = 'offer'
ENTITY_DEBT = 'debt'
ENTITY_SAD_INTERN = 'sad_intern'
ENTITY_MANAGER = 'manager'
ENTITY_COMPANY = 'company'
ENTITY_DIRECTION = 'direction'
ENTITY_INTERN_WEEKLY_STATUS = 'intern_weekly_status'
ENTITY_INTERVIEW_TRANSCRIPTION = 'interview_transcription'
ENTITY_KB_ARTICLE = 'kb_article'

VECTOR_ENTITY_TYPES = (
    ENTITY_INTERVIEW,
    ENTITY_INTERN,
    ENTITY_OFFER,
    ENTITY_DEBT,
    ENTITY_SAD_INTERN,
    ENTITY_MANAGER,
    ENTITY_COMPANY,
    ENTITY_DIRECTION,
    ENTITY_INTERN_WEEKLY_STATUS,
    ENTITY_INTERVIEW_TRANSCRIPTION,
    ENTITY_KB_ARTICLE,
)


def extract_kb_article_text(article) -> str:
    """
    Текст статьи базы знаний для эмбеддинга (заголовок + Markdown).
    """
    title = getattr(article, 'title', None) or ''
    content = getattr(article, 'content', None) or ''
    return f'{title}\n\n{content}'.strip()


def extract_interview_text(interview) -> str:
    """
    Извлекает текстовое представление собеседования.

    Args:
        interview: Объект Interview

    Returns:
        Текстовая строка для векторизации
    """
    parts = []

    # Тип собеседования
    if interview.interview_type:
        parts.append(f"Тип: {interview.get_interview_type_display()}")

    # Информация о студенте
    if interview.intern:
        parts.append(f"Студент: {interview.intern.full_name}")

    # Компания
    try:
        company = interview.company
        if company:
            parts.append(f"Компания: {company.name}")
    except Exception as e:
        logger.debug('Извлечение company для interview: %s', e)

    # Направление
    try:
        direction = interview.direction
        if direction:
            parts.append(f"Направление: {direction.name}")
    except Exception as e:
        logger.debug('Извлечение direction для interview: %s', e)

    # HR информация
    if interview.hr_name:
        parts.append(f"HR: {interview.hr_name}")
    if interview.hr_contacts:
        parts.append(f"Контакты HR: {interview.hr_contacts}")

    # Ссылки
    if interview.vacancy_link:
        parts.append(f"Вакансия: {interview.vacancy_link}")

    # Дата
    if interview.date:
        parts.append(f"Дата: {interview.date.strftime('%d.%m.%Y')}")

    return " | ".join(parts)


def extract_intern_text(intern) -> str:
    """
    Извлекает текстовое представление студента.

    Args:
        intern: Объект Intern

    Returns:
        Текстовая строка для векторизации
    """
    parts = []

    # Основная информация
    parts.append(f"Имя: {intern.full_name}")

    if intern.email:
        parts.append(f"Email: {intern.email}")

    if intern.telegram_username:
        parts.append(f"Telegram: {intern.telegram_username}")

    # Направление
    try:
        direction = intern.direction
        if direction:
            parts.append(f"Направление: {direction.name}")
    except Exception as e:
        logger.debug('Извлечение direction для intern: %s', e)

    # Группа и тип обучения
    if intern.group:
        parts.append(f"Группа: {intern.group}")

    if intern.type_of_training:
        parts.append(f"Тип обучения: {intern.get_type_of_training_display()}")

    # HR информация
    if intern.hiring_hr:
        parts.append(f"Нанимающий HR: {intern.hiring_hr}")

    if intern.responsible_hr:
        parts.append(f"Ответственный HR: {intern.responsible_hr}")

    # Отзывы (важно для поиска!)
    if intern.hr_feedback:
        parts.append(f"Отзыв HR: {intern.hr_feedback}")

    if intern.mentor_feedback:
        parts.append(f"Отзыв ментора: {intern.mentor_feedback}")

    # Статус
    try:
        parts.append(f"Статус: {intern.status_display}")
    except Exception as e:
        logger.debug('Извлечение status_display для intern: %s', e)

    return " | ".join(parts)


def extract_offer_text(offer) -> str:
    """
    Извлекает текстовое представление оффера.

    Args:
        offer: Объект Offer

    Returns:
        Текстовая строка для векторизации
    """
    parts = []

    # Студент
    if offer.intern:
        parts.append(f"Студент: {offer.intern.full_name}")

    # Компания
    if offer.company:
        parts.append(f"Компания: {offer.company}")

    # Направление
    try:
        direction = offer.direction
        if direction:
            parts.append(f"Направление: {direction.name}")
    except Exception as e:
        logger.debug('Извлечение direction для offer: %s', e)

    # Сумма
    if offer.amount:
        parts.append(f"Сумма: {offer.amount} руб.")

    # Период
    parts.append(f"Период: {offer.month}/{offer.year}")

    return " | ".join(parts)


def extract_debt_text(debt) -> str:
    """
    Извлекает текстовое представление долга.

    Args:
        debt: Объект Debt

    Returns:
        Текстовая строка для векторизации
    """
    parts = []

    # Студент
    if debt.intern:
        parts.append(f"Студент: {debt.intern.full_name}")

    if debt.telegram_username:
        parts.append(f"Telegram: {debt.telegram_username}")

    if debt.email:
        parts.append(f"Email: {debt.email}")

    # Направление
    try:
        direction = debt.direction
        if direction:
            parts.append(f"Направление: {direction.name}")
    except Exception as e:
        logger.debug('Извлечение direction для debt: %s', e)

    # Финансовая информация
    parts.append(f"Общая сумма: {debt.total_amount} руб.")
    parts.append(f"Уже заплатил: {debt.paid_amount} руб.")
    parts.append(f"Остаток: {debt.balance} руб.")

    if debt.payment_status:
        parts.append(f"Статус оплаты: {debt.get_payment_status_display()}")

    # Дата акта
    if debt.act_date:
        parts.append(f"Дата акта: {debt.act_date.strftime('%d.%m.%Y')}")

    return " | ".join(parts)


def extract_sad_intern_text(sad_intern) -> str:
    """
    Извлекает текстовое представление грустного студента.

    Args:
        sad_intern: Объект SadIntern

    Returns:
        Текстовая строка для векторизации
    """
    parts = []

    # Студент
    if sad_intern.intern:
        parts.append(f"Студент: {sad_intern.intern.full_name}")

    if sad_intern.telegram_username:
        parts.append(f"Telegram: {sad_intern.telegram_username}")

    # Период ожидания
    parts.append(f"Дней ожидания: {sad_intern.days_waiting}")

    if sad_intern.waiting_since:
        parts.append(f"Ждет с: {sad_intern.waiting_since.strftime('%d.%m.%Y')}")

    # Статус
    if sad_intern.status:
        parts.append(f"Статус: {sad_intern.get_status_display()}")

    # Примечание (важно!)
    if sad_intern.note:
        parts.append(f"Примечание: {sad_intern.note}")

    return " | ".join(parts)


def extract_manager_text(manager) -> str:
    """
    Извлекает текстовое представление менеджера.

    Args:
        manager: Объект Manager

    Returns:
        Текстовая строка для векторизации
    """
    parts = []
    raw_name = manager.full_name or ''
    display_name = transliterate_name_to_cyrillic(raw_name) or raw_name
    parts.append(f"Имя: {display_name}")
    parts.append(f"Email: {manager.email}")

    if manager.username:
        parts.append(f"Username: {manager.username}")

    # Группы/роли
    if manager.groups:
        groups_str = ", ".join(manager.groups)
        parts.append(f"Роли: {groups_str}")

    # Статус
    status = "Активен" if manager.is_active else "Неактивен"
    parts.append(f"Статус: {status}")

    return " | ".join(parts)


def extract_company_text(company) -> str:
    """
    Извлекает текстовое представление компании.

    Args:
        company: Объект Company

    Returns:
        Текстовая строка для векторизации
    """
    parts = []

    parts.append(f"Компания: {company.name}")

    if company.is_bigtech:
        parts.append("Тип: Бигтех")

    aliases = company.get_aliases_list()
    if aliases:
        parts.append(f"Псевдонимы: {', '.join(aliases)}")

    return " | ".join(parts)


def extract_direction_text(direction) -> str:
    """
    Извлекает текстовое представление направления.

    Args:
        direction: Объект Direction

    Returns:
        Текстовая строка для векторизации
    """
    parts = []
    parts.append(f"Направление: {direction.name}")
    return " | ".join(parts)


def extract_intern_weekly_status_text(intern_weekly_status) -> str:
    """
    Извлекает текстовое представление недельного статуса студента.

    Args:
        intern_weekly_status: Объект InternWeeklyStatus (с select_related('intern'))

    Returns:
        Текстовая строка для векторизации
    """
    parts = []

    if intern_weekly_status.intern:
        parts.append(f"Студент: {intern_weekly_status.intern.full_name}")

    if intern_weekly_status.week_start:
        parts.append(f"Неделя: {intern_weekly_status.week_start.strftime('%d.%m.%Y')}")

    if intern_weekly_status.absence_status:
        parts.append(f"Отсутствие: {intern_weekly_status.get_absence_status_display()}")

    if intern_weekly_status.absence_notes:
        parts.append(f"Комментарий: {intern_weekly_status.absence_notes}")

    if intern_weekly_status.manual_interview_count is not None:
        parts.append(f"Ручное кол-во собесов: {intern_weekly_status.manual_interview_count}")

    return " | ".join(parts)


def extract_transcription_text(transcription) -> str:
    """
    Извлекает текст транскрипции собеседования для векторизации.

    Args:
        transcription: Объект InterviewTranscription

    Returns:
        Текстовая строка для векторизации
    """
    return transcription.text or ''


def extract_metadata(obj, entity_type: str) -> Dict[str, Any]:
    """
    Извлекает метаданные для фильтрации.

    Args:
        obj: Объект модели
        entity_type: Тип сущности

    Returns:
        Словарь с метаданными
    """
    metadata = {
        'entity_type': entity_type,
    }

    # Общие поля
    if hasattr(obj, 'direction_id') and obj.direction_id:
        metadata['direction_id'] = obj.direction_id
        try:
            direction = getattr(obj, 'direction', None)
            if direction:
                metadata['direction_name'] = direction.name
        except Exception as e:
            logger.debug('Метаданные direction_name: %s', e)

    if hasattr(obj, 'manager_email') and obj.manager_email:
        metadata['manager_email'] = obj.manager_email

    # Специфичные для типа
    if entity_type == ENTITY_INTERVIEW:
        if hasattr(obj, 'interview_type'):
            metadata['interview_type'] = obj.interview_type
        if hasattr(obj, 'company_id') and obj.company_id:
            metadata['company_id'] = obj.company_id
            try:
                company = getattr(obj, 'company', None)
                if company:
                    metadata['company_name'] = company.name
            except Exception as e:
                logger.debug('Метаданные company_name: %s', e)
        if hasattr(obj, 'date') and obj.date:
            metadata['date'] = obj.date.isoformat()

    elif entity_type == ENTITY_INTERN:
        if hasattr(obj, 'type_of_training'):
            metadata['type_of_training'] = obj.type_of_training
        if hasattr(obj, 'group'):
            metadata['group'] = obj.group
        try:
            metadata['status'] = obj.status
        except Exception as e:
            logger.debug('Метаданные status для intern: %s', e)

    elif entity_type == ENTITY_OFFER:
        if hasattr(obj, 'company'):
            metadata['company'] = obj.company
        if hasattr(obj, 'month'):
            metadata['month'] = obj.month
        if hasattr(obj, 'year'):
            metadata['year'] = obj.year

    elif entity_type == ENTITY_DEBT:
        if hasattr(obj, 'payment_status'):
            metadata['payment_status'] = obj.payment_status

    elif entity_type == ENTITY_SAD_INTERN:
        if hasattr(obj, 'status'):
            metadata['status'] = obj.status
        if hasattr(obj, 'days_waiting'):
            metadata['days_waiting'] = obj.days_waiting

    elif entity_type == ENTITY_COMPANY:
        if hasattr(obj, 'name'):
            metadata['company_name'] = obj.name
        if hasattr(obj, 'is_bigtech'):
            metadata['is_bigtech'] = obj.is_bigtech

    elif entity_type == ENTITY_DIRECTION:
        if hasattr(obj, 'id'):
            metadata['direction_id'] = obj.id
        if hasattr(obj, 'name'):
            metadata['direction_name'] = obj.name

    elif entity_type == ENTITY_INTERN_WEEKLY_STATUS:
        if hasattr(obj, 'intern') and obj.intern:
            if getattr(obj.intern, 'direction_id', None):
                metadata['direction_id'] = obj.intern.direction_id
            if getattr(obj.intern, 'manager_email', None):
                metadata['manager_email'] = obj.intern.manager_email
        if hasattr(obj, 'week_start') and obj.week_start:
            metadata['week_start'] = obj.week_start.isoformat()
        if hasattr(obj, 'absence_status') and obj.absence_status:
            metadata['absence_status'] = obj.absence_status

    elif entity_type == ENTITY_INTERVIEW_TRANSCRIPTION:
        if hasattr(obj, 'interview') and obj.interview:
            metadata['interview_id'] = str(obj.interview_id)
            if hasattr(obj.interview, 'direction_id') and obj.interview.direction_id:
                metadata['direction_id'] = obj.interview.direction_id
            if hasattr(obj.interview, 'manager_email') and obj.interview.manager_email:
                metadata['manager_email'] = obj.interview.manager_email

    elif entity_type == ENTITY_KB_ARTICLE:
        section = getattr(obj, 'section', None)
        if section is not None:
            metadata['section_id'] = str(section.section_id)
        if hasattr(obj, 'filename') and obj.filename is not None:
            metadata['filename'] = str(obj.filename)
        if hasattr(obj, 'title') and obj.title is not None:
            metadata['title'] = str(obj.title)

    return metadata


# Маппинг типов сущностей к функциям извлечения текста
TEXT_EXTRACTORS = {
    ENTITY_INTERVIEW: extract_interview_text,
    ENTITY_INTERN: extract_intern_text,
    ENTITY_OFFER: extract_offer_text,
    ENTITY_DEBT: extract_debt_text,
    ENTITY_SAD_INTERN: extract_sad_intern_text,
    ENTITY_MANAGER: extract_manager_text,
    ENTITY_COMPANY: extract_company_text,
    ENTITY_DIRECTION: extract_direction_text,
    ENTITY_INTERN_WEEKLY_STATUS: extract_intern_weekly_status_text,
    ENTITY_INTERVIEW_TRANSCRIPTION: extract_transcription_text,
    ENTITY_KB_ARTICLE: extract_kb_article_text,
}


def extract_text_from_entity(entity_type: str, obj) -> str:
    """
    Универсальная функция извлечения текста.

    Args:
        entity_type: Тип сущности
        obj: Объект модели

    Returns:
        Текстовая строка
    """
    extractor = TEXT_EXTRACTORS.get(entity_type)
    if extractor:
        return extractor(obj)
    return str(obj)
