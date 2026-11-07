"""
Сериализаторы для API приложения managers.
"""
from rest_framework import serializers

from core.intern_utils import transliterate_name_to_cyrillic
from .models import Manager


class ManagerListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка менеджеров.
    Используется в GET /api/managers/.
    """
    is_admin = serializers.BooleanField(read_only=True)
    is_employment_manager = serializers.BooleanField(read_only=True)
    is_cv_manager = serializers.BooleanField(read_only=True)
    is_education_manager = serializers.BooleanField(read_only=True)

    class Meta:
        model = Manager
        fields = [
            'email',
            'full_name',
            'username',
            'groups',
            'is_active',
            'is_admin',
            'is_employment_manager',
            'is_cv_manager',
            'is_education_manager',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['email', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        raw = instance.full_name or ''
        data['full_name'] = transliterate_name_to_cyrillic(raw) or raw
        return data


class ManagerForFilterSerializer(serializers.ModelSerializer):
    """Минимальный набор для выпадающего фильтра на странице собеседований."""

    class Meta:
        model = Manager
        fields = ['email', 'full_name']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        raw = instance.full_name or ''
        data['full_name'] = transliterate_name_to_cyrillic(raw) or raw
        return data


class ManagerUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления менеджера.
    Только администратор может менять is_active.
    """

    class Meta:
        model = Manager
        fields = ['full_name', 'username', 'is_active']
