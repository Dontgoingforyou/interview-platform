from rest_framework import serializers
from vector_search.models import VectorEmbedding, SearchLog
from vector_search.utils import VECTOR_ENTITY_TYPES


class SemanticSearchRequestSerializer(serializers.Serializer):
    """Сериализатор запроса для семантического поиска."""

    query = serializers.CharField(
        required=True,
        help_text='Поисковый запрос на естественном языке'
    )

    entity_type = serializers.ChoiceField(
        choices=list(VECTOR_ENTITY_TYPES),
        required=False,
        allow_null=True,
        help_text='Фильтр по типу сущности'
    )

    top_k = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        help_text='Количество результатов (по умолчанию: 10)'
    )

    min_score = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=1.0,
        help_text='Минимальный score схожести (по умолчанию: 0.3)'
    )

    # Фильтры по метаданным
    direction_id = serializers.IntegerField(required=False, allow_null=True)
    manager_email = serializers.EmailField(required=False, allow_null=True)
    interview_type = serializers.CharField(required=False, allow_null=True)
    status = serializers.CharField(required=False, allow_null=True)


class SemanticSearchResultSerializer(serializers.Serializer):
    """Сериализатор результата семантического поиска."""

    entity_type = serializers.CharField()
    entity_id = serializers.IntegerField()
    text_content = serializers.CharField()
    similarity_score = serializers.FloatField()
    metadata = serializers.JSONField()


class SemanticSearchResponseSerializer(serializers.Serializer):
    """Сериализатор ответа семантического поиска."""

    query = serializers.CharField()
    results = SemanticSearchResultSerializer(many=True)
    total_found = serializers.IntegerField()
    search_time_ms = serializers.FloatField()


class SimilarEntitiesRequestSerializer(serializers.Serializer):
    """Сериализатор запроса для поиска похожих сущностей."""

    entity_type = serializers.ChoiceField(
        choices=list(VECTOR_ENTITY_TYPES),
        required=True,
        help_text='Тип сущности'
    )

    entity_id = serializers.IntegerField(
        required=True,
        help_text='ID сущности'
    )

    top_k = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=50,
        default=5,
        help_text='Количество похожих результатов'
    )


class VectorEmbeddingSerializer(serializers.ModelSerializer):
    """Сериализатор для модели VectorEmbedding."""

    entity_id = serializers.CharField()

    class Meta:
        model = VectorEmbedding
        fields = [
            'id',
            'entity_type',
            'entity_id',
            'text_content',
            'metadata',
            'created_at',
            'updated_at'
        ]
        # Не показываем сам вектор (слишком большой)


class SearchLogSerializer(serializers.ModelSerializer):
    """Сериализатор для логов поиска."""

    class Meta:
        model = SearchLog
        fields = '__all__'
