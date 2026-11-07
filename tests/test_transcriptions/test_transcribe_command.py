"""Тесты management-команды transcribe_interviews."""
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command


@pytest.mark.django_db(databases=['default'])
class TestTranscribeInterviewsCommand:
    def test_dry_run_no_interviews(self):
        out = StringIO()
        call_command('transcribe_interviews', '--dry-run', stdout=out)
        assert 'dry-run' in out.getvalue()

    @patch('django.core.cache.cache.get', return_value=True)
    def test_balance_exhausted_stops(self, _mock_cache_get):
        out = StringIO()
        call_command('transcribe_interviews', stdout=out)
        assert 'Deepgram' in out.getvalue() or 'баланс' in out.getvalue().lower()

    @patch('django.core.cache.cache.delete')
    @patch('django.core.cache.cache.get', return_value=None)
    def test_reset_balance_flag(self, _mock_get, mock_delete):
        out = StringIO()
        call_command('transcribe_interviews', '--reset-balance-flag', stdout=out)
        mock_delete.assert_called()
        assert 'сброшен' in out.getvalue().lower() or 'Сброшен' in out.getvalue()
