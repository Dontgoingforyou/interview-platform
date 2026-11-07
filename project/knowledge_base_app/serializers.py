from rest_framework import serializers

from .constants import (
    MAX_ARTICLE_TITLE_LENGTH,
    MAX_SECTION_DESCRIPTION_LENGTH,
    MAX_SECTION_ID_LENGTH,
    MAX_SECTION_TITLE_LENGTH,
)


class KBSectionReadSerializer(serializers.Serializer):
    """Раздел (список / деталь)."""

    id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    icon = serializers.CharField()
    order = serializers.IntegerField()
    article_count = serializers.IntegerField()


class KBSectionCreateSerializer(serializers.Serializer):
    """Создание раздела."""

    section_id = serializers.CharField(max_length=MAX_SECTION_ID_LENGTH)
    title = serializers.CharField(max_length=MAX_SECTION_TITLE_LENGTH)
    description = serializers.CharField(
        required=False, allow_blank=True, default='', max_length=MAX_SECTION_DESCRIPTION_LENGTH
    )
    icon = serializers.CharField(required=False, allow_blank=True, default='📁')


class KBSectionUpdateSerializer(serializers.Serializer):
    """Обновление раздела (частичное)."""

    title = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    icon = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class KBArticleListItemSerializer(serializers.Serializer):
    """Элемент списка статей в разделе."""

    filename = serializers.CharField()
    title = serializers.CharField()
    slug = serializers.CharField()


class KBArticleDetailSerializer(serializers.Serializer):
    """Детали статьи для просмотра / редактора."""

    filename = serializers.CharField()
    title = serializers.CharField()
    markdown = serializers.CharField()
    full_content = serializers.CharField()
    html = serializers.CharField()
    section_id = serializers.CharField()


class KBArticleCreateSerializer(serializers.Serializer):
    """Создание статьи."""

    title = serializers.CharField(max_length=MAX_ARTICLE_TITLE_LENGTH)
    content = serializers.CharField(required=False, allow_blank=True, default='')


class KBArticleUpdateSerializer(serializers.Serializer):
    """Обновление статьи."""

    title = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)


class KBSearchResultSerializer(serializers.Serializer):
    """Элемент результата полнотекстового поиска."""

    section_id = serializers.CharField()
    section_title = serializers.CharField()
    section_icon = serializers.CharField()
    filename = serializers.CharField()
    title = serializers.CharField()
