from rest_framework import serializers
from .models import Direction


class DirectionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка и деталей направления.
    Используется в GET /api/directions/ и GET /api/directions/<id>/.
    """

    class Meta:
        model = Direction
        fields = ['id', 'name']
        read_only_fields = ['id']
