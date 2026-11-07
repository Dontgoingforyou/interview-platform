"""
Тесты SSRF-защиты транскрипции.

Покрывают _is_allowed_transcription_url и интеграцию с _resolve_yandex_disk_url:
- Разрешённые домены (yandex.ru, disk.yandex.ru, googleapis.com) → True
- Приватные IP-диапазоны → False (SSRF)
- Loopback (127.0.0.1, localhost) → False
- Link-local (169.254.x.x) → False (AWS metadata, cloud instances)
- Неразрешённые внешние домены → False
- Недопустимые схемы (ftp, file) → False
- Поддоменный allowlist работает корректно
- _resolve_yandex_disk_url выбрасывает ValueError для неразрешённого URL
"""
import pytest
from unittest.mock import MagicMock

from transcriptions.services import _is_allowed_transcription_url


class TestIsAllowedTranscriptionUrl:
    """Юнит-тесты для _is_allowed_transcription_url (без DB)."""

    @pytest.mark.parametrize('url', [
        'https://disk.yandex.ru/i/abc123',
        'https://yandex.ru/something',
        'https://yandex.net/d/link',
        'https://downloader.disk.yandex.ru/d/abc',
        'https://cloud-api.yandex.net/v1/disk/public/resources',
        'https://storage.googleapis.com/bucket/file.mp4',
        'https://googleapis.com/anything',
        'https://api.deepgram.com/v1/listen',
        'https://storage.googleapis.com/interview-videos/file.mp4',
        'https://disk.yandex.ru/interview-videos/file.mp4',
    ])
    def test_allowed_domains(self, url):
        """Разрешённые домены и поддомены возвращают True."""
        assert _is_allowed_transcription_url(url) is True

    @pytest.mark.parametrize('url', [
        'http://169.254.169.254/latest/meta-data/',   # AWS metadata
        'http://169.254.169.254/',                     # link-local
        'http://192.168.1.1/admin',                    # private class C
        'http://10.0.0.1/internal',                    # private class A
        'http://172.16.0.1/secret',                    # private class B
        'http://127.0.0.1:6379',                       # loopback (Redis)
        'http://0.0.0.0/',                             # any-local
    ])
    def test_blocks_private_and_loopback_ips(self, url):
        """Приватные и loopback IP-адреса возвращают False (SSRF-защита)."""
        assert _is_allowed_transcription_url(url) is False

    @pytest.mark.parametrize('url', [
        'https://evil.com/video.mp4',
        'https://attacker.example.com/',
        'https://not-yandex.ru/fake',
        'https://yandex.ru.evil.com/',      # subdomain spoofing
        'https://disk-yandex.ru/fake',      # typosquatting
    ])
    def test_blocks_external_unknown_domains(self, url):
        """Сторонние и поддельные домены возвращают False."""
        assert _is_allowed_transcription_url(url) is False

    @pytest.mark.parametrize('url', [
        'ftp://disk.yandex.ru/file.mp4',
        'file:///etc/passwd',
        'dict://localhost:6379',
        'gopher://internal.host/',
    ])
    def test_blocks_non_http_schemes(self, url):
        """Схемы, отличные от http/https, возвращают False."""
        assert _is_allowed_transcription_url(url) is False

    def test_allows_configured_s3_endpoint_host(self, settings):
        settings.S3_ENDPOINT_URL = 'https://files.example.test'
        assert _is_allowed_transcription_url('https://files.example.test/bucket/file.mp4') is True

    def test_empty_url_returns_false(self):
        assert _is_allowed_transcription_url('') is False

    def test_malformed_url_returns_false(self):
        assert _is_allowed_transcription_url('not-a-url-at-all') is False


class TestResolveYandexDiskUrlSsrfGuard:
    """Интеграционный тест: _resolve_yandex_disk_url отклоняет неразрешённые входные URL."""

    def test_raises_for_ssrf_url(self):
        """Передача приватного IP вместо публичной ссылки → ValueError."""
        from transcriptions.services import TranscriptionService

        with pytest.raises(ValueError, match='SSRF-защита'):
            TranscriptionService._resolve_yandex_disk_url('http://169.254.169.254/meta-data/')

    def test_raises_for_external_domain(self):
        """Передача внешнего неразрешённого домена → ValueError."""
        from transcriptions.services import TranscriptionService

        with pytest.raises(ValueError, match='SSRF-защита'):
            TranscriptionService._resolve_yandex_disk_url('https://evil.com/steal.mp4')

    def test_raises_for_file_scheme(self):
        """Схема file:// для локального пути → ValueError."""
        from transcriptions.services import TranscriptionService

        with pytest.raises(ValueError, match='SSRF-защита'):
            TranscriptionService._resolve_yandex_disk_url('file:///etc/passwd')

    def test_allowed_url_passes_guard_and_calls_yadisk(self):
        """Разрешённый Yandex URL проходит SSRF-проверку и вызывает yadisk API."""
        import sys
        from types import ModuleType
        from transcriptions.services import TranscriptionService

        fake_yadisk = ModuleType('yadisk')
        download_link = 'https://downloader.disk.yandex.ru/d/xyz'

        mock_meta = type('Meta', (), {'name': 'test.mp4'})()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get_public_download_link.return_value = download_link
        mock_client.get_public_meta.return_value = mock_meta

        fake_yadisk.Client = MagicMock(return_value=mock_client)

        original = sys.modules.get('yadisk')
        sys.modules['yadisk'] = fake_yadisk
        try:
            result = TranscriptionService._resolve_yandex_disk_url('https://disk.yandex.ru/i/test')
        finally:
            if original is None:
                sys.modules.pop('yadisk', None)
            else:
                sys.modules['yadisk'] = original

        assert result == download_link
