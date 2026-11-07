import pytest
from unittest.mock import patch

from django.core.cache import cache

from transcriptions.models import InterviewTranscription, TranscriptionStatus
from transcriptions.tasks import (
    _BALANCE_EXHAUSTED_CACHE_KEY,
    _is_balance_exhausted,
    _should_fail_without_retry,
    _start_processing_heartbeat,
    _touch_processing_updated_at,
    _trigger_vector_embedding,
    transcribe_interview,
)


@pytest.mark.django_db
@pytest.mark.services
class TestTranscribeInterviewTask:
    """Тесты Celery-задачи transcribe_interview."""

    def test_task_not_found_transcript(self):
        """Задача не падает если транскрипция не найдена."""
        transcribe_interview(99999)

    def test_task_no_video_link(self, transcription):
        """Задача пропускается, если нет URL для транскрипции (video_link / Яндекс в link)."""
        transcribe_interview(transcription.pk)
        transcription.refresh_from_db()
        assert transcription.status == TranscriptionStatus.PENDING

    def test_task_success(self, interview, settings):
        """Задача успешно транскрибирует и сохраняет текст."""
        settings.DEEPGRAM_API_KEY = 'test-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(video_link='https://disk.yandex.ru/i/test-video')
        interview.refresh_from_db()

        obj = InterviewTranscription.objects.create(interview=interview)

        with patch('transcriptions.services.TranscriptionService.transcribe_from_url', return_value='Текст транскрипции'):
            with patch('transcriptions.tasks._trigger_vector_embedding'):
                transcribe_interview(obj.pk)

        obj.refresh_from_db()
        assert obj.status == TranscriptionStatus.COMPLETED
        assert obj.text == 'Текст транскрипции'
        assert obj.error_message is None

    def test_task_success_from_yandex_link_in_link_field(self, interview_yandex_link_only, settings):
        """Транскрипция по ссылке Яндекс.Диска в поле link (без video_link)."""
        settings.DEEPGRAM_API_KEY = 'test-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        interview = interview_yandex_link_only
        obj = InterviewTranscription.objects.create(interview=interview)

        with patch('transcriptions.services.TranscriptionService.transcribe_from_url', return_value='Текст из link') as mock_tr:
            with patch('transcriptions.tasks._trigger_vector_embedding'):
                transcribe_interview(obj.pk)

        mock_tr.assert_called_once_with('https://disk.yandex.ru/i/from-link-field')
        obj.refresh_from_db()
        assert obj.status == TranscriptionStatus.COMPLETED
        assert obj.text == 'Текст из link'

    def test_task_sets_processing_status(self, interview, settings):
        """Задача устанавливает статус processing во время работы."""
        settings.DEEPGRAM_API_KEY = 'test-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(video_link='https://disk.yandex.ru/i/test-video')
        interview.refresh_from_db()

        obj = InterviewTranscription.objects.create(interview=interview)

        status_during_call = []

        def mock_transcribe(url):
            status_during_call.append(
                InterviewTranscription.objects.get(pk=obj.pk).status
            )
            return 'Текст'

        with patch('transcriptions.services.TranscriptionService.transcribe_from_url', side_effect=mock_transcribe):
            with patch('transcriptions.tasks._trigger_vector_embedding'):
                transcribe_interview(obj.pk)

        assert status_during_call[0] == TranscriptionStatus.PROCESSING

    def test_task_marks_failed_after_max_retries(self, interview, settings):
        """После исчерпания попыток задача сохраняет статус failed."""
        settings.DEEPGRAM_API_KEY = 'test-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(video_link='https://disk.yandex.ru/i/test-video')
        interview.refresh_from_db()

        obj = InterviewTranscription.objects.create(interview=interview)

        class FakeMaxRetriesExceeded(Exception):
            pass

        def fake_retry(exc, countdown):
            raise FakeMaxRetriesExceeded()

        with patch('transcriptions.services.TranscriptionService.transcribe_from_url', side_effect=RuntimeError('Сеть недоступна')):
            with patch.object(transcribe_interview, 'MaxRetriesExceededError', FakeMaxRetriesExceeded):
                with patch.object(transcribe_interview, 'retry', side_effect=fake_retry):
                    transcribe_interview(obj.pk)

        obj.refresh_from_db()
        assert obj.status == TranscriptionStatus.FAILED
        assert 'Сеть недоступна' in obj.error_message

    def test_task_fails_immediately_on_captcha_no_retry(self, interview, settings):
        """Капча / битая ссылка — сразу failed, без retry Celery."""
        settings.DEEPGRAM_API_KEY = 'test-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(video_link='https://disk.yandex.ru/i/bad')
        interview.refresh_from_db()

        obj = InterviewTranscription.objects.create(interview=interview)
        err = RuntimeError(
            'Не удалось получить прямую ссылку на файл: Яндекс.Диск вернул страницу с капчей '
            'или ресурс недоступен (проверьте публичную ссылку и токен YA_TOKEN).'
        )

        with patch('transcriptions.services.TranscriptionService.transcribe_from_url', side_effect=err):
            with patch.object(transcribe_interview, 'retry') as mock_retry:
                transcribe_interview(obj.pk)

        mock_retry.assert_not_called()
        obj.refresh_from_db()
        assert obj.status == TranscriptionStatus.FAILED
        assert 'капч' in (obj.error_message or '').lower()


