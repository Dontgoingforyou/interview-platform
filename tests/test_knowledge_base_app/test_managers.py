"""
Тесты для KnowledgeBaseManager.

Разделы и статьи хранятся в БД (модели KBSection, KBArticle).
"""
import pytest

from knowledge_base_app.managers import _sanitize_filename


# ---------------------------------------------------------------------------
# get_sections / create_section / delete_section / update_section
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSections:
    def test_get_sections_empty(self, kb_manager):
        assert kb_manager.get_sections() == []

    def test_create_section_appears_in_get_sections(self, kb_manager):
        kb_manager.create_section('docs', 'Документация', 'Описание', '📚')
        sections = kb_manager.get_sections()
        assert len(sections) == 1
        assert sections[0]['id'] == 'docs'
        assert sections[0]['title'] == 'Документация'
        assert sections[0]['icon'] == '📚'

    def test_create_section_adds_to_index(self, kb_manager):
        kb_manager.create_section('docs', 'Документация', 'Описание', '📚')
        sections = kb_manager.get_sections()
        assert len(sections) == 1
        assert sections[0]['id'] == 'docs'
        assert sections[0]['title'] == 'Документация'
        assert sections[0]['icon'] == '📚'

    def test_create_section_invalid_id_raises(self, kb_manager):
        with pytest.raises(ValueError, match='ID раздела'):
            kb_manager.create_section('Invalid ID!', 'Заголовок')

    def test_create_section_duplicate_raises(self, kb_manager_with_section):
        with pytest.raises(ValueError, match='уже существует'):
            kb_manager_with_section.create_section('test-section', 'Дубликат')

    def test_delete_section_removes_from_list(self, kb_manager_with_section):
        kb_manager_with_section.delete_section('test-section')
        assert kb_manager_with_section.get_sections() == []

    def test_delete_section_not_found_raises(self, kb_manager):
        with pytest.raises(ValueError, match='не найден'):
            kb_manager.delete_section('nonexistent')

    @pytest.mark.parametrize('field,value', [
        ('title', 'Новое название'),
        ('icon', '🔑'),
    ])
    def test_update_section_field(self, field, value, kb_manager_with_section):
        kb_manager_with_section.update_section('test-section', **{field: value})
        sections = kb_manager_with_section.get_sections()
        assert sections[0][field] == value

    def test_update_section_not_found_raises(self, kb_manager):
        with pytest.raises(ValueError, match='не найден'):
            kb_manager.update_section('nonexistent', title='X')

    def test_sections_order_preserved(self, kb_manager):
        kb_manager.create_section('alpha', 'Alpha')
        kb_manager.create_section('beta', 'Beta')
        sections = kb_manager.get_sections()
        ids = [s['id'] for s in sections]
        assert ids == ['alpha', 'beta']


# ---------------------------------------------------------------------------
# get_articles / create_article / get_article / save_article / delete_article
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestArticles:
    def test_get_articles_empty_section(self, kb_manager_with_section):
        articles = kb_manager_with_section.get_articles('test-section')
        assert articles == []

    def test_create_article_returns_filename(self, kb_manager_with_section):
        filename = kb_manager_with_section.create_article('test-section', 'Моя статья', 'Контент')
        assert filename.endswith('.md')

    def test_create_article_appears_in_list(self, kb_manager_with_section):
        kb_manager_with_section.create_article('test-section', 'Первая статья', 'Текст')
        articles = kb_manager_with_section.get_articles('test-section')
        assert len(articles) == 1
        assert articles[0]['title'] == 'Первая статья'

    def test_create_multiple_articles_numbered(self, kb_manager_with_section):
        kb_manager_with_section.create_article('test-section', 'Статья 1', 'Текст 1')
        kb_manager_with_section.create_article('test-section', 'Статья 2', 'Текст 2')
        articles = kb_manager_with_section.get_articles('test-section')
        assert len(articles) == 2

    def test_get_article_content(self, kb_manager_with_section):
        filename = kb_manager_with_section.create_article('test-section', 'Заголовок', 'Тело статьи')
        article = kb_manager_with_section.get_article('test-section', filename)
        assert article is not None
        assert article['title'] == 'Заголовок'
        assert 'Тело статьи' in article['markdown']

    def test_get_article_not_found_returns_none(self, kb_manager_with_section):
        result = kb_manager_with_section.get_article('test-section', 'nonexistent.md')
        assert result is None

    def test_get_article_contains_html(self, kb_manager_with_section):
        filename = kb_manager_with_section.create_article('test-section', 'Тест', '**жирный**')
        article = kb_manager_with_section.get_article('test-section', filename)
        assert '<strong>' in article['html']

    def test_save_article_updates_content(self, kb_manager_with_section):
        filename = kb_manager_with_section.create_article('test-section', 'Заголовок', 'Старый текст')
        kb_manager_with_section.save_article('test-section', filename, 'Новый текст', title='Заголовок')
        article = kb_manager_with_section.get_article('test-section', filename)
        assert 'Новый текст' in article['markdown']

    def test_delete_article_removes_from_db(self, kb_manager_with_section):
        filename = kb_manager_with_section.create_article('test-section', 'Удаляемая', 'Текст')
        result = kb_manager_with_section.delete_article('test-section', filename)
        assert result is True
        assert kb_manager_with_section.get_article('test-section', filename) is None

    def test_delete_article_not_found_returns_false(self, kb_manager_with_section):
        result = kb_manager_with_section.delete_article('test-section', 'ghost.md')
        assert result is False


