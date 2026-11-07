"""
Сериализаторы для API приложения offers.
"""
from rest_framework import serializers
from directions.models import Direction
from .models import Offer


class OfferListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка офферов.
    Используется в GET /api/offers/.
    """
    intern_name = serializers.CharField(source='intern.full_name', read_only=True)
    intern_telegram_username = serializers.CharField(
        source='intern.telegram_username',
        read_only=True,
        allow_null=True,
    )
    direction_id = serializers.IntegerField(read_only=True)
    direction_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id',
            'intern',
            'intern_name',
            'intern_telegram_username',
            'direction_id',
            'direction_name',
            'company',
            'amount',
            'month',
            'year',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_direction_name(self, obj):
        """Название направления для списков и карточек."""
        if obj.direction:
            return obj.direction.name
        return None


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор оффера.
    Используется в GET /api/offers/{id}/.
    """
    intern_name = serializers.CharField(source='intern.full_name', read_only=True)
    intern_telegram_username = serializers.CharField(
        source='intern.telegram_username',
        read_only=True,
        allow_null=True,
    )
    direction_id = serializers.IntegerField(read_only=True)
    direction_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id',
            'intern',
            'intern_name',
            'intern_telegram_username',
            'direction_id',
            'direction_name',
            'company',
            'amount',
            'month',
            'year',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_direction_name(self, obj):
        """Название направления для списков и карточек."""
        if obj.direction:
            return obj.direction.name
        return None


class OfferCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления оффера.
    """
    direction_id = serializers.PrimaryKeyRelatedField(
        source='direction',
        queryset=Direction.objects.all(),
    )

    class Meta:
        model = Offer
        fields = [
            'intern',
            'direction_id',
            'company',
            'amount',
            'month',
            'year',
        ]
