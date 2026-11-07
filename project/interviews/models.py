from urllib.parse import urlparse

from django.contrib.postgres.indexes import GinIndex
from django.db import models

from core.constants import (
    MAX_LONG_URL_LENGTH,
    MAX_NAME_LENGTH,
    MAX_GROUP_LENGTH,
    MAX_TELEGRAM_LENGTH,
    INTERVIEW_TYPE_SCREENING,
    INTERVIEW_TYPE_TECH,
    INTERVIEW_TYPE_HR,
    INTERVIEW_TYPE_FINAL,
    INTERVIEW_TYPE_MOCK,
    INTERVIEW_TYPE_TEST,
    INTERVIEW_TYPE_TECH_QUESTIONNAIRE,
    INTERVIEW_TYPE_CANCELLED,
    INTERVIEW_FORMAT_CHOICES,
    INTERVIEW_FORMAT_ONLINE,
    INTERVIEW_FORMAT_OFFICE,
    INTERVIEW_FORMAT_PHONE,
)
from core.mixins import ExternalReferencesMixin
from core.validators import validate_hr_contacts_telegram

NULLABLE = {'blank': True, 'null': True}

# Хосты публичных ссылок на файлы Яндекс.Диска / Яндекс 360 (транскрипция, публичные шары)
_YANDEX_DISK_PUBLIC_HOSTS = frozenset({
    'disk.yandex.ru',
    'disk.yandex.com',
    'disk.yandex.kz',
    'yadi.sk',
    'disk.360.yandex.ru',
})


def is_yandex_disk_public_file_url(url: str | None) -> bool:
    """
    True, если URL похож на публичную ссылку на файл/папку Яндекс.Диска для API.
    """
    if not url or not isinstance(url, str):
        return False
    s = url.strip()
    if not s.lower().startswith(('http://', 'https://')):
        return False
    try:
        parsed = urlparse(s)
    except ValueError:
        return False
    host = (parsed.netloc or '').lower()
    if ':' in host:
        host = host.split(':', 1)[0]
    # Не использовать host.endswith('.360.yandex.ru'): туда попадает telemost.360.yandex.ru
    # (комната Телемоста, не файл на Диске).
    if (
        host not in _YANDEX_DISK_PUBLIC_HOSTS
        and not host.endswith('.disk.yandex.ru')
    ):
        return False
    path = (parsed.path or '').strip('/')
    if not path:
        return False
    first = path.split('/', 1)[0].lower()
    if first in ('client', 'showcaptcha'):
        return False
    return True


# Поля Interview, при изменении которых может появиться или смениться URL для транскрипции
INTERVIEW_TRANSCRIPTION_URL_FIELDS = frozenset({'video_link', 'link', 'interview_link'})