@pytest.mark.django_db
@pytest.mark.signals
class TestTranscriptionSignal:
    """Тесты сигнала post_save для Interview."""

    def test_signal_not_fired_without_transcription_url(self, interview):
        """Сигнал не создаёт транскрипцию если нет URL для транскрипции."""
        interview.date = None
        interview.save(update_fields=['date'])
        assert not InterviewTranscription.objects.filter(interview=interview).exists()

    @pytest.mark.django_db(transaction=True)
    def test_signal_creates_transcription_on_video_link(self, interview):
        """Сигнал создаёт транскрипцию когда video_link появляется (on_commit выполняется при коммите)."""
        with patch('transcriptions.tasks.transcribe_interview.delay') as mock_delay:
            interview.video_link = 'https://disk.yandex.ru/i/test'
            interview.save(update_fields=['video_link'])

        obj = InterviewTranscription.objects.filter(interview=interview).first()
        assert obj is not None
        assert obj.status == TranscriptionStatus.PENDING
        mock_delay.assert_called_once_with(obj.pk)

    @pytest.mark.django_db(transaction=True)
    def test_signal_creates_transcription_on_yandex_link_in_link(self, interview):
        """Сигнал ставит транскрипцию в очередь при появлении Яндекс-ссылки в поле link."""
        with patch('transcriptions.tasks.transcribe_interview.delay') as mock_delay:
            interview.link = 'https://disk.yandex.ru/i/new-from-bot'
            interview.save(update_fields=['link'])

        obj = InterviewTranscription.objects.filter(interview=interview).first()
        assert obj is not None
        assert obj.status == TranscriptionStatus.PENDING
        mock_delay.assert_called_once_with(obj.pk)

    def test_signal_skips_completed_transcription(self, completed_transcription, interview):
        """Сигнал не перезапускает задачу если транскрипция уже завершена."""
        with patch('transcriptions.tasks.transcribe_interview.delay') as mock_delay:
            interview.video_link = 'https://disk.yandex.ru/i/another'
            interview.save(update_fields=['video_link'])

        mock_delay.assert_not_called()

    def test_signal_skips_when_video_link_not_changed(self, interview):
        """Сигнал игнорирует сохранение, не затрагивающее video_link."""
        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(video_link='https://disk.yandex.ru/i/test')
        interview.refresh_from_db()
        InterviewTranscription.objects.filter(interview=interview).delete()

        with patch('transcriptions.tasks.transcribe_interview.delay') as mock_delay:
            interview.hr_name = 'Новый HR'
            interview.save(update_fields=['hr_name'])

        mock_delay.assert_not_called()

    def test_signal_skips_when_link_not_changed(self, interview):
        """Сигнал игнорирует сохранение, не затрагивающее link / interview_link / video_link."""
        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(
            link='https://disk.yandex.ru/i/test',
        )
        interview.refresh_from_db()
        InterviewTranscription.objects.filter(interview=interview).delete()

        with patch('transcriptions.tasks.transcribe_interview.delay') as mock_delay:
            interview.hr_name = 'Другой HR'
            interview.save(update_fields=['hr_name'])

        mock_delay.assert_not_called()

    def test_signal_not_fired_for_zoom_link_only(self, interview):
        """Обновление link на созвон Zoom не создаёт транскрипцию."""
        with patch('transcriptions.tasks.transcribe_interview.delay') as mock_delay:
            interview.link = 'https://zoom.us/j/123456789'
            interview.save(update_fields=['link'])

        mock_delay.assert_not_called()
        assert not InterviewTranscription.objects.filter(interview=interview).exists()


