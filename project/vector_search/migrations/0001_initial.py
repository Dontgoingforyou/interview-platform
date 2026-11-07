# Generated manually for vector_search initial models

from django.db import migrations, models, connection
import os


def get_embedding_field():
    """Возвращает правильное поле в зависимости от окружения."""
    # Проверяем, тестовая ли среда
    if os.environ.get('DJANGO_TESTING') == '1' or connection.vendor == 'sqlite':
        # В тестах используем JSONField
        return models.JSONField(
            default=list,
            help_text='Вектор размерности 1536',
            verbose_name='Вектор эмбеддинга'
        )
    else:
        # В продакшене используем ArrayField
        import django.contrib.postgres.fields
        return django.contrib.postgres.fields.ArrayField(
            base_field=models.FloatField(),
            help_text='Вектор размерности 1536',
            size=1536,
            verbose_name='Вектор эмбеддинга'
        )


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='VectorEmbedding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entity_type', models.CharField(db_index=True, help_text='Тип объекта (interview, intern, offer, debt, manager, sad_intern)', max_length=50, verbose_name='Тип сущности')),
                ('entity_id', models.IntegerField(db_index=True, help_text='ID объекта в основной таблице', verbose_name='ID сущности')),
                ('text_content', models.TextField(help_text='Текст, который был векторизован', verbose_name='Текстовое содержимое')),
                ('embedding', models.JSONField(default=list, help_text='Вектор размерности 1536', verbose_name='Вектор эмбеддинга')),
                ('metadata', models.JSONField(default=dict, help_text='Дополнительная информация для фильтрации (direction_id, manager_email, etc.)', verbose_name='Метаданные')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Векторный эмбеддинг',
                'verbose_name_plural': 'Векторные эмбеддинги',
                'db_table': 'vector_embeddings',
                'unique_together': {('entity_type', 'entity_id')},
            },
        ),
        migrations.CreateModel(
            name='SearchLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query', models.TextField(verbose_name='Поисковый запрос')),
                ('entity_type', models.CharField(blank=True, db_index=True, max_length=50, null=True, verbose_name='Тип поиска')),
                ('results_count', models.IntegerField(verbose_name='Количество результатов')),
                ('search_time_ms', models.FloatField(help_text='Время выполнения запроса в миллисекундах', verbose_name='Время поиска (мс)')),
                ('user_email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email пользователя')),
                ('filters', models.JSONField(default=dict, verbose_name='Примененные фильтры')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Дата запроса')),
            ],
            options={
                'verbose_name': 'Лог поиска',
                'verbose_name_plural': 'Логи поиска',
                'db_table': 'search_logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='vectorembedding',
            index=models.Index(fields=['entity_type', 'entity_id'], name='vector_embe_entity__abbc2f_idx'),
        ),
        migrations.AddIndex(
            model_name='vectorembedding',
            index=models.Index(fields=['created_at'], name='vector_embe_created_10ff8d_idx'),
        ),
    ]
