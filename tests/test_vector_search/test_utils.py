"""
Тесты для утилит приложения vector_search.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.utils - для группировки тестов утилит
"""
import pytest

from vector_search.utils import (
    extract_interview_text,
    extract_intern_text,
    extract_offer_text,
    extract_debt_text,
    extract_sad_intern_text,
    extract_manager_text,
    extract_company_text,
    extract_metadata,
    extract_text_from_entity,
)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.utils
class TestTextExtractors:
    """Тесты для функций извлечения текста."""

    def test_extract_interview_text_basic(self, interview):
        """Проверка извлечения текста из интервью."""
        text = extract_interview_text(interview)

        assert 'Тип:' in text
        assert 'Скрининг' in text
        assert interview.intern.full_name in text

    def test_extract_interview_text_with_company(self, interview_with_company):
        """Проверка извлечения текста из интервью с компанией."""
        text = extract_interview_text(interview_with_company)

        assert 'Компания:' in text
        assert interview_with_company.hr_name in text
        assert interview_with_company.hr_contacts in text

    def test_extract_interview_text_with_direction(self, interview, direction):
        """Проверка что направление включается в текст."""
        text = extract_interview_text(interview)

        assert 'Направление:' in text
        assert direction.name in text

    def test_extract_interview_text_with_date(self, interview):
        """Проверка что дата включается в текст."""
        text = extract_interview_text(interview)

        assert 'Дата:' in text
        assert interview.date.strftime('%d.%m.%Y') in text

    def test_extract_intern_text_basic(self, intern):
        """Проверка извлечения текста из студента."""
        text = extract_intern_text(intern)

        assert f'Имя: {intern.full_name}' in text
        assert f'Email: {intern.email}' in text

    def test_extract_intern_text_with_telegram(self, intern):
        """Проверка извлечения telegram из студента."""
        intern.telegram_username = '@test_user'
        intern.save()

        text = extract_intern_text(intern)

        assert 'Telegram: @test_user' in text

    def test_extract_intern_text_with_direction(self, intern, direction):
        """Проверка что направление включается в текст."""
        text = extract_intern_text(intern)

        assert 'Направление:' in text
        assert direction.name in text

    def test_extract_intern_text_with_feedback(self, intern):
        """Проверка извлечения отзывов."""
        intern.hr_feedback = 'Отличный кандидат'
        intern.mentor_feedback = 'Хорошо работает'
        intern.save()

        text = extract_intern_text(intern)

        assert 'Отзыв HR: Отличный кандидат' in text
        assert 'Отзыв ментора: Хорошо работает' in text

    def test_extract_intern_text_with_training_type(self, intern):
        """Проверка извлечения типа обучения."""
        text = extract_intern_text(intern)

        assert 'Тип обучения:' in text

    def test_extract_offer_text_basic(self, offer, intern):
        """Проверка извлечения текста из оффера."""
        text = extract_offer_text(offer)

        assert f'Студент: {intern.full_name}' in text
        assert 'Компания: Test Company' in text
        assert 'Сумма: 100000.00 руб.' in text
        assert 'Период: 12/2025' in text

    def test_extract_offer_text_with_direction(self, offer, direction):
        """Проверка что направление включается в оффер."""
        text = extract_offer_text(offer)

        assert 'Направление:' in text
        assert direction.name in text

    def test_extract_debt_text_basic(self, debt, intern):
        """Проверка извлечения текста из долга."""
        text = extract_debt_text(debt)

        assert f'Студент: {intern.full_name}' in text
        assert 'Telegram: @test' in text
        assert 'Общая сумма: 50000.00 руб.' in text
        assert 'Уже заплатил: 10000.00 руб.' in text
        assert 'Остаток: 40000.00 руб.' in text

    def test_extract_debt_text_with_statuses(self, debt):
        """Проверка извлечения статусов из долга."""
        text = extract_debt_text(debt)

        assert 'Статус оплаты:' in text

    def test_extract_sad_intern_text_basic(self, sad_intern):
        """Проверка извлечения текста из грустного студента."""
        text = extract_sad_intern_text(sad_intern)

        assert f'Студент: {sad_intern.intern.full_name}' in text
        assert f'Telegram: {sad_intern.telegram_username}' in text
        assert 'Дней ожидания:' in text
        assert 'Статус:' in text

    def test_extract_sad_intern_text_with_note(self, sad_intern):
        """Проверка извлечения примечания."""
        text = extract_sad_intern_text(sad_intern)

        assert f'Примечание: {sad_intern.note}' in text

    def test_extract_manager_text_basic(self, manager):
        """Проверка извлечения текста из менеджера."""
        text = extract_manager_text(manager)

        assert f'Имя: {manager.full_name}' in text
        assert f'Email: {manager.email}' in text
        assert f'Username: {manager.username}' in text

    def test_extract_manager_text_with_groups(self, manager):
        """Проверка извлечения групп/ролей менеджера."""
        text = extract_manager_text(manager)

        assert 'Роли:' in text

    def test_extract_manager_text_active_status(self, manager):
        """Проверка отображения статуса активности."""
        text = extract_manager_text(manager)

        assert 'Статус: Активен' in text

    def test_extract_manager_text_inactive_status(self, manager):
        """Проверка отображения статуса неактивности."""
        manager.is_active = False
        manager.save()

        text = extract_manager_text(manager)

        assert 'Статус: Неактивен' in text

    def test_extract_company_text_basic(self, company):
        """Проверка извлечения текста из компании: название присутствует."""
        text = extract_company_text(company)

        assert f'Компания: {company.name}' in text

    def test_extract_company_text_bigtech_flag(self, company):
        """Бигтех-компания содержит метку 'Бигтех' в тексте."""
        company.is_bigtech = True
        company.save()

        text = extract_company_text(company)

        assert 'Бигтех' in text

    def test_extract_company_text_no_bigtech(self):
        """Не-бигтех компания НЕ содержит метку 'Бигтех'."""
        from companies.models import Company
        c = Company(name='Маленькая Компания', is_bigtech=False)
        text = extract_company_text(c)

        assert 'Бигтех' not in text

    def test_extract_company_text_with_aliases(self):
        """Псевдонимы включаются в текст."""
        from companies.models import Company
        c = Company(name='Yandex', is_bigtech=True, aliases='Яндекс\nYa')
        text = extract_company_text(c)

        assert 'Псевдонимы:' in text
        assert 'Яндекс' in text
        assert 'Ya' in text

    def test_extract_company_text_empty_aliases(self):
        """Пустые псевдонимы не добавляют лишний раздел."""
        from companies.models import Company
        c = Company(name='Solo', is_bigtech=False, aliases='')
        text = extract_company_text(c)

        assert 'Псевдонимы' not in text


