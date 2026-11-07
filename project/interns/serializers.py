"""
Сериализаторы для API приложения interns.
"""
from rest_framework import serializers
from directions.models import Direction
from managers.models import Manager

from core.intern_utils import transliterate_name_to_cyrillic

from .models import Intern
from .validators import normalize_telegram_username, validate_telegram_username


def build_manager_display_map(emails: set[str]) -> dict[str, str]:
    """ФИО менеджеров для списка студентов (латиница → кириллица)."""
    if not emails:
        return {}
    out: dict[str, str] = {}
    for m in Manager.objects.filter(email__in=emails).only('email', 'full_name'):
        raw = m.full_name or ''
        out[m.email] = transliterate_name_to_cyrillic(raw) or raw
    return out


class InternListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка студентов (облегчённый).
    Используется в GET /api/interns/.
    """
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    direction_id = serializers.IntegerField(read_only=True)
    direction_name = serializers.SerializerMethodField(read_only=True)
    type_of_training_display = serializers.CharField(read_only=True)
    manager_display_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Intern
        fields = [
            'id',
            'full_name',
            'email',
            'telegram_username',
            'direction_id',
            'direction_name',
            'group',
            'city',
            'type_of_training',
            'type_of_training_display',
            'status',
            'status_display',
            'manual_status',
            'manager_email',
            'manager_display_name',
            'date_of_receipt',
            'date_of_birth',
            'hiring_hr',
            'responsible_hr',
            'real_interview_date',
            'cv',
            'legend',
        ]

    def get_direction_name(self, obj):
        """Название направления для списка."""
        if obj.direction:
            return obj.direction.name
        return None

    def get_manager_display_name(self, obj):
        if not obj.manager_email:
            return None
        m = self.context.get('manager_display_map') or {}
        return m.get(obj.manager_email)


class InternDetailSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор студента.
    Используется в GET /api/interns/{id}/.
    """
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    direction_id = serializers.IntegerField(read_only=True)
    direction_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Intern
        fields = [
            'id',
            'full_name',
            'email',
            'telegram_username',
            'direction_id',
            'direction_name',
            'city',
            'cv',
            'date_of_receipt',
            'date_of_birth',
            'hiring_hr',
            'responsible_hr',
            'group',
            'type_of_training',
            'legend',
            'hr_feedback',
            'mentor_feedback',
            'real_interview_date',
            'manual_status',
            'status',
            'status_display',
            'manager_email',
        ]

    def get_direction_name(self, obj):
        """Название направления для карточки."""
        if obj.direction:
            return obj.direction.name
        return None


class InternCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления студента.
    Используется в POST /api/interns/ и PATCH /api/interns/{id}/.
    """
    direction_id = serializers.PrimaryKeyRelatedField(
        source='direction',
        queryset=Direction.objects.all(),
    )

    class Meta:
        model = Intern
        fields = [
            'full_name',
            'email',
            'telegram_username',
            'direction_id',
            'city',
            'cv',
            'date_of_receipt',
            'date_of_birth',
            'hiring_hr',
            'responsible_hr',
            'group',
            'type_of_training',
            'legend',
            'hr_feedback',
            'mentor_feedback',
            'real_interview_date',
            'manual_status',
            'manager_email',
        ]

    def validate_telegram_username(self, value):
        if not value:
            return value
        value = normalize_telegram_username(value)
        validate_telegram_username(value)
        return value

    def validate_manager_email(self, value):
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        if user and not getattr(user, 'is_superuser', False) and not getattr(user, 'is_admin', False):
            value = getattr(user, 'email', None) or ''
            if not value:
                raise serializers.ValidationError(
                    'Не удалось определить email менеджера для назначения студента.'
                )
        if not value:
            return value
        if not Manager.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError(
                f'Менеджер с email "{value}" не найден или неактивен.'
            )
        return value
