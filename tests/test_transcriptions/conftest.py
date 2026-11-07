import pytest

from transcriptions.models import InterviewTranscription, TranscriptionStatus


@pytest.fixture
def interview_with_video(db, interview):
    """Собеседование с video_link (через queryset.update, чтобы не срабатывал сигнал)."""
    from interviews.models import Interview
    Interview.objects.filter(pk=interview.pk).update(video_link='https://disk.yandex.ru/i/test-video-link')
    interview.refresh_from_db()
    return interview


@pytest.fixture
def interview_yandex_link_only(db, interview):
    """Собеседование без video_link, ссылка на файл только в link (Яндекс.Диск)."""
    from interviews.models import Interview
    Interview.objects.filter(pk=interview.pk).update(
        video_link=None,
        link='https://disk.yandex.ru/i/from-link-field',
    )
    interview.refresh_from_db()
    return interview


@pytest.fixture
def transcription(db, interview):
    """Базовая запись транскрипции со статусом pending."""
    return InterviewTranscription.objects.create(interview=interview)


@pytest.fixture
def completed_transcription(db, interview):
    """Завершённая транскрипция."""
    return InterviewTranscription.objects.create(
        interview=interview,
        status=TranscriptionStatus.COMPLETED,
        text='Привет, это тестовая транскрипция.',
    )


@pytest.fixture
def failed_transcription(db, interview):
    """Транскрипция с ошибкой."""
    return InterviewTranscription.objects.create(
        interview=interview,
        status=TranscriptionStatus.FAILED,
        error_message='Deepgram timeout',
    )
