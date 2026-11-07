from django.db import models
from interns.models import Intern

NULLABLE = {'blank': True, 'null': True}


class InternWeeklyStatus(models.Model):
    """
    Хранит дополнительную информацию о статусе студента на конкретной неделе:
    - Ручные корректировки количества собеседований
    - Статусы отсутствия
    """

    ABSENCE_STATUS_CHOICES = [
        ('болеет', 'Болеет'),
        ('отпуск', 'Отпуск'),
        ('уехал', 'Уехал'),
        ('другое', 'Другое'),
    ]
    ABSENCE_STATUS_VALUES = [choice[0] for choice in ABSENCE_STATUS_CHOICES]

    intern = models.ForeignKey(
        Intern,
        on_delete=models.CASCADE,
        verbose_name='Студент',
        related_name='weekly_statuses',
        db_index=True,
    )
    week_start = models.DateField(
        verbose_name='Начало недели (понедельник)',
        db_index=True,
        help_text='Понедельник недели'
    )
    manual_interview_count = models.IntegerField(
        verbose_name='Ручное количество собесов',
        help_text='Если указано, используется вместо автоматического подсчёта',
        **NULLABLE
    )
    absence_status = models.CharField(
        max_length=20,
        verbose_name='Статус отсутствия',
        choices=ABSENCE_STATUS_CHOICES,
        help_text='Статус отсутствия на эту неделю',
        **NULLABLE
    )
    absence_notes = models.TextField(
        verbose_name='Комментарий к отсутствию',
        help_text='Дополнительная информация о причине отсутствия',
        **NULLABLE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'intern_weekly_statuses'
        verbose_name = 'Недельный статус студента'
        verbose_name_plural = 'Недельные статусы студентов'
        # Один студент может иметь только одну запись на конкретную неделю
        unique_together = [['intern', 'week_start']]
        ordering = ['-week_start', 'intern__full_name']

    def __str__(self):
        return f'{self.intern.full_name} - неделя {self.week_start.strftime("%d.%m.%Y")}'
