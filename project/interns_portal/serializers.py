from rest_framework import serializers

from core.intern_utils import transliterate_name_to_cyrillic
from core.s3_video_storage import resolve_video_play_url
from interviews.models import Interview


class InternPortalInterviewSerializer(serializers.ModelSerializer):
    """Строка таблицы портала."""

    intern_full_name = serializers.SerializerMethodField()
    interview_type_display = serializers.SerializerMethodField()

    def get_interview_type_display(self, obj):
        return obj.get_interview_type_display()

    direction_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    upload_action_state = serializers.CharField(read_only=True)
    upload_action_url = serializers.SerializerMethodField()
    video_link = serializers.SerializerMethodField()
    interview_display = serializers.SerializerMethodField()
    needs_student_video_upload = serializers.BooleanField(read_only=True)

    class Meta:
        model = Interview
        fields = [
            'id',
            'intern_full_name',
            'direction_name',
            'company_name',
            'interview_type_display',
            'date',
            'time',
            'vacancy_link',
            'video_link',
            'upload_task_id',
            'upload_action_state',
            'upload_action_url',
            'interview_display',
            'needs_student_video_upload',
        ]

    def get_intern_full_name(self, obj):
        raw = obj.intern.full_name if obj.intern_id else ''
        return transliterate_name_to_cyrillic(raw) or raw

    def get_direction_name(self, obj):
        return obj.direction.name if obj.direction_id else None

    def get_company_name(self, obj):
        return obj.company.name if obj.company_id else None

    def get_video_link(self, obj):
        return resolve_video_play_url(obj.video_link)

    def get_upload_action_url(self, obj):
        return resolve_video_play_url(obj.video_link)

    def get_interview_display(self, obj):
        url, label = obj.interview_display_url
        if url and obj.video_link:
            url = resolve_video_play_url(obj.video_link)
        return {'url': url, 'label': label}
