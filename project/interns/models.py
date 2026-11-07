from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone

from core.constants import (
    INTERN_INACTIVE_STATUSES,
    INTERN_STATUS_ACTIVE,
    INTERN_STATUS_LEFT,
    INTERN_STATUS_OFFER,
    INTERN_TRAINING_EXTERNAL,
    INTERN_TRAINING_EXTERNAL_OR_OUTSTAFF,
    INTERN_TRAINING_INTERNAL,
    INTERN_TRAINING_OUTSTAFF,
    MAX_GROUP_LENGTH,
    MAX_NAME_LENGTH,
    MAX_TELEGRAM_LENGTH,
)
from core.mixins import ExternalReferencesMixin
from core.validators import validate_date_of_birth

NULLABLE = {'blank': True, 'null': True}


class Intern(ExternalReferencesMixin, models.Model):
    """
    Таблица студентов.

    Менеджеры:
    - manager_email: email менеджера из таблицы managers
    """

    TYPE_OF_TRAINING = [
        (INTERN_TRAINING_INTERNAL, 'Внутреннее обучение'),
        (INTERN_TRAINING_OUTSTAFF, 'Аутстафф'),
        (INTERN_TRAINING_EXTERNAL, 'Во вне'),
        (INTERN_TRAINING_EXTERNAL_OR_OUTSTAFF, 'Во вне / аутстафф'),
    ]

    STATUS_CHOICES = [
        (INTERN_STATUS_ACTIVE, 'Активный'),
        (INTERN_STATUS_LEFT, 'Ушёл'),
        (INTERN_STATUS_OFFER, 'Оффер'),
    ]

    manager_email = models.EmailField(verbose_name='Email менеджера', db_index=True, **NULLABLE)
    full_name = models.CharField(max_length=MAX_NAME_LENGTH, verbose_name='Имя')
    email = models.EmailField(**NULLABLE)
    corporate_email = models.EmailField(
        verbose_name='Почта входа на портал',
        db_index=True,
        **NULLABLE,
        help_text='Заполняется при первой привязке по ФИО и используется для входа на портал.',
    )
    telegram_username = models.CharField(max_length=MAX_TELEGRAM_LENGTH, verbose_name='@tg', **NULLABLE)
    direction = models.ForeignKey(
        'directions.Direction',
        on_delete=models.PROTECT,
        verbose_name='Направление',
        db_index=True,
        related_name='interns',
    )
    city = models.CharField(max_length=MAX_NAME_LENGTH, verbose_name='Город', **NULLABLE)
    cv = models.URLField(max_length=500, verbose_name='Ссылка на резюме', **NULLABLE)
    date_of_receipt = models.DateField(verbose_name='Дата приемки студента', **NULLABLE)
    date_of_birth = models.DateField(verbose_name='Дата рождения', validators=[validate_date_of_birth], **NULLABLE)
    hiring_hr = models.CharField(max_length=MAX_NAME_LENGTH, verbose_name='Нанимающий HR')
    responsible_hr = models.CharField(max_length=MAX_NAME_LENGTH, verbose_name='Ответственный HR')
    group = models.CharField(max_length=MAX_GROUP_LENGTH, verbose_name='Имя группы')
    type_of_training = models.CharField(
        max_length=MAX_TELEGRAM_LENGTH, verbose_name='Тип обучения', choices=TYPE_OF_TRAINING
    )
    legend = models.URLField(max_length=500, verbose_name='Ссылка на легенду', **NULLABLE)
    hr_feedback = models.TextField(verbose_name='Отзыв HR после оценки кандидата', **NULLABLE)
    mentor_feedback = models.TextField(verbose_name='Отзыв ментора после экзамена', **NULLABLE)
    real_interview_date = models.DateField(verbose_name='Дата выхода на реальные собеседования', **NULLABLE)
    manual_status = models.CharField(
        max_length=MAX_GROUP_LENGTH, verbose_name='Статус (ручной)', choices=STATUS_CHOICES, db_index=True, **NULLABLE
    )
    inactive_since = models.DateTimeField(verbose_name='Дата перехода в неактивный статус', **NULLABLE)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата обновления', auto_now=True)

    class Meta:
        db_table = 'interns'
        ordering = ['-date_of_receipt']
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'
        indexes = [
            models.Index(fields=['manager_email', 'manual_status'], name='interns_mgr_status_idx'),
            GinIndex(fields=['full_name'], name='interns_full_name_trgm_idx', opclasses=['gin_trgm_ops']),
        ]

    def __str__(self):
        return f'{self.full_name} ({self.group})'

    @property
    def status(self):
        """Возвращает статус студента. Если статус не задан явно, возвращает INTERN_STATUS_ACTIVE по умолчанию."""
        return self.manual_status if self.manual_status else INTERN_STATUS_ACTIVE

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, 'Активный')

    @property
    def type_of_training_display(self):
        """Человекочитаемое отображение типа обучения для шаблонов и API."""
        if not self.type_of_training:
            return None
        return dict(self.TYPE_OF_TRAINING).get(self.type_of_training, self.type_of_training)

    def save(self, *args, **kwargs):
        if self.manual_status in INTERN_INACTIVE_STATUSES:
            if not self.pk:
                self.inactive_since = timezone.now()
            else:
                prev = Intern.objects.filter(pk=self.pk).values_list('manual_status', flat=True).first()
                if prev is None or prev not in INTERN_INACTIVE_STATUSES:
                    self.inactive_since = timezone.now()
        else:
            self.inactive_since = None
        super().save(*args, **kwargs)
