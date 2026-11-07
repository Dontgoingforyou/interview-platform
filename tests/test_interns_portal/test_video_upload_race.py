"""
Тесты защиты от race condition при загрузке видео.

Покрывают:
- Повторный POST при уже активном upload_task_id ('__uploading__') → 409 Conflict
- Повторный POST при task в состоянии PENDING/STARTED/PROGRESS → 409 Conflict
- POST при завершённом (SUCCESS/FAILURE) task → допускается (начать новую загрузку)
- POST при отсутствии upload_task_id → допускается
- GET статуса задачи при FAILURE → upload_task_id сбрасывается, студент может повторить
"""
import pytest
from datetime import date, time
from unittest.mock import patch, MagicMock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from core.constants import INTERVIEW_FORMAT_ONLINE
from interviews.models import Interview
from tests.helpers import make_keycloak_user

from .conftest import STUDENT_CORPORATE_EMAIL, STUDENT_FULL_NAME


def _student_user():
    return make_keycloak_user(
        email=STUDENT_CORPORATE_EMAIL,
        groups=['students'],
        full_name=STUDENT_FULL_NAME,
    )


def _mp4_file(name='test.mp4'):
    """SimpleUploadedFile в формате MP4 (magic bytes + минимальный ftyp box)."""
    return SimpleUploadedFile(name, b'\x00\x00\x00\x18ftypmp42', content_type='video/mp4')


def _upload_url(interview_id):
    return reverse('api_intern_portal_upload', kwargs={'interview_id': interview_id})