class Interview(ExternalReferencesMixin, models.Model):
    """
    Основная таблица управления собеседованиями.

    Менеджеры:
    - manager_email: email менеджера из таблицы managers
    """

    INTERVIEW_TYPES = [
        (INTERVIEW_TYPE_SCREENING, 'Скрининг'),
        (INTERVIEW_TYPE_TECH, 'Техническое собеседование'),
        (INTERVIEW_TYPE_HR, 'HR собеседование'),
        (INTERVIEW_TYPE_FINAL, 'Финальное собеседование'),
        (INTERVIEW_TYPE_MOCK, 'МОК собеседование'),
        (INTERVIEW_TYPE_TEST, 'Тестовое задание'),
        (INTERVIEW_TYPE_TECH_QUESTIONNAIRE, 'Анкета с большим кол-вом технички'),
        (INTERVIEW_TYPE_CANCELLED, 'НЕ СОСТОЯЛОСЬ'),
    ]

    intern = models.ForeignKey(
        'interns.Intern',
        on_delete=models.CASCADE,
        verbose_name='Студент',
        related_name='interviews',
        db_index=True,
    )
    direction = models.ForeignKey(
        'directions.Direction',
        on_delete=models.PROTECT,
        verbose_name='Направление',
        db_index=True,
        related_name='interviews_by_direction',
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.PROTECT,
        verbose_name='Компания',
        db_index=True,
        **NULLABLE,
    )
    manager_email = models.EmailField(verbose_name='Email менеджера', db_index=True, **NULLABLE)
    interview_type = models.CharField(
        max_length=MAX_TELEGRAM_LENGTH,
        choices=INTERVIEW_TYPES,
        verbose_name='Тип интервью',
        db_index=True,
    )
    interview_format = models.CharField(
        max_length=MAX_GROUP_LENGTH,
        choices=INTERVIEW_FORMAT_CHOICES,
        default=INTERVIEW_FORMAT_ONLINE,
        verbose_name='Формат собеседования',
        db_index=True,
    )
    date = models.DateField(verbose_name='Дата интервью', db_index=True, **NULLABLE)
    time = models.TimeField(verbose_name='Время интервью', **NULLABLE)
    link = models.URLField(verbose_name='Ссылка на созвон', **NULLABLE, max_length=MAX_LONG_URL_LENGTH)
    vacancy_link = models.CharField(
        verbose_name='Ссылка на вакансию', max_length=MAX_LONG_URL_LENGTH, **NULLABLE
    )
    interview_link = models.URLField(
        verbose_name='Ссылка на собеседование', **NULLABLE, max_length=MAX_LONG_URL_LENGTH
    )
    video_link = models.URLField(
        verbose_name='Ссылка на видео', **NULLABLE, max_length=MAX_LONG_URL_LENGTH
    )
    upload_task_id = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name='ID задачи загрузки видео (Celery)',
        **NULLABLE,
        db_index=True,
    )
    hr_name = models.CharField(max_length=MAX_NAME_LENGTH, verbose_name='Имя HR', **NULLABLE)
    hr_contacts = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name='Контакты HR',
        validators=[validate_hr_contacts_telegram],
        **NULLABLE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'interviews'
        ordering = ['-date', '-time']
        verbose_name = 'Собеседование'
        verbose_name_plural = 'Собеседования'
        indexes = [
            models.Index(fields=['intern', 'date'], name='interviews_intern_date_idx'),
            GinIndex(fields=['hr_name'], name='interviews_hr_name_trgm_idx', opclasses=['gin_trgm_ops']),
        ]

    def __str__(self):
        return f'{self.intern.full_name} - {self.get_interview_type_display()}'

    @property
    def interview_display_url(self):
        """
        Возвращает (url, label) для колонки «Собеседование» в портале студента.
        Только загруженная запись (video_link); созвон (link) сюда не подставляется.
        Для офиса/телефона — подпись формата.
        """
        if self.video_link:
            return (self.video_link, 'Видео')
        if self.interview_format == INTERVIEW_FORMAT_OFFICE:
            return (None, 'Офис')
        if self.interview_format == INTERVIEW_FORMAT_PHONE:
            return (None, 'Телефонный звонок')
        return (None, None)

    @property
    def upload_action_state(self):
        """
        Состояние для колонки «Статус загрузки» в портале студента.
        Возвращает: 'video' | 'uploading' | 'office' | 'phone' | 'none'.
        """
        if self.video_link:
            return 'video'
        if self.upload_task_id:
            return 'uploading'
        if self.interview_format == INTERVIEW_FORMAT_OFFICE:
            return 'office'
        if self.interview_format == INTERVIEW_FORMAT_PHONE:
            return 'phone'
        return 'none'

    @property
    def needs_student_video_upload(self):
        """True, если студенту нужно загрузить запись (только онлайн, без записи и без активной загрузки)."""
        if self.video_link:
            return False
        if self.upload_task_id:
            return False
        return self.interview_format == INTERVIEW_FORMAT_ONLINE

    @property
    def upload_action_url(self):
        """URL для кнопки «Смотреть запись» (presigned для S3, иначе как в БД)."""
        from core.s3_video_storage import resolve_video_play_url

        return resolve_video_play_url(self.video_link)

    @property
    def is_link_url(self):
        """True, если link выглядит как URL (начинается с http). Для отображения в шаблоне."""
        return bool(self.link and self.link.strip().lower().startswith('http'))

    @property
    def is_vacancy_url(self):
        """True, если vacancy_link выглядит как URL (начинается с http). Для отображения в шаблоне."""
        return bool(self.vacancy_link and self.vacancy_link.strip().lower().startswith('http'))

    @property
    def vacancy_link_is_url(self):
        """True, если vacancy_link выглядит как URL (начинается с http). Для отображения в шаблоне."""
        return self.is_vacancy_url

    @property
    def transcription_status(self):
        """Возвращает статус транскрипции или None, если транскрипции нет."""
        from transcriptions.models import InterviewTranscription
        try:
            return self.transcription.status
        except InterviewTranscription.DoesNotExist:
            return None

    @property
    def transcription_media_url(self) -> str | None:
        """
        URL медиафайла для транскрипции (Deepgram + публичная ссылка Яндекс.Диска).
        Приоритет: video_link → link (если Яндекс.Диск) → interview_link (если Яндекс.Диск).
        """
        if self.video_link:
            return self.video_link.strip()
        if self.link and is_yandex_disk_public_file_url(self.link):
            return self.link.strip()
        if self.interview_link and is_yandex_disk_public_file_url(self.interview_link):
            return self.interview_link.strip()
        return None

    @property
    def show_transcription_controls(self) -> bool:
        """
        Показывать UI транскрипции в таблицах: есть источник медиа для запуска
        или уже есть запись InterviewTranscription (просмотр готового текста, статус, повтор).
        """
        if self.transcription_media_url:
            return True
        return self.transcription_status is not None
