"""Тесты core.s3_video_storage."""
import pytest
from unittest.mock import MagicMock, patch

from core.s3_video_storage import (
    build_object_key,
    build_stable_video_url,
    is_s3_video_url,
    parse_s3_video_url,
    presigned_get_url,
    resolve_video_play_url,
    user_friendly_storage_error,
)
from botocore.exceptions import ClientError


@pytest.mark.parametrize('url,expected', [
    ('https://s3.test.example/interview-videos/foo.mp4', ('interview-videos', 'foo.mp4')),
    (
        'https://s3.test.example/interview-videos/dir/file%20name.mp4',
        ('interview-videos', 'dir/file name.mp4'),
    ),
    ('https://disk.yandex.ru/i/x', None),
    ('', None),
])
def test_parse_s3_video_url(url, expected, settings):
    settings.S3_ENDPOINT_URL = 'https://s3.test.example'
    assert parse_s3_video_url(url) == expected
    assert is_s3_video_url(url) == (expected is not None)


def test_build_stable_video_url_encodes_spaces(settings):
    settings.S3_ENDPOINT_URL = 'https://s3.test.example'
    url = build_stable_video_url('interview-videos', 'a b.mp4')
    assert url == 'https://s3.test.example/interview-videos/a%20b.mp4'


def test_build_object_key_with_prefix(settings):
    settings.S3_VIDEO_PREFIX = 'legacy'
    assert build_object_key('x.mp4') == 'legacy/x.mp4'


def test_build_object_key_flat_in_bucket_root(settings):
    settings.S3_VIDEO_PREFIX = ''
    assert build_object_key('a.mp4') == 'a.mp4'


def test_resolve_video_play_url_yandex_unchanged():
    ya = 'https://disk.yandex.ru/i/abc'
    assert resolve_video_play_url(ya) == ya


def test_resolve_video_play_url_presigns_s3(settings):
    settings.S3_ENDPOINT_URL = 'https://s3.test.example'
    stored = 'https://s3.test.example/interview-videos/v.mp4'
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = 'https://s3.test.example/signed'
    with patch('core.s3_video_storage.get_s3_client', return_value=mock_client):
        assert resolve_video_play_url(stored) == 'https://s3.test.example/signed'
    mock_client.generate_presigned_url.assert_called_once()
    params = mock_client.generate_presigned_url.call_args[1]['Params']
    assert params['ResponseContentDisposition'].startswith('inline')
    assert params['ResponseContentType'] == 'video/mp4'


def test_user_friendly_storage_error_client_error():
    exc = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'denied'}},
        'PutObject',
    )
    msg = user_friendly_storage_error(exc)
    assert 'доступа' in msg.lower() or 'S3' in msg


def test_presigned_get_url_non_s3_passthrough():
    url = 'https://disk.yandex.ru/i/x'
    assert presigned_get_url(url) == url
