import pytest

from transcriptions.models import InterviewTranscription, TranscriptionStatus


@pytest.mark.django_db
@pytest.mark.models
class TestInterviewTranscriptionModel:
    """Тесты модели InterviewTranscription."""

    def test_create_transcription(self, interview):
        obj = InterviewTranscription.objects.create(interview=interview)
        assert obj.pk is not None
        assert obj.status == TranscriptionStatus.PENDING
        assert obj.text is None
        assert obj.error_message is None

    def test_str_representation(self, interview):
        obj = InterviewTranscription.objects.create(
            interview=interview,
            status=TranscriptionStatus.COMPLETED,
        )
        assert f'#{interview.pk}' in str(obj)
        assert 'Завершена' in str(obj)

    def test_one_to_one_constraint(self, interview):
        InterviewTranscription.objects.create(interview=interview)
        with pytest.raises(Exception):
            InterviewTranscription.objects.create(interview=interview)

    def test_cascade_delete(self, interview):
        obj = InterviewTranscription.objects.create(interview=interview)
        pk = obj.pk
        interview.delete()
        assert not InterviewTranscription.objects.filter(pk=pk).exists()

    def test_status_choices(self, interview):
        for status_value, _ in TranscriptionStatus.choices:
            obj = InterviewTranscription(
                interview_id=interview.pk,
                status=status_value,
            )
            assert obj.status == status_value

    def test_db_table_name(self):
        assert InterviewTranscription._meta.db_table == 'interview_transcriptions'


@pytest.mark.django_db
@pytest.mark.models
class TestInterviewTranscriptionStatusProperty:
    """Тесты property transcription_status на модели Interview."""

    def test_no_transcription_returns_none(self, interview):
        assert interview.transcription_status is None

    def test_pending_status(self, interview):
        InterviewTranscription.objects.create(interview=interview, status=TranscriptionStatus.PENDING)
        interview.refresh_from_db()
        assert interview.transcription_status == TranscriptionStatus.PENDING

    def test_completed_status(self, completed_transcription, interview):
        assert interview.transcription_status == TranscriptionStatus.COMPLETED

    def test_failed_status(self, failed_transcription, interview):
        assert interview.transcription_status == TranscriptionStatus.FAILED
