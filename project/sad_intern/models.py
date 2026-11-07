from django.db import models
from core.constants import (
    MAX_GROUP_LENGTH,
    MAX_TELEGRAM_LENGTH,
    SAD_INTERN_STATUS_ACCEPTED,
    SAD_INTERN_STATUS_FIRED,
    SAD_INTERN_STATUS_OFFERED,
    SAD_INTERN_STATUS_ON_PROJECT,
    SAD_INTERN_STATUS_REJECTED,
)
from core.mixins import ExternalReferencesMixin
from .managers import SadInternManager


NULLABLE = {'null': True, 'blank': True}


class SadIntern(ExternalReferencesMixin, models.Model):
    """
    Модель для отслеживания студентов, которые долго ждут собеседования или обратной связи.
    """

    STATUS_CHOICES = [
        (SAD_INTERN_STATUS_REJECTED, 'Отказ'),
        (SAD_INTERN_STATUS_ACCEPTED, 'Взяли'),
        (SAD_INTERN_STATUS_OFFERED, 'Предложили'),
        (SAD_INTERN_STATUS_FIRED, 'Уволили'),
        (SAD_INTERN_STATUS_ON_PROJECT, 'Вышел на проект'),
    ]

    intern = models.ForeignKey(
        'interns.Intern',
        on_delete=models.CASCADE,
        verbose_name='Студент',
        related_name='sad_periods',
        db_index=True,
    )
    date_added = models.DateField(auto_now_add=True, verbose_name='Дата добавления в список грустящих')
    waiting_since = models.DateField(
        verbose_name='Ждет с',
        help_text="Дата выхода на собеседования (real_interview_date). Показывает, сколько дней студент у нас."
    )
    days_waiting = models.PositiveIntegerField(verbose_name='Дней с нами', editable=False, db_index=True)
    telegram_username = models.CharField(max_length=MAX_TELEGRAM_LENGTH, verbose_name='@tg', **NULLABLE)
    manager_email = models.EmailField(verbose_name='Email менеджера', db_index=True, **NULLABLE)
    status = models.CharField(
        max_length=MAX_GROUP_LENGTH, verbose_name='Статус', db_index=True, choices=STATUS_CHOICES, **NULLABLE
    )
    note = models.TextField(verbose_name='Примечание', **NULLABLE)

    class Meta:
        db_table = 'sad_interns'
        ordering = ['-days_waiting']
        verbose_name = 'Грустящий студент'
        verbose_name_plural = 'Грустящие студенты'

    def __str__(self):
        return f'{self.intern.full_name} - {self.days_waiting} дней в ожидании'

    def save(self, *args, **kwargs):
        """Пересчёт days_waiting по waiting_since. Статус on_project задаётся вручную (форма, API, импорт)."""
        from django.utils import timezone
        today = timezone.now().date()
        if self.waiting_since:
            days_diff = (today - self.waiting_since).days
            # Защита от отрицательных значений (если waiting_since в будущем)
            self.days_waiting = max(0, days_diff)
        else:
            self.days_waiting = 0

        super().save(*args, **kwargs)

    objects = SadInternManager()
