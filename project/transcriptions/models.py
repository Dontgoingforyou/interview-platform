from django.db import models

NULLABLE = {'null': True, 'blank': True}


class TranscriptionStatus(models.TextChoices):
    PENDING = 'pending', 'Ожидает'
    PROCESSING = 'processing', 'В процессе'
    COMPLETED = 'completed', 'Завершена'
    FAILED = 'failed', 'Ошибка'


class InterviewTranscription(models.Model):
    interview = models.OneToOneField(
        'interviews.Interview',
        on_delete=models.CASCADE,
        related_name='transcription',
        verbose_name='Собеседование',
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=TranscriptionStatus.choices,
        default=TranscriptionStatus.PENDING,
        verbose_name='Статус',
        db_index=True,
    )
    text = models.TextField(verbose_name='Текст транскрипции', **NULLABLE)
    error_message = models.CharField(
        max_length=500,
        verbose_name='Сообщение об ошибке',
        **NULLABLE,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'interview_transcriptions'
        verbose_name = 'Транскрипция собеседования'
        verbose_name_plural = 'Транскрипции собеседований'
        ordering = ['-created_at']

    def __str__(self):
        return f'Транскрипция #{self.interview_id} [{self.get_status_display()}]'
