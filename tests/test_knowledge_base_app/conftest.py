import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def kb_manager_mock():
    """Мок KnowledgeBaseManager для изоляции views от файловой системы."""
    with patch('knowledge_base_app.views.KnowledgeBaseManager') as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield instance


@pytest.fixture
def sample_sections():
    return [
        {'id': 'docs', 'title': 'Документация', 'description': 'Описание', 'icon': '📚', 'order': 1, 'article_count': 2},
    ]


@pytest.fixture
def sample_article():
    return {
        'filename': '01-test.md',
        'title': 'Тестовая статья',
        'markdown': '# Заголовок\n\nТекст статьи.',
        'full_content': '---\ntitle: Тестовая статья\n---\n\n# Заголовок\n\nТекст статьи.',
        'html': '<h1>Заголовок</h1><p>Текст статьи.</p>',
        'section_id': 'docs',
    }


@pytest.fixture
def kb_manager(db):
    """Менеджер для работы с базой знаний (БД)."""
    from knowledge_base_app.managers import KnowledgeBaseManager
    return KnowledgeBaseManager()


@pytest.fixture
def kb_manager_with_section(kb_manager, db):
    """Менеджер с уже созданным разделом в БД."""
    kb_manager.create_section('test-section', 'Тестовый раздел', 'Описание', '📝')
    return kb_manager
