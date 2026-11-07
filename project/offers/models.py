from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.mixins import ExternalReferencesMixin

NULLABLE = {'blank': True, 'null': True}


class Offer(ExternalReferencesMixin, models.Model):
    """ Таблица управления офферами. """

    intern = models.ForeignKey(
        'interns.Intern',
        on_delete=models.CASCADE,
        verbose_name='Студент',
        related_name='offers',
        db_index=True,
    )
    direction = models.ForeignKey(
        'directions.Direction',
        on_delete=models.PROTECT,
        verbose_name='Направление',
        db_index=True,
        related_name='offers',
    )
    company = models.CharField(verbose_name='Компания', **NULLABLE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма в оффере', **NULLABLE)
    month = models.IntegerField(verbose_name='Месяц', db_index=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField(verbose_name='Год', db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'offers'
        ordering = ['-year', '-month', '-created_at']
        verbose_name = 'Оффер'
        verbose_name_plural = 'Офферы'
        indexes = [
            models.Index(fields=['year', 'month'], name='offers_year_month_idx'),
        ]

    def __str__(self):
        return f'{self.intern.full_name} - {self.company} ({self.amount})'
