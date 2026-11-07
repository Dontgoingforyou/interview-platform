"""Тесты core.celery_task_status."""
from unittest.mock import MagicMock, patch

from core.celery_task_status import celery_task_status_payload


class TestCeleryTaskStatusPayload:
    @patch('core.celery_task_status.AsyncResult')
    def test_pending(self, mock_result_cls):
        mock_result_cls.return_value.state = 'PENDING'
        payload = celery_task_status_payload('task-1')
        assert payload['state'] == 'PENDING'
        assert payload['current'] == 0

    @patch('core.celery_task_status.AsyncResult')
    def test_progress(self, mock_result_cls):
        task = MagicMock()
        task.state = 'PROGRESS'
        task.info = {'status': 'Импорт...', 'current': 10, 'total': 100}
        mock_result_cls.return_value = task
        payload = celery_task_status_payload('task-2')
        assert payload['current'] == 10
        assert payload['total'] == 100

    @patch('core.celery_task_status.AsyncResult')
    def test_success(self, mock_result_cls):
        task = MagicMock()
        task.state = 'SUCCESS'
        task.result = {'created': 5}
        task.info = None
        mock_result_cls.return_value = task
        payload = celery_task_status_payload('task-3')
        assert payload['state'] == 'SUCCESS'
        assert payload['result'] == {'created': 5}

    @patch('core.celery_task_status.AsyncResult')
    def test_failure(self, mock_result_cls):
        task = MagicMock()
        task.state = 'FAILURE'
        task.info = Exception('boom')
        mock_result_cls.return_value = task
        payload = celery_task_status_payload('task-4')
        assert payload['state'] == 'FAILURE'

    @patch('core.celery_task_status.AsyncResult')
    def test_unknown_state_fallback(self, mock_result_cls):
        task = MagicMock()
        task.state = 'REVOKED'
        task.info = None
        mock_result_cls.return_value = task
        payload = celery_task_status_payload('task-5')
        assert payload['state'] == 'REVOKED'
