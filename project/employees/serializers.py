"""
Сериализаторы для API приложения employees.
"""
from rest_framework import serializers
from .models import InternWeeklyStatus


class InternWeeklyStatusSerializer(serializers.ModelSerializer):
    """
    Сериализатор недельного статуса студента.
    Используется в GET/POST/PATCH /api/employees/weekly-statuses/.
    """
    intern_name = serializers.CharField(source='intern.full_name', read_only=True)

    class Meta:
        model = InternWeeklyStatus
        fields = [
            'id',
            'intern',
            'intern_name',
            'week_start',
            'manual_interview_count',
            'absence_status',
            'absence_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InternWeeklyStatusCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления недельного статуса.
    """

    class Meta:
        model = InternWeeklyStatus
        fields = [
            'intern',
            'week_start',
            'manual_interview_count',
            'absence_status',
            'absence_notes',
        ]

    def validate(self, attrs):
        if 'manual_interview_count' in attrs:
            request = self.context.get('request')
            user = getattr(request, 'user', None) if request else None
            if not user or not getattr(user, 'is_authenticated', False):
                raise serializers.ValidationError({'manual_interview_count': 'Требуется аутентификация.'})
            if not (getattr(user, 'is_admin', False) or getattr(user, 'is_superuser', False)):
                raise serializers.ValidationError({
                    'manual_interview_count': (
                        'Ручное количество собеседований может задавать только администратор.'
                    ),
                })
        return attrs