# ---------------------------------------------------------------------------
# Санитизация имени файла (защита от path traversal)
# ---------------------------------------------------------------------------

class TestSanitizeFilename:
    def test_sanitize_filename_removes_dangerous_chars(self):
        result = _sanitize_filename('../../../etc/passwd')
        assert '/' not in result
        assert '..' not in result

    def test_sanitize_filename_keeps_safe_name(self):
        result = _sanitize_filename('01-article-name.md')
        assert result == '01-article-name.md'


# ---------------------------------------------------------------------------
# search_articles
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSearch:
    def test_search_finds_by_title(self, kb_manager_with_section):
        kb_manager_with_section.create_article('test-section', 'Unique Title Here', 'Body')
        results = kb_manager_with_section.search_articles('unique')
        assert len(results) == 1
        assert results[0]['title'] == 'Unique Title Here'

    def test_search_finds_by_content(self, kb_manager_with_section):
        kb_manager_with_section.create_article('test-section', 'Some', 'RareWordXyZ in content')
        results = kb_manager_with_section.search_articles('rarewordxyz')
        assert len(results) == 1

    def test_search_empty_query_matches_all(self, kb_manager_with_section):
        kb_manager_with_section.create_article('test-section', 'Статья', 'Текст')
        results = kb_manager_with_section.search_articles('')
        assert len(results) == 1

    def test_search_respects_limit(self, kb_manager_with_section):
        for i in range(10):
            kb_manager_with_section.create_article('test-section', f'Статья {i}', 'общий текст')
        results = kb_manager_with_section.search_articles('общий', limit=3)
        assert len(results) <= 3

    def test_search_returns_section_info(self, kb_manager_with_section):
        kb_manager_with_section.create_article('test-section', 'Find Me Title', 'Text')
        results = kb_manager_with_section.search_articles('find')
        assert len(results) == 1
        assert results[0]['section_id'] == 'test-section'
        assert 'section_title' in results[0]


# ---------------------------------------------------------------------------
# markdown_to_html — XSS и безопасность
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMarkdownToHtml:
    @pytest.mark.parametrize('malicious_input,forbidden_str', [
        ('<script>alert("xss")</script>', '<script>'),
        ('<p onclick="alert(1)">Текст</p>', 'onclick'),
    ])
    def test_xss_stripped(self, kb_manager, malicious_input, forbidden_str):
        html = kb_manager.markdown_to_html(malicious_input)
        assert forbidden_str not in html

    def test_external_link_gets_target_blank(self, kb_manager):
        html = kb_manager.markdown_to_html('[Ссылка](https://example.com)')
        assert 'target="_blank"' in html
        assert 'noopener noreferrer' in html

    def test_iframe_allowed_domain_passes(self, kb_manager):
        md = '<iframe src="https://www.youtube.com/embed/abc123"></iframe>'
        html = kb_manager.markdown_to_html(md)
        assert 'youtube.com' in html

    def test_iframe_unknown_domain_blocked(self, kb_manager):
        md = '<iframe src="https://evil.example.com/hack"></iframe>'
        html = kb_manager.markdown_to_html(md)
        assert 'evil.example.com' not in html

    def test_basic_markdown_rendered(self, kb_manager):
        html = kb_manager.markdown_to_html('**жирный** и *курсив*')
        assert '<strong>' in html
        assert '<em>' in html

    def test_code_block_preserved(self, kb_manager):
        html = kb_manager.markdown_to_html('```\nprint("hello")\n```')
        assert 'print' in html
