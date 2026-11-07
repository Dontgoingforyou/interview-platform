from django.utils import timezone
from rest_framework import serializers

from core.intern_utils import transliterate_name_to_cyrillic
from core.validators import normalize_telegram_username, validate_telegram_username
from interns.models import Intern
from .models import SadIntern


class SadInternListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка «грустящих» (таблица, группировка, on_project).
    """

    intern_name = serializers.CharField(source='intern.full_name', read_only=True)
    real_interview_date = serializers.DateField(source='intern.real_interview_date', read_only=True, allow_null=True)
    direction_id = serializers.IntegerField(source='intern.direction_id', read_only=True, allow_null=True)
    direction_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    intern_manager_name = serializers.SerializerMethodField()

    class Meta:
        model = SadIntern
        fields = [
            'id',
            'intern',
            'intern_name',
            'real_interview_date',
            'direction_id',
            'direction_name',
            'date_added',
            'waiting_since',
            'days_waiting',
            'telegram_username',
            'manager_email',
            'intern_manager_name',
            'status',
            'status_display',
            'note',
        ]
        read_only_fields = ['id', 'date_added', 'days_waiting']

    def get_direction_name(self, obj):
        if obj.intern and obj.intern.direction_id:
            if hasattr(obj.intern, 'direction') and obj.intern.direction:
                return obj.intern.direction.name
        return None

    def get_status_display(self, obj):
        if obj.status:
            return obj.get_status_display()
        return None

    def get_intern_manager_name(self, obj):
        cache = self.context.get('intern_manager_display')
        email = obj.intern.manager_email if obj.intern else None
        if not email:
            return None
        if cache is not None:
            return cache.get(email)
        from managers.models import Manager

        try:
            m = Manager.objects.get(email=email, is_active=True)
        except Manager.DoesNotExist:
            return None
        raw = m.full_name or ''
        return transliterate_name_to_cyrillic(raw) or raw


class SadInternDetailSerializer(SadInternListSerializer):
    """Детали записи — те же поля, что в списке."""

    class Meta(SadInternListSerializer.Meta):
        pass


class SadInternCreateUpdateSerializer(serializers.ModelSerializer):
    """Создание и обновление с логикой, близкой к SadInternForm / before_save."""

    waiting_since = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = SadIntern
        fields = [
            'intern',
            'waiting_since',
            'telegram_username',
            'manager_email',
            'status',
            'note',
        ]

    def validate_telegram_username(self, value):
        if not value:
            return value
        value = normalize_telegram_username(value)
        validate_telegram_username(value)
        return value

    def validate_intern(self, value):
        if not isinstance(value, Intern):
            raise serializers.ValidationError('Некорректный студент.')
        return value

    def create(self, validated_data):
        intern = validated_data.pop('intern')
        user = self.context['request'].user
        waiting_since = validated_data.pop('waiting_since', None)
        telegram_username = validated_data.pop('telegram_username', None)
        manager_email = validated_data.pop('manager_email', None)
        status = validated_data.pop('status', None)
        note = validated_data.pop('note', None)

        instance = SadIntern(
            intern=intern,
            status=status,
            note=note,
        )
        if telegram_username:
            instance.telegram_username = telegram_username
        elif intern.telegram_username:
            instance.telegram_username = intern.telegram_username

        if getattr(user, 'is_admin', False):
            if manager_email:
                instance.manager_email = manager_email
            else:
                instance.manager_email = getattr(user, 'email', None)
        else:
            instance.manager_email = getattr(user, 'email', None)

        if not instance.manager_email and intern.manager_email:
            instance.manager_email = intern.manager_email

        if waiting_since:
            instance.waiting_since = waiting_since
        elif intern.real_interview_date:
            instance.waiting_since = intern.real_interview_date
        else:
            instance.waiting_since = timezone.now().date()

        instance.save()
        return instance

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if not getattr(user, 'is_admin', False):
            validated_data.pop('manager_email', None)

        intern = validated_data.pop('intern', None)
        if intern is not None:
            instance.intern = intern
            if intern.real_interview_date:
                instance.waiting_since = intern.real_interview_date

        for attr in ('telegram_username', 'status', 'note', 'manager_email', 'waiting_since'):
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])

        instance.save()
        return instance
