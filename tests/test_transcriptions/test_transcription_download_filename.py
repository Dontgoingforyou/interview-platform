"""Тесты формирования имени файла для скачивания транскрипции."""

import pytest

from interviews.models import Interview
from transcriptions.transcription_download_filename import build_interview_transcription_download_filename


@pytest.mark.django_db
@pytest.mark.utils
def test_filename_default_interview(interview):
    """ФИО, тип и дата из фикстуры; компании нет."""
    name = build_interview_transcription_download_filename(interview)
    assert name == 'Иван Иванов_Скрининг_01.12.2025.txt'


@pytest.mark.django_db
@pytest.mark.utils
def test_filename_with_company(interview_with_company, company):
    """Сегмент компании из FK."""
    name = build_interview_transcription_download_filename(interview_with_company)
    assert name == f'Иван Иванов_HR собеседование_{company.name}_03.12.2025.txt'


@pytest.mark.django_db
@pytest.mark.utils
def test_filename_sanitizes_invalid_chars(db, intern, direction):
    """Спецсимволы в ФИО и компании заменяются."""
    intern.full_name = 'Петров:Петр*Петрович'
    intern.save()
    from companies.models import Company

    co = Company.objects.create(name='ООО "Рога/Копыта"')
    iv = Interview.objects.create(
        intern=intern,
        direction=direction,
        company=co,
        manager_email='manager@example.com',
        interview_type='tech',
        date=None,
    )
    name = build_interview_transcription_download_filename(iv)
    assert ':' not in name
    assert '*' not in name
    assert '"' not in name
    assert '/' not in name
    assert name.endswith('.txt')


@pytest.mark.django_db
@pytest.mark.utils
def test_filename_truncates_long_stem(db, intern, direction):
    """Очень длинное ФИО обрезается до лимита."""
    intern.full_name = 'А' * 300
    intern.save()
    iv = Interview.objects.create(
        intern=intern,
        direction=direction,
        manager_email='m@example.com',
        interview_type='screening',
        date=None,
    )
    name = build_interview_transcription_download_filename(iv)
    assert name.endswith('.txt')
    assert len(name) <= 184  # 180 + .txt


@pytest.mark.utils
def test_filename_fallback_when_no_metadata_segments():
    """Если нет ни одного непустого сегмента — используется pk."""

    class StubInterview:
        pk = 42
        intern = None
        company = None
        date = None

        def get_interview_type_display(self):
            return ''

    name = build_interview_transcription_download_filename(StubInterview())
    assert name == 'Транскрипция_42.txt'
