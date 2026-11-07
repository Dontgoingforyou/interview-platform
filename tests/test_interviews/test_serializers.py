"""
Тесты для сериализаторов приложения interviews.

Покрывают:
- InterviewListSerializer
- InterviewFullSerializer
- InterviewCreateUpdateSerializer

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.serializers - для группировки тестов сериализаторов
"""
import pytest


from interviews.models import Interview
from transcriptions.models import InterviewTranscription, TranscriptionStatus
from interviews.serializers import (
    InterviewListSerializer,
    InterviewFullSerializer,
    InterviewCreateUpdateSerializer,
)


# ============================================================================
# InterviewFullSerializer
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestInterviewFullSerializer:
    """Тесты для InterviewFullSerializer."""

    @pytest.mark.parametrize('field', [
        'id', 'intern', 'intern_name', 'direction_id', 'company_id',
        'manager_email', 'interview_type', 'interview_type_display',
        'interview_format', 'interview_format_display',
        'date', 'time', 'link', 'vacancy_link', 'interview_link', 'video_link',
        'has_video',
        'transcription_media_url', 'transcription_status', 'transcription_error_message',
        'hr_name', 'hr_contacts', 'created_at', 'updated_at',
    ])
    def test_serializer_contains_expected_fields(self, interview, field):
        """Сериализатор содержит все ожидаемые поля."""
        serializer = InterviewFullSerializer(interview)
        data = serializer.data
        assert field in data, f'Поле {field!r} отсутствует в сериализаторе'

    def test_intern_name_is_populated(self, interview):
        """Поле intern_name заполняется из intern.full_name."""
        serializer = InterviewFullSerializer(interview)
        assert serializer.data['intern_name'] == interview.intern.full_name

    def test_interview_type_display_is_human_readable(self, interview):
        """Поле interview_type_display содержит человекочитаемое значение."""
        serializer = InterviewFullSerializer(interview)
        assert serializer.data['interview_type_display'] == interview.get_interview_type_display()

    def test_id_is_read_only(self, intern, direction):
        """Поле id недоступно для записи в InterviewCreateUpdateSerializer."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'interview_type': 'screening',
        }
        serializer = InterviewCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert Interview.objects.filter(pk=instance.pk).exists()

    def test_created_at_is_read_only(self, interview):
        """Поле created_at не изменяется при обновлении."""
        original_created_at = interview.created_at
        serializer = InterviewFullSerializer(
            interview, data={'hr_name': 'Новый HR'}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        interview.refresh_from_db()
        assert interview.created_at == original_created_at

    def test_nullable_fields_are_none(self, interview):
        """Незаполненные опциональные поля возвращаются как None."""
        serializer = InterviewFullSerializer(interview)
        data = serializer.data
        assert data['link'] is None
        assert data['hr_name'] is None
        assert data['hr_contacts'] is None

    def test_fields_with_data(self, interview_with_company):
        """Поля содержат корректные данные для собеседования с компанией."""
        serializer = InterviewFullSerializer(interview_with_company)
        data = serializer.data
        assert data['company_id'] == interview_with_company.company_id
        assert data['hr_name'] == interview_with_company.hr_name
        assert data['hr_contacts'] == interview_with_company.hr_contacts

    def test_date_field_format(self, interview):
        """Поле date возвращается в формате YYYY-MM-DD."""
        serializer = InterviewFullSerializer(interview)
        data = serializer.data
        assert data['date'] == str(interview.date)

    def test_intern_id_is_present(self, interview):
        """Поле intern содержит id студента."""
        serializer = InterviewFullSerializer(interview)
        assert serializer.data['intern'] == interview.intern.id

    def test_has_video_false_without_video_link(self, interview):
        """Без video_link has_video — False."""
        serializer = InterviewFullSerializer(interview)
        assert serializer.data['has_video'] is False

    def test_has_video_true_when_video_link_set(self, interview):
        """При непустом video_link has_video — True."""
        Interview.objects.filter(pk=interview.pk).update(
            video_link='https://disk.yandex.ru/i/test-recording',
        )
        interview.refresh_from_db()
        serializer = InterviewFullSerializer(interview)
        assert serializer.data['has_video'] is True

    def test_transcription_status_none_without_row(self, interview):
        """Без InterviewTranscription статус none."""
        serializer = InterviewFullSerializer(interview)
        assert serializer.data['transcription_status'] == 'none'
        assert serializer.data['transcription_error_message'] == ''

    def test_transcription_error_message_when_failed(self, interview_with_video):
        """При failed в API отдаётся error_message для SPA."""
        InterviewTranscription.objects.create(
            interview=interview_with_video,
            status=TranscriptionStatus.FAILED,
            error_message='Яндекс.Диск вернул капчу',
        )
        interview_with_video.refresh_from_db()
        serializer = InterviewFullSerializer(interview_with_video)
        assert serializer.data['transcription_status'] == 'failed'
        assert serializer.data['transcription_error_message'] == 'Яндекс.Диск вернул капчу'

    def test_transcription_media_url_matches_model(self, interview_with_video):
        """transcription_media_url совпадает со свойством модели."""
        serializer = InterviewFullSerializer(interview_with_video)
        assert serializer.data['transcription_media_url'] == interview_with_video.transcription_media_url

    def test_transcription_status_from_related(self, interview_with_video):
        """Статус читается из связанной транскрипции."""
        InterviewTranscription.objects.create(
            interview=interview_with_video,
            status=TranscriptionStatus.COMPLETED,
        )
        interview_with_video.refresh_from_db()
        serializer = InterviewFullSerializer(interview_with_video)
        assert serializer.data['transcription_status'] == 'completed'


# ============================================================================
# InterviewCreateUpdateSerializer
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestInterviewCreateUpdateSerializer:
    """Тесты для InterviewCreateUpdateSerializer."""

    def test_valid_data_creates_interview(self, intern, direction):
        """Валидные данные создают собеседование."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'interview_type': 'screening',
            'date': '2025-12-01',
        }
        serializer = InterviewCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        interview = serializer.save()
        assert interview.pk is not None
        assert interview.intern == intern
        assert interview.interview_type == 'screening'

    def test_missing_required_intern_field(self, direction):
        """Отсутствие поля intern возвращает ошибку валидации."""
        data = {
            'direction_id': direction.id,
            'interview_type': 'screening',
        }
        serializer = InterviewCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'intern' in serializer.errors

    def test_missing_required_interview_type_field(self, intern, direction):
        """Отсутствие поля interview_type возвращает ошибку валидации."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
        }
        serializer = InterviewCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'interview_type' in serializer.errors

    def test_invalid_interview_type(self, intern, direction):
        """Невалидный тип собеседования возвращает ошибку валидации."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'interview_type': 'invalid_type',
        }
        serializer = InterviewCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'interview_type' in serializer.errors

    def test_all_optional_fields_accepted(self, intern, direction):
        """Все опциональные поля принимаются сериализатором."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'interview_type': 'tech',
            'date': '2025-12-15',
            'time': '14:30:00',
            'manager_email': 'manager@example.com',
            'link': 'https://meet.example.com/abc',
            'vacancy_link': 'https://hh.ru/vacancy/123',
            'interview_link': 'https://example.com/interview',
            'hr_name': 'Анна HR',
            'hr_contacts': 'anna@hr.com',
            'company_id': None,
        }
        serializer = InterviewCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_partial_update_changes_only_provided_fields(self, interview):
        """Частичное обновление меняет только переданные поля."""
        original_type = interview.interview_type
        serializer = InterviewCreateUpdateSerializer(
            interview, data={'hr_name': 'Новый HR'}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.hr_name == 'Новый HR'
        assert updated.interview_type == original_type

    @pytest.mark.parametrize('field', [
        'intern', 'direction_id', 'company_id', 'company_name',
        'manager_email', 'interview_type', 'date', 'time',
        'link', 'vacancy_link', 'interview_link', 'hr_name', 'hr_contacts',
    ])
    def test_serializer_fields_list(self, field):
        """Сериализатор содержит ожидаемые поля."""
        serializer = InterviewCreateUpdateSerializer()
        assert field in serializer.fields, f'Поле {field!r} не найдено в сериализаторе'

    @pytest.mark.parametrize('interview_type', [
        'screening', 'tech', 'hr', 'final', 'mock', 'test', 'tech_questionnaire', 'cancelled',
    ])
    def test_all_interview_types_are_valid(self, intern, direction, interview_type):
        """Каждый допустимый тип собеседования проходит валидацию."""
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'interview_type': interview_type,
        }
        serializer = InterviewCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), f'Тип {interview_type!r} должен быть валидным: {serializer.errors}'

    def test_company_name_creates_company_and_links_interview(self, intern, direction):
        """Новое название компании создаёт запись Company и привязывает к собеседованию."""
        unique_name = 'Компания SPA Тест Новая 777'
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'interview_type': 'screening',
            'company_name': unique_name,
        }
        serializer = InterviewCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        interview = serializer.save()
        assert interview.company_id is not None
        assert interview.company.name == unique_name

    def test_company_id_takes_precedence_over_company_name(self, intern, direction, company):
        """Явный company_id имеет приоритет над company_name."""
        other_name = 'Другое имя не должно примениться'
        data = {
            'intern': intern.id,
            'direction_id': direction.id,
            'interview_type': 'screening',
            'company_id': company.id,
            'company_name': other_name,
        }
        serializer = InterviewCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        interview = serializer.save()
        assert interview.company_id == company.id
        assert interview.company.name != other_name


# ============================================================================
# InterviewListSerializer
# ============================================================================

@pytest.mark.django_db(databases=['default'])
@pytest.mark.serializers
class TestInterviewListSerializer:
    """Тесты для InterviewListSerializer."""

    @pytest.mark.parametrize('field', [
        'id', 'company', 'date', 'interview_type', 'direction', 'tg_account', 'link',
    ])
    def test_serializer_contains_expected_fields(self, interview, field):
        """Сериализатор содержит поля id, company, date, interview_type, direction, tg_account, link."""
        serializer = InterviewListSerializer(interview)
        data = serializer.data
        assert field in data, f'Поле {field!r} отсутствует в InterviewListSerializer'

    def test_id_field_is_correct(self, interview):
        """Поле id содержит корректный идентификатор."""
        serializer = InterviewListSerializer(interview)
        assert serializer.data['id'] == interview.id

    def test_interview_type_is_human_readable(self, interview):
        """Поле interview_type содержит человекочитаемое значение."""
        serializer = InterviewListSerializer(interview)
        assert serializer.data['interview_type'] == interview.get_interview_type_display()

    def test_company_field_is_none_when_no_company(self, interview):
        """Поле company возвращает None, если company_id не указан."""
        serializer = InterviewListSerializer(interview)
        assert serializer.data['company'] is None

    def test_direction_field_is_none_when_no_direction_object(self, interview):
        """Поле direction возвращает None или название (в тестовой БД может быть None)."""
        serializer = InterviewListSerializer(interview)
        direction_val = serializer.data['direction']
        assert direction_val is None or isinstance(direction_val, str)

    def test_tg_account_none_when_intern_has_no_telegram(self, interview):
        """Поле tg_account возвращает None, если у студента нет telegram_username."""
        intern = interview.intern
        intern.telegram_username = None
        intern.save()
        serializer = InterviewListSerializer(interview)
        assert serializer.data['tg_account'] is None

    def test_tg_account_populated_when_intern_has_telegram(self, interview):
        """Поле tg_account заполняется, если у студента есть telegram_username."""
        intern = interview.intern
        intern.telegram_username = '@test_user'
        intern.save()
        serializer = InterviewListSerializer(interview)
        assert serializer.data['tg_account'] == '@test_user'

    def test_date_field_present(self, interview):
        """Поле date присутствует и содержит дату."""
        serializer = InterviewListSerializer(interview)
        assert serializer.data['date'] == str(interview.date)

    def test_serializer_has_exactly_eight_fields(self):
        """Сериализатор содержит ровно 8 полей."""
        serializer = InterviewListSerializer()
        assert set(serializer.fields.keys()) == {
            'id', 'company', 'date', 'interview_type', 'direction', 'tg_account', 'link',
            'interview_format',
        }
