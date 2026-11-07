"""
Фикстуры для тестов приложения vector_search.
"""
import pytest
import os
from decimal import Decimal
from unittest.mock import Mock, patch


@pytest.fixture(autouse=True)
def enable_vector_signals_for_signal_tests(request):
    """
    Включает сигналы vector_search только для тестов сигналов.
    """
    # Проверяем, есть ли маркер signals
    if 'signals' in [marker.name for marker in request.node.iter_markers()]:
        # Для тестов сигналов включаем сигналы
        old_value = os.environ.get('DISABLE_VECTOR_SIGNALS')
        os.environ.pop('DISABLE_VECTOR_SIGNALS', None)

        # Импортируем сигналы (они подключатся)
        import vector_search.signals  # noqa: F401

        yield

        # Восстанавливаем переменную окружения
        if old_value:
            os.environ['DISABLE_VECTOR_SIGNALS'] = old_value
        else:
            os.environ['DISABLE_VECTOR_SIGNALS'] = '1'
    else:
        # Для остальных тестов просто продолжаем (сигналы уже отключены)
        yield


@pytest.fixture(autouse=True)
def mock_openai_embedding():
    """
    Автоматически мокирует OpenAI эмбеддинг для всех тестов.
    Возвращает фиксированный вектор размерности 1536.
    """
    # Создаём тестовый вектор
    test_vector = [0.1] * 1536

    with patch('vector_search.services.EmbeddingService.get_client') as mock_client:
        mock_openai = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=test_vector)]
        mock_openai.embeddings.create.return_value = mock_response
        mock_client.return_value = mock_openai
        yield mock_openai


@pytest.fixture
def mock_embedding_service():
    """
    Мок для EmbeddingService.
    Используется для тестов, где не нужны реальные эмбеддинги.
    """
    with patch('vector_search.services.EmbeddingService.generate_embedding') as mock_generate:
        # Возвращаем фиксированный тестовый вектор
        mock_generate.return_value = [0.1] * 1536
        yield mock_generate


@pytest.fixture
def vector_embedding_interview(db, interview):
    """
    Создаёт векторный эмбеддинг для тестового собеседования.
    """
    from vector_search.models import VectorEmbedding

    # В тестах используем default БД (SQLite), а не vector_db
    # Используем get_or_create для избежания дубликатов
    embedding, _ = VectorEmbedding.objects.get_or_create(
        entity_type='interview',
        entity_id=str(interview.id),  # Явно преобразуем в строку
        defaults={
            'text_content': f'Тип: Скрининг | Студент: {interview.intern.full_name}',
            'embedding': [0.1] * 1536,
            'metadata': {
                'direction_id': interview.direction_id,
                'manager_email': interview.manager_email,
                'interview_type': interview.interview_type,
            }
        }
    )
    return embedding


@pytest.fixture
def vector_embedding_intern(db, intern):
    """
    Создаёт векторный эмбеддинг для тестового студента.
    """
    from vector_search.models import VectorEmbedding

    # В тестах используем default БД (SQLite), а не vector_db
    # Используем get_or_create для избежания дубликатов
    embedding, _ = VectorEmbedding.objects.get_or_create(
        entity_type='intern',
        entity_id=str(intern.id),  # Явно преобразуем в строку
        defaults={
            'text_content': f'Имя: {intern.full_name} | Email: {intern.email}',
            'embedding': [0.2] * 1536,
            'metadata': {
                'direction_id': intern.direction_id,
                'manager_email': intern.manager_email,
            }
        }
    )
    return embedding


@pytest.fixture
def search_log(db):
    """
    Создаёт тестовый лог поиска.
    """
    from vector_search.models import SearchLog

    return SearchLog.objects.create(
        query='тестовый запрос',
        entity_type='interview',
        results_count=5,
        search_time_ms=123.45,
        user_email='test@example.com',
        filters={'direction_id': 1}
    )


@pytest.fixture
def offer(db, intern, direction):
    """Создаёт тестовый оффер для тестов vector_search."""
    from offers.models import Offer

    return Offer.objects.create(
        intern=intern,
        direction=direction,
        company='Test Company',
        amount=Decimal('100000.00'),
        month=12,
        year=2025
    )


@pytest.fixture
def debt(db, intern, direction):
    """Создаёт тестовый долг для тестов vector_search."""
    from debts.models import Debt

    return Debt.objects.create(
        intern=intern,
        direction=direction,
        email=intern.email,
        telegram_username='@test',
        total_amount=Decimal('50000.00'),
        paid_amount=Decimal('10000.00'),
        balance=Decimal('40000.00'),
        payment_status='paying'
    )


@pytest.fixture
def intern_weekly_status(db, intern):
    """Создаёт тестовый недельный статус студента для тестов vector_search."""
    from datetime import date
    from employees.models import InternWeeklyStatus

    return InternWeeklyStatus.objects.create(
        intern=intern,
        week_start=date(2025, 3, 3),
        absence_status='отпуск',
        absence_notes='Тест отсутствия',
        manual_interview_count=2
    )