@pytest.mark.django_db(databases=['default'])
@pytest.mark.utils
class TestMetadataExtraction:
    """Тесты для функции извлечения метаданных."""

    def test_extract_metadata_interview(self, interview):
        """Проверка извлечения метаданных из интервью."""
        metadata = extract_metadata(interview, 'interview')

        assert metadata['entity_type'] == 'interview'
        assert metadata['direction_id'] == interview.direction_id
        assert metadata['manager_email'] == interview.manager_email
        assert metadata['interview_type'] == interview.interview_type
        assert 'date' in metadata

    def test_extract_metadata_intern(self, intern):
        """Проверка извлечения метаданных из студента."""
        metadata = extract_metadata(intern, 'intern')

        assert metadata['entity_type'] == 'intern'
        assert metadata['direction_id'] == intern.direction_id
        assert metadata['manager_email'] == intern.manager_email
        assert metadata['type_of_training'] == intern.type_of_training
        assert metadata['group'] == intern.group

    def test_extract_metadata_offer(self, offer):
        """Проверка извлечения метаданных из оффера."""
        metadata = extract_metadata(offer, 'offer')

        assert metadata['entity_type'] == 'offer'
        assert metadata['company'] == 'Test Company'
        assert metadata['month'] == 12
        assert metadata['year'] == 2025

    def test_extract_metadata_debt(self, debt):
        """Проверка извлечения метаданных из долга."""
        metadata = extract_metadata(debt, 'debt')

        assert metadata['entity_type'] == 'debt'
        assert metadata['payment_status'] == 'paying'

    def test_extract_metadata_sad_intern(self, sad_intern):
        """Проверка извлечения метаданных из грустного студента."""
        metadata = extract_metadata(sad_intern, 'sad_intern')

        assert metadata['entity_type'] == 'sad_intern'
        assert metadata['status'] == sad_intern.status
        assert 'days_waiting' in metadata

    def test_extract_metadata_manager(self, manager):
        """Проверка извлечения метаданных из менеджера."""
        metadata = extract_metadata(manager, 'manager')

        assert metadata['entity_type'] == 'manager'

    def test_extract_metadata_company(self, company):
        """Проверка извлечения метаданных из компании."""
        metadata = extract_metadata(company, 'company')

        assert metadata['entity_type'] == 'company'
        assert metadata['company_name'] == company.name
        assert metadata['is_bigtech'] == company.is_bigtech

    def test_extract_metadata_interview_with_company(self, interview_with_company):
        """Проверка что company_name добавлен в metadata."""
        metadata = extract_metadata(interview_with_company, 'interview')

        assert metadata['company_id'] == interview_with_company.company_id
        assert metadata['company_name'] == interview_with_company.company.name

    def test_extract_metadata_missing_fields(self, interview):
        """Проверка что отсутствующие поля не вызывают ошибок."""
        # Убираем опциональное поле
        interview.company_id = None
        interview.save()

        metadata = extract_metadata(interview, 'interview')

        # Не должно быть company_id в metadata
        assert 'company_id' not in metadata


