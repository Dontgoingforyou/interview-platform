from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.mixins import ExternalReferencesMixin
from core.constants import (
    MAX_TELEGRAM_LENGTH,
    DEBT_PAYMENT_STATUS_SEARCHING,
    DEBT_PAYMENT_STATUS_PAYING,
    DEBT_PAYMENT_STATUS_UNKNOWN,
)

NULLABLE = {'blank': True, 'null': True}


class Debt(ExternalReferencesMixin, models.Model):
    """ Таблица долгов. """

    PAYMENT_STATUS_CHOICES = [
        (DEBT_PAYMENT_STATUS_SEARCHING, 'Снова ищем'),
        (DEBT_PAYMENT_STATUS_PAYING, 'Платит'),
        (DEBT_PAYMENT_STATUS_UNKNOWN, 'Без статуса'),
    ]

    direction = models.ForeignKey(
        'directions.Direction',
        on_delete=models.SET_NULL,
        verbose_name='Направление',
        db_index=True,
        **NULLABLE,
    )
    intern = models.ForeignKey(
        'interns.Intern',
        on_delete=models.CASCADE,
        related_name='debts',
        verbose_name='Студент',
        db_index=True,
    )
    telegram_username = models.CharField(max_length=MAX_TELEGRAM_LENGTH, verbose_name='@tg', **NULLABLE)
    email = models.EmailField(**NULLABLE)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False, validators=[MinValueValidator(0)], verbose_name='Общая сумма')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name='Уже заплатил')
    balance = models.DecimalField(
        max_digits=12, decimal_places=2, editable=False, verbose_name='Остаток', db_index=True
    )
    act_date = models.DateField(db_index=True, **NULLABLE, verbose_name='Дата акта')
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=DEBT_PAYMENT_STATUS_UNKNOWN,
        verbose_name='Статус',
        db_index=True,
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Долг'
        verbose_name_plural = 'Долги'
        db_table = 'debts'
        ordering = ['id']

    def __str__(self):
        return f"Долг: {self.intern.full_name} - {self.balance}"

    def save(self, *args, **kwargs):
        """ Метод автоматически вычисляет остаток перед сохранением. """
        self.balance = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)

    @property
    def last_payment_month_year(self):
        """ Возвращает (месяц, год) последнего платежа или (None, None). """

        last_record = self.payment_history.order_by('-year', '-month').first()
        if last_record:
            return last_record.month, last_record.year
        return None, None

    @property
    def last_three_payments(self):
        """ Возвращает последние 3 записи платежей. """
        return self.payment_history.order_by('-year', '-month')[:3]


class PaymentHistory(models.Model):
    """ Модель хранения истории платежей, включая последние 3 месяца. """

    debt = models.ForeignKey(
        Debt,
        related_name='payment_history',
        on_delete=models.CASCADE,
        verbose_name='Долг',
        db_index=True,
    )
    month = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], verbose_name='Месяц (1-12)')
    year = models.PositiveIntegerField(verbose_name='Год')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], verbose_name='Сумма платежа')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания записи')

    class Meta:
        verbose_name = 'Запись истории платежа'
        verbose_name_plural = 'История платежей'
        unique_together = ('debt', 'month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.debt.intern.full_name} - {self.month}/{self.year} - {self.amount}"
