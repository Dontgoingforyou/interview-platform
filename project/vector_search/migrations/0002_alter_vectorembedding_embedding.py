# Миграция для изменения типа поля embedding с double precision[] на vector

from django.db import migrations, connection
from pgvector.django import VectorField
from django.conf import settings


def create_vector_extension(apps, schema_editor):
    """Создаёт расширение pgvector только для PostgreSQL."""
    if connection.vendor == 'postgresql':
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def rename_embedding_column(apps, schema_editor):
    """Переименовывает колонку только для PostgreSQL."""
    if connection.vendor == 'postgresql':
        # Проверяем, не была ли колонка уже переименована
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name='vector_embeddings' AND column_name='embedding_old';
            """)
            if cursor.fetchone()[0] == 0:
                # Колонка embedding_old не существует, переименовываем
                schema_editor.execute("ALTER TABLE vector_embeddings RENAME COLUMN embedding TO embedding_old;")


def add_vector_column(apps, schema_editor):
    """Добавляет колонку vector только для PostgreSQL."""
    if connection.vendor == 'postgresql':
        # Проверяем, не была ли колонка уже добавлена
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name='vector_embeddings' AND column_name='embedding';
            """)
            result = cursor.fetchone()
            # Если колонка не существует или не является vector типом
            if result is None:
                schema_editor.execute("ALTER TABLE vector_embeddings ADD COLUMN embedding vector(1536);")


def copy_data(apps, schema_editor):
    """Копирует данные только для PostgreSQL."""
    if connection.vendor == 'postgresql':
        # Проверяем, есть ли данные в таблице
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM vector_embeddings;")
            count = cursor.fetchone()[0]

            if count > 0:
                # Преобразуем jsonb массив в текстовое представление, а затем в vector
                # jsonb_array_elements_text разворачивает массив JSON
                # string_agg собирает элементы обратно
                # '[' || ... || ']' формирует строку вида '[0.1,0.2,...]'
                # ::vector преобразует строку в тип vector
                schema_editor.execute("""
                    UPDATE vector_embeddings
                    SET embedding = (
                        SELECT ('['||string_agg(value::text, ',')||']')::vector
                        FROM jsonb_array_elements_text(embedding_old)
                    );
                """)


def set_not_null(apps, schema_editor):
    """Устанавливает NOT NULL только для PostgreSQL."""
    if connection.vendor == 'postgresql':
        schema_editor.execute("ALTER TABLE vector_embeddings ALTER COLUMN embedding SET NOT NULL;")


def drop_old_column(apps, schema_editor):
    """Удаляет старую колонку только для PostgreSQL."""
    if connection.vendor == 'postgresql':
        schema_editor.execute("ALTER TABLE vector_embeddings DROP COLUMN embedding_old;")


def create_hnsw_index(apps, schema_editor):
    """Создаёт HNSW индекс только для PostgreSQL."""
    if connection.vendor == 'postgresql':
        schema_editor.execute("""
            CREATE INDEX IF NOT EXISTS vector_embe_embedding_cosine_idx
            ON vector_embeddings
            USING hnsw (embedding vector_cosine_ops);
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('vector_search', '0001_initial'),
    ]

    operations = [
        # Шаг 1: Создаём расширение pgvector (только для PostgreSQL)
        migrations.RunPython(
            code=create_vector_extension,
            reverse_code=migrations.RunPython.noop
        ),

        # Шаг 2: Переименовываем старую колонку
        migrations.RunPython(
            code=rename_embedding_column,
            reverse_code=migrations.RunPython.noop
        ),

        # Шаг 3: Создаём новую колонку с типом vector
        migrations.RunPython(
            code=add_vector_column,
            reverse_code=migrations.RunPython.noop
        ),

        # Шаг 4: Копируем данные из старой колонки в новую
        migrations.RunPython(
            code=copy_data,
            reverse_code=migrations.RunPython.noop
        ),

        # Шаг 5: Делаем новую колонку NOT NULL
        migrations.RunPython(
            code=set_not_null,
            reverse_code=migrations.RunPython.noop
        ),

        # Шаг 6: Удаляем старую колонку
        migrations.RunPython(
            code=drop_old_column,
            reverse_code=migrations.RunPython.noop
        ),

        # Шаг 7: Создаём индекс HNSW для быстрого векторного поиска
        migrations.RunPython(
            code=create_hnsw_index,
            reverse_code=migrations.RunPython.noop
        ),
    ]