@pytest.mark.django_db(databases=['default'])
@pytest.mark.utils
class TestUniversalTextExtractor:
    """Тесты для универсальной функции извлечения текста."""

    def test_extract_text_from_interview(self, interview):
        """Проверка извлечения текста из интервью через универсальную функцию."""
        text = extract_text_from_entity('interview', interview)

        assert 'Тип:' in text
        assert interview.intern.full_name in text

    def test_extract_text_from_intern(self, intern):
        """Проверка извлечения текста из студента через универсальную функцию."""
        text = extract_text_from_entity('intern', intern)

        assert intern.full_name in text
        assert intern.email in text

    def test_extract_text_from_manager(self, manager):
        """Проверка извлечения текста из менеджера через универсальную функцию."""
        text = extract_text_from_entity('manager', manager)

        assert manager.full_name in text
        assert manager.email in text

    def test_extract_text_from_company(self, company):
        """Проверка извлечения текста из компании через универсальную функцию."""
        text = extract_text_from_entity('company', company)

        assert company.name in text

    def test_extract_text_from_direction(self, direction):
        """Проверка извлечения текста из направления через универсальную функцию."""
        text = extract_text_from_entity('direction', direction)

        assert direction.name in text
        assert 'Направление' in text

    def test_extract_text_from_intern_weekly_status(self, intern_weekly_status):
        """Проверка извлечения текста из недельного статуса студента."""
        text = extract_text_from_entity('intern_weekly_status', intern_weekly_status)

        assert intern_weekly_status.intern.full_name in text
        assert 'Неделя' in text
        assert 'Отсутствие' in text
        assert intern_weekly_status.absence_notes in text
        assert '2' in text  # manual_interview_count

    def test_extract_text_from_unknown_type(self, interview):
        """Проверка обработки неизвестного типа сущности."""
        text = extract_text_from_entity('unknown_type', interview)

        # Должен вернуть str(obj)
        assert text == str(interview)
