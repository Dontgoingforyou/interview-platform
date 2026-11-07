from rest_framework import serializers

from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    """
    Список и детали компании; запись полей name, is_bigtech, aliases.
    """

    aliases_list = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        source='get_aliases_list',
    )
    interviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'name', 'is_bigtech', 'aliases', 'aliases_list', 'interviews_count']
        read_only_fields = ['id', 'aliases_list']

    def get_interviews_count(self, obj):
        return getattr(obj, 'interviews_count', 0)


class CompanyMergeSerializer(serializers.Serializer):
    """Тело POST /api/companies/merge/."""

    primary_id = serializers.IntegerField()
    duplicate_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )

    def validate(self, attrs):
        primary_id = attrs['primary_id']
        dup_ids = attrs['duplicate_ids']
        if primary_id in dup_ids:
            raise serializers.ValidationError(
                {'duplicate_ids': 'Главная компания не может быть в списке дублей.'},
            )
        return attrs
