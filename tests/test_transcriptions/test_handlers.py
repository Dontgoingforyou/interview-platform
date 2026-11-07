"""Тесты логики transcribe_interview_payload и transcription_status_payload."""
from datetime import timedelta

import pytest
from django.utils import timezone

from transcriptions.constants import TRANSCRIPTION_PROCESSING_STALE_MINUTES
from transcriptions.interview_transcription_handlers import (
    transcribe_interview_payload,
    transcription_status_payload,
)
from transcriptions.models import InterviewTranscription, TranscriptionStatus


@pytest.fixture
def run_on_commit_immediately(mocker):
    """В тестах транзакция не коммитится — выполняем on_commit-колбэки сразу."""
    mocker.patch(
        'django.db.transaction.on_commit',
        side_effect=lambda func, using=None, robust=False: func(),
    )


@pytest.mark.django_db(databases=['default'])
def test_transcribe_pending_cooldown_skips_delay(interview_with_video, mocker, run_on_commit_immediately):
    """Повторный запуск при свежем pending не ставит вторую задачу в Celery."""
    mock_delay = mocker.patch('transcriptions.tasks.transcribe_interview.delay')
    InterviewTranscription.objects.create(
        interview=interview_with_video,
        status=TranscriptionStatus.PENDING,
    )
    payload, code = transcribe_interview_payload(interview_with_video.pk, log_user_label='admin')
    assert code == 200
    assert payload['status'] == 'pending'
    assert payload['message'] == 'Уже в очереди'
    mock_delay.assert_not_called()


@pytest.mark.django_db(databases=['default'])
def test_transcribe_stale_pending_schedules_delay(interview_with_video, mocker, run_on_commit_immediately):
    """Зависший pending старше cooldown снова ставит задачу."""
    mock_delay = mocker.patch('transcriptions.tasks.transcribe_interview.delay')
    tr = InterviewTranscription.objects.create(
        interview=interview_with_video,
        status=TranscriptionStatus.PENDING,
    )
    past = timezone.now() - timedelta(minutes=30)
    InterviewTranscription.objects.filter(pk=tr.pk).update(updated_at=past)
    payload, code = transcribe_interview_payload(interview_with_video.pk, log_user_label='admin')
    assert code == 200
    assert payload['message'] == 'Транскрипция поставлена в очередь'
    mock_delay.assert_called_once_with(tr.pk)


@pytest.mark.django_db(databases=['default'])
def test_transcribe_processing_returns_busy(interview_with_video, mocker, run_on_commit_immediately):
    mock_delay = mocker.patch('transcriptions.tasks.transcribe_interview.delay')
    InterviewTranscription.objects.create(
        interview=interview_with_video,
        status=TranscriptionStatus.PROCESSING,
    )
    payload, code = transcribe_interview_payload(interview_with_video.pk, log_user_label='admin')
    assert code == 200
    assert payload['message'] == 'Уже выполняется'
    mock_delay.assert_not_called()


@pytest.mark.django_db(databases=['default'])
def test_transcription_status_stale_processing_marks_failed(interview):
    tr = InterviewTranscription.objects.create(
        interview=interview,
        status=TranscriptionStatus.PROCESSING,
    )
    past = timezone.now() - timedelta(minutes=TRANSCRIPTION_PROCESSING_STALE_MINUTES + 5)
    InterviewTranscription.objects.filter(pk=tr.pk).update(updated_at=past)
    payload, code = transcription_status_payload(interview.pk)
    assert code == 200
    assert payload['status'] == 'failed'
    assert 'прервана' in (payload.get('error_message') or '')
    tr.refresh_from_db()
    assert tr.status == TranscriptionStatus.FAILED


@pytest.mark.django_db(databases=['default'])
def test_transcribe_on_commit_calls_delay(interview_with_video, mocker, run_on_commit_immediately):
    """delay вызывается после коммита транзакции."""
    mock_delay = mocker.patch('transcriptions.tasks.transcribe_interview.delay')
    failed = InterviewTranscription.objects.create(
        interview=interview_with_video,
        status=TranscriptionStatus.FAILED,
        error_message='old',
    )
    payload, code = transcribe_interview_payload(interview_with_video.pk, log_user_label='admin')
    assert code == 200
    assert payload['message'] == 'Транскрипция поставлена в очередь'
    mock_delay.assert_called_once_with(failed.pk)
