from django.db import models
import os

NULLABLE = {'blank': True, 'null': True}

# Определяем, используем ли мы тестовую среду
TESTING = os.environ.get('DJANGO_TESTING') == '1'

# Выбираем поле для вектора в зависимости от среды
if TESTING:
    # В тестах используем JSONField вместо VectorField (для SQLite)
    class EmbeddingField(models.JSONField):
        """Обёртка для тестов - использует JSONField для хранения массива float."""

        def __init__(self, *args, **kwargs):
            # Игнорируем dimensions для совместимости
            kwargs.pop('dimensions', None)
            # JSONField не принимает default=list напрямую, используем callable
            if 'default' not in kwargs:
                kwargs['default'] = list
            super().__init__(*args, **kwargs)
else:
    # В PostgreSQL поле — pgvector.
    from pgvector.django import VectorField as EmbeddingField


class VectorEmbedding(models.Model):
    """
    Базовая модель для хранения векторных эмбеддингов любых сущностей.

    Использует pgvector для эффективного поиска по векторам.
    Хранится в основной БД (default), таблица vector_embeddings.
    """

    # Тип сущности (interview, intern, offer, debt, etc.)
    entity_type = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name='Тип сущности',
        help_text='Тип объекта (interview, intern, offer, debt, manager, sad_intern)'
    )

    # ID сущности в основной БД
    entity_id = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='ID сущности',
        help_text='ID объекта в основной таблице (может быть числом или строкой для Manager)'
    )

    # Текстовое представление для поиска
    text_content = models.TextField(
        verbose_name='Текстовое содержимое',
        help_text='Текст, который был векторизован'
    )

    # Векторное представление (эмбеддинг)
    embedding = EmbeddingField(
        dimensions=1536,  # Фиксированное значение для совместимости с миграциями
        verbose_name='Вектор эмбеддинга',
        help_text='Вектор размерности 1536'
    )

    # Метаданные (JSON) для фильтрации
    metadata = models.JSONField(
        default=dict,
        verbose_name='Метаданные',
        help_text='Дополнительная информация для фильтрации (direction_id, manager_email, etc.)'
    )

    # Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        db_table = 'vector_embeddings'
        verbose_name = 'Векторный эмбеддинг'
        verbose_name_plural = 'Векторные эмбеддинги'
        # Уникальность: один эмбеддинг на одну сущность
        unique_together = [['entity_type', 'entity_id']]
        indexes = [
            models.Index(fields=['entity_type', 'entity_id'], name='vector_embe_entity__abbc2f_idx'),
            models.Index(fields=['created_at'], name='vector_embe_created_10ff8d_idx'),
        ]

    def __str__(self):
        return f'{self.entity_type}#{self.entity_id}'


class SearchLog(models.Model):
    """
    Логирование поисковых запросов для аналитики и улучшения.
    """

    query = models.TextField(
        verbose_name='Поисковый запрос'
    )

    entity_type = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name='Тип поиска',
        **NULLABLE
    )

    results_count = models.IntegerField(
        verbose_name='Количество результатов'
    )

    search_time_ms = models.FloatField(
        verbose_name='Время поиска (мс)',
        help_text='Время выполнения запроса в миллисекундах'
    )

    user_email = models.EmailField(
        verbose_name='Email пользователя',
        **NULLABLE
    )

    filters = models.JSONField(
        default=dict,
        verbose_name='Примененные фильтры'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата запроса'
    )

    class Meta:
        db_table = 'search_logs'
        verbose_name = 'Лог поиска'
        verbose_name_plural = 'Логи поиска'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.query[:50]} ({self.results_count} рез.)'
