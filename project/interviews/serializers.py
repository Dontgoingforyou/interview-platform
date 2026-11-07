"""
Сериализаторы для API Interview приложения.
"""
import logging

from rest_framework import serializers

from companies.models import Company
from directions.models import Direction
from core.intern_utils import transliterate_name_to_cyrillic
from core.s3_video_storage import resolve_video_play_url
from core.validators import normalize_telegram_username, validate_hr_contacts_telegram
from managers.models import Manager
from transcriptions.models import InterviewTranscription, TranscriptionStatus

from .models import Interview
from .utils import get_or_create_company

logger = logging.getLogger(__name__)


class InterviewListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения списка собеседований.
    Возвращает: id, компания, дата, тип, направление, tg_account, ссылка на видео.
    """
    company = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()
    interview_type = serializers.CharField(source='get_interview_type_display')
    tg_account = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = [
            'id', 'company', 'date', 'interview_type', 'direction', 'tg_account', 'link',
            'interview_format',
        ]

    def get_company(self, obj):
        """Получает название компании."""
        if obj.company:
            return obj.company.name
        return None

    def get_direction(self, obj):
        """Получает название направления."""
        if obj.direction:
            return obj.direction.name
        return None

    def get_tg_account(self, obj):
        """Получает telegram аккаунт из связанного Intern."""
        try:
            if obj.intern and obj.intern.telegram_username:
                return obj.intern.telegram_username
        except Exception as e:
            logger.warning('Не удалось получить telegram из intern для interview id=%s: %s', obj.pk, e)
        return None


class InterviewFullListSerializer(serializers.ListSerializer):
    """Пакетная подстановка имён менеджеров без N+1."""

    def to_representation(self, data):
        rows = list(data)
        emails = {
            obj.manager_email
            for obj in rows
            if getattr(obj, 'manager_email', None)
        }
        display_map: dict[str, str] = {}
        if emails:
            for m in Manager.objects.filter(email__in=emails).only('email', 'full_name'):
                raw = m.full_name or ''
                display_map[m.email] = transliterate_name_to_cyrillic(raw) or raw
        self.child._manager_display_map = display_map
        return [self.child.to_representation(item) for item in rows]


class InterviewFullSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор собеседования.
    Используется в GET /api/interviews/{id}/ и общем списке.
    Поле has_video — загруженная запись (непустой video_link), не путать с link (ссылка на созвон).
    """
    intern_name = serializers.CharField(source='intern.full_name', read_only=True)
    interview_type_display = serializers.CharField(source='get_interview_type_display', read_only=True)
    interview_format_display = serializers.CharField(source='get_interview_format_display', read_only=True)
    direction_id = serializers.IntegerField(read_only=True)
    direction_name = serializers.SerializerMethodField(read_only=True)
    company_id = serializers.IntegerField(read_only=True)
    company_name = serializers.SerializerMethodField(read_only=True)
    manager_display_name = serializers.SerializerMethodField(read_only=True)
    has_video = serializers.SerializerMethodField(read_only=True)
    video_link = serializers.SerializerMethodField(read_only=True)
    transcription_media_url = serializers.SerializerMethodField(read_only=True)
    transcription_status = serializers.SerializerMethodField(read_only=True)
    transcription_error_message = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Interview
        list_serializer_class = InterviewFullListSerializer
        fields = [
            'id',
            'intern',
            'intern_name',
            'direction_id',
            'direction_name',
            'company_id',
            'company_name',
            'manager_email',
            'manager_display_name',
            'interview_type',
            'interview_type_display',
            'interview_format',
            'interview_format_display',
            'date',
            'time',
            'link',
            'vacancy_link',
            'interview_link',
            'video_link',
            'upload_task_id',
            'has_video',
            'transcription_media_url',
            'transcription_status',
            'transcription_error_message',
            'hr_name',
            'hr_contacts',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'upload_task_id', 'created_at', 'updated_at']

    def get_company_name(self, obj):
        """Название компании для списков и карточек."""
        if obj.company:
            return obj.company.name
        return None

    def get_direction_name(self, obj):
        """Название направления для списков и карточек."""
        if obj.direction:
            return obj.direction.name
        return None

    def get_manager_display_name(self, obj):
        """Имя менеджера для таблицы (как в Django list: кириллица из справочника)."""
        email = getattr(obj, 'manager_email', None)
        if not email:
            return None
        cache = getattr(self, '_manager_display_map', None)
        if cache is not None and email in cache:
            return cache[email]
        try:
            m = Manager.objects.only('full_name', 'email').get(email=email)
        except Manager.DoesNotExist:
            return email
        raw = m.full_name or ''
        return transliterate_name_to_cyrillic(raw) or raw

    def get_has_video(self, obj):
        """True, если в БД сохранена непустая ссылка на загруженную запись (video_link)."""
        if not obj.video_link:
            return False
        return bool(obj.video_link.strip())

    def get_video_link(self, obj):
        """Ссылка на просмотр записи (presigned для S3)."""
        return resolve_video_play_url(obj.video_link)

    def get_transcription_media_url(self, obj):
        """URL медиа для транскрибации и кнопки «Смотреть запись» в SPA."""
        raw = obj.transcription_media_url
        return resolve_video_play_url(raw) if raw else None

    def get_transcription_status(self, obj):
        """Статус транскрипции для SPA: none, если записи нет."""
        try:
            return obj.transcription.status
        except InterviewTranscription.DoesNotExist:
            return 'none'

    def get_transcription_error_message(self, obj):
        """Текст ошибки Celery при status=failed — для подсказки и тоста в SPA."""
        try:
            row = obj.transcription
        except InterviewTranscription.DoesNotExist:
            return ''
        if row.status != TranscriptionStatus.FAILED:
            return ''
        return row.error_message or ''


class InterviewCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления собеседования.
    """

    direction_id = serializers.PrimaryKeyRelatedField(
        source='direction',
        queryset=Direction.objects.all(),
    )
    company_id = serializers.PrimaryKeyRelatedField(
        source='company',
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
    )
    company_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        help_text='Название новой или существующей компании (если нет company_id). Создаёт запись через get_or_create.',
    )

    class Meta:
        model = Interview
        fields = [
            'intern',
            'direction_id',
            'company_id',
            'company_name',
            'manager_email',
            'interview_type',
            'interview_format',
            'date',
            'time',
            'link',
            'vacancy_link',
            'interview_link',
            'hr_name',
            'hr_contacts',
        ]

    def validate_hr_contacts(self, value):
        if not value:
            return value
        value = value.strip()
        if value.startswith('@') or 't.me/' in value:
            validate_hr_contacts_telegram(value)
            return normalize_telegram_username(value) or value
        return value

    def validate(self, attrs):
        """
        Связывает company_id и company_name: приоритет у явного company_id.
        При необходимости создаёт компанию по имени через get_or_create_company (utils).
        """
        company_name_in = attrs.pop('company_name', None)

        if 'company' in attrs:
            company = attrs.pop('company')
            if company is not None:
                attrs['company'] = company
            elif company_name_in and str(company_name_in).strip():
                try:
                    cid = get_or_create_company(str(company_name_in).strip())
                except Exception as exc:
                    logger.exception('Ошибка при создании компании из company_name')
                    raise serializers.ValidationError(
                        {'company_name': f"Не удалось создать компанию: {exc}"},
                    ) from exc
                attrs['company'] = Company.objects.filter(pk=cid).first() if cid else None
            else:
                attrs['company'] = None
        elif company_name_in is not None:
            stripped = str(company_name_in).strip()
            if stripped:
                try:
                    cid = get_or_create_company(stripped)
                except Exception as exc:
                    logger.exception('Ошибка при создании компании из company_name')
                    raise serializers.ValidationError(
                        {'company_name': f"Не удалось создать компанию: {exc}"},
                    ) from exc
                attrs['company'] = Company.objects.filter(pk=cid).first() if cid else None
            else:
                attrs['company'] = None

        return attrs
