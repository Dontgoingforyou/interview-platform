from rest_framework import serializers


class DeveloperStatSerializer(serializers.Serializer):
    """Сериализатор для статистики по разработчику."""

    intern_id = serializers.IntegerField()
    intern_name = serializers.CharField()
    direction_id = serializers.IntegerField(allow_null=True)
    interview_count = serializers.IntegerField()
    first_interview_date = serializers.DateField(allow_null=True)
    last_interview_date = serializers.DateField(allow_null=True)
    id = serializers.IntegerField(source='intern_id')
    full_name = serializers.CharField(source='intern_name')
    direction_name = serializers.CharField(allow_null=True)
    email = serializers.EmailField(allow_null=True, required=False)
