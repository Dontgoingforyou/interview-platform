import pytest
from unittest.mock import patch, MagicMock

from transcriptions.services import TranscriptionService


def _make_deepgram_ok_response(utterances=None, transcript=None):
    """Хелпер: успешный ответ Deepgram с utterances или plain transcript."""
    mock = MagicMock()
    mock.status_code = 200
    if utterances is not None:
        mock.json.return_value = {'results': {'utterances': utterances}}
    else:
        mock.json.return_value = {
            'results': {
                'channels': [{'alternatives': [{'transcript': transcript or ''}]}]
            }
        }
    return mock


def _make_deepgram_408_response():
    """Хелпер: ответ Deepgram 408 SLOW_UPLOAD."""
    mock = MagicMock()
    mock.status_code = 408
    mock.text = '{"err_code":"SLOW_UPLOAD","err_msg":"Request upload timeout"}'
    return mock


def _make_download_response(content=b'fake-video-data', content_type='video/mp4'):
    """Хелпер: успешный ответ на скачивание файла (для _download_to_tempfile)."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {'Content-Type': content_type}
    mock.iter_content.return_value = [content]
    return mock


@pytest.mark.services
class TestTranscriptionService:
    """Тесты TranscriptionService."""

    def test_get_api_key_missing(self, settings):
        settings.DEEPGRAM_API_KEY = ''
        with pytest.raises(ValueError, match='DEEPGRAM_API_KEY'):
            TranscriptionService._get_api_key()

    def test_get_api_key_returns_value(self, settings):
        settings.DEEPGRAM_API_KEY = 'test-key-123'
        assert TranscriptionService._get_api_key() == 'test-key-123'

    def test_transcribe_from_url_success_fallback_no_utterances(self, settings):
        """Без utterances в ответе используется старый путь channels[0].alternatives[0].transcript."""
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        mock_response = _make_deepgram_ok_response(transcript='Привет, это тест транскрипции.')

        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value='https://direct.url/video.mp4'):
            with patch('transcriptions.services.requests.post', return_value=mock_response):
                text = TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/test')

        assert text == 'Привет, это тест транскрипции.'

    def test_transcribe_from_url_success_with_utterances_diarization(self, settings):
        """При наличии utterances текст собирается с подписями Спикер 1, Спикер 2 и т.д."""
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        utterances = [
            {'speaker': 0, 'transcript': 'Здравствуйте, расскажите о себе.'},
            {'speaker': 1, 'transcript': 'Добрый день. Я разработчик.'},
            {'speaker': 0, 'transcript': 'Отлично, какие у вас проекты?'},
        ]
        mock_response = _make_deepgram_ok_response(utterances=utterances)

        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value='https://direct.url/video.mp4'):
            with patch('transcriptions.services.requests.post', return_value=mock_response):
                text = TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/test')

        assert 'Спикер 1: Здравствуйте, расскажите о себе.' in text
        assert 'Спикер 2: Добрый день. Я разработчик.' in text
        assert 'Спикер 1: Отлично, какие у вас проекты?' in text
        assert text.count('Спикер 1') == 2
        assert text.count('Спикер 2') == 1

    def test_transcribe_from_url_utterances_speaker_3(self, settings):
        """Поддерживаются три и более спикеров (Спикер 3 и т.д.)."""
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        utterances = [
            {'speaker': 0, 'transcript': 'Реплика первого.'},
            {'speaker': 2, 'transcript': 'Реплика третьего спикера.'},
        ]
        mock_response = _make_deepgram_ok_response(utterances=utterances)

        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value='https://direct.url/video.mp4'):
            with patch('transcriptions.services.requests.post', return_value=mock_response):
                text = TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/test')

        assert 'Спикер 1: Реплика первого.' in text
        assert 'Спикер 3: Реплика третьего спикера.' in text

    def test_transcribe_from_url_utterances_merge_consecutive_same_speaker(self, settings):
        """Подряд идущие реплики одного спикера объединяются в один блок."""
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        utterances = [
            {'speaker': 0, 'transcript': 'Да, доброе'},
            {'speaker': 0, 'transcript': 'утро. Еще раз'},
            {'speaker': 1, 'transcript': 'Привет.'},
            {'speaker': 0, 'transcript': 'Слышно?'},
        ]
        mock_response = _make_deepgram_ok_response(utterances=utterances)

        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value='https://direct.url/video.mp4'):
            with patch('transcriptions.services.requests.post', return_value=mock_response):
                text = TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/test')

        assert 'Спикер 1: Да, доброе утро. Еще раз' in text
        assert 'Спикер 2: Привет.' in text
        assert 'Спикер 1: Слышно?' in text
        assert text.count('Спикер 1:') == 2
        assert text.count('Спикер 2:') == 1

    def test_transcribe_from_url_utterances_sandwich_short_fragment(self, settings):
        """Короткая реплика между двумя репликами одного спикера сливается с ними (ошибка диризации)."""
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        utterances = [
            {'speaker': 0, 'transcript': 'Раз-раз.'},
            {'speaker': 1, 'transcript': 'меня'},
            {'speaker': 0, 'transcript': 'слышно? Да, да'},
        ]
        mock_response = _make_deepgram_ok_response(utterances=utterances)

        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value='https://direct.url/video.mp4'):
            with patch('transcriptions.services.requests.post', return_value=mock_response):
                text = TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/test')

        assert 'Спикер 1: Раз-раз. меня слышно? Да, да' in text
        assert 'Спикер 2' not in text

    def test_transcribe_from_url_yandex_showcaptcha_raises(self, settings):
        """Если Яндекс отдал страницу капчи вместо файла — понятная ошибка до запроса в Deepgram."""
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        captcha_url = 'https://yadi.sk/showcaptcha?cc=1&form-fb-hint=2'
        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value=captcha_url):
            with pytest.raises(RuntimeError, match='капч'):
                TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/bad')

    def test_transcribe_from_url_deepgram_error(self, settings):
        """Ошибка Deepgram (не 408) пробрасывается без fallback."""
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Bad request'

        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value='https://direct.url/video.mp4'):
            with patch('transcriptions.services.requests.post', return_value=mock_response):
                with pytest.raises(RuntimeError, match='400'):
                    TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/test')

    def test_transcribe_unexpected_response_format(self, settings):
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'results': {}}

        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value='https://direct.url/video.mp4'):
            with patch('transcriptions.services.requests.post', return_value=mock_response):
                with pytest.raises(RuntimeError, match='формат ответа'):
                    TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/test')

    # --- Тесты fallback (408 SLOW_UPLOAD → скачивание в RAM) ---

    def test_transcribe_from_url_408_triggers_tempfile_fallback(self, settings):
        """При 408 SLOW_UPLOAD от Deepgram автоматически запускается fallback через диск."""
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        ok_response = _make_deepgram_ok_response(transcript='Текст через fallback.')
        download_response = _make_download_response()

        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value='https://direct.url/video.mp4'):
            with patch('transcriptions.services.requests.post', side_effect=[_make_deepgram_408_response(), ok_response]) as mock_post:
                with patch('transcriptions.services.requests.get', return_value=download_response):
                    text = TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/test')

        assert text == 'Текст через fallback.'
        assert mock_post.call_count == 2

    def test_transcribe_from_url_408_fallback_uses_binary_content_type(self, settings):
        """При fallback файл скачивается на диск и отправляется с корректным Content-Type."""
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        ok_response = _make_deepgram_ok_response(transcript='OK')
        download_response = _make_download_response(content_type='video/webm')

        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value='https://direct.url/video.webm'):
            with patch('transcriptions.services.requests.post', side_effect=[_make_deepgram_408_response(), ok_response]) as mock_post:
                with patch('transcriptions.services.requests.get', return_value=download_response):
                    TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/test')

        _, fallback_kwargs = mock_post.call_args
        assert fallback_kwargs['headers']['Content-Type'] == 'video/webm'
        assert hasattr(fallback_kwargs['data'], 'read')

    def test_transcribe_from_url_non_408_error_no_fallback(self, settings):
        """При ошибке не-408 fallback не вызывается — ошибка сразу пробрасывается."""
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = 'Internal Server Error'

        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value='https://direct.url/video.mp4'):
            with patch('transcriptions.services.requests.post', return_value=error_response) as mock_post:
                with patch('transcriptions.services.requests.get') as mock_get:
                    with pytest.raises(RuntimeError, match='500'):
                        TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/test')

        assert mock_post.call_count == 1
        mock_get.assert_not_called()

    def test_transcribe_from_url_408_fallback_download_fails(self, settings):
        """Если скачивание файла в RAM завершилось ошибкой — пробрасываем исключение."""
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.YANDEX_DISK_TOKEN = 'ya-token'

        failed_download = MagicMock()
        failed_download.status_code = 403
        failed_download.text = 'Forbidden'

        with patch.object(TranscriptionService, '_resolve_yandex_disk_url', return_value='https://direct.url/video.mp4'):
            with patch('transcriptions.services.requests.post', return_value=_make_deepgram_408_response()):
                with patch('transcriptions.services.requests.get', return_value=failed_download):
                    with pytest.raises(RuntimeError, match='403'):
                        TranscriptionService.transcribe_from_url('https://disk.yandex.ru/i/test')

    def test_download_to_tempfile_writes_chunks(self, settings):
        """_download_to_tempfile корректно записывает чанки во временный файл."""
        chunks = [b'chunk1_', b'chunk2_', b'chunk3']
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {'Content-Type': 'video/mp4'}
        mock_resp.iter_content.return_value = chunks

        with patch('transcriptions.services.requests.get', return_value=mock_resp):
            tmp_path, ct = TranscriptionService._download_to_tempfile('https://direct.url/video.mp4')

        try:
            import os
            with open(tmp_path, 'rb') as f:
                assert f.read() == b'chunk1_chunk2_chunk3'
            assert ct == 'video/mp4'
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # --- Тесты get_balance ---

    def test_get_balance_success(self, settings):
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.DEEPGRAM_PROJECT_ID = 'test-project-id'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'balances': [{'amount': 42.5, 'units': 'usd'}]
        }

        with patch('transcriptions.services.requests.get', return_value=mock_response):
            result = TranscriptionService.get_balance()

        assert result['amount'] == 42.5
        assert result['units'] == 'usd'

    def test_get_balance_missing_project_id(self, settings):
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.DEEPGRAM_PROJECT_ID = ''

        with pytest.raises(ValueError, match='DEEPGRAM_PROJECT_ID'):
            TranscriptionService.get_balance()

    def test_get_balance_empty_balances(self, settings):
        settings.DEEPGRAM_API_KEY = 'test-api-key'
        settings.DEEPGRAM_PROJECT_ID = 'test-project-id'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'balances': []}

        with patch('transcriptions.services.requests.get', return_value=mock_response):
            result = TranscriptionService.get_balance()

        assert result['amount'] == 0.0
