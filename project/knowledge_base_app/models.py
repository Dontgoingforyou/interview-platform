"""
Модели базы знаний: разделы и статьи хранятся в БД.
"""
from django.db import models

from .constants import (
    MAX_ARTICLE_TITLE_LENGTH,
    MAX_FILENAME_LENGTH,
    MAX_SECTION_ID_LENGTH,
    MAX_SECTION_TITLE_LENGTH,
)


class KBSection(models.Model):
    """Раздел базы знаний."""

    section_id = models.CharField(
        'ID раздела', max_length=MAX_SECTION_ID_LENGTH, unique=True
    )
    title = models.CharField('Название', max_length=MAX_SECTION_TITLE_LENGTH)
    description = models.TextField('Описание', blank=True)
    icon = models.CharField('Иконка', max_length=20, default='📄')
    order = models.PositiveIntegerField('Порядок', default=0)
    visible = models.BooleanField('Отображать', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)

    class Meta:
        db_table = 'knowledge_base_sections'
        ordering = ['order', 'section_id']
        verbose_name = 'Раздел базы знаний'
        verbose_name_plural = 'Разделы базы знаний'

    def __str__(self):
        return f'{self.section_id}: {self.title}'


class KBArticle(models.Model):
    """Статья базы знаний (Markdown)."""

    section = models.ForeignKey(
        KBSection,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='Раздел',
        db_index=True,
    )
    filename = models.CharField('Имя файла', max_length=MAX_FILENAME_LENGTH)
    title = models.CharField('Заголовок', max_length=MAX_ARTICLE_TITLE_LENGTH)
    content = models.TextField('Содержимое (Markdown)', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)

    class Meta:
        db_table = 'knowledge_base_articles'
        ordering = ['filename']
        constraints = [
            models.UniqueConstraint(
                fields=['section', 'filename'],
                name='knowledge_base_articles_section_filename_uniq',
            ),
        ]
        verbose_name = 'Статья базы знаний'
        verbose_name_plural = 'Статьи базы знаний'

    def __str__(self):
        return f'{self.section.section_id}/{self.filename}: {self.title}'
