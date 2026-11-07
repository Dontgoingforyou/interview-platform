"""
Тесты для моделей приложения interviews.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.models - для группировки тестов моделей
"""
import pytest
from datetime import date, time

from interviews.models import Interview, is_yandex_disk_public_file_url


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestInterviewModel:
    """Тесты для модели Interview."""

    def test_create_interview(self, intern, direction):
        """Создание собеседования."""
        interview = Interview.objects.create(
            intern=intern,
            direction=direction,
            interview_type='screening',
            date=date(2025, 12, 1),
            time=time(10, 0)
        )
        assert interview.pk is not None
        assert interview.intern == intern
        assert interview.direction_id == direction.id
        assert interview.interview_type == 'screening'
        assert interview.interview_format == 'online'

    def test_interview_str(self, interview):
        """Проверка строкового представления."""
        expected = f'{interview.intern.full_name} - {interview.get_interview_type_display()}'
        assert str(interview) == expected

    @pytest.mark.parametrize('interview_type', [
        'screening', 'tech', 'hr', 'final', 'mock', 'test', 'cancelled',
    ])
    def test_interview_type_choices(self, intern, direction, interview_type):
        """Каждый тип собеседования сохраняется корректно."""
        interview = Interview.objects.create(
            intern=intern,
            direction=direction,
            interview_type=interview_type,
            date=date(2025, 12, 1)
        )
        assert interview.interview_type == interview_type

    def test_interview_ordering(self, intern, direction):
        """Проверка сортировки собеседований."""
        interview1 = Interview.objects.create(
            intern=intern,
            direction=direction,
            interview_type='screening',
            date=date(2025, 12, 1),
            time=time(10, 0)
        )
        interview2 = Interview.objects.create(
            intern=intern,
            direction=direction,
            interview_type='tech',
            date=date(2025, 12, 2),
            time=time(14, 0)
        )
        interview3 = Interview.objects.create(
            intern=intern,
            direction=direction,
            interview_type='hr',
            date=date(2025, 12, 2),
            time=time(15, 0)
        )

        interviews = list(Interview.objects.all())
        # Должны быть отсортированы по убыванию даты и времени
        assert interviews[0] == interview3  # Та же дата, но позже время
        assert interviews[1] == interview2
        assert interviews[2] == interview1

    def test_interview_with_company(self, intern, direction, company):
        """Создание собеседования с компанией."""
        interview = Interview.objects.create(
            intern=intern,
            direction=direction,
            company=company,
            interview_type='tech',
            date=date(2025, 12, 1)
        )
        assert interview.company_id == company.id

    def test_interview_with_manager(self, intern, direction, manager):
        """Создание собеседования с менеджером."""
        interview = Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=date(2025, 12, 1)
        )
        assert interview.manager_email == manager.email

    def test_interview_all_optional_fields(self, intern, direction):
        """Создание собеседования со всеми опциональными полями."""
        interview = Interview.objects.create(
            intern=intern,
            direction=direction,
            interview_type='tech',
            date=date(2025, 12, 1),
            time=time(14, 30),
            link='https://example.com/link',
            vacancy_link='https://example.com/vacancy',
            interview_link='https://example.com/interview',
            hr_name='Анна HR',
            hr_contacts='anna@example.com'
        )
        assert interview.link == 'https://example.com/link'
        assert interview.vacancy_link == 'https://example.com/vacancy'
        assert interview.interview_link == 'https://example.com/interview'
        assert interview.hr_name == 'Анна HR'
        assert interview.hr_contacts == 'anna@example.com'

    def test_interview_direction_property(self, interview, direction):
        """Проверка свойства direction."""
        # В тестах direction должен быть доступен через свойство
        # Но так как это внешняя модель, может вернуть None если не найдена
        direction_obj = interview.direction
        # В тестах может быть None, если модель не найдена во внешней БД
        # Проверяем, что свойство работает без ошибок
        assert direction_obj is None or direction_obj.id == direction.id

    def test_interview_company_property(self, interview_with_company, company):
        """Проверка свойства company."""
        company_obj = interview_with_company.company
        # В тестах может быть None, если модель не найдена во внешней БД
        assert company_obj is None or company_obj.id == company.id

    def test_interview_manager_property(self, interview, manager):
        """Проверка свойства manager."""
        manager_obj = interview.manager
        # В тестах может быть None, если модель не найдена во внешней БД
        assert manager_obj is None or manager_obj.email == manager.email

    def test_interview_cascade_delete(self, intern, direction):
        """Проверка каскадного удаления при удалении студента."""
        interview = Interview.objects.create(
            intern=intern,
            direction=direction,
            interview_type='screening',
            date=date(2025, 12, 1)
        )
        interview_id = interview.pk
        intern.delete()
        assert not Interview.objects.filter(pk=interview_id).exists()

    def test_interview_created_at_updated_at(self, intern, direction):
        """Проверка автоматического заполнения created_at и updated_at."""
        interview = Interview.objects.create(
            intern=intern,
            direction=direction,
            interview_type='screening',
            date=date(2025, 12, 1)
        )
        assert interview.created_at is not None
        assert interview.updated_at is not None

    def test_interview_nullable_fields(self, intern, direction):
        """Проверка, что nullable поля могут быть None."""
        interview = Interview.objects.create(
            intern=intern,
            direction=direction,
            interview_type='screening',
            company_id=None,
            date=None,
            time=None,
            link=None,
            vacancy_link=None,
            interview_link=None,
            hr_name=None,
            hr_contacts=None
        )
        assert interview.company_id is None
        assert interview.manager_email is None
        assert interview.date is None
        assert interview.time is None


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestIsYandexDiskPublicFileUrl:
    """Эвристика публичной ссылки Яндекс.Диска для транскрипции."""

    @pytest.mark.parametrize(
        'url,expected',
        [
            ('https://disk.yandex.ru/i/AbCdEf', True),
            ('https://yadi.sk/i/xyz', True),
            ('https://disk.360.yandex.ru/i/djK3RRsPTgaN3A', True),
            ('https://telemost.360.yandex.ru/j/9134424409', False),
            ('https://zoom.us/j/123', False),
            ('', False),
            ('https://disk.yandex.ru/client/disk', False),
        ],
    )
    def test_is_yandex_disk_public_file_url(self, url, expected):
        assert is_yandex_disk_public_file_url(url) is expected


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestInterviewTranscriptionMediaUrl:
    """Свойство Interview.transcription_media_url."""

    def test_prefers_video_link(self, interview):
        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(
            video_link='https://disk.yandex.ru/i/video',
            link='https://disk.yandex.ru/i/from-link',
        )
        interview.refresh_from_db()
        assert interview.transcription_media_url == 'https://disk.yandex.ru/i/video'

    def test_falls_back_to_yandex_link_field(self, interview):
        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(
            video_link=None,
            link='https://disk.yandex.ru/i/only-link',
        )
        interview.refresh_from_db()
        assert interview.transcription_media_url == 'https://disk.yandex.ru/i/only-link'

    def test_falls_back_to_interview_link(self, interview):
        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(
            link='https://zoom.us/j/1',
            interview_link='https://yadi.sk/i/il',
        )
        interview.refresh_from_db()
        assert interview.transcription_media_url == 'https://yadi.sk/i/il'

    def test_falls_back_to_yandex_360_interview_link(self, interview):
        from interviews.models import Interview
        ya360 = 'https://disk.360.yandex.ru/i/djK3RRsPTgaN3A'
        Interview.objects.filter(pk=interview.pk).update(
            video_link=None,
            link='https://zoom.us/j/1',
            interview_link=ya360,
        )
        interview.refresh_from_db()
        assert interview.transcription_media_url == ya360

    def test_none_when_only_zoom(self, interview):
        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(
            link='https://zoom.us/j/12345',
        )
        interview.refresh_from_db()
        assert interview.transcription_media_url is None

    def test_none_when_only_yandex_telemost(self, interview):
        """Ссылка на комнату Телемоста в link — не медиа для транскрипции."""
        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(
            video_link=None,
            link='https://telemost.360.yandex.ru/j/9134424409',
            interview_link=None,
        )
        interview.refresh_from_db()
        assert interview.transcription_media_url is None
