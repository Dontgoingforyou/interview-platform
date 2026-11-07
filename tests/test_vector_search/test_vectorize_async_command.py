"""Тесты management-команды vectorize_async."""
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command


@pytest.mark.django_db(databases=['default'])
class TestVectorizeAsyncCommand:
    def test_no_args_raises(self):
        with pytest.raises(CommandError, match='--all|--entity-type'):
            call_command('vectorize_async')

    @patch('vector_search.management.commands.vectorize_async.vectorize_batch_task.delay')
    def test_entity_type_schedules_tasks(self, mock_delay, company):
        out = StringIO()
        call_command('vectorize_async', '--entity-type=company', '--batch-size=10', stdout=out)
        mock_delay.assert_called_once()
        args = mock_delay.call_args[0]
        assert args[0] == 'company'
        assert str(company.pk) in [str(x) for x in args[1]]
        assert 'company' in out.getvalue()

    @patch('vector_search.management.commands.vectorize_async.Command.schedule_vectorization', return_value=2)
    def test_all_entity_types(self, mock_schedule):
        out = StringIO()
        call_command('vectorize_async', '--all', stdout=out)
        assert mock_schedule.call_count == 9
        assert 'Всего запланировано' in out.getvalue()

    def test_empty_company_no_tasks(self):
        out = StringIO()
        call_command('vectorize_async', '--entity-type=company', stdout=out)
        assert 'не найдено' in out.getvalue().lower() or '0' in out.getvalue()