@pytest.mark.django_db
class TestVideoUploadRaceCondition:
    """Повторная загрузка видео — protection via select_for_update + sentinel."""

    def _make_online_interview(self, student_intern, direction, upload_task_id=''):
        """Создаёт online-собеседование с заданным upload_task_id."""
        return Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            interview_format=INTERVIEW_FORMAT_ONLINE,
            date=date(2025, 12, 1),
            time=time(10, 0),
            upload_task_id=upload_task_id,
        )

    def test_returns_409_when_sentinel_uploading(self, api_client, student_intern, direction):
        """Если upload_task_id='__uploading__', второй запрос получает 409."""
        interview = self._make_online_interview(student_intern, direction, upload_task_id='__uploading__')

        api_client.force_authenticate(user=_student_user())
        response = api_client.post(
            _upload_url(interview.pk),
            {'video': _mp4_file()},
            format='multipart',
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert 'выполняется' in response.data.get('error', '')

    @pytest.mark.parametrize('task_state', ['PENDING', 'STARTED', 'PROGRESS'])
    def test_returns_409_for_active_celery_states(
        self, api_client, student_intern, direction, task_state,
    ):
        """Активные состояния Celery для существующего task_id → 409."""
        interview = self._make_online_interview(student_intern, direction, upload_task_id='existing-task-uuid')

        api_client.force_authenticate(user=_student_user())

        with patch('interns_portal.api.views.AsyncResult') as mock_ar:
            mock_ar.return_value.state = task_state
            response = api_client.post(
                _upload_url(interview.pk),
                {'video': _mp4_file()},
                format='multipart',
            )

        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.parametrize('task_state', ['SUCCESS', 'FAILURE', 'REVOKED'])
    def test_allows_upload_after_completed_task(
        self, api_client, student_intern, direction, task_state, settings, tmp_path,
    ):
        """Завершённые состояния Celery — повторная загрузка разрешена (не 409)."""
        settings.MEDIA_ROOT = str(tmp_path)
        interview = self._make_online_interview(student_intern, direction, upload_task_id='finished-task-uuid')

        api_client.force_authenticate(user=_student_user())

        with patch('interns_portal.api.views.AsyncResult') as mock_ar:
            mock_ar.return_value.state = task_state
            with patch('interns_portal.api.views.upload_video_to_s3.delay') as mock_delay:
                mock_delay.return_value = MagicMock(id='new-task-uuid')
                response = api_client.post(
                    _upload_url(interview.pk),
                    {'video': _mp4_file()},
                    format='multipart',
                )

        assert response.status_code != status.HTTP_409_CONFLICT

    def test_no_task_id_allows_upload(self, api_client, student_intern, direction, settings, tmp_path):
        """Отсутствие upload_task_id — загрузка разрешена (не 409)."""
        settings.MEDIA_ROOT = str(tmp_path)
        interview = self._make_online_interview(student_intern, direction, upload_task_id='')

        api_client.force_authenticate(user=_student_user())

        with patch('interns_portal.api.views.upload_video_to_s3.delay') as mock_delay:
            mock_delay.return_value = MagicMock(id='fresh-task-uuid')
            response = api_client.post(
                _upload_url(interview.pk),
                {'video': _mp4_file()},
                format='multipart',
            )

        assert response.status_code != status.HTTP_409_CONFLICT

    def test_invalid_magic_clears_sentinel_and_allows_retry(
        self, api_client, student_intern, direction,
    ):
        """Невалидный magic bytes — upload_task_id сброшен, повторный POST не 409."""
        interview = self._make_online_interview(student_intern, direction, upload_task_id='')
        api_client.force_authenticate(user=_student_user())

        bad_file = SimpleUploadedFile('fake.mp4', b'not-a-video-file', content_type='video/mp4')
        url = _upload_url(interview.pk)
        first = api_client.post(url, {'video': bad_file}, format='multipart')
        assert first.status_code == status.HTTP_400_BAD_REQUEST
        interview.refresh_from_db()
        assert interview.upload_task_id == ''

        with patch('interns_portal.api.views.upload_video_to_s3.delay') as mock_delay:
            mock_delay.return_value = MagicMock(id='after-validation-retry')
            second = api_client.post(url, {'video': _mp4_file()}, format='multipart')
        assert second.status_code != status.HTTP_409_CONFLICT


@pytest.mark.django_db
class TestUploadTaskStatusFailureClearsSlot:
    """Статусный эндпоинт при FAILURE сбрасывает upload_task_id, чтобы студент мог повторить."""

    def test_failure_state_clears_upload_task_id(self, api_client, student_intern, direction):
        """GET /upload-tasks/{task_id}/ при FAILURE → upload_task_id = None в БД."""
        from datetime import date, time
        from interviews.models import Interview

        task_id = 'failed-celery-task-uuid'
        interview = Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            interview_format='online',
            date=date(2025, 12, 1),
            time=time(10, 0),
            upload_task_id=task_id,
        )
        api_client.force_authenticate(user=_student_user())
        url = reverse('api_intern_portal_upload_task', kwargs={'task_id': task_id})

        with patch('interns_portal.api.views.celery_task_status_payload') as mock_payload:
            mock_payload.return_value = {
                'state': 'FAILURE',
                'status': 'FileNotFoundError: tmp not found',
                'current': 0,
                'total': 100,
            }
            response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['state'] == 'FAILURE'

        interview.refresh_from_db()
        assert interview.upload_task_id is None

    def test_failure_state_upload_action_state_resets(self, api_client, student_intern, direction):
        """После FAILURE и рефетча списка студент видит 'none' (кнопку «Загрузить»)."""
        from datetime import date, time
        from interviews.models import Interview

        task_id = 'another-failed-uuid'
        interview = Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            interview_format='online',
            date=date(2025, 12, 2),
            time=time(11, 0),
            upload_task_id=task_id,
        )
        api_client.force_authenticate(user=_student_user())
        url = reverse('api_intern_portal_upload_task', kwargs={'task_id': task_id})

        with patch('interns_portal.api.views.celery_task_status_payload') as mock_payload:
            mock_payload.return_value = {
                'state': 'FAILURE',
                'status': '',
                'current': 0,
                'total': 100,
            }
            api_client.get(url)

        interview.refresh_from_db()
        assert interview.upload_task_id is None
        assert interview.upload_action_state == 'none'

    def test_pending_state_does_not_clear_upload_task_id(self, api_client, student_intern, direction):
        """PENDING-состояние с живым alive-ключом — upload_task_id остаётся (задача ещё в очереди)."""
        from datetime import date, time
        from django.core.cache import cache
        from interviews.models import Interview

        task_id = 'pending-celery-task-uuid'
        interview = Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            interview_format='online',
            date=date(2025, 12, 3),
            time=time(12, 0),
            upload_task_id=task_id,
        )
        # Симулируем свежеотправленную задачу: alive-ключ активен
        cache.set(f'portal_upload_alive:{task_id}', '1', timeout=900)
        api_client.force_authenticate(user=_student_user())
        url = reverse('api_intern_portal_upload_task', kwargs={'task_id': task_id})

        with patch('interns_portal.api.views.celery_task_status_payload') as mock_payload:
            mock_payload.return_value = {
                'state': 'PENDING',
                'status': 'Ожидание...',
                'current': 0,
                'total': 100,
            }
            response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        interview.refresh_from_db()
        assert interview.upload_task_id == task_id

    def test_pending_without_alive_key_clears_upload_task_id(self, api_client, student_intern, direction):
        """PENDING без alive-ключа (задача потеряна) — upload_task_id сбрасывается, возвращается FAILURE."""
        from datetime import date, time
        from django.core.cache import cache
        from interviews.models import Interview

        task_id = 'lost-celery-task-uuid'
        interview = Interview.objects.create(
            intern=student_intern,
            direction=direction,
            manager_email='manager@example.com',
            interview_type='screening',
            interview_format='online',
            date=date(2025, 12, 3),
            time=time(12, 0),
            upload_task_id=task_id,
        )
        # Alive-ключ намеренно не ставим — симулируем истёкший/потерянный ключ
        cache.delete(f'portal_upload_alive:{task_id}')
        api_client.force_authenticate(user=_student_user())
        url = reverse('api_intern_portal_upload_task', kwargs={'task_id': task_id})

        with patch('interns_portal.api.views.celery_task_status_payload') as mock_payload:
            mock_payload.return_value = {
                'state': 'PENDING',
                'status': 'Ожидание...',
                'current': 0,
                'total': 100,
            }
            response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['state'] == 'FAILURE'
        interview.refresh_from_db()
        assert interview.upload_task_id is None
