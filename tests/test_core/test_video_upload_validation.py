"""Тесты core.video_upload_validation."""
import pytest

from core.video_upload_validation import validate_video_magic_header, validate_video_upload_size


class TestValidateVideoUploadSize:
    def test_none_returns_error(self):
        assert validate_video_upload_size(None) == 'Не удалось определить размер файла.'

    def test_size_ok_returns_none(self):
        assert validate_video_upload_size(1024) is None


def _pad(header: bytes, length: int = 12) -> bytes:
    return header + b'\x00' * max(0, length - len(header))


class TestValidateVideoMagicHeader:
    def test_short_header(self):
        assert validate_video_magic_header(b'abc', '.mp4') == 'Файл слишком мал или повреждён.'

    @pytest.mark.parametrize(
        'ext,header',
        [
            ('.mp4', _pad(b'\x00\x00\x00\x00ftyp')),
            ('.mov', _pad(b'\x00\x00\x00\x00ftyp')),
            ('.webm', _pad(b'\x1a\x45\xdf\xa3')),
            ('.mkv', _pad(b'\x1a\x45\xdf\xa3')),
            ('.avi', _pad(b'RIFF\x00\x00\x00\x00AVI ')),
            ('.flv', _pad(b'FLV\x01')),
            ('.wmv', _pad(b'\x30\x26\xb2\x75')),
        ],
    )
    def test_valid_headers(self, ext, header):
        assert validate_video_magic_header(header, ext) is None

    def test_invalid_mp4(self):
        header = _pad(b'\x00\x00\x00\x00xxxx')
        assert 'MP4' in validate_video_magic_header(header, '.mp4')

    def test_invalid_webm(self):
        header = _pad(b'RIFF\x00\x00\x00\x00')
        assert 'WebM' in validate_video_magic_header(header, '.webm')

    def test_unknown_extension_returns_none(self):
        header = _pad(b'\x00' * 12)
        assert validate_video_magic_header(header, '.xyz') is None
