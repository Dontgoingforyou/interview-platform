"""
Утилиты для работы с базой знаний (разделы и статьи в БД, Markdown → HTML).
"""
import os
import re
from datetime import datetime
from typing import List, Dict, Optional

from django.db.models import Count, Max, Q
from django.db.models.functions import Lower

import markdown
import bleach  # type: ignore[import-untyped]
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

from .constants import (
    MARKDOWN_EXTENSIONS,
    RUSSIAN_MONTHS,
    SECTION_ID_PATTERN
)
from .models import KBSection, KBArticle

# ---------------------------------------------------------------------------
# Константы для bleach-санитизации (модульный уровень, единое определение)
# ---------------------------------------------------------------------------

_BLEACH_ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's', 'sup', 'sub',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    'a', 'code', 'pre', 'div', 'span',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
    'blockquote', 'hr', 'img', 'iframe',
]

_BLEACH_ALLOWED_ATTRS = {
    '*': ['class', 'id'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'iframe': ['width', 'height', 'frameborder', 'allowfullscreen'],
    'code': ['class'],
    'div': ['class'],
    'span': ['class'],
}

_BLEACH_ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

_IFRAME_ALLOWED_DOMAINS = [
    'youtube.com', 'www.youtube.com', 'youtube-nocookie.com',
    'vimeo.com', 'www.vimeo.com', 'player.vimeo.com',
]

_SEARCH_RESULTS_LIMIT = 50


def _bleach_attribute_filter(tag: str, name: str, value: str) -> bool:
    """Фильтр атрибутов для bleach.clean()."""
    if tag == 'iframe' and name == 'src':
        return any(domain in value for domain in _IFRAME_ALLOWED_DOMAINS)
    allowed = _BLEACH_ALLOWED_ATTRS.get(tag, []) + _BLEACH_ALLOWED_ATTRS.get('*', [])
    return name in allowed


def _sanitize_filename(filename: str) -> str:
    """Очистить имя файла от опасных символов."""
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    return filename


class KnowledgeBaseManager:
    """Менеджер для работы с базой знаний (разделы и статьи в БД)."""

    def __init__(self):
        pass

    def get_sections(self) -> List[Dict]:
        """Получить список всех разделов с метаданными и количеством статей."""
        sections_qs = (
            KBSection.objects.filter(visible=True)
            .annotate(article_count=Count('articles'))
            .order_by('order', 'section_id')
        )
        return [
            {
                'id': s.section_id,
                'title': s.title,
                'description': s.description or '',
                'icon': s.icon or '📄',
                'order': s.order,
                'article_count': s.article_count,
            }
            for s in sections_qs
        ]

    def get_articles(self, section_id: str) -> List[Dict]:
        """Получить список всех статей в разделе."""
        articles = (
            KBArticle.objects.filter(section__section_id=section_id)
            .order_by('filename')
        )
        return [
            {
                'filename': a.filename,
                'title': a.title,
                'slug': a.filename.replace('.md', '') if a.filename.endswith('.md') else a.filename,
            }
            for a in articles
        ]

    def _create_frontmatter(self, title: str, content: str) -> str:
        """Создать полный контент с frontmatter (для совместимости API)."""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].lstrip('\n')
        frontmatter = f"---\ntitle: {title}\n---\n\n"
        return frontmatter + content

    def get_article(self, section_id: str, filename: str) -> Optional[Dict]:
        """Получить содержимое статьи."""
        filename = _sanitize_filename(filename)
        article = (
            KBArticle.objects.filter(
                section__section_id=section_id,
                filename=filename,
            )
            .select_related('section')
            .first()
        )
        if not article:
            return None

        html_content = self.markdown_to_html(article.content)
        full_content = self._create_frontmatter(article.title, article.content)

        return {
            'filename': article.filename,
            'title': article.title,
            'markdown': article.content,
            'full_content': full_content,
            'html': html_content,
            'section_id': article.section.section_id,
        }

    def save_article(
        self,
        section_id: str,
        filename: str,
        content: str,
        title: Optional[str] = None,
    ) -> bool:
        """Сохранить или обновить статью."""
        filename = _sanitize_filename(filename)
        if not filename.endswith('.md'):
            filename = f"{filename}.md"

        section = KBSection.objects.filter(section_id=section_id).first()
        if not section:
            return False

        article, _ = KBArticle.objects.get_or_create(
            section=section,
            filename=filename,
            defaults={'title': title or filename.replace('.md', ''), 'content': content},
        )
        if not _:
            article.content = content
            if title is not None:
                article.title = title
            article.save()
        return True

    def create_article(self, section_id: str, title: str, content: str = '') -> str:
        """Создать новую статью."""
        section = KBSection.objects.filter(section_id=section_id).first()
        if not section:
            raise ValueError(f'Раздел с ID "{section_id}" не найден')

        slug = re.sub(r'[^\w\s\-]', '', title.lower())
        slug = re.sub(r'[\s]+', '-', slug).strip('-') or 'article'

        existing = (
            KBArticle.objects.filter(section=section)
            .values_list('filename', flat=True)
        )
        max_num = 0
        for f in existing:
            match = re.match(r'^(\d+)', f.replace('.md', ''))
            if match:
                max_num = max(max_num, int(match.group(1)))
        next_num = max_num + 1
        filename = f"{next_num:02d}-{slug}.md"

        if not content:
            content = f"*Документ создан: {self._get_current_date()}*\n"

        KBArticle.objects.create(
            section=section,
            filename=filename,
            title=title,
            content=content,
        )
        return filename

    def delete_article(self, section_id: str, filename: str) -> bool:
        """Удалить статью."""
        filename = _sanitize_filename(filename)
        deleted, _ = (
            KBArticle.objects.filter(
                section__section_id=section_id,
                filename=filename,
            ).delete()
        )
        return deleted > 0

    def markdown_to_html(self, md_content: str) -> str:
        """
        Конвертировать Markdown в HTML с санитизацией для защиты от XSS.
        Внешние ссылки открываются в новой вкладке, iframe ограничен whitelist-доменами.
        """

        class ExternalLinksExtension(Extension):
            def extendMarkdown(self, md):
                md.treeprocessors.register(ExternalLinksProcessor(md), 'externallinks', 15)

        class ExternalLinksProcessor(Treeprocessor):
            def run(self, root):
                for element in root.iter('a'):
                    href = element.get('href', '')
                    if href.startswith('http://') or href.startswith('https://'):
                        element.set('target', '_blank')
                        element.set('rel', 'noopener noreferrer')
                return root

        md = markdown.Markdown(
            extensions=MARKDOWN_EXTENSIONS + [ExternalLinksExtension()]
        )
        html = md.convert(md_content)
        clean_html = bleach.clean(
            html,
            tags=_BLEACH_ALLOWED_TAGS,
            attributes=_bleach_attribute_filter,
            protocols=_BLEACH_ALLOWED_PROTOCOLS,
            strip=True,
        )
        clean_html = bleach.linkify(
            clean_html,
            callbacks=[],
            skip_tags=['pre', 'code'],
        )
        return clean_html

    def search_articles(
        self,
        query: str,
        limit: int = _SEARCH_RESULTS_LIMIT,
    ) -> List[Dict]:
        """Поиск по статьям. Возвращает не более limit результатов."""
        if not query.strip():
            articles_qs = (
                KBArticle.objects.select_related('section')
                .filter(section__visible=True)[:limit]
            )
            return [
                {
                    'section_id': a.section.section_id,
                    'section_title': a.section.title,
                    'section_icon': a.section.icon or '📁',
                    'filename': a.filename,
                    'title': a.title,
                }
                for a in articles_qs
            ]

        query_lower = query.lower()
        articles_qs = (
            KBArticle.objects.select_related('section')
            .filter(section__visible=True)
            .annotate(
                title_lower=Lower('title'),
                content_lower=Lower('content'),
            )
            .filter(
                Q(title_lower__contains=query_lower) | Q(content_lower__contains=query_lower)
            )[:limit]
        )
        return [
            {
                'section_id': a.section.section_id,
                'section_title': a.section.title,
                'section_icon': a.section.icon or '📁',
                'filename': a.filename,
                'title': a.title,
            }
            for a in articles_qs
        ]

    @staticmethod
    def _get_current_date() -> str:
        """Получить текущую дату в формате 'месяц год'."""
        now = datetime.now()
        return f"{RUSSIAN_MONTHS[now.month]} {now.year}"

    def create_section(
        self,
        section_id: str,
        title: str,
        description: str = '',
        icon: str = '📁',
    ) -> bool:
        """Создать новый раздел."""
        if not re.match(SECTION_ID_PATTERN, section_id):
            raise ValueError('ID раздела может содержать только строчные буквы, цифры и дефис')

        if KBSection.objects.filter(section_id=section_id).exists():
            raise ValueError(f'Раздел с ID "{section_id}" уже существует')

        max_order = (
            KBSection.objects.aggregate(max_order=Max('order'))['max_order'] or 0
        )
        KBSection.objects.create(
            section_id=section_id,
            title=title,
            description=description,
            icon=icon,
            order=max_order + 1,
            visible=True,
        )
        return True

    def delete_section(self, section_id: str) -> bool:
        """Удалить раздел со всеми статьями."""
        section = KBSection.objects.filter(section_id=section_id).first()
        if not section:
            raise ValueError(f'Раздел с ID "{section_id}" не найден')
        section.delete()
        return True

    def update_section(
        self,
        section_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> bool:
        """Обновить метаданные раздела."""
        section = KBSection.objects.filter(section_id=section_id).first()
        if not section:
            raise ValueError(f'Раздел с ID "{section_id}" не найден')

        if title is not None:
            section.title = title
        if description is not None:
            section.description = description
        if icon is not None:
            section.icon = icon
        section.save()
        return True
