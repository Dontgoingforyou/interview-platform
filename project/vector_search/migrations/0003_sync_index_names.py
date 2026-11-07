# Миграция для синхронизации состояния модели с БД после изменения типа поля через SQL

from django.db import migrations
from pgvector.django import VectorField


class Migration(migrations.Migration):

    dependencies = [
        ('vector_search', '0002_alter_vectorembedding_embedding'),
    ]

    operations = [
        # Используем SeparateDatabaseAndState для синхронизации состояния без изменения БД
        # Поле embedding уже было изменено на vector(1536) в миграции 0002 через SQL
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='vectorembedding',
                    name='embedding',
                    field=VectorField(
                        dimensions=1536,  # Используем фиксированное значение
                        verbose_name='Вектор эмбеддинга',
                        help_text='Вектор размерности 1536'
                    ),
                ),
            ],
            database_operations=[
                # Ничего не делаем в БД - изменения уже применены в 0002
            ],
        ),
    ]