@pytest.mark.django_db
class TestTranscriptionTaskHelpers:
    """Unit-тесты вспомогательных функций transcribe_interview."""

    def test_should_fail_without_retry_terminal_markers(self):
        assert _should_fail_without_retry(RuntimeError('unsupported media type')) is True
        assert _should_fail_without_retry(RuntimeError('HTTP 415')) is True
        assert _should_fail_without_retry(RuntimeError('temporary network')) is False

    def test_is_balance_exhausted_markers(self):
        assert _is_balance_exhausted(RuntimeError('402 payment required')) is True
        assert _is_balance_exhausted(RuntimeError('asr_payment_required')) is True
        assert _is_balance_exhausted(RuntimeError('timeout')) is False

    def test_touch_processing_updated_at_updates_row(self, interview, settings):
        settings.DEEPGRAM_API_KEY = 'k'
        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(video_link='https://disk.yandex.ru/i/v')
        obj = InterviewTranscription.objects.create(
            interview=interview,
            status=TranscriptionStatus.PROCESSING,
        )
        old_updated = obj.updated_at
        _touch_processing_updated_at(obj.pk)
        obj.refresh_from_db()
        assert obj.updated_at >= old_updated

    def test_start_processing_heartbeat_stops_on_event(self, interview, settings):
        settings.DEEPGRAM_API_KEY = 'k'
        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(video_link='https://disk.yandex.ru/i/v')
        obj = InterviewTranscription.objects.create(
            interview=interview,
            status=TranscriptionStatus.PROCESSING,
        )
        stop, thread = _start_processing_heartbeat(obj.pk)
        stop.set()
        thread.join(timeout=2)
        assert not thread.is_alive()

    def test_trigger_vector_embedding_success(self):
        with patch('vector_search.tasks.update_embedding_task.delay') as mock_delay:
            _trigger_vector_embedding(42)
        mock_delay.assert_called_once_with('interview_transcription', 42)

    def test_trigger_vector_embedding_logs_warning_on_failure(self):
        with patch('vector_search.tasks.update_embedding_task.delay', side_effect=ImportError('no celery')):
            _trigger_vector_embedding(42)


@pytest.mark.django_db
@pytest.mark.services
class TestTranscribeInterviewBalanceExhausted:
    """Баланс Deepgram исчерпан — cache и ранний выход."""

    def test_skips_when_balance_flag_in_cache(self, interview, settings):
        settings.DEEPGRAM_API_KEY = 'test-key'
        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(video_link='https://disk.yandex.ru/i/v')
        obj = InterviewTranscription.objects.create(interview=interview)
        cache.set(_BALANCE_EXHAUSTED_CACHE_KEY, True, timeout=60)
        try:
            transcribe_interview(obj.pk)
        finally:
            cache.delete(_BALANCE_EXHAUSTED_CACHE_KEY)
        obj.refresh_from_db()
        assert obj.status == TranscriptionStatus.FAILED
        assert 'Deepgram' in (obj.error_message or '')

    def test_balance_exhausted_on_transcribe_sets_cache(self, interview, settings):
        settings.DEEPGRAM_API_KEY = 'test-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'
        from interviews.models import Interview
        Interview.objects.filter(pk=interview.pk).update(video_link='https://disk.yandex.ru/i/v')
        obj = InterviewTranscription.objects.create(interview=interview)
        cache.delete(_BALANCE_EXHAUSTED_CACHE_KEY)
        with patch(
            'transcriptions.services.TranscriptionService.transcribe_from_url',
            side_effect=RuntimeError('402 payment required'),
        ):
            with patch.object(transcribe_interview, 'retry') as mock_retry:
                transcribe_interview(obj.pk)
        mock_retry.assert_not_called()
        obj.refresh_from_db()
        assert obj.status == TranscriptionStatus.FAILED
        assert cache.get(_BALANCE_EXHAUSTED_CACHE_KEY) is True
        cache.delete(_BALANCE_EXHAUSTED_CACHE_KEY)
