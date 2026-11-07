"""Тесты management-команды check_vector_sync."""
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from vector_search.models import VectorEmbedding


@pytest.mark.django_db(databases=['default'])
class TestCheckVectorSyncCommand:
    def test_empty_db_reports_synced(self):
        out = StringIO()
        call_command('check_vector_sync', '--entity-type=company', stdout=out)
        text = out.getvalue()
        assert 'company' in text
        assert 'Расхождений нет' in text or 'Пропущено: 0' in text

    def test_missing_embedding_reported(self, company):
        out = StringIO()
        call_command('check_vector_sync', '--entity-type=company', stdout=out)
        text = out.getvalue()
        assert 'Пропущено' in text

    def test_with_embedding_synced(self, company):
        VectorEmbedding.objects.create(
            entity_type='company',
            entity_id=str(company.pk),
            text_content='Google',
            embedding=[0.1] * 8,
        )
        out = StringIO()
        call_command('check_vector_sync', '--entity-type=company', stdout=out)
        assert 'Пропущено: 0' in out.getvalue()

    @patch('django.core.management.call_command')
    def test_fix_calls_vectorize_async(self, mock_call, company):
        out = StringIO()
        call_command('check_vector_sync', '--entity-type=company', '--fix', stdout=out)
        mock_call.assert_called_once_with('vectorize_async', '--entity-type', 'company')
