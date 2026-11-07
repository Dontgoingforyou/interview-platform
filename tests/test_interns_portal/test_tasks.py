"""
Тесты для interns_portal/tasks.py — загрузка видео в S3.
"""
import pytest
from unittest.mock import patch
from celery.exceptions import MaxRetriesExceededError, Retry

from core.s3_video_storage import S3VideoStorageError
from interns_portal.tasks import upload_video_to_s3
from transcriptions.models import InterviewTranscription, TranscriptionStatus

_UPDATE_STATE_TARGET = 'celery.app.task.Task.update_state'
_STABLE_URL = 'https://s3.test.example/interview-videos/test.mp4'


def _noop_update_state(self, *args, **kwargs):
    pass


@pytest.mark.django_db(databases=['default'])
class TestUploadVideoToS3:
    """Тесты Celery-задачи upload_video_to_s3."""

    def _run_task(self, interview_id, file_path, filename):
        with patch(_UPDATE_STATE_TARGET, _noop_update_state):
            return upload_video_to_s3(interview_id, file_path, filename)

    def test_successful_upload_saves_stable_video_link(self, student_interview, tmp_path):
        tmp_file = tmp_path / 'video.mp4'
        tmp_file.write_bytes(b'fake_video_data')

        with patch('interns_portal.tasks.upload_file_to_s3', return_value=_STABLE_URL):
            self._run_task(student_interview.pk, str(tmp_file), 'video.mp4')

        student_interview.refresh_from_db()
        assert student_interview.video_link == _STABLE_URL
        assert student_interview.upload_task_id is None

    @pytest.mark.django_db(transaction=True)
    def test_successful_upload_queues_transcription_via_signal(self, student_interview, tmp_path):
        tmp_file = tmp_path / 'video.mp4'
        tmp_file.write_bytes(b'fake_video_data')

        with patch('interns_portal.tasks.upload_file_to_s3', return_value=_STABLE_URL):
            with patch('transcriptions.tasks.transcribe_interview.delay') as mock_delay:
                with patch(_UPDATE_STATE_TARGET, _noop_update_state):
                    upload_video_to_s3(student_interview.pk, str(tmp_file), 'video.mp4')

        tr = InterviewTranscription.objects.filter(interview=student_interview).first()
        assert tr is not None
        assert tr.status == TranscriptionStatus.PENDING
        mock_delay.assert_called_once_with(tr.pk)

    def test_temp_file_deleted_after_upload(self, student_interview, tmp_path):
        tmp_file = tmp_path / 'video.mp4'
        tmp_file.write_bytes(b'fake_video_data')

        with patch('interns_portal.tasks.upload_file_to_s3', return_value=_STABLE_URL):
            self._run_task(student_interview.pk, str(tmp_file), 'video.mp4')

        assert not tmp_file.exists()

    def test_temp_file_deleted_on_max_retries_exceeded(self, student_interview, tmp_path):
        tmp_file = tmp_path / 'video.mp4'
        tmp_file.write_bytes(b'fake_video_data')

        with patch(
            'interns_portal.tasks.upload_file_to_s3',
            side_effect=Exception('Ошибка сети'),
        ), patch(_UPDATE_STATE_TARGET, _noop_update_state), patch.object(
            upload_video_to_s3, 'retry', side_effect=MaxRetriesExceededError()
        ):
            with pytest.raises(S3VideoStorageError):
                upload_video_to_s3(student_interview.pk, str(tmp_file), 'test.mp4')

        assert not tmp_file.exists()

    def test_temp_file_kept_on_retry(self, student_interview, tmp_path):
        tmp_file = tmp_path / 'video.mp4'
        tmp_file.write_bytes(b'fake_video_data')

        with patch(
            'interns_portal.tasks.upload_file_to_s3',
            side_effect=Exception('Ошибка сети'),
        ), patch(_UPDATE_STATE_TARGET, _noop_update_state), patch.object(
            upload_video_to_s3, 'retry', side_effect=Retry()
        ):
            with pytest.raises(Retry):
                upload_video_to_s3(student_interview.pk, str(tmp_file), 'test.mp4')

        assert tmp_file.exists()

    def test_upload_task_id_kept_on_max_retries_exceeded(self, student_interview, tmp_path):
        student_interview.upload_task_id = 'some-task-id'
        student_interview.save(update_fields=['upload_task_id'])

        tmp_file = tmp_path / 'video.mp4'
        tmp_file.write_bytes(b'data')

        with patch(
            'interns_portal.tasks.upload_file_to_s3',
            side_effect=Exception('API error'),
        ), patch(_UPDATE_STATE_TARGET, _noop_update_state), patch.object(
            upload_video_to_s3, 'retry', side_effect=MaxRetriesExceededError()
        ):
            with pytest.raises(S3VideoStorageError):
                upload_video_to_s3(student_interview.pk, str(tmp_file), 'test.mp4')

        student_interview.refresh_from_db()
        assert student_interview.upload_task_id == 'some-task-id'

    def test_upload_passes_object_key_from_filename(self, student_interview, tmp_path):
        tmp_file = tmp_path / 'video.mp4'
        tmp_file.write_bytes(b'data')
        filename = 'Студент_Тест.mp4'

        with patch('interns_portal.tasks.upload_file_to_s3', return_value=_STABLE_URL) as mock_upload:
            self._run_task(student_interview.pk, str(tmp_file), filename)

        mock_upload.assert_called_once()
        object_key = mock_upload.call_args[0][1]
        assert object_key == filename

    @patch('interns_portal.tasks.portal_upload_log')
    def test_missing_tmp_file_logs_file_not_found(self, mock_log, student_interview):
        missing = '/tmp/nonexistent_portal_video_test.mp4'

        with patch(_UPDATE_STATE_TARGET, _noop_update_state):
            with pytest.raises(FileNotFoundError):
                upload_video_to_s3(student_interview.pk, missing, 'video.mp4')

        mock_log.assert_any_call(
            'error',
            'worker_start',
            student_interview.pk,
            reason='file_not_found',
            tmp_basename='nonexistent_portal_video_test.mp4',
        )
